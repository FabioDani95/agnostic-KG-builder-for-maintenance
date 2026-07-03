from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.graph.state import GraphPhase
from backend.graph.store import append_supervisor_log, seed_graph_state, update_scoping_state
from backend.main import app
from backend.models import CutPlan, PageRange, SectionInfo
from backend.routers.upload import pdf_store
from backend.runstore import RunStore, append_trace_step, clear_registry
from backend.services.run_metrics import record_stage_metrics


client = TestClient(app)


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_trace_recorder_writes_phase_metrics_and_supervisor_steps(tmp_path, monkeypatch):
    monkeypatch.setenv("KG_RUNS_DIR", str(tmp_path))
    clear_registry()
    store = {
        "pdf_id": "pdf-trace",
        "filename": "trace.pdf",
        "pages": [{"page_number": 1, "text": "Do not persist full manual text in trace."}],
        "page_count": 1,
        "selected_models": {"scoping": "mock", "ontology_draft": "mock", "extraction": "mock"},
    }
    seed_graph_state(store, "pdf-trace")
    run_dir = RunStore().create_run(store)

    record_stage_metrics(store, "scoping", {
        "stage": "scoping",
        "duration_seconds": 1.25,
        "llm_calls": 1,
        "prompt_tokens": 7,
        "completion_tokens": 5,
        "total_tokens": 12,
        "estimated_cost_usd": 0.001,
        "operations": ["scoping"],
        "details": {"total_pages": 1, "selected_pages": 1},
    })
    cut_plan = CutPlan(
        pdf_id="pdf-trace",
        total_pages=1,
        sections=[SectionInfo(name="Troubleshooting", page_range=PageRange(start=1, end=1), source="toc")],
        pages_to_keep=[1],
        page_offset=0,
    )
    update_scoping_state(store, cut_plan, model_name="mock")
    append_supervisor_log(
        store,
        {
            "timestamp": "2026-07-03T12:00:00Z",
            "phase": GraphPhase.SCOPING.value,
            "condition_met": "cut_plan_requires_review",
            "next_step": "cut_plan_review",
        },
        run_status="awaiting_operator",
        next_step="cut_plan_review",
    )

    trace = _jsonl(run_dir / "trace.jsonl")
    assert [step["step"] for step in trace] == ["scoping_metrics", "scoping", "supervisor_decision"]
    assert trace[0]["tokens"] == 12
    assert trace[0]["cost"] == 0.001
    assert trace[1]["decision"] == "selected 1 pages"
    assert trace[1]["input_digest"]["type"] == "dict"
    assert "Do not persist full manual text" not in json.dumps(trace, ensure_ascii=False)
    assert trace[2]["human_handoff"] is True


def test_multi_agent_audit_reads_persisted_trace_when_run_is_not_in_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("KG_RUNS_DIR", str(tmp_path))
    clear_registry()
    pdf_store.clear()
    store = {
        "pdf_id": "pdf-trace-audit",
        "filename": "trace-audit.pdf",
        "pages": [{"page_number": 1, "text": "Troubleshooting"}],
        "page_count": 1,
        "selected_models": {"scoping": "mock", "ontology_draft": "mock", "extraction": "mock"},
    }
    seed_graph_state(store, "pdf-trace-audit")
    run_dir = RunStore().create_run(store)
    append_trace_step("pdf-trace-audit", {
        "step": "scoping",
        "phase": "scoping",
        "agent": "ScopingAgent",
        "decision": "selected 1 pages",
        "tokens": 3,
        "cost": 0.0001,
    })
    store["graph_state"]["current_phase"] = "scoping"
    store["graph_state"]["phase_history"].append({
        "phase": "scoping",
        "agent": "ScopingAgent",
        "timestamp": "2026-07-03T12:00:00Z",
        "decision": "selected 1 pages",
    })
    RunStore().snapshot(store)
    pdf_store.clear()

    response = client.get(f"/multi-agent/audit/{store['run_id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == store["run_id"]
    assert payload["pipeline_trace"][0]["step"] == "scoping"
    assert payload["pipeline_trace"][0]["tokens"] == 3
    assert (run_dir / "trace.jsonl").exists()
