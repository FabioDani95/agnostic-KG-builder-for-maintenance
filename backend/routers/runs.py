"""Run/session listing and review-decision endpoints for the HITL console.

The RunStore already persists every run under ``data/runs/<run_id>/``
(manifest.json, pages.json, trace.jsonl, events.jsonl, state_snapshots/…).
These endpoints expose that persisted history so the console can list past
sessions, reopen one, and record per-element review verdicts in the same
audit trail (events.jsonl).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.graph.projections import build_status_payload
from backend.graph.store import find_store_by_run_id
from backend.routers.upload import pdf_store
from backend.runstore import RunStore

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _read_json(path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _live_store_for(run_id: str) -> dict[str, Any] | None:
    return find_store_by_run_id(pdf_store, run_id)


def _run_summary(store: RunStore, run_id: str) -> dict[str, Any] | None:
    run_dir = store.run_dir(run_id)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = _read_json(manifest_path)
    except Exception:
        # Corrupt manifest: surface the directory instead of failing the list.
        manifest = {}

    live = _live_store_for(run_id)
    if live is not None:
        state = live.get("graph_state") or {}
    else:
        try:
            state = store.latest_snapshot(run_id)
        except Exception:
            state = {}

    selected_models = state.get("selected_models") or manifest.get("selected_models") or {}
    return {
        "run_id": manifest.get("run_id") or run_id,
        "pdf_id": manifest.get("pdf_id") or state.get("pdf_id") or "",
        "manual_filename": manifest.get("filename") or state.get("filename") or "",
        "created_at": manifest.get("created_at") or state.get("started_at") or "",
        "operator": state.get("operator") or manifest.get("operator") or "",
        "selected_scoping_model": selected_models.get("scoping"),
        "selected_extraction_model": selected_models.get("extraction"),
        "run_status": state.get("run_status") or "unknown",
        "last_phase": state.get("current_phase") or "",
        "is_live": live is not None,
        "has_export": (run_dir / "export").is_dir() and any((run_dir / "export").iterdir()),
    }


@router.get("")
async def list_runs() -> list[dict[str, Any]]:
    """List all persisted runs, newest first. Corrupt entries never break the list."""
    store = RunStore()
    if not store.root_dir.exists():
        return []
    runs: list[dict[str, Any]] = []
    for entry in store.root_dir.iterdir():
        if not entry.is_dir():
            continue
        try:
            summary = _run_summary(store, entry.name)
        except Exception:
            summary = None
        if summary is not None:
            runs.append(summary)
    runs.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return runs


@router.get("/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    """Full payload to reopen a session: manifest, latest state, trace, events, status."""
    store = RunStore()
    run_dir = store.run_dir(run_id)
    live = _live_store_for(run_id)
    if live is None and not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found.")

    manifest = store.load_manifest(run_id)
    if live is not None:
        state = live.get("graph_state") or {}
        resolved = live
    else:
        state = store.latest_snapshot(run_id)
        resolved = store.load_persisted_store(run_id) or {"graph_state": state}

    export_dir = run_dir / "export"
    export_files = sorted(f.name for f in export_dir.iterdir() if f.is_file()) if export_dir.is_dir() else []
    return {
        "run_id": run_id,
        "manifest": manifest,
        "state": state,
        "trace": store.read_trace(run_id),
        "events": _read_jsonl(run_dir / "events.jsonl"),
        "status": build_status_payload(resolved),
        "is_live": live is not None,
        "has_export": bool(export_files),
        "export_files": export_files,
    }


@router.get("/{run_id}/export/{filename}")
async def download_export_file(run_id: str, filename: str):
    """Download one persisted export artifact of an archived run."""
    run_dir = RunStore().run_dir(run_id)
    path = (run_dir / "export" / filename).resolve()
    if not str(path).startswith(str((run_dir / "export").resolve())) or not path.is_file():
        raise HTTPException(status_code=404, detail="Export file not found.")
    return FileResponse(path, filename=path.name)


class ReviewDecision(BaseModel):
    kind: str
    target_id: str
    target_type: str = ""
    verdict: Literal[
        "confirmed", "rejected", "accepted", "resolved", "ignored", "acknowledged", "reopened"
    ]
    note: str = ""
    operator: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/{run_id}/review-decisions")
async def record_review_decision(run_id: str, decision: ReviewDecision) -> dict[str, Any]:
    """Append a per-element review verdict to the run's audit trail (events.jsonl)."""
    store = RunStore()
    run_dir = store.run_dir(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found.")

    event = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "kind": "review_decision",
        "decision": decision.model_dump(),
    }
    path = run_dir / "events.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return {"status": "ok", "event": event}


@router.get("/{run_id}/review-decisions")
async def list_review_decisions(run_id: str) -> list[dict[str, Any]]:
    """Return recorded review decisions so a reopened session restores its verdicts."""
    store = RunStore()
    run_dir = store.run_dir(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found.")
    return [
        event for event in _read_jsonl(run_dir / "events.jsonl")
        if event.get("kind") == "review_decision"
    ]
