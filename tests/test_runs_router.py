"""Tests for the HITL console run endpoints (backend/routers/runs.py)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("KG_RUNS_DIR", str(tmp_path))
    from backend.runstore.run_store import clear_registry
    clear_registry()
    from backend.main import create_app
    return TestClient(create_app())


def _make_run(tmp_path, run_id="run_abc123", created_at="2026-07-01T09:00:00Z"):
    run_dir = tmp_path / run_id
    (run_dir / "state_snapshots").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({
        "run_id": run_id,
        "pdf_id": "pdf-1",
        "filename": "manual.pdf",
        "created_at": created_at,
        "selected_models": {"scoping": "gpt-5.4-mini", "extraction": "gpt-5.4"},
    }), encoding="utf-8")
    (run_dir / "state_snapshots" / "validation.json").write_text(json.dumps({
        "run_id": run_id,
        "pdf_id": "pdf-1",
        "current_phase": "validation",
        "run_status": "needs_human_review",
        "operator": "FD",
        "selected_models": {"scoping": "gpt-5.4-mini", "extraction": "gpt-5.4"},
    }), encoding="utf-8")
    (run_dir / "trace.jsonl").write_text(json.dumps({
        "step": "scoping_metrics", "agent": "scoping_agent", "decision": "kept pages",
        "tokens": 1000, "cost": 0.5, "output_summary": {"duration_seconds": 12.0, "llm_calls": 2},
    }) + "\n", encoding="utf-8")
    return run_dir


def test_list_runs_sorted_and_tolerant(tmp_path, client):
    _make_run(tmp_path, "run_old", "2026-06-01T09:00:00Z")
    _make_run(tmp_path, "run_new", "2026-07-01T09:00:00Z")
    # Corrupt manifest must not break the listing.
    broken = tmp_path / "run_broken"
    broken.mkdir()
    (broken / "manifest.json").write_text("{not json", encoding="utf-8")

    res = client.get("/api/runs")
    assert res.status_code == 200
    runs = res.json()
    ids = [r["run_id"] for r in runs]
    assert ids[:2] == ["run_new", "run_old"]
    assert "run_broken" in ids
    top = runs[0]
    assert top["manual_filename"] == "manual.pdf"
    assert top["operator"] == "FD"
    assert top["run_status"] == "needs_human_review"
    assert top["last_phase"] == "validation"
    assert top["selected_extraction_model"] == "gpt-5.4"


def test_get_run_payload_and_metrics_fallback(tmp_path, client):
    _make_run(tmp_path)
    res = client.get("/api/runs/run_abc123")
    assert res.status_code == 200
    payload = res.json()
    assert payload["manifest"]["pdf_id"] == "pdf-1"
    assert payload["state"]["current_phase"] == "validation"
    assert len(payload["trace"]) == 1
    assert payload["is_live"] is False
    # Metrics recovered from trace.jsonl for persisted runs.
    metrics = payload["status"]["metrics"]
    assert metrics["duration_seconds"] == 12.0
    assert metrics["estimated_cost_usd"] == 0.5
    assert metrics["total_tokens"] == 1000


def test_get_run_404(client):
    assert client.get("/api/runs/run_missing").status_code == 404


def test_review_decisions_roundtrip(tmp_path, client):
    _make_run(tmp_path)
    body = {"kind": "low_confidence", "target_id": "fm_gear_wear", "target_type": "FailureMode", "verdict": "confirmed", "note": "checked on p.128"}
    res = client.post("/api/runs/run_abc123/review-decisions", json=body)
    assert res.status_code == 200

    res = client.get("/api/runs/run_abc123/review-decisions")
    decisions = res.json()
    assert len(decisions) == 1
    assert decisions[0]["decision"]["verdict"] == "confirmed"
    assert decisions[0]["decision"]["target_id"] == "fm_gear_wear"

    # Also embedded in the full run payload events.
    events = client.get("/api/runs/run_abc123").json()["events"]
    assert any(e.get("kind") == "review_decision" for e in events)


def test_review_decision_invalid_verdict(tmp_path, client):
    _make_run(tmp_path)
    res = client.post("/api/runs/run_abc123/review-decisions", json={"kind": "x", "target_id": "y", "verdict": "maybe"})
    assert res.status_code == 422
