"""JSON parsing and repair helpers for the ontology pipeline LLM calls."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


_PARSE_REPAIR_EVENTS: list[dict[str, Any]] = []


def _reset_parse_repair_events() -> None:
    _PARSE_REPAIR_EVENTS.clear()


def consume_parse_repair_events() -> list[dict[str, Any]]:
    events = list(_PARSE_REPAIR_EVENTS)
    _PARSE_REPAIR_EVENTS.clear()
    return events


def _record_parse_repair(strategy: str, original_error: str) -> None:
    event = {"strategy": strategy, "original_error": original_error}
    _PARSE_REPAIR_EVENTS.append(event)
    logger.warning("[ontology] JSON parse repaired via %s (original: %s)", strategy, original_error)


def _extract_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object from an LLM response with progressive repair fallbacks.

    Strategy ladder:
      1. Strict json.loads on the trimmed text.
      2. Substring between first '{' and last '}' (unchanged legacy behavior).
      3. json_repair library if available (best-effort semantic repair).
      4. Lightweight regex repair (strip trailing commas, add commas between
         adjacent closing/opening tokens).

    Each non-strict path records a parse_repair event consumable via
    consume_parse_repair_events() so run_metrics / supervisor_log can surface it.
    """
    raw = raw.strip()
    if not raw:
        raise json.JSONDecodeError("Empty LLM response", raw, 0)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as strict_err:
        original_error = str(strict_err)

        candidate = raw
        first_brace = raw.find("{")
        last_brace = raw.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            candidate = raw[first_brace : last_brace + 1]
            try:
                parsed = json.loads(candidate)
                _record_parse_repair("substring_extraction", original_error)
                return parsed
            except json.JSONDecodeError:
                pass

        try:
            from json_repair import repair_json  # type: ignore

            repaired = repair_json(candidate, return_objects=False)
            parsed = json.loads(repaired)
            if isinstance(parsed, dict):
                _record_parse_repair("json_repair_library", original_error)
                return parsed
        except ImportError:
            pass
        except (json.JSONDecodeError, ValueError):
            pass

        regex_repaired = _regex_repair_json(candidate)
        if regex_repaired is not None:
            try:
                parsed = json.loads(regex_repaired)
                if isinstance(parsed, dict):
                    _record_parse_repair("regex_repair", original_error)
                    return parsed
            except json.JSONDecodeError:
                pass

        raise strict_err


def _completion_hit_output_limit(
    *,
    usage: dict[str, Any],
    finish_reason: str | None,
    max_output_tokens: int,
) -> bool:
    completion_tokens = int((usage or {}).get("completion", 0) or 0)
    return str(finish_reason or "").lower() == "length" or completion_tokens >= int(max_output_tokens or 0)


class _JsonCompletionRetryExhausted(json.JSONDecodeError):
    def __init__(self, msg: str, doc: str, pos: int, *, usages: list[dict[str, Any]]):
        super().__init__(msg, doc, pos)
        self.usages = list(usages)


def _parse_json_completion_with_retry(
    *,
    phase_label: str,
    run_completion,
    initial_max_output_tokens: int,
    retry_max_output_tokens: int,
    empty_visible_output: set[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run a JSON-producing completion, retrying once when the visible output was truncated.

    Two failure signatures are retried with a larger completion budget:
    1. visible output is just an empty JSON object at the completion limit
    2. JSON parsing fails and the completion appears to have hit the output limit
    """
    empty_visible_output = empty_visible_output or {"{}"}

    def _parse_with_repair_tracking(payload: str) -> tuple[dict[str, Any], bool]:
        before = len(_PARSE_REPAIR_EVENTS)
        parsed = _extract_json_object(payload)
        return parsed, len(_PARSE_REPAIR_EVENTS) > before

    def _parse_retry_result(
        payload: str,
        retry_usage: dict[str, Any],
        retry_finish_reason: str | None,
        *,
        retried_max_output_tokens: int,
    ) -> tuple[dict[str, Any], bool]:
        parsed, repaired = _parse_with_repair_tracking(payload)
        retry_hit_limit = _completion_hit_output_limit(
            usage=retry_usage,
            finish_reason=retry_finish_reason,
            max_output_tokens=retried_max_output_tokens,
        )
        if retry_hit_limit and (payload.strip() in empty_visible_output or repaired):
            raise json.JSONDecodeError(
                "Retry output still appears truncated at the completion limit",
                payload,
                0,
            )
        return parsed, repaired

    raw, usage, finish_reason = run_completion(initial_max_output_tokens)
    usages = [usage]
    hit_limit = _completion_hit_output_limit(
        usage=usage,
        finish_reason=finish_reason,
        max_output_tokens=initial_max_output_tokens,
    )

    if raw.strip() in empty_visible_output and hit_limit and retry_max_output_tokens > initial_max_output_tokens:
        logger.warning(
            "[ontology] %s returned empty visible JSON at completion limit (%d tokens, finish_reason=%s); retrying once with max_output_tokens=%d",
            phase_label,
            initial_max_output_tokens,
            finish_reason or "unknown",
            retry_max_output_tokens,
        )
        raw, retry_usage, retry_finish_reason = run_completion(retry_max_output_tokens)
        usages.append(retry_usage)
        try:
            parsed, _ = _parse_retry_result(
                raw,
                retry_usage,
                retry_finish_reason,
                retried_max_output_tokens=retry_max_output_tokens,
            )
        except json.JSONDecodeError as exc:
            raise _JsonCompletionRetryExhausted(exc.msg, exc.doc, exc.pos, usages=usages) from exc
        return parsed, usages

    try:
        parsed, repaired = _parse_with_repair_tracking(raw)
    except json.JSONDecodeError:
        if not hit_limit or retry_max_output_tokens <= initial_max_output_tokens:
            raise
        logger.warning(
            "[ontology] %s JSON parse failed at completion limit (%d tokens, finish_reason=%s); retrying once with max_output_tokens=%d",
            phase_label,
            initial_max_output_tokens,
            finish_reason or "unknown",
            retry_max_output_tokens,
        )
        raw, retry_usage, retry_finish_reason = run_completion(retry_max_output_tokens)
        usages.append(retry_usage)
        try:
            parsed, _ = _parse_retry_result(
                raw,
                retry_usage,
                retry_finish_reason,
                retried_max_output_tokens=retry_max_output_tokens,
            )
        except json.JSONDecodeError as exc:
            raise _JsonCompletionRetryExhausted(exc.msg, exc.doc, exc.pos, usages=usages) from exc
        return parsed, usages

    if repaired and hit_limit and retry_max_output_tokens > initial_max_output_tokens:
        logger.warning(
            "[ontology] %s JSON required repair at completion limit (%d tokens, finish_reason=%s); retrying once with max_output_tokens=%d",
            phase_label,
            initial_max_output_tokens,
            finish_reason or "unknown",
            retry_max_output_tokens,
        )
        raw, retry_usage, retry_finish_reason = run_completion(retry_max_output_tokens)
        usages.append(retry_usage)
        try:
            parsed, _ = _parse_retry_result(
                raw,
                retry_usage,
                retry_finish_reason,
                retried_max_output_tokens=retry_max_output_tokens,
            )
        except json.JSONDecodeError as exc:
            raise _JsonCompletionRetryExhausted(exc.msg, exc.doc, exc.pos, usages=usages) from exc
        return parsed, usages

    return parsed, usages


def _regex_repair_json(text: str) -> str | None:
    """Best-effort regex repair for the most common LLM JSON mistakes."""
    if not text:
        return None
    repaired = re.sub(r",\s*([\]\}])", r"\1", text)
    repaired = re.sub(r"([\]\}\"])\s*\n\s*(?=[\"\{\[])", r"\1,\n", repaired)
    open_braces = repaired.count("{")
    close_braces = repaired.count("}")
    if open_braces > close_braces:
        repaired = repaired + ("}" * (open_braces - close_braces))
    open_brackets = repaired.count("[")
    close_brackets = repaired.count("]")
    if open_brackets > close_brackets:
        repaired = repaired + ("]" * (open_brackets - close_brackets))
    return repaired
