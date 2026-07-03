from __future__ import annotations

from backend.graph.store import seed_graph_state
from backend.schemas.run_state import RunState


def test_run_state_validates_seeded_graph_state():
    store = {
        "pdf_id": "pdf-run-state",
        "filename": "manual.pdf",
        "page_count": 2,
        "pages": [{"page_number": 1, "text": "A"}, {"page_number": 2, "text": "B"}],
        "source_type": "",
        "source_title": "",
        "selected_models": {"scoping": None, "ontology_draft": None, "extraction": None},
    }

    graph_state = seed_graph_state(store, "pdf-run-state")
    run_state = RunState.model_validate(graph_state)

    assert run_state.pdf_id == "pdf-run-state"
    assert run_state.run_id.startswith("run_")
    assert run_state.current_phase == "loaded"
    assert run_state.config_snapshot["pipeline"]["mode"] == "multi_agent"
