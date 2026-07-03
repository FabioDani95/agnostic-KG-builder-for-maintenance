from __future__ import annotations

import time
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.graph.state import GraphPhase
from backend.main import app
from backend.routers.upload import pdf_store
from backend.services.conversation import events as evt_bus
from tests.chat_event_fixtures import (
    KNOWN_EVENT_TYPES,
    KNOWN_WIDGET_TYPES,
    sample_chat_events,
    sample_extraction_graph,
    sample_triplet,
    sample_widget_payloads,
)


def _store(pdf_id: str) -> dict:
    return {
        "pdf_id": pdf_id,
        "filename": "characterization.pdf",
        "page_count": 5,
        "pages": [
            {"page_number": page_number, "text": f"Page {page_number}"}
            for page_number in range(1, 6)
        ],
        "source_type": "manual",
        "source_title": "Characterization Manual",
        "target_language": "en",
        "selected_models": {"scoping": None, "ontology_draft": None, "extraction": None},
        "cut_plan": {
            "total_pages": 5,
            "sections": [{"name": "Troubleshooting", "start": 2, "end": 4, "source": "llm"}],
            "pages_to_keep": [2, 3, 4],
            "page_offset": 0,
        },
        "graph_state": {
            "pdf_id": pdf_id,
            "run_id": "run-characterization",
            "current_phase": GraphPhase.SCOPING.value,
            "total_pages": 5,
            "selected_pages": [2, 3, 4],
            "phase_history": [],
            "selected_models": {"scoping": None, "ontology_draft": None, "extraction": None},
        },
        "conversation": {"messages": [], "tool_calls": [], "critiques": []},
    }


async def _fake_handle_message(pdf_id: str, store: dict, user_message=None, auto_start=False):
    on_event = evt_bus.make_on_event(pdf_id)
    on_event(evt_bus.chat_delta_event("Chat session started."))
    on_event(evt_bus.done_event())


async def _fake_dispatch(tool_name: str, args: dict, store: dict, on_event=None):
    payloads = sample_widget_payloads()
    if tool_name == "approve_cut_plan":
        store["graph_state"]["current_phase"] = GraphPhase.ONTOLOGY_DRAFT.value
        return {
            "status": "ok",
            "pages_approved": 3,
            "message": "Section selection approved - 3 pages will be processed.",
        }
    if tool_name == "draft_ontology":
        if on_event:
            on_event(evt_bus.critique_event("Ontology draft has an advisory issue.", "SYM-001", "Review it."))
        return {"widget": "ontology_review", **payloads["ontology_review"]}
    if tool_name == "run_extraction":
        store["graph_state"]["current_phase"] = GraphPhase.EXTRACTION.value
        store["graph_state"]["cleaned_triplets"] = [sample_triplet()]
        store["review_index"] = 0
        return {
            "status": "ok",
            "triplet_count": 1,
            "message": "Extraction complete - 1 triplet ready for review.",
            "graph": sample_extraction_graph(),
            "widget": "extraction_graph",
        }
    if tool_name == "get_next_triplet":
        triplets = store["graph_state"].get("cleaned_triplets") or []
        review_index = int(store.get("review_index") or 0)
        if review_index >= len(triplets):
            store["graph_state"]["current_phase"] = GraphPhase.EXPORT.value
            return {"widget": "export", **payloads["export"]}
        if on_event:
            on_event(evt_bus.critique_event("Triplet needs a quick logic check.", "SYM-001", "Confirm evidence."))
        return {"widget": "triplet", **payloads["triplet"]}
    if tool_name == "approve_triplet":
        store.setdefault("validated_triplets", []).append(sample_triplet())
        store["review_index"] = 1
        return {"widget": "extraction_graph", **payloads["extraction_graph"]}
    if tool_name == "export_ontology":
        store["graph_state"]["current_phase"] = GraphPhase.COMPLETED.value
        return {
            "widget": "export",
            "status": "ok",
            "exported": True,
            "output_path": "/tmp/characterization-ontology.json",
            "message": "Export complete.",
        }
    raise AssertionError(f"Unexpected tool call: {tool_name}")


def _drain_events(pdf_id: str, *, expected_done_count: int, timeout: float = 2.0) -> list[dict]:
    queue = evt_bus._queues[pdf_id]
    deadline = time.monotonic() + timeout
    events: list[dict] = []
    while time.monotonic() < deadline:
        while not queue.empty():
            events.append(queue.get_nowait())
        if sum(1 for event in events if event.get("type") == evt_bus.EVT_DONE) >= expected_done_count:
            return events
        time.sleep(0.01)
    return events


def test_chat_action_flow_characterizes_event_and_widget_contracts():
    pdf_id = "pdf-characterization"
    pdf_store[pdf_id] = _store(pdf_id)
    evt_bus.unregister(pdf_id)

    try:
        with patch("backend.routers.chat.handle_message", side_effect=_fake_handle_message), patch(
            "backend.services.conversation.tools.dispatch",
            side_effect=_fake_dispatch,
        ):
            with TestClient(app) as client:
                start = client.post(f"/chat/start/{pdf_id}", json={"target_language": "en"})
                assert start.status_code == 200
                events = _drain_events(pdf_id, expected_done_count=1)

                for action, payload, phase in [
                    ("approve_cut_plan", {}, GraphPhase.SCOPING.value),
                    ("run_extraction", {}, GraphPhase.ONTOLOGY_DRAFT.value),
                    ("approve_triplet", {"index": 0}, GraphPhase.EXTRACTION.value),
                    ("export_ontology", {}, GraphPhase.EXPORT.value),
                ]:
                    pdf_store[pdf_id]["graph_state"]["current_phase"] = phase
                    response = client.post(
                        "/chat/action",
                        json={
                            "pdf_id": pdf_id,
                            "action": action,
                            "payload": payload,
                            "client_action_id": f"client-{action}",
                        },
                    )
                    assert response.status_code == 200
                    assert response.json()["status"] == "ok"
                    events.extend(_drain_events(pdf_id, expected_done_count=1))

        event_types = {event.get("type") for event in events}
        widget_types = {
            event.get("widget")
            for event in events
            if event.get("type") == evt_bus.EVT_WIDGET
        }

        assert {evt_bus.EVT_PROGRESS, evt_bus.EVT_CHAT_DELTA, evt_bus.EVT_WIDGET, evt_bus.EVT_CRITIQUE, evt_bus.EVT_DONE} <= event_types
        assert {"ontology_review", "extraction_graph", "triplet", "export"} <= widget_types

        for event in events + sample_chat_events():
            assert event.get("type") in KNOWN_EVENT_TYPES
            if event.get("type") == evt_bus.EVT_WIDGET:
                assert event.get("widget") in KNOWN_WIDGET_TYPES
                assert isinstance(event.get("payload"), dict)

        for widget_type in KNOWN_WIDGET_TYPES:
            assert widget_type in sample_widget_payloads()
    finally:
        evt_bus.unregister(pdf_id)
        pdf_store.pop(pdf_id, None)
