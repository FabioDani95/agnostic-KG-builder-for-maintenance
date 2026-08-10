"""Source-scoped candidate graph contracts used by the human generation step."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class RelationEvidenceRef(BaseModel):
    """Claim-specific support retained on one published graph relation.

    This is revision/provenance metadata, not an ontology property.  Keeping it
    separate from ``GraphEvidenceRef`` prevents the adapter from replacing a
    relation's exact support with the union of its endpoint evidence.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: OpaqueId
    quote: str = Field(min_length=1)
    source_anchor: str = Field(min_length=1)
    locator: dict[str, Any]
    support_role: Literal["direct", "derived_structural"] = "direct"


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
    evidence_refs: list[RelationEvidenceRef] = Field(default_factory=list)


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
    graph_invariant_errors: int = Field(default=0, ge=0)
    duplicate_ids: int = Field(default=0, ge=0)
    provenance_total: int = Field(default=0, ge=0)
    provenance_resolvable: int = Field(default=0, ge=0)
    relation_grounding_total: int = Field(default=0, ge=0)
    relation_grounding_passed: int = Field(default=0, ge=0)
    unresolved_mapping_diagnostics: int = Field(default=0, ge=0)
    passed: bool = False
    issues: list[GraphValidationIssue] = Field(default_factory=list)


class TokenCostMetrics(BaseModel):
    """Measured token usage with a list-price cost estimate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    llm_calls: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    cached_prompt_tokens: int = Field(default=0, ge=0)
    non_cached_prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0)


class SourceGenerationStageMetrics(TokenCostMetrics):
    model_config = ConfigDict(extra="forbid", frozen=True)

    duration_seconds: float = Field(default=0.0, ge=0)
    models: list[str] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class SourceGenerationMetrics(TokenCostMetrics):
    """Immutable KPI ledger persisted with the generated source revision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    duration_seconds: float = Field(default=0.0, ge=0)
    models: list[str] = Field(default_factory=list)
    by_model: dict[str, TokenCostMetrics] = Field(default_factory=dict)
    stages: dict[str, SourceGenerationStageMetrics] = Field(default_factory=dict)
    execution_mode: str = ""
    pricing_currency: Literal["USD"] = "USD"
    pricing_kind: Literal["estimated_list_price"] = "estimated_list_price"


class KnowledgeGap(BaseModel):
    """Declared incompleteness; never silently promoted to a graph assertion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    evidence_ids: list[OpaqueId] = Field(default_factory=list)
    target_kind: str = ""
    target_id: str = ""
    stage: str = ""
    blocking: bool = False
    disposition: Literal["gap", "exclude", "review"] = "gap"


class GraphProjection(BaseModel):
    """An ID-only view over the same canonical graph payload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)


class PdfExtractionSection(BaseModel):
    """One diagnostic section selected from the immutable PDF inventory."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    start_page: int = Field(ge=1)
    end_page: int = Field(ge=1)
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_range(self) -> "PdfExtractionSection":
        if self.end_page < self.start_page:
            raise ValueError("PDF extraction section end_page must not precede start_page")
        return self


class PdfExtractionScope(BaseModel):
    """Derived semantic selection; it never replaces the all-pages G1 scope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    method: Literal["retained_cut_plan"] = "retained_cut_plan"
    total_pages: int = Field(ge=1)
    selected_pages: list[int] = Field(min_length=1)
    unselected_pages: list[int]
    sections: list[PdfExtractionSection] = Field(default_factory=list)
    diagnostic_pages: list[int] = Field(default_factory=list)
    structural_pages: list[int] = Field(default_factory=list)
    retrieval_pages: list[int] = Field(default_factory=list)
    page_offset: int = 0
    skipped: bool = False

    @model_validator(mode="after")
    def validate_partition(self) -> "PdfExtractionScope":
        selected = self.selected_pages
        unselected = self.unselected_pages
        if selected != sorted(set(selected)) or unselected != sorted(set(unselected)):
            raise ValueError("PDF extraction pages must be unique and sorted")
        if selected[0] < 1 or (unselected and unselected[0] < 1):
            raise ValueError("PDF extraction pages must be positive")
        if set(selected) & set(unselected):
            raise ValueError("PDF extraction selected and unselected pages must be disjoint")
        physical_pages = set(selected) | set(unselected)
        if len(physical_pages) != self.total_pages:
            raise ValueError("PDF extraction pages must partition total_pages")
        if any(
            section.start_page not in physical_pages
            or section.end_page not in physical_pages
            for section in self.sections
        ):
            raise ValueError("PDF extraction section ranges must reference physical pages")
        for role_name, role_pages in (
            ("diagnostic_pages", self.diagnostic_pages),
            ("structural_pages", self.structural_pages),
            ("retrieval_pages", self.retrieval_pages),
        ):
            if role_pages != sorted(set(role_pages)):
                raise ValueError(f"PDF extraction {role_name} must be unique and sorted")
            if not set(role_pages).issubset(physical_pages):
                raise ValueError(f"PDF extraction {role_name} must reference physical pages")
        return self


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
    pdf_extraction_scope: PdfExtractionScope | None = None
    generation_metrics: SourceGenerationMetrics | None = None
    pipeline_version: str = "legacy"
    projections: dict[str, GraphProjection] = Field(default_factory=dict)
    review_queue: list[dict[str, Any]] = Field(default_factory=list)
    review_summary: dict[str, Any] = Field(default_factory=dict)
    publication_metrics: dict[str, Any] = Field(default_factory=dict)
    canonicalization_report: dict[str, Any] = Field(default_factory=dict)
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
