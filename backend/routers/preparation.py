"""Compact G1 preparation status and evidence endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.domain.evidence import EvidenceUnit
from backend.domain.structured import (
    ExceptionResolution,
    G2PreparationView,
    JoinDecision,
)
from backend.services.foundation_run_metrics import foundation_run_report
from backend.services.pdf_auto_preparation import PdfAutoPreparationService
from backend.services.structured_preparation import (
    StructuredPreparationError,
    StructuredPreparationService,
)
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.sources import SourceNotFoundError, SourceRepository
from backend.storage.repositories.workspaces import WorkspaceRepository

router = APIRouter(prefix="/api", tags=["preparation"])


def _context(source_id: str):
    try:
        source = SourceRepository().get(source_id)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source not found") from exc
    workspace = WorkspaceRepository().get_by_id(source.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if source.source_kind.value != "pdf":
        raise HTTPException(status_code=409, detail="This preparation endpoint accepts only PDF sources")
    return workspace, source


@router.get("/sources/{source_id}/pdf/preparation")
def pdf_preparation(source_id: str):
    workspace, source = _context(source_id)
    return PdfAutoPreparationService().prepare(workspace=workspace, source=source)


@router.get("/workspaces/{workspace_id}/evidence", response_model=list[EvidenceUnit])
def list_evidence(workspace_id: str, source_id: str | None = None):
    workspace = WorkspaceRepository().get_by_id(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return EvidenceRepository().list_evidence(workspace_id=workspace_id, source_id=source_id)


@router.get("/foundation/runs/{run_id}/accounting")
def get_foundation_run_accounting(run_id: str):
    try:
        return foundation_run_report(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Foundation run not found") from exc


@router.get(
    "/workspaces/{workspace_id}/g2/preparation",
    response_model=G2PreparationView,
)
def get_g2_preparation(workspace_id: str):
    try:
        return StructuredPreparationService().snapshot(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found") from exc


@router.post(
    "/workspaces/{workspace_id}/g2/preparation",
    response_model=G2PreparationView,
)
def start_g2_preparation(workspace_id: str):
    try:
        return StructuredPreparationService().ensure_workspace(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found") from exc
    except StructuredPreparationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/g2/exceptions/{exception_id}/resolve",
    response_model=G2PreparationView,
)
def resolve_g2_exception(exception_id: str, resolution: ExceptionResolution):
    try:
        return StructuredPreparationService().resolve_exception(
            exception_id,
            resolution.model_dump(exclude_none=True),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Eccezione di preparazione non trovata") from exc
    except (ValueError, StructuredPreparationError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/g2/joins/{join_id}/decision",
    response_model=G2PreparationView,
)
def decide_g2_join(join_id: str, decision: JoinDecision):
    try:
        return StructuredPreparationService().decide_join(join_id, decision.action)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Proposta di collegamento non trovata") from exc
    except StructuredPreparationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/g2/profiles/{profile_id}/confirm",
    response_model=G2PreparationView,
)
def confirm_g2_profile(profile_id: str):
    try:
        return StructuredPreparationService().confirm_profile(profile_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Fonte strutturata non trovata") from exc
    except StructuredPreparationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/workspaces/{workspace_id}/g2/complete",
    response_model=G2PreparationView,
)
def complete_g2_preparation(workspace_id: str):
    try:
        return StructuredPreparationService().complete(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found") from exc
    except StructuredPreparationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
