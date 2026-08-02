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
from backend.graph.state import GraphPhase
from backend.graph.store import (
    _record_phase,
    find_store_by_run_id,
    persist_graph_state,
    set_run_progress,
)
from backend.routers.upload import pdf_store
from backend.runstore import RunStore
from backend.security.boundary import contained_file, validate_inventory_name
from backend.services.ontology_patch_service import apply_ontology_patch

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
        "next_step": state.get("next_step") or "",
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
    try:
        inventory_name = validate_inventory_name(filename)
        path = contained_file(run_dir / "export", run_dir / "export" / inventory_name)
    except (ValueError, FileNotFoundError):
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


def _value_references_node(value: Any, node_id: str) -> bool:
    if isinstance(value, dict):
        if any(
            str(item or "") == node_id
            for key, item in value.items()
            if key == "id" or key.endswith("_id")
        ):
            return True
        return any(_value_references_node(item, node_id) for item in value.values())
    if isinstance(value, list):
        return any(_value_references_node(item, node_id) for item in value)
    return False


def _apply_rejected_node(run_id: str, decision: ReviewDecision) -> bool:
    if decision.verdict != "rejected":
        return False
    live = _live_store_for(run_id)
    if live is None:
        return False
    state = live.get("graph_state") or {}
    pipeline = state.get("ontology_pipeline") or {}
    ontology = pipeline.get("ontology") or {}
    updated, report = apply_ontology_patch(
        ontology,
        {"remove_node_ids": [decision.target_id]},
    )
    if not report["removed_nodes"]:
        return False

    pipeline["ontology"] = updated
    state["ontology_pipeline"] = pipeline
    state["cleaned_triplets"] = [
        triplet for triplet in state.get("cleaned_triplets") or []
        if not _value_references_node(triplet, decision.target_id)
    ]
    live["validated_triplets"] = [
        triplet for triplet in live.get("validated_triplets") or []
        if not _value_references_node(triplet, decision.target_id)
    ]
    persist_graph_state(live, state)
    return True


def _finalize_review_if_ready(run_id: str, events: list[dict[str, Any]]) -> bool:
    live = _live_store_for(run_id)
    if live is None:
        return False
    state = live.get("graph_state") or {}
    if state.get("current_phase") != GraphPhase.EXTRACTION.value:
        return False

    queue = ((state.get("ontology_pipeline") or {}).get("review_queue") or [])
    queue_keys = {
        (str(item.get("kind") or ""), str(item.get("target_id") or ""))
        for item in queue
    }
    active_decisions: set[tuple[str, str]] = set()
    for event in events:
        if event.get("kind") != "review_decision":
            continue
        saved = event.get("decision") or {}
        key = (str(saved.get("kind") or ""), str(saved.get("target_id") or ""))
        if saved.get("verdict") == "reopened":
            active_decisions.discard(key)
        else:
            active_decisions.add(key)
    if not queue_keys or not queue_keys.issubset(active_decisions):
        return False

    triplets = list(state.get("cleaned_triplets") or [])
    live["validated_triplets"] = triplets
    live["review_index"] = len(triplets)
    _record_phase(
        live,
        phase=GraphPhase.EXPORT,
        agent="TripletReviewAgent",
        decision="review_queue_completed",
    )
    set_run_progress(live, run_status="awaiting_operator", next_step="export")
    return True


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
    node_removed = _apply_rejected_node(run_id, decision)
    review_completed = _finalize_review_if_ready(run_id, _read_jsonl(path))
    return {
        "status": "ok",
        "event": event,
        "node_removed": node_removed,
        "review_completed": review_completed,
    }


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
