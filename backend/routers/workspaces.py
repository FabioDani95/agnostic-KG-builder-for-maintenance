"""Workspace onboarding API for the single-machine MVP."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.domain.workspace import (
    AssetIdentifier,
    OperatorAssertion,
    Workspace,
    attested_text,
)
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.workspaces import WorkspaceConflictError, WorkspaceRepository

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


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


@router.get("", response_model=WorkspaceResponse | None)
def get_workspace():
    repository = WorkspaceRepository()
    workspace = repository.get()
    if workspace is None:
        return None
    assertion = repository.latest_asset_assertion(workspace.workspace_id)
    if assertion is None:
        raise HTTPException(status_code=500, detail="Workspace assertion is missing")
    EvidenceRepository().ensure_asset_assertion_evidence(workspace, assertion)
    return WorkspaceResponse(workspace=workspace, assertion=assertion, resumed=True)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(request: CreateWorkspaceRequest):
    repository = WorkspaceRepository()
    try:
        workspace, assertion, resumed = repository.create_confirmed(
            asset_values=request.asset.model_dump(),
            identifiers=request.identifiers,
            assertion_reason=request.assertion.reason,
            observation_basis=request.assertion.observation_basis,
            operator=request.assertion.operator,
        )
    except WorkspaceConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    EvidenceRepository().ensure_asset_assertion_evidence(workspace, assertion)
    return WorkspaceResponse(workspace=workspace, assertion=assertion, resumed=resumed)
