"""Workspace onboarding API for the single-machine MVP."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.domain.workspace import (
    AssetIdentifier,
    OperatorAssertion,
    Workspace,
    WorkspaceState,
    attested_text,
)
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.sources import SourceRepository
from backend.storage.repositories.workspaces import WorkspaceConflictError, WorkspaceRepository

router = APIRouter(prefix="/api/workspace", tags=["workspace"])
inventory_router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


class AssetOnboardingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    brand: str
    model: str
    asset_type: str | None = None

    @field_validator("name", "description", "brand", "model")
    @classmethod
    def reject_placeholders(cls, value: str, info) -> str:
        return attested_text(value, field_name=info.field_name)

    @field_validator("asset_type")
    @classmethod
    def normalize_optional_asset_type(cls, value: str | None) -> str | None:
        if value is None or not str(value).strip():
            return None
        return attested_text(value, field_name="asset_type")


class AssertionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=10, max_length=2000)
    observation_basis: Literal["direct_observation", "nameplate", "operator_record"]
    operator: str = Field(min_length=1, max_length=200)

    @field_validator("reason", "operator")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset: AssetOnboardingInput
    identifiers: list[AssetIdentifier] = Field(default_factory=list)
    assertion: AssertionInput


class WorkspaceResponse(BaseModel):
    workspace: Workspace
    assertion: OperatorAssertion
    resumed: bool = False


class WorkspaceHomeItem(BaseModel):
    workspace_id: str
    asset_name: str
    brand: str
    model: str
    status: WorkspaceState
    document_count: int = Field(ge=0)
    updated_at: str


def _workspace_response(workspace: Workspace) -> WorkspaceResponse:
    assertion = WorkspaceRepository().latest_asset_assertion(workspace.workspace_id)
    if assertion is None:
        raise HTTPException(status_code=500, detail="Workspace assertion is missing")
    EvidenceRepository().ensure_asset_assertion_evidence(workspace, assertion)
    return WorkspaceResponse(workspace=workspace, assertion=assertion, resumed=True)


@router.get("", response_model=WorkspaceResponse | None)
def get_workspace():
    repository = WorkspaceRepository()
    workspace = repository.get()
    if workspace is None:
        return None
    return _workspace_response(workspace)


@inventory_router.get("", response_model=list[WorkspaceHomeItem])
def list_workspaces():
    source_repository = SourceRepository()
    items = []
    for workspace in WorkspaceRepository().list_all():
        sources = source_repository.list_for_workspace(workspace.workspace_id)
        documents = [source for source in sources if source.source_kind.value != "operator_input"]
        updated_at = max([workspace.updated_at, *(source.created_at for source in documents)])
        items.append(
            WorkspaceHomeItem(
                workspace_id=workspace.workspace_id,
                asset_name=workspace.asset.name,
                brand=workspace.asset.brand,
                model=workspace.asset.model,
                status=workspace.status,
                document_count=len(documents),
                updated_at=updated_at,
            )
        )
    return items


@inventory_router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace_by_id(workspace_id: str):
    workspace = WorkspaceRepository().get_by_id(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return _workspace_response(workspace)


def _create_workspace(request: CreateWorkspaceRequest, *, allow_new: bool) -> WorkspaceResponse:
    repository = WorkspaceRepository()
    try:
        workspace, assertion, resumed = repository.create_confirmed(
            asset_values=request.asset.model_dump(),
            identifiers=request.identifiers,
            assertion_reason=request.assertion.reason,
            observation_basis=request.assertion.observation_basis,
            operator=request.assertion.operator,
            allow_new=allow_new,
        )
    except WorkspaceConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    EvidenceRepository().ensure_asset_assertion_evidence(workspace, assertion)
    return WorkspaceResponse(workspace=workspace, assertion=assertion, resumed=resumed)


@inventory_router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_new_workspace(request: CreateWorkspaceRequest):
    return _create_workspace(request, allow_new=True)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(request: CreateWorkspaceRequest):
    return _create_workspace(request, allow_new=False)
