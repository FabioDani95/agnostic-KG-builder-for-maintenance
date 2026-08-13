from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from httpx import Timeout
from openai import AsyncOpenAI, OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

_BUDGET_LEDGERS: dict[tuple[str, str], Any] = {}
_BUDGET_LEDGERS_LOCK = threading.Lock()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_MOCK_RESPONSES_DIR = ROOT_DIR / "tests" / "golden" / "mock_responses"


def llm_mode() -> str:
    return str(os.environ.get("KG_LLM_MODE", "real") or "real").strip().lower()


def is_mock_mode() -> bool:
    return llm_mode() == "mock"


def chat_temperature_kwargs(model_name: str | None, temperature: float) -> dict[str, float]:
    """Return temperature kwargs only for models that support custom values."""
    raw = str(model_name or settings.MODEL_NAME or "").strip().lower()
    if raw in {"gpt-5.5", "gpt-5.6"} or raw.startswith(("gpt-5.5-", "gpt-5.6-")):
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
    unsupported parameter.  Current GPT-5.6 pipeline models accept all values
    below through the installed OpenAI SDK.
    """
    effort = str(reasoning_effort or "").strip().lower()
    if not effort:
        return {}
    model = str(model_name or settings.MODEL_NAME or "").strip().lower()
    if not (model in {"gpt-5.5", "gpt-5.6"} or model.startswith(("gpt-5.5-", "gpt-5.6-"))):
        return {}
    allowed_efforts = (
        _GPT_56_REASONING_EFFORTS
        if model == "gpt-5.6" or model.startswith("gpt-5.6-")
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
    if is_mock_mode():
        return MockOpenAI()
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
    if is_mock_mode():
        return MockAsyncOpenAI()
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
    key = (str(Path(path).resolve()), budget)
    with _BUDGET_LEDGERS_LOCK:
        ledger = _BUDGET_LEDGERS.get(key)
        if ledger is None:
            from backend.services.real_call_budget_ledger import RealCallBudgetLedger

            ledger = RealCallBudgetLedger(key[0], absolute_budget_usd=budget)
            _BUDGET_LEDGERS[key] = ledger
    return ledger


def _structured_schema_characters(response_format: Any) -> int:
    schema = getattr(response_format, "model_json_schema", None)
    if not callable(schema):
        return 0
    try:
        return len(json.dumps(schema(), sort_keys=True, ensure_ascii=False))
    except Exception:
        return 0


def _real_call_envelope(kwargs: dict[str, Any]) -> Any:
    from backend.services.real_call_budget_ledger import TokenEnvelope

    serializable = {
        key: value
        for key, value in kwargs.items()
        if key not in {"response_format", "api_key"}
    }
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
        max_prompt_tokens=request_characters + schema_characters + fixed_overhead,
        max_completion_tokens=max(0, max_completion),
    )


def _real_call_stage(method: str, kwargs: dict[str, Any]) -> str:
    response_format = kwargs.get("response_format")
    format_name = str(getattr(response_format, "__name__", "") or "").strip()
    if format_name:
        return f"chat.{method}:{format_name}"
    messages = _messages_text(kwargs).casefold()
    if "relation extraction agent" in messages:
        return f"chat.{method}:relation_extraction"
    if "semantic" in messages and "validation" in messages:
        return f"chat.{method}:semantic_validation"
    if (
        "ontology extraction agent" in messages
        or "ontology instance" in messages
        or "ontology schema" in messages
    ):
        return f"chat.{method}:ontology"
    if "table of contents" in messages or "toc_entries" in messages:
        return f"chat.{method}:scoping"
    return f"chat.{method}:unclassified"


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


class _BudgetedCompletions:
    def __init__(self, wrapped: Any):
        self._wrapped = wrapped

    def _call(self, method: str, kwargs: dict[str, Any]) -> Any:
        reservation = _reserve_real_call(method, kwargs)
        try:
            response = getattr(self._wrapped, method)(**kwargs)
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
            raise
        if reservation is not None:
            usage = _actual_usage(response)
            reservation.finalize(
                status="succeeded" if usage is not None else "succeeded_unknown_cost",
                usage=usage,
            )
        return response

    def create(self, **kwargs: Any) -> Any:
        return self._call("create", kwargs)

    def parse(self, **kwargs: Any) -> Any:
        return self._call("parse", kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _BudgetedAsyncCompletions(_BudgetedCompletions):
    async def _async_call(self, method: str, kwargs: dict[str, Any]) -> Any:
        reservation = _reserve_real_call(method, kwargs)
        try:
            response = await getattr(self._wrapped, method)(**kwargs)
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
            raise
        if reservation is not None:
            usage = _actual_usage(response)
            reservation.finalize(
                status="succeeded" if usage is not None else "succeeded_unknown_cost",
                usage=usage,
            )
        return response

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
    if not str(os.environ.get("KG_REAL_CALL_BUDGET_LEDGER", "") or "").strip():
        return client
    # Validate configuration and the existing event stream before returning a
    # client that could reach the network.
    _configured_budget_ledger()
    return _BudgetedClient(client, asynchronous=asynchronous)


class _MockUsage:
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    prompt_tokens_details = SimpleNamespace(
        cached_tokens=0,
        cache_write_tokens=0,
    )


class _MockMessage:
    def __init__(
        self,
        content: str,
        tool_calls: list[Any] | None = None,
        *,
        parsed: Any = None,
        refusal: str | None = None,
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.parsed = parsed
        self.refusal = refusal


class _MockChoice:
    def __init__(
        self,
        content: str,
        *,
        finish_reason: str = "stop",
        tool_calls: list[Any] | None = None,
        parsed: Any = None,
        refusal: str | None = None,
    ):
        self.finish_reason = finish_reason
        self.message = _MockMessage(
            content,
            tool_calls=tool_calls,
            parsed=parsed,
            refusal=refusal,
        )


class _MockResponse:
    def __init__(self, content: str, *, model: str, parsed: Any = None):
        self.id = "chatcmpl-mock"
        self.model = model
        self.usage = _MockUsage()
        self.choices = [_MockChoice(content, parsed=parsed, refusal=None)]


def _structured_mock_stage(response_format: Any) -> str | None:
    """Resolve a fixture stage from a Pydantic response model without importing it."""
    format_name = str(getattr(response_format, "__name__", "") or "").strip().lower()
    return {
        "diagnosticchunkoutput": "diagnostic_bundles",
        "coveragecompletionoutput": "coverage",
        "resolutioncompletionoutput": "resolution",
    }.get(format_name)


def _mock_parsed_response(kwargs: dict[str, Any]) -> _MockResponse:
    response_format = kwargs.get("response_format")
    validator = getattr(response_format, "model_validate_json", None)
    if not callable(validator):
        raise TypeError(
            "Mock chat.completions.parse requires a Pydantic response_format "
            "with model_validate_json()."
        )

    stage = _structured_mock_stage(response_format)
    content = _fixture_mock_content(stage) if stage else None
    if content is None and stage == "diagnostic_bundles":
        content = json.dumps({
            "schema_version": "1.0",
            "source_language": "en",
            "records": [],
        })
    if content is None:
        content = _mock_content(kwargs)
    parsed = validator(content)
    model = str(kwargs.get("model") or settings.MODEL_NAME)
    return _MockResponse(content, model=model, parsed=parsed)


class _MockCompletions:
    def create(self, **kwargs: Any) -> _MockResponse:
        model = str(kwargs.get("model") or settings.MODEL_NAME)
        return _MockResponse(_mock_content(kwargs), model=model)

    def parse(self, **kwargs: Any) -> _MockResponse:
        return _mock_parsed_response(kwargs)


class _MockAsyncCompletions:
    async def create(self, **kwargs: Any) -> _MockResponse:
        model = str(kwargs.get("model") or settings.MODEL_NAME)
        return _MockResponse(_mock_content(kwargs), model=model)

    async def parse(self, **kwargs: Any) -> _MockResponse:
        return _mock_parsed_response(kwargs)


class MockOpenAI:
    def __init__(self, *args: Any, **kwargs: Any):
        self.chat = SimpleNamespace(completions=_MockCompletions())


class MockAsyncOpenAI:
    def __init__(self, *args: Any, **kwargs: Any):
        self.chat = SimpleNamespace(completions=_MockAsyncCompletions())


def _messages_text(kwargs: dict[str, Any]) -> str:
    parts: list[str] = []
    for message in kwargs.get("messages") or []:
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
        if isinstance(content, str):
            parts.append(content)
    return "\n\n".join(parts)


def _fixture_mock_content(stage: str) -> str | None:
    """Return the fixture-specific mock response for `stage`, if configured.

    `KG_LLM_FIXTURE` selects a directory under tests/golden/mock_responses/
    (overridable via `KG_LLM_MOCK_DIR`). A `<stage>.json` holding only a
    "content" key is returned as raw text; any other JSON payload is dumped
    verbatim, matching what the real model would emit for that stage.
    """
    fixture_id = str(os.environ.get("KG_LLM_FIXTURE", "") or "").strip()
    if not fixture_id or not stage:
        return None
    base = str(os.environ.get("KG_LLM_MOCK_DIR", "") or "").strip()
    base_dir = Path(base) if base else DEFAULT_MOCK_RESPONSES_DIR
    if not base_dir.is_absolute():
        base_dir = ROOT_DIR / base_dir
    path = base_dir / fixture_id / f"{stage}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Unreadable mock fixture response: %s", path)
        return None
    if isinstance(payload, dict) and set(payload.keys()) == {"content"}:
        return str(payload["content"])
    return json.dumps(payload)


def _mock_content(kwargs: dict[str, Any]) -> str:
    text = _messages_text(kwargs)
    lower = text.lower()
    if kwargs.get("tools"):
        return "Mock assistant response."
    stage, generic = _stage_mock_content(lower, text)
    if stage:
        fixture_content = _fixture_mock_content(stage)
        if fixture_content is not None:
            return fixture_content
    return generic


def _stage_mock_content(lower: str, text: str) -> tuple[str | None, str]:
    """Detect the pipeline stage from the prompt and return (stage, generic reply)."""
    if "toc_entries" in lower or "table of contents" in lower:
        return "scoping", json.dumps({
            "product_info": {
                "product_name": "Mock Maintenance Manual",
                "product_short_name": "mock_manual",
                "brand": "Mock",
                "model": "M-1",
                "asset_type": "machine",
                "document_type": "maintenance manual",
                "language": "en",
            },
            "toc_entries": [
                {"title": "Troubleshooting", "page": 1},
                {"title": "Corrective Actions", "page": 2},
            ],
        })
    if "manual_page_start" in lower or '"sections"' in lower or "section selection" in lower:
        return "sections", json.dumps({
            "sections": [
                {
                    "name": "Troubleshooting",
                    "manual_page_start": 1,
                    "manual_page_end": 2,
                    "reasoning": "Mock diagnostic section.",
                }
            ]
        })
    if "exactly three markdown tables" in lower or "output only the three tables" in lower:
        return "extraction", _mock_extraction_tables()
    if "return the same keys" in lower or "stylistically normalized" in lower:
        return None, _echo_json_object(text)
    if "translate" in lower or "translating" in lower:
        return None, _echo_json_object(text)
    if "issues" in lower and ("semantic" in lower or "validation" in lower):
        return "validation", json.dumps({"issues": []})
    if "normalize an ontology node" in lower:
        return "node_normalization", json.dumps({"name": "Mock Node", "description": "Mock normalized node."})
    if "relation extraction agent" in lower:
        # Must win over the generic ontology branch: this stage merges its
        # output after asset-id canonicalisation, so echoing a full ontology
        # here would reintroduce unmapped node ids.
        return "relations", json.dumps({"relations": []})
    if "missing_chains" in lower:
        # Coverage completion: must also win over the generic ontology branch.
        # The deterministic mock baseline declares full coverage; a fixture can
        # override via mock_responses/<fixture>/coverage.json.
        return "coverage", json.dumps({"missing_chains": []})
    if "complete missing troubleshooting resolution links" in lower:
        # Resolution completion prompts contain both "ontology" and "nodes",
        # so this specific stage must win over the generic ontology branch.
        return "resolution", json.dumps({
            "status": "not_found",
            "failure_mode": {},
            "corrective_actions": [],
        })
    if "ontology" in lower or "nodes" in lower:
        return "ontology", json.dumps(_mock_ontology())
    if "relations" in lower and ("relation" in lower or "candidate" in lower):
        return "relations", json.dumps({"relations": []})
    return None, "Mock assistant response."


def _echo_json_object(text: str) -> str:
    start = text.rfind("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return json.dumps({str(key): str(value) for key, value in parsed.items()})
        except Exception:
            pass
    return "{}"


def _mock_extraction_tables() -> str:
    return "\n\n".join([
        "| symptom_id | name | description | severity | evidence_page |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| SYM-001 | Low Flow | Pump flow is below target. | Medium | 1 |",
        "| failure_mode_id | name | description | material_context | linked_symptom_id | evidence_page |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| FM-001 | Clogged Filter | The inlet filter is clogged. | Hydraulic circuit | SYM-001 | 1 |",
        "| action_id | name | description | instruction_text | source_page | linked_failure_mode_id |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| CA-001 | Clean Filter | Clean or replace the inlet filter. | Stop the pump and clean the filter. | 2 | FM-001 |",
    ])


def _mock_ontology() -> dict[str, Any]:
    return {
        "ontology_name": "MockMaintenanceOntology",
        "version": "1.0",
        "language": "en",
        "source_type": "maintenance manual",
        "source_title": "Mock Maintenance Manual",
        "nodes": {
            "Asset": [
                {
                    "asset_id": "ASSET-001",
                    "name": "Mock Machine",
                    "description": "Machine covered by the mock manual.",
                    "brand": "Mock",
                    "model": "M-1",
                    "asset_type": "machine",
                }
            ],
            "Component": [
                {
                    "component_id": "CMP-001",
                    "name": "Inlet Filter",
                    "description": "Filter on the inlet circuit.",
                    "category": "Hydraulic",
                }
            ],
            "Symptom": [
                {
                    "symptom_id": "SYM-001",
                    "name": "Low Flow",
                    "description": "Pump flow is below target.",
                    "severity": "Medium",
                    "evidence_page": 1,
                }
            ],
            "FailureMode": [
                {
                    "failure_mode_id": "FM-001",
                    "name": "Clogged Filter",
                    "description": "The inlet filter is clogged.",
                    "material_context": "Hydraulic circuit",
                    "linked_symptom_id": "SYM-001",
                    "evidence_page": 1,
                }
            ],
            "CorrectiveAction": [
                {
                    "action_id": "CA-001",
                    "name": "Clean Filter",
                    "description": "Clean or replace the inlet filter.",
                    "instruction_text": "Stop the pump and clean the filter.",
                    "source_type": "maintenance manual",
                    "source_title": "Mock Maintenance Manual",
                    "source_reference": "PAGE 2",
                    "linked_failure_mode_id": "FM-001",
                }
            ],
            "ErrorCode": [],
        },
        "relations": [
            {
                "name": "MAY_INDICATE",
                "from_type": "Symptom",
                "from_id": "SYM-001",
                "to_type": "FailureMode",
                "to_id": "FM-001",
                "evidence": [{"source_page": 1, "source_reference": "", "quote": ""}],
            },
            {
                "name": "RESOLVED_BY",
                "from_type": "FailureMode",
                "from_id": "FM-001",
                "to_type": "CorrectiveAction",
                "to_id": "CA-001",
                "evidence": [{"source_page": 2, "source_reference": "", "quote": ""}],
            },
        ],
    }
