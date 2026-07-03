from __future__ import annotations

import json
import subprocess
import sys

from backend.graph.store import seed_graph_state
from backend.runstore import RunStore, append_chat_event, append_human_action, append_trace_step, clear_registry


def _make_run(tmp_path, monkeypatch, pdf_id: str, *, triplets: int = 1):
    monkeypatch.setenv("KG_RUNS_DIR", str(tmp_path))
    clear_registry()
    store = {
        "pdf_id": pdf_id,
        "filename": f"{pdf_id}.pdf",
        "pages": [{"page_number": 1, "text": "Troubleshooting"}],
        "page_count": 1,
        "source_type": "manual",
        "source_title": "Replay Manual",
        "selected_models": {"scoping": None, "ontology_draft": None, "extraction": None},
    }
    seed_graph_state(store, pdf_id)
    store["graph_state"]["cleaned_triplets"] = [{"id": f"t-{idx}"} for idx in range(triplets)]
    store["graph_state"]["phase_history"].append({"phase": "scoping", "agent": "ScopingAgent"})
    run_dir = RunStore().create_run(store)
    RunStore().snapshot(store)
    append_chat_event(pdf_id, {"type": "progress", "phase": "scoping", "message": "Running"})
    append_human_action(pdf_id, {"action": "approve_cut_plan", "payload": {}})
    append_trace_step(pdf_id, {
        "step": "scoping",
        "phase": "scoping",
        "agent": "ScopingAgent",
        "decision": "selected 1 page",
    })
    return store, run_dir


def _run_script(*args: str):
    result = subprocess.run(
        [sys.executable, "scripts/replay_run.py", *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def test_replay_run_summary_events_state_and_diff(tmp_path, monkeypatch):
    store_a, run_a = _make_run(tmp_path, monkeypatch, "pdf-replay-a", triplets=1)
    _, run_b = _make_run(tmp_path, monkeypatch, "pdf-replay-b", triplets=2)

    summary = _run_script(str(run_a))
    events = _run_script(str(run_a), "--events", "--type", "progress")
    state = _run_script(str(run_a), "--state", "loaded")
    diff = _run_script(str(run_a), "--diff", str(run_b))

    assert summary["run_id"] == store_a["run_id"]
    assert summary["event_counts"] == {"chat_events": 1, "human_actions": 1, "trace_steps": 1}
    assert summary["trace_timeline"][0]["step"] == "scoping"
    assert events[0]["event"]["type"] == "progress"
    assert state["run_id"] == store_a["run_id"]
    assert diff["delta"]["triplets"] == 1
