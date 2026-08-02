"""G1 PDF preview and scope approval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.adapters.pdf import PdfAdapter
from backend.domain.evidence import EvidenceUnit
from backend.domain.sources import SourceState
from backend.services.foundation_ingestion import FoundationIngestionService
from backend.services.foundation_run_metrics import foundation_run_report
from backend.storage.raw_store import RawStore
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.operational_runs import OperationalRunRepository
from backend.storage.repositories.raw_units import RawUnitRepository
from backend.storage.repositories.sources import SourceNotFoundError, SourceRepository
from backend.storage.repositories.workspaces import WorkspaceRepository

router = APIRouter(prefix="/api", tags=["preparation"])


class PdfScopeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    included_pages: list[int] = Field(min_length=1)
    excluded_pages: dict[int, str] = Field(default_factory=dict)
    operator: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_pages(self) -> "PdfScopeRequest":
        if len(set(self.included_pages)) != len(self.included_pages):
            raise ValueError("included_pages must be unique")
        if set(self.included_pages) & set(self.excluded_pages):
            raise ValueError("A page cannot be both included and excluded")
        return self


class PdfPreparationResponse(BaseModel):
    source_id: str
    current_scope: dict | None
    pages: list[dict]
    raw_units: list[dict]
    evidence_units: list[EvidenceUnit]
    run: dict | None = None
    accounting: dict | None = None


def _context(source_id: str):
    workspace = WorkspaceRepository().get()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        source = SourceRepository().get(source_id)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source not found") from exc
    if source.workspace_id != workspace.workspace_id:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.source_kind.value != "pdf":
        raise HTTPException(status_code=409, detail="This preparation endpoint accepts only PDF sources")
    if source.status is not SourceState.ACCEPTED:
        raise HTTPException(status_code=409, detail="Only a compatible accepted source can enter preparation")
    path = RawStore().resolve(source.raw_relpath or "")
    return workspace, source, path


@router.get("/sources/{source_id}/pdf/preview", response_model=PdfPreparationResponse)
def preview_pdf(source_id: str):
    workspace, source, path = _context(source_id)
    current = EvidenceRepository().current_scope(source_id)
    included = set((current or {}).get("included_pages", [])) or None
    result = PdfAdapter().inspect(
        path=path,
        workspace=workspace,
        source=source,
        included_pages=included,
        scope_version=(current or {}).get("version"),
    )
    run = OperationalRunRepository().latest_for_source(source_id)
    accounting = (
        RawUnitRepository().accounting_report(run.run_id)
        if run is not None
        else None
    )
    return PdfPreparationResponse(
        source_id=source_id,
        current_scope=current,
        pages=result.page_previews,
        raw_units=[item.model_dump(mode="json") for item in result.raw_units],
        evidence_units=result.evidence_units,
        run=run.model_dump(mode="json") if run else None,
        accounting=accounting,
    )


@router.post("/sources/{source_id}/pdf/scope", response_model=PdfPreparationResponse)
def approve_pdf_scope(source_id: str, request: PdfScopeRequest):
    workspace, source, path = _context(source_id)
    initial = PdfAdapter().inspect(path=path, workspace=workspace, source=source)
    # Inventory persistence intentionally precedes scope validation and every
    # downstream filter. An invalid operator request cannot make a raw unit vanish.
    RawUnitRepository().register_inventory(initial.raw_units)
    physical_pages = {int(item["page"]) for item in initial.page_previews}
    included = set(request.included_pages)
    excluded = set(request.excluded_pages)
    if included | excluded != physical_pages:
        missing = sorted(physical_pages - included - excluded)
        extra = sorted((included | excluded) - physical_pages)
        raise HTTPException(
            status_code=422,
            detail={"message": "Scope must classify every physical page", "missing": missing, "extra": extra},
        )
    if any(not str(reason).strip() for reason in request.excluded_pages.values()):
        raise HTTPException(status_code=422, detail="Every excluded page requires a reason")
    result = PdfAdapter().inspect(
        path=path,
        workspace=workspace,
        source=source,
        included_pages=included,
        scope_version=((EvidenceRepository().current_scope(source_id) or {}).get("version", 0) + 1),
    )
    scope = EvidenceRepository().save_scope(
        workspace_id=workspace.workspace_id,
        source_id=source_id,
        included_pages=sorted(included),
        excluded_pages={str(key): value for key, value in request.excluded_pages.items()},
        operator=request.operator,
        evidence_units=result.evidence_units,
    )
    run, accounting = FoundationIngestionService().inventory_pdf_scope(
        workspace=workspace,
        source=source,
        scope=scope,
        adapter_result=result,
    )
    persisted = EvidenceRepository().list_evidence(
        workspace_id=workspace.workspace_id,
        source_id=source_id,
    )
    return PdfPreparationResponse(
        source_id=source_id,
        current_scope=scope,
        pages=result.page_previews,
        raw_units=[item.model_dump(mode="json") for item in result.raw_units],
        evidence_units=persisted,
        run=run,
        accounting=accounting,
    )


@router.get("/workspaces/{workspace_id}/evidence", response_model=list[EvidenceUnit])
def list_evidence(workspace_id: str, source_id: str | None = None):
    workspace = WorkspaceRepository().get()
    if workspace is None or workspace.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return EvidenceRepository().list_evidence(workspace_id=workspace_id, source_id=source_id)


@router.get("/foundation/runs/{run_id}/accounting")
def get_foundation_run_accounting(run_id: str):
    try:
        return foundation_run_report(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Foundation run not found") from exc
