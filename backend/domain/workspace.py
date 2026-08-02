"""Workspace, Asset and onboarding assertion contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.domain.ids import OpaqueId, UtcTimestamp

_PLACEHOLDERS = {
    "-",
    "n/a",
    "na",
    "none",
    "non disponibile",
    "not available",
    "placeholder",
    "tbd",
    "todo",
    "unknown",
}


def attested_text(value: str, *, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized or normalized.casefold() in _PLACEHOLDERS:
        raise ValueError(f"{field_name} requires an attested, non-placeholder value")
    return normalized


class WorkspaceState(StrEnum):
    EMPTY = "empty"
    SOURCES_REQUIRED = "sources_required"
    PREPARATION_REQUIRED = "preparation_required"
    READY = "ready"
    PROCESSING = "processing"
    PAUSED = "paused"
    FAILED_RESUMABLE = "failed_resumable"
    FAILED_TERMINAL = "failed_terminal"
    AWAITING_REVIEW = "awaiting_review"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"


class Asset(BaseModel):
    """The exact six-property Asset shape declared by ontology_schema.JSON."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_id: OpaqueId
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


class AssetIdentifier(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    namespace: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=300)
    kind: Literal["serial", "equipment_tag", "customer_asset_id", "alias"]

    @field_validator("namespace", "value")
    @classmethod
    def reject_blank_identifier(cls, value: str, info) -> str:
        return attested_text(value, field_name=info.field_name)


class AssertionSubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["asset_identity"]
    asset_id: OpaqueId
    asset_identity_version: int = Field(ge=1)


class OperatorAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: OpaqueId
    workspace_id: OpaqueId
    subject_ref: AssertionSubject
    field_path: Literal["Asset"]
    asserted_value: dict[str, Any]
    reason: str = Field(min_length=10, max_length=2000)
    evidence_ids_seen: list[OpaqueId] = Field(default_factory=list)
    observation_basis: Literal["direct_observation", "nameplate", "operator_record"]
    decision_id: OpaqueId
    operator: str = Field(min_length=1, max_length=200)
    supersedes: OpaqueId | None = None
    created_at: UtcTimestamp

    @field_validator("reason", "operator")
    @classmethod
    def reject_placeholder_assertion_text(cls, value: str, info) -> str:
        return attested_text(value, field_name=info.field_name)


class Workspace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: OpaqueId
    status: WorkspaceState
    asset: Asset
    asset_identity_version: int = Field(ge=1)
    ontology_version: str
    ontology_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_at: UtcTimestamp
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    identifiers: list[AssetIdentifier] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_one_asset(self) -> "Workspace":
        if self.asset.asset_id == self.workspace_id:
            raise ValueError("Asset and Workspace IDs must be globally distinct")
        return self
