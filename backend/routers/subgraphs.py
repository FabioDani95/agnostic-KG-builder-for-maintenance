"""Human-facing source subgraph generation and approval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.domain.subgraphs import DiagnosticRecordCorrectionRequest, G3WorkspaceView, SourceSubgraphDecisionRequest
from backend.services.source_subgraph_generation import (
    SourceSubgraphGenerationError,
    SourceSubgraphGenerationService,
)

router = APIRouter(prefix="/api", tags=["source-subgraphs"])


@router.post("/g3/subgraphs/{revision_id}/records/{branch_id}/correction", response_model=G3WorkspaceView)
def correct_diagnostic_record(revision_id: str, branch_id: str, request: DiagnosticRecordCorrectionRequest):
    from backend.services.diagnostic_record_review import correct_record
    from backend.services.pdf_source_subgraph_generation import pdf_input_config_hash, pdf_preparation_fingerprint

    service = SourceSubgraphGenerationService()
    try:
        revision = service.subgraphs.get(revision_id)
        evidence = service.evidence.list_evidence(workspace_id=revision.workspace_id, source_id=revision.source_id)
        source = service.sources.get(revision.source_id)
        scope = service.evidence.current_scope(revision.source_id)
        current_fingerprint = pdf_preparation_fingerprint(source=source, scope=scope,
            evidence=[e for e in evidence if e.eligible_for_semantic_processing])
        if revision.preparation_fingerprint != current_fingerprint or (revision.review_base_config_hash or revision.input_config_hash) != pdf_input_config_hash():
            raise ValueError("Fonte o configurazione cambiate: genera una nuova revisione prima di correggere")
        corrected = correct_record(revision, branch_id, request, evidence)
        service.subgraphs.create(corrected, expected_current_revision_id=revision_id)
        return service.snapshot(revision.workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Record o fonte non trovati") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/workspaces/{workspace_id}/g3/subgraphs", response_model=G3WorkspaceView)
def get_source_subgraphs(workspace_id: str):
    try:
        return SourceSubgraphGenerationService().snapshot(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Workspace non trovato") from exc


@router.post(
    "/workspaces/{workspace_id}/g3/sources/{source_id}/generate",
    response_model=G3WorkspaceView,
)
async def generate_source_subgraph(workspace_id: str, source_id: str):
    try:
        return await SourceSubgraphGenerationService().generate(workspace_id, source_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Fonte non trovata") from exc
    except SourceSubgraphGenerationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/g3/subgraphs/{revision_id}/decision", response_model=G3WorkspaceView)
def decide_source_subgraph(revision_id: str, request: SourceSubgraphDecisionRequest):
    try:
        return SourceSubgraphGenerationService().decide(
            revision_id,
            action=request.action,
            note=request.note,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Sottografo non trovato") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
