"""Read-only observability endpoints for the Phase 2 multi-agent layer."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.graph.store import build_audit_payload, build_status_payload, find_store_by_run_id
from backend.routers.upload import pdf_store

router = APIRouter(prefix="/multi-agent", tags=["multi-agent"])


def _resolve_store(run_id: str):
    store = find_store_by_run_id(pdf_store, run_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return store


@router.get("/status")
async def get_multi_agent_status(run_id: str = Query(...)):
    return build_status_payload(_resolve_store(run_id))


@router.get("/status/{run_id}")
async def get_multi_agent_status_by_path(run_id: str):
    return build_status_payload(_resolve_store(run_id))


@router.get("/audit")
async def get_multi_agent_audit(run_id: str = Query(...)):
    return build_audit_payload(_resolve_store(run_id))


@router.get("/audit/{run_id}")
async def get_multi_agent_audit_by_path(run_id: str):
    return build_audit_payload(_resolve_store(run_id))
