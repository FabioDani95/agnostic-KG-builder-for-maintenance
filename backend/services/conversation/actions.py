"""Deterministic chat widget action service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable

from backend.observability.trace import compact_digest
from backend.schemas.actions import HumanAction
from backend.schemas.widgets import validate_widget_payload
from backend.runstore import append_human_action, append_trace_step
from backend.services.conversation import events as evt_bus
from backend.services.conversation.gate import check as gate_check

OnEvent = Callable[[dict[str, Any]], None]


@dataclass
class ActionOutcome:
    status: str
    reason: str = ""
    task: asyncio.Task | None = None


_CHAIN_ON_SUCCESS: dict[str, str] = {
    "approve_cut_plan": "draft_ontology",
    "run_extraction": "get_next_triplet",
    "approve_triplet": "get_next_triplet",
    "skip_triplet": "get_next_triplet",
}

_CHAIN_PREAMBLE: dict[str, str] = {
    "approve_cut_plan": "Section selection confirmed. Starting ontology draft now…",
    "run_extraction": "",
    "approve_triplet": "",
    "skip_triplet": "",
}


def run_action(
    pdf_id: str,
    store: dict[str, Any],
    action: HumanAction,
    on_event: OnEvent,
) -> ActionOutcome:
    """Validate and schedule a deterministic chat action.

    The router needs an immediate accepted/refused response, while accepted
    actions must continue to run in the background so SSE remains the delivery
    channel for progress and widgets.
    """
    tagged_on_event = _tag_client_action(on_event, action.client_action_id)
    ok, reason = gate_check(action.action, action.payload, store)
    recorded_action = action.model_copy(update={"gate_result": {"allowed": ok, "reason": reason}})
    append_human_action(pdf_id, recorded_action.model_dump())
    append_trace_step(pdf_id, {
        "step": "human_action",
        "phase": str((store.get("graph_state") or {}).get("current_phase") or ""),
        "agent": "Operator",
        "input_digest": compact_digest(action.payload),
        "output_summary": {
            "action": action.action,
            "client_action_id": action.client_action_id,
            "gate_result": {"allowed": ok, "reason": reason},
        },
        "decision": action.action,
        "human_handoff": True,
        "error": None if ok else reason,
    })
    if not ok:
        tagged_on_event(evt_bus.error_event(reason))
        return ActionOutcome(status="refused", reason=reason)

    task = asyncio.create_task(
        _run_accepted_action(
            pdf_id,
            store,
            action.action,
            action.payload,
            tagged_on_event,
        )
    )
    return ActionOutcome(status="ok", task=task)


def _tag_client_action(on_event: OnEvent, client_action_id: str | None) -> OnEvent:
    if not client_action_id:
        return on_event

    def _emit(event: dict[str, Any]) -> None:
        tagged = dict(event)
        tagged["client_action_id"] = client_action_id
        on_event(tagged)

    return _emit


async def _run_accepted_action(
    pdf_id: str,
    store: dict[str, Any],
    action: str,
    payload: dict[str, Any],
    on_event: OnEvent,
) -> None:
    from backend.services.conversation.tools import dispatch

    on_event(evt_bus.progress_event(action, f"Running {action.replace('_', ' ')}…"))
    result = await dispatch(action, payload, store, on_event)
    _emit_result(result, on_event)

    next_tool = _CHAIN_ON_SUCCESS.get(action)
    if next_tool and result.get("status") == "ok":
        preamble = _CHAIN_PREAMBLE.get(action, "")
        if preamble:
            on_event(evt_bus.chat_delta_event(preamble))
        next_result = await dispatch(next_tool, {}, store, on_event)
        _emit_result(next_result, on_event, include_triplet_review_start=True)

    on_event(evt_bus.done_event())


def _emit_result(
    result: dict[str, Any],
    on_event: OnEvent,
    *,
    include_triplet_review_start: bool = False,
) -> None:
    widget = result.get("widget")
    if widget and (include_triplet_review_start or widget not in ("triplet_review_start",)):
        payload = {key: value for key, value in result.items() if key != "widget"}
        validate_widget_payload({"widget": widget, **payload})
        on_event(evt_bus.widget_event(widget, payload))

    summary = result.get("message") or ""
    if summary:
        on_event(evt_bus.chat_delta_event(summary))
