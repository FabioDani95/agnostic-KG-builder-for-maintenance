from __future__ import annotations

import asyncio
from unittest.mock import patch

from backend.graph.state import GraphPhase
from backend.schemas.actions import HumanAction
from backend.services.conversation.actions import run_action


async def _fake_dispatch(tool_name: str, args: dict, store: dict, on_event=None):
    store.setdefault("called_tools", []).append((tool_name, args))
    if tool_name == "approve_cut_plan":
        return {"status": "ok", "message": "Cut plan approved."}
    if tool_name == "draft_ontology":
        return {
            "status": "ready",
            "widget": "ontology_review",
            "node_count": 1,
            "node_type_counts": {"Asset": 1},
            "human_required_fields": [],
            "review_queue": [],
        }
    raise AssertionError(f"Unexpected tool call: {tool_name}")


def test_run_action_chains_approve_cut_plan_to_draft_ontology_without_http():
    store = {
        "pdf_id": "pdf-actions",
        "pages": [{"page_number": 1}],
        "graph_state": {"current_phase": GraphPhase.SCOPING.value},
    }
    events: list[dict] = []

    async def run():
        with patch("backend.services.conversation.tools.dispatch", side_effect=_fake_dispatch):
            outcome = run_action(
                "pdf-actions",
                store,
                HumanAction(action="approve_cut_plan", payload={}, client_action_id="client-1"),
                events.append,
            )
            assert outcome.status == "ok"
            assert outcome.task is not None
            await outcome.task

    asyncio.run(run())

    assert store["called_tools"] == [("approve_cut_plan", {}), ("draft_ontology", {})]
    assert [event["type"] for event in events] == ["progress", "chat_delta", "chat_delta", "widget", "done"]
    assert events[0]["client_action_id"] == "client-1"
    assert events[3]["widget"] == "ontology_review"
    assert events[3]["payload"]["node_count"] == 1


def test_run_action_refuses_action_when_gate_blocks_it():
    store = {
        "pdf_id": "pdf-actions",
        "pages": [{"page_number": 1}],
        "graph_state": {"current_phase": GraphPhase.LOADED.value},
    }
    events: list[dict] = []

    outcome = run_action(
        "pdf-actions",
        store,
        HumanAction(action="approve_cut_plan", payload={}, client_action_id="client-2"),
        events.append,
    )

    assert outcome.status == "refused"
    assert outcome.reason
    assert outcome.task is None
    assert events[0]["type"] == "error"
    assert events[0]["client_action_id"] == "client-2"
