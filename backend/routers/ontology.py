"""Deprecated step-wise ontology endpoints.

These routes are kept only for legacy/manual compatibility and are mounted
when KG_ENABLE_LEGACY_ROUTES=1. Chat-first multi-agent services are the active
runtime path.
"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.agents.ontology_draft_agent import run_ontology_draft_agent
from backend.graph.supervisor import record_ontology_review_route, record_ontology_route
from backend.graph.store import sync_ontology_pipeline_state
from backend.models import (
    ApplySuggestionsRequest,
    OntologyDraftRequest,
    OntologyExportRequest,
    OntologyPipelineResponse,
    OntologyReviewRequest,
)
from backend.routers.upload import pdf_store
from backend.services.ontology_pipeline import (
    apply_human_binding,
    ontology_export_payload,
)
from backend.services.pipeline_actions import apply_ontology_suggestions

router = APIRouter(prefix="/ontology", tags=["legacy-step-wise"], deprecated=True)


@router.post("/draft", response_model=OntologyPipelineResponse)
async def draft_ontology(req: OntologyDraftRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found. Upload a PDF first.")

    store = pdf_store[req.pdf_id]
    result = await run_ontology_draft_agent(store, req)
    record_ontology_route(store)
    return result


@router.get("/{pdf_id}", response_model=OntologyPipelineResponse)
async def get_ontology_state(pdf_id: str):
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    pipeline_state = pdf_store[pdf_id].get("ontology_pipeline")
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Ontology pipeline has not been run yet.")
    return OntologyPipelineResponse.model_validate(pipeline_state)


@router.post("/review", response_model=OntologyPipelineResponse)
async def review_ontology(req: OntologyReviewRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    store = pdf_store[req.pdf_id]
    pipeline_state = store.get("ontology_pipeline")
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Run /ontology/draft first.")
    existing = OntologyPipelineResponse.model_validate(pipeline_state)
    try:
        result = apply_human_binding(existing.ontology, req.answers)
    except RuntimeError as exc:
        detail = str(exc)
        status_code = 408 if "stopped after" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    if existing.semantic_issues:
        result.semantic_issues = existing.semantic_issues
    store["ontology_pipeline"] = result.model_dump()
    sync_ontology_pipeline_state(store)
    record_ontology_review_route(store)
    return result


@router.post("/apply-suggestions", response_model=OntologyPipelineResponse)
async def apply_suggestions(req: ApplySuggestionsRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    store = pdf_store[req.pdf_id]
    if not store.get("ontology_pipeline"):
        raise HTTPException(status_code=404, detail="Run /ontology/draft first.")
    return apply_ontology_suggestions(store, req.accepted_suggestions)


@router.post("/export")
async def export_ontology(req: OntologyExportRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    pipeline_state = pdf_store[req.pdf_id].get("ontology_pipeline")
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Run /ontology/draft first.")
    result = OntologyPipelineResponse.model_validate(pipeline_state)
    if result.schema_issues or result.human_required_fields:
        detail = {
            "message": "Ontology is not exportable yet.",
            "schema_issues": [issue.model_dump() for issue in result.schema_issues],
            "human_required_fields": [field.model_dump() for field in result.human_required_fields],
        }
        raise HTTPException(status_code=409, detail=json.dumps(detail, ensure_ascii=False))
    try:
        json_str = ontology_export_payload(result.ontology)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=ontology_instance.json"},
    )
