"""Endpoints for PDF cut-plan: propose and approve page selection."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.agents.scoping_agent import run_scoping_agent
from backend.app_config import get_pipeline_config
from backend.graph.supervisor import record_cut_plan_approval_route, record_scoping_route
from backend.graph.store import update_cut_plan_approval
from backend.models import CutPlan, CutPlanApproval, CutPlanRequest
from backend.routers.upload import pdf_store
from backend.services.scoping_workflow import (
    approve_cut_plan_workflow,
    create_cut_plan_workflow,
)

router = APIRouter()


@router.post("/cut-plan", response_model=CutPlan)
async def create_cut_plan(req: CutPlanRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found. Upload a PDF first.")

    store = pdf_store[req.pdf_id]
    if get_pipeline_config().get("mode") == "multi_agent":
        result = run_scoping_agent(store, req)
        record_scoping_route(store)
        return result
    return create_cut_plan_workflow(store, req)


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
    if get_pipeline_config().get("mode") == "multi_agent":
        record_cut_plan_approval_route(store)
    return response
