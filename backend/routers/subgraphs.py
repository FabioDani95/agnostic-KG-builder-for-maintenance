"""Human-facing source subgraph generation and approval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.domain.subgraphs import G3WorkspaceView, SourceSubgraphDecisionRequest
from backend.services.source_subgraph_generation import (
    SourceSubgraphGenerationError,
    SourceSubgraphGenerationService,
)

router = APIRouter(prefix="/api", tags=["source-subgraphs"])


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
