"""Source-scoped candidate graph contracts used by the human generation step."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.ids import OpaqueId, UtcTimestamp
from backend.domain.sources import SourceKind

NodeType = Literal[
    "Asset",
    "Component",
    "Symptom",
    "FailureMode",
    "CorrectiveAction",
    "ErrorCode",
]


class SourceSubgraphStatus(StrEnum):
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"


class GraphEvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: OpaqueId
    label: str
    excerpt: str
    locator: dict[str, Any]


class SourceGraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str = Field(min_length=1)
    node_type: NodeType
    label: str = Field(min_length=1)
    description: str = ""
    evidence_ids: list[OpaqueId] = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)


class SourceGraphRelation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    relation_id: str = Field(min_length=1)
    relation_type: Literal[
        "HAS_COMPONENT",
        "MAY_INDICATE",
        "AFFECTS",
        "RESOLVED_BY",
        "GENERATES_ERROR",
        "INDICATES",
    ]
    from_id: str = Field(min_length=1)
    to_id: str = Field(min_length=1)
    evidence_ids: list[OpaqueId] = Field(min_length=1)


class GraphValidationIssue(BaseModel):
    """A concrete failure found against the source-subgraph payload itself."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    node_type: NodeType | Literal["relation", "provenance", "mapping"]
    node_id: str | None = None
    property_name: str | None = None


class GraphValidationReport(BaseModel):
    """Strict ontology/provenance checks that gate source-level approval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    required_properties_total: int = Field(default=0, ge=0)
    required_properties_present: int = Field(default=0, ge=0)
    extra_properties: int = Field(default=0, ge=0)
    domain_range_errors: int = Field(default=0, ge=0)
    endpoint_errors: int = Field(default=0, ge=0)
    duplicate_ids: int = Field(default=0, ge=0)
    provenance_total: int = Field(default=0, ge=0)
    provenance_resolvable: int = Field(default=0, ge=0)
    unresolved_mapping_diagnostics: int = Field(default=0, ge=0)
    passed: bool = False
    issues: list[GraphValidationIssue] = Field(default_factory=list)


class KnowledgeGap(BaseModel):
    """Declared incompleteness; never silently promoted to a graph assertion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    evidence_ids: list[OpaqueId] = Field(default_factory=list)


class SourceSubgraphRevision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_subgraph_revision_id: OpaqueId
    workspace_id: OpaqueId
    source_id: OpaqueId
    source_name: str
    source_kind: SourceKind
    preparation_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_ids: list[OpaqueId]
    nodes: list[SourceGraphNode]
    relations: list[SourceGraphRelation]
    evidence: list[GraphEvidenceRef]
    status: SourceSubgraphStatus
    approval_decision_id: OpaqueId | None = None
    decision_note: str | None = None
    duplicate_nodes_consolidated: int = Field(default=0, ge=0)
    duplicate_relations_consolidated: int = Field(default=0, ge=0)
    validation: GraphValidationReport = Field(default_factory=GraphValidationReport)
    knowledge_gaps: list[KnowledgeGap] = Field(default_factory=list)
    approval_eligible: bool = False
    supersedes: OpaqueId | None = None
    created_at: UtcTimestamp


class G3SourceView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: OpaqueId
    source_name: str
    source_kind: SourceKind
    state: Literal["waiting", "ready", "reviewing", "approved", "rejected", "deferred"]
    message: str
    subgraph: SourceSubgraphRevision | None = None


class CrossSourceMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_type: NodeType
    normalized_label: str
    label: str
    occurrences: list[dict[str, str]] = Field(min_length=2)


class MergeBarrierView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: Literal["waiting_for_generation", "waiting_for_approval", "ready"]
    pending_source_ids: list[OpaqueId]
    exact_matches: list[CrossSourceMatch]


class G3WorkspaceView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: OpaqueId
    sources: list[G3SourceView]
    counts: dict[str, int]
    merge_barrier: MergeBarrierView


class SourceSubgraphDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["approve", "reject"]
    note: str | None = Field(default=None, max_length=1000)
