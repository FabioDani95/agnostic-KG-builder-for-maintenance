"""Deprecated step-wise cut-plan endpoints.

These routes are kept only for legacy/manual compatibility and are mounted
when KG_ENABLE_LEGACY_ROUTES=1. Chat-first multi-agent services are the active
runtime path.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.agents.scoping_agent import run_scoping_agent
from backend.graph.store import update_cut_plan_approval
from backend.graph.supervisor import record_cut_plan_approval_route, record_scoping_route
from backend.models import CutPlan, CutPlanApproval, CutPlanRequest
from backend.routers.upload import pdf_store
from backend.services.scoping_workflow import (
    approve_cut_plan_workflow,
)

router = APIRouter(tags=["legacy-step-wise"], deprecated=True)


@router.post("/cut-plan", response_model=CutPlan)
async def create_cut_plan(req: CutPlanRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found. Upload a PDF first.")

    store = pdf_store[req.pdf_id]
    result = run_scoping_agent(store, req)
    record_scoping_route(store)
    return result


@router.post("/cut-plan/approve")
async def approve_cut_plan(req: CutPlanApproval):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    if not req.pages_to_keep:
        raise HTTPException(status_code=400, detail="At least one page must be selected.")

    store = pdf_store[req.pdf_id]
    response = approve_cut_plan_workflow(store, req)
    sections_for_state = [
        {
            "name": section.name,
            "start": section.page_range.start,
            "end": section.page_range.end,
            "source": section.source,
        }
        for section in req.sections
    ] if req.sections else store.get("cut_plan", {}).get("sections", [])
    update_cut_plan_approval(
        store,
        pages_to_keep=req.pages_to_keep,
        page_offset=req.page_offset,
        sections=sections_for_state,
    )
    record_cut_plan_approval_route(store)
    return response
