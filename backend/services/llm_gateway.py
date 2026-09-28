from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Any

from httpx import Timeout
from openai import AsyncOpenAI, OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

_BUDGET_LEDGERS: dict[tuple[str, str, str], Any] = {}
_BUDGET_LEDGERS_LOCK = threading.Lock()

def chat_temperature_kwargs(model_name: str | None, temperature: float) -> dict[str, float]:
    """Return temperature kwargs only for models that support custom values."""
    raw = str(model_name or settings.MODEL_NAME or "").strip().lower()
    if raw in {"gpt-5.5", "gpt-5.6", "gpt-6-luna", "gpt-6-sol"} or raw.startswith(("gpt-5.5-", "gpt-5.6-", "gpt-6-luna-", "gpt-6-sol-")):
        return {}
    return {"temperature": temperature}


_REASONING_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh", "max"}
_GPT_56_REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh", "max"}


def chat_reasoning_kwargs(
    model_name: str | None,
    reasoning_effort: str | None,
) -> dict[str, str]:
    """Return a validated Chat Completions reasoning setting when requested.

    Keeping this opt-in prevents legacy/non-reasoning models from receiving an
    unsupported parameter.  Current GPT-5.6 and GPT-6 Luna pipeline models accept the values
    below through the installed OpenAI SDK.
    """
    effort = str(reasoning_effort or "").strip().lower()
    if not effort:
        return {}
    model = str(model_name or settings.MODEL_NAME or "").strip().lower()
    if not (model in {"gpt-5.5", "gpt-5.6", "gpt-6-luna", "gpt-6-sol"} or model.startswith(("gpt-5.5-", "gpt-5.6-", "gpt-6-luna-", "gpt-6-sol-"))):
        return {}
    allowed_efforts = (
        _GPT_56_REASONING_EFFORTS
        if model in {"gpt-5.6", "gpt-6-luna", "gpt-6-sol"} or model.startswith(("gpt-5.6-", "gpt-6-luna-", "gpt-6-sol-"))
        else _REASONING_EFFORTS
    )
    if effort not in allowed_efforts:
        allowed = ", ".join(sorted(allowed_efforts))
        raise ValueError(f"Unsupported reasoning_effort '{reasoning_effort}'. Expected one of: {allowed}")
    return {"reasoning_effort": effort}


def get_client(
    *,
    timeout: Timeout | float | int | None = None,
    api_key: str | None = None,
    client_factory: Any = OpenAI,
    max_retries: int | None = None,
) -> Any:
    kwargs: dict[str, Any] = {
        "api_key": api_key if api_key is not None else settings.OPENAI_API_KEY,
        "timeout": timeout,
    }
    if str(os.environ.get("KG_REAL_CALL_BUDGET_LEDGER", "") or "").strip():
        # One durable reservation represents one actual provider attempt.
        # SDK-internal retries would otherwise escape per-attempt accounting.
        kwargs["max_retries"] = 0
    elif max_retries is not None:
        kwargs["max_retries"] = max(0, int(max_retries))
    return _with_real_call_budget(client_factory(**kwargs))


def get_async_client(
    *,
    timeout: Timeout | float | int | None = None,
    api_key: str | None = None,
    client_factory: Any = AsyncOpenAI,
    max_retries: int | None = None,
) -> Any:
    kwargs: dict[str, Any] = {
        "api_key": api_key if api_key is not None else settings.OPENAI_API_KEY,
        "timeout": timeout,
    }
    if str(os.environ.get("KG_REAL_CALL_BUDGET_LEDGER", "") or "").strip():
        kwargs["max_retries"] = 0
    elif max_retries is not None:
        kwargs["max_retries"] = max(0, int(max_retries))
    return _with_real_call_budget(client_factory(**kwargs), asynchronous=True)


def _configured_budget_ledger() -> Any | None:
    path = str(os.environ.get("KG_REAL_CALL_BUDGET_LEDGER", "") or "").strip()
    if not path:
        return None
    budget = str(os.environ.get("KG_REAL_CALL_BUDGET_USD", "") or "").strip()
    run_id = str(os.environ.get("KG_REAL_CALL_RUN_ID", "") or "").strip()
    pdf_id = str(os.environ.get("KG_REAL_CALL_PDF_ID", "") or "").strip()
    if not (budget and run_id and pdf_id):
        raise RuntimeError(
            "Real-call budget instrumentation requires BUDGET_USD, RUN_ID and PDF_ID"
        )
    ceiling = str(os.environ.get("KG_REAL_CALL_SPEND_CEILING_USD", "") or "").strip()
    key = (str(Path(path).resolve()), budget, ceiling)
    with _BUDGET_LEDGERS_LOCK:
        ledger = _BUDGET_LEDGERS.get(key)
        if ledger is None:
            from backend.services.real_call_budget_ledger import RealCallBudgetLedger

            ledger = RealCallBudgetLedger(key[0], absolute_budget_usd=budget, spend_ceiling_usd=ceiling or None)
            _BUDGET_LEDGERS[key] = ledger
    return ledger


def _structured_schema_characters(response_format: Any) -> int:
    if isinstance(response_format, dict):
        return len(json.dumps(response_format, ensure_ascii=False).encode("utf-8"))
    schema = getattr(response_format, "model_json_schema", None)
    if not callable(schema):
        return 0
    try:
        return len(json.dumps(schema(), sort_keys=True, ensure_ascii=False))
    except Exception:
        return 0


def _without_images(value: Any) -> tuple[Any, int]:
    """The request with image data left out, and how many images it carries."""

    if isinstance(value, dict):
        if value.get("type") == "image_url":
            return {"type": "image_url"}, 1
        items = {key: _without_images(item) for key, item in value.items()}
        return {key: item for key, (item, _) in items.items()}, sum(count for _, count in items.values())
    if isinstance(value, list):
        items = [_without_images(item) for item in value]
        return [item for item, _ in items], sum(count for _, count in items)
    return value, 0


def _real_call_envelope(kwargs: dict[str, Any]) -> Any:
    from backend.services.real_call_budget_ledger import TokenEnvelope

    serializable, images = _without_images({
        key: value
        for key, value in kwargs.items()
        if key not in {"response_format", "api_key"}
    })
    # An image is billed by its size in tiles, not by the length of its base64 text:
    # counting its characters overstated one flowchart call a hundredfold.
    image_tokens = images * max(0, int(os.environ.get("KG_REAL_CALL_IMAGE_TOKENS", "6000") or 6000))
    try:
        request_characters = len(
            json.dumps(serializable, ensure_ascii=False, default=str).encode("utf-8")
        )
    except Exception:
        request_characters = len(str(serializable).encode("utf-8"))
    schema_characters = _structured_schema_characters(kwargs.get("response_format"))
    fixed_overhead = max(
        0,
        int(os.environ.get("KG_REAL_CALL_FIXED_OVERHEAD_TOKENS", "4096") or 4096),
    )
    max_completion = int(
        kwargs.get("max_completion_tokens")
        or kwargs.get("max_tokens")
        or os.environ.get("KG_REAL_CALL_DEFAULT_MAX_COMPLETION_TOKENS", "16000")
        or 16000
    )
    # One UTF-8 byte per prompt token is a deliberately conservative upper
    # bound for the request plus strict response schema.  No cache credit is
    # assumed by the durable ledger.
    return TokenEnvelope(
        max_prompt_tokens=request_characters + image_tokens + schema_characters + fixed_overhead,
        max_completion_tokens=max(0, max_completion),
    )


def _real_call_stage(method: str, kwargs: dict[str, Any]) -> str:
    response_format = kwargs.get("response_format")
    format_name = str(getattr(response_format, "__name__", "") or "").strip()
    if isinstance(response_format, dict):
        format_name = str(response_format.get("json_schema", {}).get("name") or "")
    # Every V3 call names its structured response; the name is the stage.
    return f"chat.{method}:{format_name or 'unclassified'}"


def _actual_usage(response: Any) -> Any | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    from backend.services.real_call_budget_ledger import ActualTokenUsage

    prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage, "completion_tokens", 0) or 0)
    details = getattr(usage, "prompt_tokens_details", None)
    cached = int(getattr(details, "cached_tokens", 0) or 0) if details else 0
    cache_write = int(getattr(details, "cache_write_tokens", 0) or 0) if details else 0
    return ActualTokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        cached_prompt_tokens=min(prompt, cached),
        cache_write_prompt_tokens=min(max(0, prompt - cached), cache_write),
    )


def _reserve_real_call(method: str, kwargs: dict[str, Any]) -> Any | None:
    ledger = _configured_budget_ledger()
    if ledger is None:
        return None
    model = str(kwargs.get("model") or settings.MODEL_NAME or "").strip()
    reasoning = str(kwargs.get("reasoning_effort") or "default").strip()
    run_id = str(os.environ["KG_REAL_CALL_RUN_ID"])
    pdf_id = str(os.environ["KG_REAL_CALL_PDF_ID"])
    return ledger.call(
        call_id=f"{run_id}:{uuid.uuid4().hex}",
        stage=_real_call_stage(method, kwargs),
        run_id=run_id,
        pdf_id=pdf_id,
        model=model,
        reasoning_effort=reasoning,
        token_envelope=_real_call_envelope(kwargs),
    )


def _transport_request(wrapped, method, kwargs):
    from backend.services.llm_response_archive import response_format_for

    kwargs = dict(kwargs)
    kwargs.setdefault("service_tier", "default")
    schema = kwargs.get("response_format")
    if method == "parse" and isinstance(schema, type) and hasattr(schema, "model_json_schema") and hasattr(wrapped, "create"):
        kwargs["response_format"] = response_format_for(schema)
        return "create", kwargs, schema
    return method, kwargs, None


def _parse_archived_response(response, schema, archive, kwargs):
    if schema is None:
        setattr(response, "_kg_response_archive", str(archive.path))
        return response
    from openai.lib._parsing._completions import parse_chat_completion

    try:
        parsed = parse_chat_completion(response_format=schema, input_tools=kwargs.get("tools", []), chat_completion=response)
    except Exception as exc:
        archive.payload["local_validation"] = {"status": "failed", "error_type": type(exc).__name__}
        archive._write()
        setattr(exc, "completion", response)
        setattr(exc, "_kg_response_archive", str(archive.path))
        raise
    archive.payload["local_validation"] = {"status": "passed"}
    archive._write()
    setattr(parsed, "_kg_response_archive", str(archive.path))
    return parsed


class _BudgetedCompletions:
    def __init__(self, wrapped: Any):
        self._wrapped = wrapped

    def _call(self, method: str, kwargs: dict[str, Any]) -> Any:
        from backend.services.llm_response_archive import ResponseArchive

        provider_method, kwargs, local_schema = _transport_request(self._wrapped, method, kwargs)
        reservation = _reserve_real_call(method, kwargs)
        try:
            archive = ResponseArchive(kwargs, method=method, call_id=reservation.call_id if reservation else "")
        except Exception:
            if reservation is not None:
                reservation.mark_not_called(status="archive_failed_before_call")
            raise
        try:
            response = getattr(self._wrapped, provider_method)(**kwargs)
        except Exception as exc:
            if reservation is not None:
                completion = getattr(exc, "completion", None)
                usage = _actual_usage(completion) if completion is not None else None
                finalization = reservation.finalize(
                    status="failed_with_usage" if usage else "failed_unknown_cost",
                    usage=usage,
                )
                # Preserve the durable accounting outcome across SDK parse
                # exceptions.  The route-level metrics can then count the
                # provider attempt even when no ChatCompletion object is
                # exposed by the SDK.
                setattr(exc, "_kg_call_accounting", {
                    "call_id": finalization.call_id,
                    "status": finalization.status,
                    "model": str(kwargs.get("model") or settings.MODEL_NAME or ""),
                    "charged_cost_usd": float(finalization.charged_cost_usd),
                    "actual_cost_usd": (
                        float(finalization.actual_cost_usd)
                        if finalization.actual_cost_usd is not None
                        else None
                    ),
                    "usage_observed": usage is not None,
                })
            archive.finish(response=getattr(exc, "completion", None), error=exc)
            setattr(exc, "_kg_response_archive", str(archive.path))
            raise
        if reservation is not None:
            usage = _actual_usage(response)
            reservation.finalize(
                status="succeeded" if usage is not None else "succeeded_unknown_cost",
                usage=usage,
            )
        try:
            archive.finish(response=response)
        except Exception as exc:
            # The attempt is already charged. Expose usage even on disk failure.
            setattr(exc, "completion", response)
            raise
        return _parse_archived_response(response, local_schema, archive, kwargs)

    def create(self, **kwargs: Any) -> Any:
        return self._call("create", kwargs)

    def parse(self, **kwargs: Any) -> Any:
        return self._call("parse", kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _BudgetedAsyncCompletions(_BudgetedCompletions):
    async def _async_call(self, method: str, kwargs: dict[str, Any]) -> Any:
        from backend.services.llm_response_archive import ResponseArchive

        provider_method, kwargs, local_schema = _transport_request(self._wrapped, method, kwargs)
        reservation = _reserve_real_call(method, kwargs)
        try:
            archive = ResponseArchive(kwargs, method=method, call_id=reservation.call_id if reservation else "")
        except Exception:
            if reservation is not None:
                reservation.mark_not_called(status="archive_failed_before_call")
            raise
        try:
            response = await getattr(self._wrapped, provider_method)(**kwargs)
        except Exception as exc:
            if reservation is not None:
                completion = getattr(exc, "completion", None)
                usage = _actual_usage(completion) if completion is not None else None
                finalization = reservation.finalize(
                    status="failed_with_usage" if usage else "failed_unknown_cost",
                    usage=usage,
                )
                setattr(exc, "_kg_call_accounting", {
                    "call_id": finalization.call_id,
                    "status": finalization.status,
                    "model": str(kwargs.get("model") or settings.MODEL_NAME or ""),
                    "charged_cost_usd": float(finalization.charged_cost_usd),
                    "actual_cost_usd": (
                        float(finalization.actual_cost_usd)
                        if finalization.actual_cost_usd is not None
                        else None
                    ),
                    "usage_observed": usage is not None,
                })
            archive.finish(response=getattr(exc, "completion", None), error=exc)
            setattr(exc, "_kg_response_archive", str(archive.path))
            raise
        if reservation is not None:
            usage = _actual_usage(response)
            reservation.finalize(
                status="succeeded" if usage is not None else "succeeded_unknown_cost",
                usage=usage,
            )
        try:
            archive.finish(response=response)
        except Exception as exc:
            setattr(exc, "completion", response)
            raise
        return _parse_archived_response(response, local_schema, archive, kwargs)

    async def create(self, **kwargs: Any) -> Any:
        return await self._async_call("create", kwargs)

    async def parse(self, **kwargs: Any) -> Any:
        return await self._async_call("parse", kwargs)


class _BudgetedChat:
    def __init__(self, wrapped: Any, *, asynchronous: bool):
        self._wrapped = wrapped
        wrapper = _BudgetedAsyncCompletions if asynchronous else _BudgetedCompletions
        self.completions = wrapper(wrapped.completions)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _BudgetedClient:
    def __init__(self, wrapped: Any, *, asynchronous: bool):
        self._wrapped = wrapped
        self.chat = _BudgetedChat(wrapped.chat, asynchronous=asynchronous)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


def _with_real_call_budget(client: Any, *, asynchronous: bool = False) -> Any:
    # Validate configuration and the existing event stream before returning a
    # client that could reach the network.
    _configured_budget_ledger()
    return _BudgetedClient(client, asynchronous=asynchronous)
