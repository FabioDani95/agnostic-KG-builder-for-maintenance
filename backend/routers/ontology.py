import json
import logging
from copy import deepcopy

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.agents.ontology_draft_agent import run_ontology_draft_agent
from backend.app_config import get_pipeline_config
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
from backend.services.graph_reasoning import run_graph_analysis
from backend.services.ontology_pipeline import (
    apply_human_binding,
    ontology_export_payload,
    validate_ontology_instance,
)
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_workflow import _split_pages_by_section, draft_ontology_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ontology", tags=["ontology"])


@router.post("/draft", response_model=OntologyPipelineResponse)
async def draft_ontology(req: OntologyDraftRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found. Upload a PDF first.")

    store = pdf_store[req.pdf_id]
    if get_pipeline_config().get("mode") == "multi_agent":
        result = await run_ontology_draft_agent(store, req)
        record_ontology_route(store)
        return result
    return await draft_ontology_workflow(store, req)


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
    pipeline_state = pdf_store[req.pdf_id].get("ontology_pipeline")
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
    pdf_store[req.pdf_id]["ontology_pipeline"] = result.model_dump()
    sync_ontology_pipeline_state(pdf_store[req.pdf_id])
    if get_pipeline_config().get("mode") == "multi_agent":
        record_ontology_review_route(pdf_store[req.pdf_id])
    return result


@router.post("/apply-suggestions", response_model=OntologyPipelineResponse)
async def apply_suggestions(req: ApplySuggestionsRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    pipeline_state = pdf_store[req.pdf_id].get("ontology_pipeline")
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Run /ontology/draft first.")

    existing = OntologyPipelineResponse.model_validate(pipeline_state)
    ontology_data = deepcopy(existing.ontology.model_dump())

    existing_edges: set[tuple[str, str, str]] = {
        (relation["name"], relation["from_id"], relation["to_id"])
        for relation in ontology_data.get("relations", [])
    }

    for suggestion in req.accepted_suggestions:
        edge_key = (suggestion.relation_name, suggestion.from_id, suggestion.to_id)
        if edge_key in existing_edges:
            continue
        ontology_data["relations"].append({
            "name": suggestion.relation_name,
            "from_type": suggestion.from_type,
            "from_id": suggestion.from_id,
            "to_type": suggestion.to_type,
            "to_id": suggestion.to_id,
            "evidence": [],
        })
        existing_edges.add(edge_key)

    from backend.models import OntologyInstance

    updated_ontology = OntologyInstance.model_validate(ontology_data)

    schema = load_ontology_schema()
    schema_issues, human_fields = validate_ontology_instance(updated_ontology)
    graph_issues, suggested_relations = run_graph_analysis(updated_ontology, schema)

    result = OntologyPipelineResponse(
        status="blocked" if schema_issues else ("needs_human" if human_fields else "ready"),
        ontology=updated_ontology,
        semantic_issues=existing.semantic_issues,
        schema_issues=schema_issues,
        human_required_fields=human_fields,
        is_schema_compliant=not schema_issues and not human_fields,
        is_ready_for_human_review=not schema_issues,
        retry_count=existing.retry_count,
        graph_issues=graph_issues,
        suggested_relations=suggested_relations,
    )
    pdf_store[req.pdf_id]["ontology_pipeline"] = result.model_dump()
    sync_ontology_pipeline_state(pdf_store[req.pdf_id])
    if get_pipeline_config().get("mode") == "multi_agent":
        record_ontology_review_route(pdf_store[req.pdf_id])
    return result


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
