"""G2 structured preparation contracts exposed to API and UI."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.ids import OpaqueId, UtcTimestamp

SemanticRole = Literal[
    "observation",
    "cause",
    "action",
    "component",
    "error_code",
    "occurred_at",
    "outcome",
    "measurement",
    "attribute",
    "excluded",
]


class ColumnProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    inferred_type: str
    null_rate: float = Field(ge=0, le=1)
    cardinality: int = Field(ge=0)
    examples: list[str] = Field(default_factory=list)
    proposed_role: SemanticRole
    ambiguous: bool = False


class StructureProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    structure_id: str
    name: str
    kind: Literal["table", "sheet", "array", "jsonl"]
    row_count: int = Field(ge=0)
    included: bool = True
    hidden: bool = False
    columns: list[ColumnProfile] = Field(default_factory=list)
    preview: list[dict[str, Any]] = Field(default_factory=list, max_length=20)


class MappingColumn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: SemanticRole
    included: bool = True
    inferred_type: str = "text"


class MappingProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    structures: dict[str, dict[str, MappingColumn]]


class PreparationException(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    exception_id: OpaqueId
    profile_id: OpaqueId
    source_id: OpaqueId
    source_name: str
    exception_kind: str
    severity: Literal["blocking", "warning"]
    status: Literal["open", "queued", "resolved", "acknowledged"]
    title: str
    explanation: str
    payload: dict[str, Any]
    resolution: dict[str, Any] | None = None
    created_at: UtcTimestamp
    resolved_at: UtcTimestamp | None = None


class StructuredProfileView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: OpaqueId
    workspace_id: OpaqueId
    source_id: OpaqueId
    source_name: str
    source_kind: str
    version: int
    fingerprint: str
    state: Literal["analyzing", "needs_attention", "prepared", "failed"]
    structures: list[StructureProfile]
    mapping: MappingProfilePayload
    summary: dict[str, Any]
    run_id: OpaqueId | None = None
    confirmed: bool = False
    updated_at: UtcTimestamp


class JoinSpecView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    join_spec_id: OpaqueId
    workspace_id: OpaqueId
    status: Literal["proposed", "approved", "rejected"]
    primary_profile_id: OpaqueId
    lookup_profile_id: OpaqueId
    spec: dict[str, Any]
    preview: dict[str, Any]
    decision: dict[str, Any] | None = None


class G2PreparationView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: OpaqueId
    mode: Literal["automatic_with_exceptions"] = "automatic_with_exceptions"
    state: Literal["analyzing", "needs_attention", "ready", "failed"]
    profiles: list[StructuredProfileView]
    exceptions: list[PreparationException]
    joins: list[JoinSpecView]
    counts: dict[str, int]
    can_complete: bool
    completed: bool = False


class ExceptionResolution(BaseModel):
    role: SemanticRole | None = None
    included: bool | None = None
    acknowledge: bool = False


class JoinDecision(BaseModel):
    action: Literal["approve", "reject"]


class ColumnRoleAssignment(BaseModel):
    """Operator correction of how one column of a table was read."""

    model_config = ConfigDict(extra="forbid")

    structure_id: str = Field(min_length=1)
    column: str = Field(min_length=1)
    role: SemanticRole
