"""Immutable Source and append-only source-to-Asset assessment contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.ids import OpaqueId, UtcTimestamp
from backend.domain.locators import SourceLocator


class SourceKind(StrEnum):
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    JSONL = "jsonl"
    OPERATOR_INPUT = "operator_input"


class SourceAuthority(StrEnum):
    NORMATIVE = "normative"
    OBSERVATIONAL = "observational"
    OPERATIONAL = "operational"
    INFORMAL = "informal"


class SourceState(StrEnum):
    UPLOADED = "uploaded"
    ASSESSING = "assessing"
    ACCEPTED = "accepted"
    QUARANTINED = "quarantined"
    EXCLUDED = "excluded"
    DUPLICATE = "duplicate"
    FAILED_TERMINAL = "failed_terminal"


class AssessmentOutcome(StrEnum):
    COMPATIBLE = "compatible"
    UNCERTAIN = "uncertain"
    INCOMPATIBLE = "incompatible"


class ObservedAssetClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_kind: Literal[
        "serial",
        "equipment_tag",
        "customer_asset_id",
        "brand",
        "model",
        "model_family",
        "site",
        "department",
        "work_order",
    ]
    namespace: str
    raw_value: str
    normalized_value: str
    locator: SourceLocator


class AssessmentDecider(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["deterministic_rule", "operator_assertion", "reopened"]
    decision_id: OpaqueId | None = None
    operator_assertion_id: OpaqueId | None = None


class SourceAssetAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: OpaqueId
    source_id: OpaqueId
    workspace_id: OpaqueId
    asset_identity_version: int = Field(ge=1)
    observed_claims: list[ObservedAssetClaim]
    outcome: AssessmentOutcome
    reason_codes: list[str] = Field(min_length=1)
    decided_by: AssessmentDecider
    supersedes: OpaqueId | None = None
    created_at: UtcTimestamp


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: OpaqueId
    workspace_id: OpaqueId
    source_kind: SourceKind
    authority: SourceAuthority
    file_name: str | None
    media_type: str | None
    size_bytes: int | None = Field(default=None, ge=0)
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    language_hints: list[str] = Field(default_factory=list)
    status: SourceState
    asset_assessment_id: OpaqueId | None
    raw_relpath: str | None = None
    created_at: UtcTimestamp
    active_assessment: SourceAssetAssessment | None = None


class SourceRegistration(BaseModel):
    source: Source
    duplicate: bool
    raw_cache_hit: bool
    preparation: dict | None = None
