"""Canonical format-independent evidence contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.domain.ids import OpaqueId
from backend.domain.locators import SourceLocator
from backend.domain.sources import SourceAuthority, SourceKind


class RecordRole(StrEnum):
    MAINTENANCE_EVENT = "maintenance_event"
    MEASUREMENT = "measurement"
    ASSET_MASTER = "asset_master"
    COMPONENT_MASTER = "component_master"
    ERROR_CATALOG = "error_catalog"
    GENERIC_EVIDENCE = "generic_evidence"
    EXCLUDED = "excluded"


class LanguageQualification(StrEnum):
    QUALIFIED_EN = "qualified_en"
    UNQUALIFIED_IT = "unqualified_it"
    UNQUALIFIED_DE = "unqualified_de"
    UNKNOWN = "unknown"
    MIXED = "mixed"


class QualityFlag(StrEnum):
    MISSING_REQUIRED_SOURCE_FIELD = "MISSING_REQUIRED_SOURCE_FIELD"
    INVALID_DATE = "INVALID_DATE"
    INVALID_NUMBER = "INVALID_NUMBER"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    POSSIBLE_COLUMN_SHIFT = "POSSIBLE_COLUMN_SHIFT"
    UNKNOWN_LANGUAGE = "UNKNOWN_LANGUAGE"
    WRONG_ASSET_SUSPECTED = "WRONG_ASSET_SUSPECTED"
    SEMANTIC_TEXT_RECONSTRUCTED = "SEMANTIC_TEXT_RECONSTRUCTED"
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"
    MODEL_OUTPUT_REPAIRED = "MODEL_OUTPUT_REPAIRED"
    LOW_CONFIDENCE_LINK = "LOW_CONFIDENCE_LINK"
    UNMAPPED_FAILURE_MODE = "UNMAPPED_FAILURE_MODE"


class ProvenanceRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["primary", "lookup", "corroborating", "contradicting", "operator_assertion"]
    raw_unit_id: OpaqueId
    source_id: OpaqueId
    locator: SourceLocator
    raw_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    structure_id: str | None = None


class LanguageInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    detected: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    qualification: LanguageQualification


class EvidenceContent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = ""
    observation: str = ""
    cause: str = ""
    action: str = ""
    outcome: str = ""
    error_code: str = ""
    measurement: str = ""
    semantic_texts: dict[str, str] = Field(default_factory=dict)

    def has_semantic_content(self) -> bool:
        return any(
            str(value or "").strip()
            for value in (
                self.observation,
                self.cause,
                self.action,
                self.error_code,
                self.measurement,
            )
        )


class RawReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: OpaqueId
    raw_unit_id: OpaqueId
    locator_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class IngestionInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    adapter_version: str
    mapping_profile_id: OpaqueId | None = None
    mapping_fingerprint: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    scope_version: int | None = Field(default=None, ge=1)


class EvidenceUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: OpaqueId
    workspace_id: OpaqueId
    asset_id: OpaqueId
    source_id: OpaqueId
    source_kind: SourceKind
    authority: SourceAuthority
    locator: SourceLocator
    provenance_refs: list[ProvenanceRef] = Field(min_length=1)
    language: LanguageInfo
    record_role: RecordRole
    occurred_at: str | None = None
    content: EvidenceContent
    hints: dict[str, Any] = Field(default_factory=dict)
    measurements: list[dict[str, Any]] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    quality_flags: list[QualityFlag] = Field(default_factory=list)
    raw_ref: RawReference
    ingestion: IngestionInfo

    @model_validator(mode="after")
    def validate_primary_provenance(self) -> "EvidenceUnit":
        primary = [item for item in self.provenance_refs if item.role == "primary"]
        if len(primary) != 1:
            raise ValueError("Exactly one primary provenance reference is required")
        item = primary[0]
        if (
            item.source_id != self.source_id
            or item.raw_unit_id != self.raw_ref.raw_unit_id
            or item.locator != self.locator
        ):
            raise ValueError("Primary provenance must match source, locator and raw_ref")
        return self

    @property
    def eligible_for_semantic_processing(self) -> bool:
        return self.content.has_semantic_content() and self.record_role is not RecordRole.EXCLUDED


class RawUnitDraft(BaseModel):
    """Stable adapter inventory record before I06 adds the disposition ledger."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_unit_id: OpaqueId
    parent_raw_unit_id: OpaqueId | None
    unit_kind: str
    source_id: OpaqueId
    structure_id: str | None = None
    locator: SourceLocator
    raw_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    adapter_version: str
    quality_flags: list[QualityFlag] = Field(default_factory=list)
