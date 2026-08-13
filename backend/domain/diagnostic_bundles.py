"""Typed diagnostic records between model extraction and ontology publication.

The candidate contracts are safe structured-output targets: the model supplies
claims and exact evidence spans, but never graph identifiers or ontology
relation names.  The validated contracts are produced only by the deterministic
compiler after every span has been resolved against canonical source evidence.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResolutionStatus(StrEnum):
    """The extractor's explicit assessment of diagnostic completeness."""

    ACTION_STATED = "action_stated"
    NO_ACTION_STATED = "no_action_stated"
    CHECK_ONLY = "check_only"
    AMBIGUOUS = "ambiguous"
    NOT_DIAGNOSTIC = "not_diagnostic"


class DiagnosticEvidenceSpan(BaseModel):
    """A verbatim source span emitted by the extraction model.

    ``source_anchor`` is the opaque evidence identifier printed in the model's
    input.  It is intentionally not a graph node identifier.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_anchor: str = Field(min_length=1)
    source_page: int = Field(ge=1)
    quote: str = Field(min_length=1)


class SymptomIndicatorCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["symptom"]
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Literal["Low", "Medium", "High", "Critical"]
    claim_evidence: list[DiagnosticEvidenceSpan] = Field(min_length=1)
    failure_link_evidence: list[DiagnosticEvidenceSpan]


class ErrorCodeIndicatorCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["error_code"]
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    claim_evidence: list[DiagnosticEvidenceSpan] = Field(min_length=1)
    failure_link_evidence: list[DiagnosticEvidenceSpan]


class DiagnosticIndicatorCandidate(BaseModel):
    """Provider-safe flat indicator contract.

    OpenAI strict Structured Outputs does not accept the ``oneOf`` emitted by
    Pydantic for a discriminated model union inside an array.  Keep the wire
    shape flat and enforce the same symptom/error-code invariants locally.
    Nullable fields remain required so the provider schema is strict.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["symptom", "error_code"]
    code: str | None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Literal["Low", "Medium", "High", "Critical"] | None
    claim_evidence: list[DiagnosticEvidenceSpan] = Field(min_length=1)
    failure_link_evidence: list[DiagnosticEvidenceSpan]

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_nullable_fields(cls, value: Any) -> Any:
        """Keep stored v7 fixtures readable while the provider sees required fields."""

        if isinstance(value, dict):
            normalized = dict(value)
            normalized.setdefault("code", None)
            normalized.setdefault("severity", None)
            return normalized
        return value

    @model_validator(mode="after")
    def validate_kind_specific_fields(self) -> DiagnosticIndicatorCandidate:
        if self.kind == "symptom":
            if self.code is not None:
                raise ValueError("symptom indicators require code=null")
            if self.severity is None:
                raise ValueError("symptom indicators require severity")
        else:
            if not str(self.code or "").strip():
                raise ValueError("error_code indicators require a non-empty code")
            if self.severity is not None:
                raise ValueError("error_code indicators require severity=null")
        return self


class FailureModeCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    # Required-but-nullable for provider Structured Outputs.  ``None`` means
    # the source did not establish asset-level/component context.
    material_context: str | None
    claim_evidence: list[DiagnosticEvidenceSpan] = Field(min_length=1)


class CorrectiveActionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    instruction_text: str = Field(min_length=1)
    action_kind: str | None
    claim_evidence: list[DiagnosticEvidenceSpan] = Field(min_length=1)
    resolution_link_evidence: list[DiagnosticEvidenceSpan]


class DiagnosticInspectionStepCandidate(BaseModel):
    """A diagnostic check that is useful but does not itself restore operation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    instruction_text: str = Field(min_length=1)
    claim_evidence: list[DiagnosticEvidenceSpan] = Field(min_length=1)


class AffectedComponentCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    # Do not force an extractor to manufacture a classification absent in the
    # source.  The publication compiler treats ``None`` as an explicit gap.
    category: str | None
    claim_evidence: list[DiagnosticEvidenceSpan] = Field(min_length=1)
    affects_link_evidence: list[DiagnosticEvidenceSpan]


class DiagnosticBundleCandidate(BaseModel):
    """One source record, potentially containing several observed indicators."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Required on the provider wire schema.  Production overwrites both values
    # with the system-owned record window after parsing, so they are lineage
    # constraints rather than model assertions.
    record_window_id: str
    allowed_source_anchors: list[str]
    record_anchor: str = Field(min_length=1)
    branch_anchor: str = Field(min_length=1)
    indicators: list[DiagnosticIndicatorCandidate]
    failure: FailureModeCandidate | None
    actions: list[CorrectiveActionCandidate]
    inspection_steps: list[DiagnosticInspectionStepCandidate]
    affected_component: AffectedComponentCandidate | None
    resolution_status: ResolutionStatus

    @model_validator(mode="before")
    @classmethod
    def normalize_pre_window_fixtures(cls, value: Any) -> Any:
        """Keep immutable pre-hardening fixtures readable.

        No defaults are declared on the fields themselves: OpenAI strict
        Structured Outputs therefore still sees every property as required.
        """

        if isinstance(value, dict):
            normalized = dict(value)
            normalized.setdefault("record_window_id", "")
            normalized.setdefault("allowed_source_anchors", [])
            normalized.setdefault("inspection_steps", [])
            return normalized
        return value

    @model_validator(mode="after")
    def require_indicator_except_for_explicit_exclusion(self) -> DiagnosticBundleCandidate:
        if self.resolution_status is not ResolutionStatus.NOT_DIAGNOSTIC and not self.indicators:
            raise ValueError("indicators must not be empty for a diagnostic candidate")
        if self.resolution_status is ResolutionStatus.NOT_DIAGNOSTIC and (
            self.indicators
            or self.failure is not None
            or self.actions
            or self.inspection_steps
            or self.affected_component is not None
        ):
            raise ValueError("not_diagnostic candidates cannot carry diagnostic claims")
        return self


class DiagnosticChunkOutput(BaseModel):
    """Provider structured-output envelope for one diagnostic PDF chunk.

    All fields are required, including nullable/list fields.  This avoids the
    optional-property mismatch of strict provider JSON Schema implementations.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    source_language: str = Field(min_length=1)
    records: list[DiagnosticBundleCandidate]


class ValidatedDiagnosticEvidenceSpan(BaseModel):
    """An evidence span resolved exactly to one source evidence unit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_anchor: str = Field(min_length=1)
    source_page: int = Field(ge=1)
    quote: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    locator: dict[str, Any]


class ValidatedSymptomIndicator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["symptom"] = "symptom"
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Literal["Low", "Medium", "High", "Critical"]
    claim_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(min_length=1)
    failure_link_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(default_factory=list)


class ValidatedErrorCodeIndicator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["error_code"] = "error_code"
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    claim_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(min_length=1)
    failure_link_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(default_factory=list)


ValidatedDiagnosticIndicator = Annotated[
    ValidatedSymptomIndicator | ValidatedErrorCodeIndicator,
    Field(discriminator="kind"),
]


class ValidatedFailureMode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    material_context: str | None
    claim_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(min_length=1)


class ValidatedCorrectiveAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    instruction_text: str = Field(min_length=1)
    action_kind: str | None = None
    claim_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(min_length=1)
    resolution_link_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(default_factory=list)


class ValidatedDiagnosticInspectionStep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    instruction_text: str = Field(min_length=1)
    claim_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(min_length=1)


class ValidatedAffectedComponent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str | None
    claim_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(min_length=1)
    affects_link_evidence: list[ValidatedDiagnosticEvidenceSpan] = Field(default_factory=list)


class ValidatedDiagnosticBundle(BaseModel):
    """Evidence-resolved bundle with deterministic, non-ontology lineage IDs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_lineage_id: str = Field(pattern=r"^drec_[a-f0-9]{64}$")
    branch_lineage_id: str = Field(pattern=r"^dbranch_[a-f0-9]{64}$")
    record_window_id: str = ""
    record_anchor: str = Field(min_length=1)
    branch_anchor: str = Field(min_length=1)
    indicators: list[ValidatedDiagnosticIndicator] = Field(min_length=1)
    failure: ValidatedFailureMode | None = None
    actions: list[ValidatedCorrectiveAction] = Field(default_factory=list)
    inspection_steps: list[ValidatedDiagnosticInspectionStep] = Field(default_factory=list)
    affected_component: ValidatedAffectedComponent | None = None
    resolution_status: ResolutionStatus
