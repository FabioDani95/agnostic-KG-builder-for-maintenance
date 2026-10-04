"""One adapter between the V3 stations and the model provider.

Every call goes through the budgeted, archived gateway client. Transport errors
are retried with backoff; a truncated answer raises ``TruncatedResponse`` so the
caller can split its input; JSON is decoded tolerantly.
"""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from pydantic import BaseModel

from backend.kg_v3.run_state import digest, stable_id

logger = logging.getLogger(__name__)
_CALL_ROLE = contextvars.ContextVar('kg_call_role', default='primary')

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class TruncatedResponse(RuntimeError):
    """The provider stopped at the output limit; retry with a smaller input."""


@dataclass
class UsageTotals:
    calls: int = 0
    failed_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    by_operation: dict[str, int] = field(default_factory=dict)

    def add(self, entry: dict[str, Any], operation: str) -> None:
        self.calls += 1
        self.prompt_tokens += int(entry.get("prompt", 0) or 0)
        self.completion_tokens += int(entry.get("completion", 0) or 0)
        self.estimated_cost_usd = round(self.estimated_cost_usd + float(entry.get("estimated_cost_usd", 0) or 0), 6)
        self.by_operation[operation] = self.by_operation.get(operation, 0) + 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "calls": self.calls, "failed_calls": self.failed_calls, "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens, "estimated_cost_usd": self.estimated_cost_usd,
            "by_operation": dict(sorted(self.by_operation.items())),
        }


def decode_json(text: str) -> dict[str, Any]:
    """Decode a JSON object, repairing small syntax damage instead of failing."""

    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        from json_repair import repair_json

        value = repair_json(text, return_objects=True)
    if not isinstance(value, dict):
        raise ValueError("the model did not return a JSON object")
    return value


def _transient(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status == 429 or status >= 500
    name = type(exc).__name__
    return name in {"APIConnectionError", "APITimeoutError", "Timeout", "ReadTimeout", "ConnectError", "TimeoutError"}


class ModelClient:
    """Strict structured calls with retries, usage totals and tolerant decoding."""

    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str | None = "low",
        timeout_seconds: float = 180,
        attempts: int = 3,
        backoff_seconds: float = 2.0,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        # Hard deadline per attempt: the transport timeout alone did not stop a call that
        # never returned (one campaign run waited three hours). A late call is a failed call.
        self.deadline_seconds = timeout_seconds + 30
        self.attempts = max(1, attempts)
        self.backoff_seconds = backoff_seconds
        self.usage = UsageTotals()
        self.call_records: list[dict[str, Any]] = []
        if client_factory is None:
            from backend.services.llm_gateway import get_async_client

            def client_factory() -> Any:
                return get_async_client(timeout=timeout_seconds)
        self._client = client_factory()

    async def json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        name: str,
        max_output_tokens: int = 8000,
        reasoning_effort: str | None = None,
        images: list[str] | None = None,
    ) -> dict[str, Any]:
        from backend.services.llm_gateway import chat_reasoning_kwargs
        from backend.services.model_pricing import usage_from_response

        content = ([{"type": "text", "text": user}] + [
            {"type": "image_url", "image_url": {"url": url, "detail": "high"}} for url in images]) if images else user
        response_format = {"type": "json_schema", "json_schema": {"name": name, "strict": True, "schema": schema}}
        effort = reasoning_effort if reasoning_effort is not None else self.reasoning_effort
        last_error: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                response = await asyncio.wait_for(self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
                    response_format=response_format,
                    max_completion_tokens=max_output_tokens,
                    **chat_reasoning_kwargs(self.model, effort),
                ), timeout=self.deadline_seconds)
            except Exception as exc:
                self.usage.failed_calls += 1
                last_error = exc
                if attempt < self.attempts and _transient(exc):
                    await asyncio.sleep(self.backoff_seconds * 2 ** (attempt - 1))
                    continue
                raise
            self.usage.add(usage_from_response(response, name), name)
            self.call_records.append({'call_id': stable_id('call', [name, system, user, schema, self.model, effort, images]),
                                      'operation': name, 'requested_model': self.model,
                                      'returned_model': getattr(response, 'model', None), 'reasoning_effort': effort,
                                      'request_fingerprint': digest([system, user, schema, self.model, effort, images]),
                                      'role': _CALL_ROLE.get(), 'usage': usage_from_response(response, name),
                                      'attempt': attempt, 'provider_request_id': getattr(response, '_request_id', None)})
            choice = response.choices[0]
            if str(getattr(choice, "finish_reason", "") or "") == "length":
                raise TruncatedResponse(f"{name}: output limit of {max_output_tokens} tokens reached")
            content = str(getattr(choice.message, "content", "") or "")
            if not content.strip():
                refusal = str(getattr(choice.message, "refusal", "") or "")
                raise ValueError(f"{name}: empty answer {refusal}".strip())
            return decode_json(content)
        raise RuntimeError(f"{name}: no answer") from last_error

    async def __call__(self, *, system: str, user: str, schema: type[SchemaT],
                       images: list[str] | None = None) -> SchemaT:
        from backend.services.llm_response_archive import response_format_for

        strict = response_format_for(schema)["json_schema"]["schema"]
        data = await self.json(system=system, user=user, schema=strict, name=schema.__name__,
                               max_output_tokens=4000, images=images)
        return schema.model_validate(data)


class RoleClient:
    """Reuse the primary gateway explicitly with a role-specific effort."""
    def __init__(self, primary, reasoning_effort, *, role='primary'):
        self.primary = primary
        self.role = role
        self.model = getattr(primary, 'model', '')
        self.reasoning_effort = reasoning_effort
        self.usage = primary.usage
        self.call_records = getattr(primary, "call_records", [])

    async def json(self, **kwargs):
        token = _CALL_ROLE.set(self.role)
        try:
            return await self.primary.json(**{**kwargs, 'reasoning_effort': self.reasoning_effort})
        finally:
            _CALL_ROLE.reset(token)


def call_metadata(client):
    records = getattr(client, 'call_records', [])
    return dict(records[-1]) if records else {}


def sum_usage(clients) -> dict[str, Any]:
    """Totals over distinct usage counters: role clients share the primary's."""
    unique = {id(c.usage): c.usage for c in clients if c is not None and hasattr(c, "usage")}
    return {key: sum(u.as_dict()[key] for u in unique.values()) for key in
            ("calls", "failed_calls", "prompt_tokens", "completion_tokens", "estimated_cost_usd")}


def usage_for_role(client, role: str) -> dict[str, Any]:
    totals = UsageTotals()
    for row in getattr(client, "call_records", []):
        if row.get("role") == role:
            totals.add(row.get("usage", {}), row["operation"])
    return totals.as_dict()
