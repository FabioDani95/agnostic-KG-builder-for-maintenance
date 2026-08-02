"""Source inventory, content-addressed upload and assessment APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.domain.sources import Source, SourceAuthority, SourceKind, SourceRegistration
from backend.security.boundary import actionable_error, security_limits, validate_inventory_name
from backend.services.source_assessment import decide_assessment, observe_asset_claims
from backend.storage.raw_store import RawStore, UploadTooLargeError
from backend.storage.repositories.sources import (
    SourceAssessmentError,
    SourceNotFoundError,
    SourceRepository,
)
from backend.storage.repositories.workspaces import WorkspaceRepository

router = APIRouter(prefix="/api", tags=["sources"])
_KINDS = {
    ".pdf": (SourceKind.PDF, "application/pdf"),
    ".csv": (SourceKind.CSV, "text/csv"),
    ".xlsx": (SourceKind.XLSX, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ".json": (SourceKind.JSON, "application/json"),
    ".jsonl": (SourceKind.JSONL, "application/x-ndjson"),
}


class ResolveAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["confirm", "exclude"]
    reason: str = Field(min_length=10, max_length=2000)
    observation_basis: Literal["direct_observation", "nameplate", "operator_record"]
    operator: str = Field(min_length=1, max_length=200)
    evidence_seen: list[str] = Field(min_length=1)


@router.get("/workspaces/{workspace_id}/sources", response_model=list[Source])
def list_sources(workspace_id: str):
    workspace = WorkspaceRepository().get()
    if workspace is None or workspace.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return SourceRepository().list_for_workspace(workspace_id)


@router.post("/workspaces/{workspace_id}/sources", response_model=SourceRegistration)
async def upload_source(
    workspace_id: str,
    file: UploadFile = File(...),
    authority: SourceAuthority = Form(SourceAuthority.INFORMAL),
):
    workspace = WorkspaceRepository().get()
    if workspace is None or workspace.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        file_name = validate_inventory_name(str(file.filename or ""))
    except ValueError as exc:
        await file.close()
        raise HTTPException(
            status_code=400,
            detail=actionable_error(
                title="Nome file non ammesso",
                object_ref=str(file.filename or "upload"),
                cause="Il nome contiene traversal, separatori o encoding non inventariabile.",
                preserved="Workspace e fonti esistenti non sono stati modificati.",
                action="Rinominare il file usando un solo nome locale e riprovare.",
                technical_detail="UPLOAD_NAME_NOT_IN_INVENTORY",
                retryability="riprendibile",
            ),
        ) from exc
    suffix = Path(file_name).suffix.casefold()
    if suffix not in _KINDS:
        await file.close()
        raise HTTPException(
            status_code=415,
            detail=actionable_error(
                title="Formato non supportato",
                object_ref=file_name,
                cause="L'estensione non appartiene alla matrice dei formati MVP.",
                preserved="Le altre fonti restano inventariate e invariate.",
                action="Usare PDF, CSV, XLSX, JSON o JSONL.",
                technical_detail=f"UNSUPPORTED_SOURCE_SUFFIX {suffix}",
                retryability="richiede nuova elaborazione",
            ),
        )
    source_kind, canonical_media_type = _KINDS[suffix]
    try:
        stored = await RawStore().persist_upload(
            file,
            max_bytes=security_limits().max_upload_bytes,
        )
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail=actionable_error(
                title="File oltre il limite",
                object_ref=file_name,
                cause=str(exc),
                preserved="Il file temporaneo è stato eliminato; le altre fonti sono intatte.",
                action="Ridurre il file o aumentare consapevolmente il limite locale.",
                technical_detail="UPLOAD_LIMIT_EXCEEDED",
                retryability="riprendibile",
            ),
        ) from exc

    repository = SourceRepository()
    existing = repository.find_by_hash(workspace_id, stored.sha256)
    if existing is not None:
        source, duplicate = repository.register(
            workspace_id=workspace_id,
            source_kind=source_kind,
            authority=authority,
            file_name=Path(file_name).name,
            media_type=canonical_media_type,
            size_bytes=stored.size_bytes,
            sha256=stored.sha256,
            raw_relpath=stored.relative_path,
            observed_claims=[],
            outcome=existing.active_assessment.outcome,
            reason_codes=existing.active_assessment.reason_codes,
        )
        return SourceRegistration(source=source, duplicate=duplicate, raw_cache_hit=True)

    claims = observe_asset_claims(
        path=stored.absolute_path,
        source_kind=source_kind,
        asset=workspace.asset,
        identifiers=workspace.identifiers,
    )
    outcome, reason_codes = decide_assessment(claims, workspace.identifiers)
    source, duplicate = repository.register(
        workspace_id=workspace_id,
        source_kind=source_kind,
        authority=authority,
        file_name=Path(file_name).name,
        media_type=canonical_media_type,
        size_bytes=stored.size_bytes,
        sha256=stored.sha256,
        raw_relpath=stored.relative_path,
        observed_claims=claims,
        outcome=outcome,
        reason_codes=reason_codes,
    )
    return SourceRegistration(source=source, duplicate=duplicate, raw_cache_hit=stored.cache_hit)


@router.post("/sources/{source_id}/assessment/resolve", response_model=Source)
def resolve_assessment(source_id: str, request: ResolveAssessmentRequest):
    try:
        return SourceRepository().resolve_uncertain(
            source_id,
            action=request.action,
            reason=request.reason,
            observation_basis=request.observation_basis,
            operator=request.operator,
            evidence_seen=request.evidence_seen,
        )
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source not found") from exc
    except SourceAssessmentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/sources/{source_id}/assessment/reopen", response_model=Source)
def reopen_assessment(source_id: str):
    try:
        return SourceRepository().reopen_resolution(source_id)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source not found") from exc
    except SourceAssessmentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/sources/{source_id}/content")
def download_source(source_id: str):
    try:
        relative_path = SourceRepository().raw_reference(source_id)
        path = RawStore().resolve(relative_path)
    except (SourceNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="Source content not found") from exc
    source = SourceRepository().get(source_id)
    return FileResponse(path, media_type=source.media_type, filename=source.file_name)
