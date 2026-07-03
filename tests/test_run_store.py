from __future__ import annotations

import json
from pathlib import Path

from backend.graph.state import GraphPhase
from backend.graph.store import seed_graph_state
from backend.runstore import RunStore, append_chat_event, append_human_action, clear_registry


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_run_store_writes_manifest_events_snapshots_and_export(tmp_path, monkeypatch):
    monkeypatch.setenv("KG_RUNS_DIR", str(tmp_path))
    clear_registry()
    input_pdf = tmp_path / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n")
    store = {
        "pdf_id": "pdf-run-store",
        "filename": "source.pdf",
        "pdf_path": str(input_pdf),
        "pages": [{"page_number": 1, "text": "Troubleshooting"}],
        "page_count": 1,
        "source_type": "manual",
        "source_title": "RunStore Manual",
        "selected_models": {"scoping": None, "ontology_draft": None, "extraction": None},
    }
    seed_graph_state(store, "pdf-run-store")

    run_dir = RunStore().create_run(store, input_path=input_pdf)
    append_chat_event("pdf-run-store", {"type": "progress", "phase": "scoping", "message": "Running"})
    append_human_action(
        "pdf-run-store",
        {"action": "approve_cut_plan", "payload": {}, "gate_result": {"allowed": True, "reason": ""}},
    )
    store["graph_state"]["current_phase"] = GraphPhase.SCOPING.value
    RunStore().snapshot(store)

    export_source = tmp_path / "ontology.json"
    metrics_source = tmp_path / "metrics.json"
    conversation_source = tmp_path / "conversation.json"
    export_source.write_text('{"nodes": {}}', encoding="utf-8")
    metrics_source.write_text('{"totals": {}}', encoding="utf-8")
    conversation_source.write_text('{"messages": []}', encoding="utf-8")
    store["ontology_path"] = str(export_source)
    store["metrics_path"] = str(metrics_source)
    RunStore().copy_export_artifacts(store)

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    events = _jsonl(run_dir / "events.jsonl")

    assert manifest["run_id"] == store["run_id"]
    assert (run_dir / "input" / "manual.pdf").exists()
    assert (run_dir / "pages.json").exists()
    assert [event["kind"] for event in events] == ["chat_event", "human_action"]
    assert (run_dir / "state_snapshots" / "loaded.json").exists()
    assert (run_dir / "state_snapshots" / "scoping.json").exists()
    assert (run_dir / "export" / "ontology.json").exists()
    assert (run_dir / "export" / "metrics.json").exists()
    assert (run_dir / "export" / "conversation.json").exists()


def test_append_survives_restart_by_rebuilding_registry_from_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("KG_RUNS_DIR", str(tmp_path))
    clear_registry()
    store = {
        "pdf_id": "pdf-restart",
        "run_id": "run-restart",
        "filename": "restart.pdf",
        "pages": [{"page_number": 1, "text": "Troubleshooting"}],
        "graph_state": {"pdf_id": "pdf-restart", "run_id": "run-restart", "current_phase": "loaded"},
    }
    run_dir = RunStore().create_run(store)

    # Simulate a process restart: the in-memory pdf→run registry is gone.
    clear_registry()

    append_chat_event("pdf-restart", {"type": "progress", "phase": "scoping", "message": "after restart"})
    events = _jsonl(run_dir / "events.jsonl")

    assert [event["kind"] for event in events] == ["chat_event"]
    assert events[0]["event"]["message"] == "after restart"
