from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.schemas.pipeline import PipelineStep


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_default(value: Any) -> str:
    return str(value)


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=_json_default)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _safe_count(value: Any) -> int:
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, (list, tuple, set)):
        return len(value)
    return 0


def compact_digest(value: Any, *, preview: int = 3) -> dict[str, Any]:
    """Return a compact non-verbatim digest suitable for trace files."""
    if value is None:
        return {"sha256": _stable_digest(None), "type": "none", "count": 0}
    if isinstance(value, dict):
        keys = sorted(str(key) for key in value.keys())
        return {
            "sha256": _stable_digest(value),
            "type": "dict",
            "count": len(keys),
            "keys": keys[:preview],
        }
    if isinstance(value, list):
        return {
            "sha256": _stable_digest(value),
            "type": "list",
            "count": len(value),
            "preview_types": [type(item).__name__ for item in value[:preview]],
        }
    return {
        "sha256": _stable_digest(value),
        "type": type(value).__name__,
        "count": _safe_count(value),
    }


def compact_summary(value: Any, *, preview: int = 3) -> Any:
    """Return a bounded summary without verbatim free text."""
    if isinstance(value, dict):
        keys = sorted(str(key) for key in value.keys())
        summary: dict[str, Any] = {
            "type": "dict",
            "count": len(keys),
            "sha256": _stable_digest(value),
        }
        for key in keys[:preview]:
            summary[key] = compact_summary(value.get(key), preview=preview)
        if len(keys) > preview:
            summary["omitted_keys"] = keys[preview:]
        return summary
    if isinstance(value, list):
        return {
            "type": "list",
            "count": len(value),
            "sha256": _stable_digest(value),
            "preview": [compact_summary(item, preview=preview) for item in value[:preview]],
        }
    if isinstance(value, tuple):
        return compact_summary(list(value), preview=preview)
    if isinstance(value, str):
        return {
            "type": "str",
            "length": len(value),
            "sha256": _stable_digest(value),
        }
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return {
        "type": type(value).__name__,
        "sha256": _stable_digest(value),
    }


def _confidence_from_details(details: dict[str, Any]) -> float | None:
    for key in ("confidence", "average_grounding_score", "coverage_score", "score"):
        if key not in details:
            continue
        try:
            return round(float(details[key]), 4)
        except (TypeError, ValueError):
            continue
    return None


def _is_handoff(details: dict[str, Any], decision: str = "") -> bool:
    if details.get("human_handoff") is True:
        return True
    if int(details.get("human_required_count", 0) or 0) > 0:
        return True
    if int(details.get("needs_human", 0) or 0) > 0:
        return True
    return "needs_human" in str(decision or "").lower()


def step_from_phase_entry(entry: dict[str, Any], *, state: dict[str, Any] | None = None) -> PipelineStep:
    details = deepcopy(entry.get("details") or {})
    stage_summary = {}
    if state:
        stage_summary = ((state.get("run_metrics") or {}).get("stages") or {}).get(entry.get("phase"), {})
    return PipelineStep(
        step=str(entry.get("phase") or "phase"),
        phase=str(entry.get("phase") or ""),
        agent=str(entry.get("agent") or ""),
        timestamp=entry.get("timestamp") or _utc_now(),
        input_digest=compact_digest({
            "selected_pages": (state or {}).get("selected_pages") if state else None,
            "current_phase": (state or {}).get("current_phase") if state else entry.get("phase"),
        }),
        output_summary=compact_summary(details),
        decision=str(entry.get("decision") or ""),
        confidence=_confidence_from_details(details),
        human_handoff=_is_handoff(details, str(entry.get("decision") or "")),
        retry_count=int(details.get("retry_count", 0) or 0),
        tokens=int(entry.get("tokens_used") or stage_summary.get("total_tokens") or 0),
        cost=float(stage_summary.get("estimated_cost_usd", 0.0) or 0.0),
    )


def trace_from_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    steps = [
        step_from_phase_entry(entry, state=state).model_dump(exclude_none=True)
        for entry in (state.get("phase_history") or [])
        if isinstance(entry, dict)
    ]
    for entry in state.get("supervisor_log") or []:
        if not isinstance(entry, dict):
            continue
        phase = str(entry.get("phase") or entry.get("phase_to") or entry.get("phase_from") or state.get("current_phase") or "")
        steps.append(PipelineStep(
            step="supervisor_decision",
            phase=phase,
            agent=str(entry.get("agent") or "Supervisor"),
            timestamp=entry.get("timestamp") or _utc_now(),
            input_digest=compact_digest({
                "current_phase": state.get("current_phase"),
                "phase_history_count": len(state.get("phase_history") or []),
            }),
            output_summary=compact_summary(entry),
            decision=str(entry.get("condition_met") or entry.get("decision") or entry.get("next_step") or ""),
            human_handoff=str(entry.get("next_step") or "").endswith("_review")
            or str(entry.get("run_status") or "") == "awaiting_operator",
        ).model_dump(exclude_none=True))
    return steps


class TraceRecorder:
    """Append-only writer for RunStore trace.jsonl."""

    def __init__(self, run_dir: str | Path):
        self.run_dir = Path(run_dir)

    def record(self, step: PipelineStep | dict[str, Any]) -> dict[str, Any]:
        model = step if isinstance(step, PipelineStep) else PipelineStep.model_validate(step)
        payload = model.model_dump(exclude_none=True)
        payload.setdefault("timestamp", _utc_now())
        path = self.run_dir / "trace.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, default=_json_default) + "\n")
        return payload


def record_trace_step(run_dir: str | Path, step: PipelineStep | dict[str, Any]) -> dict[str, Any]:
    return TraceRecorder(run_dir).record(step)
