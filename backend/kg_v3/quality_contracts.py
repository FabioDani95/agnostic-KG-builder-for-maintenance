"""Supplementary evidence/applicability contracts; no domain ontology additions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

QUALITY_VERSION = "kg-ingestion-quality-1"
ScopeStatus = Literal["VERIFIED_STRUCTURE", "VERIFIED_REVIEW", "PROVISIONAL", "LEGACY_UNKNOWN"]
Denotation = Literal["STATED", "INFERRED", "PLACEHOLDER", "TEST_CONTEXT", "UNRESOLVED", "LEGACY_UNCLASSIFIED"]
Epistemic = Literal[
    "EXPLICIT", "INFERRED_FROM_TEXT", "STRUCTURAL_PLACEHOLDER", "UNRESOLVED", "SYSTEM_DERIVED", "LEGACY_UNCLASSIFIED"
]
LocatorStatus = Literal["EXACT", "APPROXIMATE", "MISSING", "LEGACY_UNVERIFIED"]
SupportStatus = Literal["UNCHECKED", "SUPPORTED", "UNSUPPORTED", "UNCLEAR"]
Method = Literal[
    "PRIMARY",
    "TABLE_RECOVERY",
    "COMPLETENESS_REVIEW",
    "CROSS_REFERENCE_RECOVERY",
    "GRAPH_REPAIR",
    "VISUAL_READ",
    "ACTION_REPAIR",
    "HUMAN_CORRECTION",
    "SYSTEM_ROOT_LINK",
]
Box = tuple[float, float, float, float]


class QualityContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["kg-ingestion-quality-1"] = QUALITY_VERSION


class DocumentIdentity(QualityContract):
    document_id: str
    pdf_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_scope_id: str
    source_title: str
    parser_fingerprint: str
    inventory_fingerprint: str


class SourceRegion(QualityContract):
    region_id: str
    document_id: str
    page: int = Field(ge=1)
    bbox: Box
    page_width: float = Field(gt=0)
    page_height: float = Field(gt=0)
    render_fingerprint: str
    kind: str = "PAGE"
    segment_ids: list[str] = Field(default_factory=list)
    coordinate_system: Literal["PDF_UNROTATED"] = "PDF_UNROTATED"
    rotation: int = 0
    image_path: str = ""

    @model_validator(mode="after")
    def bounds(self):
        x0, y0, x1, y1 = self.bbox
        if not (0 <= x0 < x1 <= self.page_width and 0 <= y0 < y1 <= self.page_height):
            raise ValueError("region bbox is outside its unrotated page")
        return self


class EvidenceRef(QualityContract):
    evidence_ref_id: str
    document_id: str
    page: int = Field(ge=1)
    kind: Literal["TEXT_SPAN", "TABLE_CELL", "TABLE_ITEM", "VISUAL_REGION"]
    locator_status: LocatorStatus
    content_sha256: str
    segment_id: str = ""
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    text_basis: str = ""
    exact_text: str = ""
    raw_evidence_id: str = ""
    table: int | None = None
    row: int | None = None
    column: int | None = None
    item_index: int | None = None
    bbox: Box | None = None
    inherited_from: list[str] = Field(default_factory=list)
    region_id: str = ""
    render_fingerprint: str = ""
    transcription: str = ""
    transcription_method: str = ""
    transcription_status: str = "NONE"

    @model_validator(mode="after")
    def locator(self):
        if self.kind == "VISUAL_REGION":
            if not (self.region_id and self.bbox and self.render_fingerprint) or self.exact_text:
                raise ValueError("visual evidence needs a region/render; transcription is not exact text")
        elif not (
            self.segment_id
            and self.text_basis
            and self.char_start is not None
            and self.char_end is not None
            and self.char_end > self.char_start
            and self.exact_text
        ):
            raise ValueError("text evidence requires an immutable basis and a nonempty span")
        return self


class EvidenceBinding(QualityContract):
    role: Literal["subject", "predicate", "object", "condition", "branch_path", "premise"]
    evidence_ref_ids: list[str] = Field(min_length=1)
    support_status: SupportStatus = "UNCHECKED"
    verification_call_id: str = ""


class SourceEntry(QualityContract):
    entry_id: str
    document_id: str
    kind: Literal["TABLE_ROW", "NUMBERED_PROCEDURE", "FLOWCHART", "PARAGRAPH", "TEST_TABLE", "UNRESOLVED"]
    anchor_refs: list[str] = Field(min_length=1)
    member_refs: list[str] = Field(min_length=1)
    heading_refs: list[str] = Field(default_factory=list)
    parent_entry_id: str = ""
    scope_status: ScopeStatus = "PROVISIONAL"
    scope_evidence_refs: list[str] = Field(default_factory=list)


class PathStep(QualityContract):
    question_ref: str
    outcome_ref: str
    outcome_value: str
    transition_ref: str
    destination_ref: str
    order: int | None = None


class BranchScope(QualityContract):
    branch_id: str
    entry_id: str
    diagram_id: str = ""
    branch_anchor_refs: list[str] = Field(min_length=1)
    path_steps: list[PathStep] = Field(default_factory=list)
    applicability: list[dict[str, Any]] = Field(default_factory=list)
    scope_status: ScopeStatus = "PROVISIONAL"
    scope_evidence_refs: list[str] = Field(default_factory=list)


class Mention(QualityContract):
    mention_id: str
    type: str
    original_name: str
    observed_names: list[str] = Field(default_factory=list)
    code: str = ""
    action_kind: str = ""
    denotation_status: Denotation = "UNRESOLVED"
    evidence_ref_ids: list[str] = Field(default_factory=list)
    entry_id: str = ""
    branch_id: str = ""
    reading_refs: list[str] = Field(default_factory=list)


class Concept(QualityContract):
    concept_id: str
    type: str
    canonical_name: str
    mention_ids: list[str]
    aliases: list[str] = Field(default_factory=list)
    identifiers: list[str] = Field(default_factory=list)
    equivalence_decisions: list[dict[str, Any]] = Field(default_factory=list)


class DiagnosticInstance(QualityContract):
    instance_id: str
    concept_id: str = ""
    branch_id: str
    mention_ids: list[str]
    asset_scope_id: str
    qualifiers: list[dict[str, Any]] = Field(default_factory=list)


class ProcessingItem(QualityContract):
    item_id: str
    kind: str
    page: int = Field(ge=1)
    status: Literal["PENDING", "PROCESSED", "OUT_OF_SCOPE", "UNREADABLE", "FAILED", "DEFERRED"] = "PENDING"
    reason: str = ""
    evidence_ref_ids: list[str] = Field(default_factory=list)
    attempts: int = 0
    stage: str = "inventory"


class CoverageItem(QualityContract):
    item_id: str
    entry_id: str
    branch_id: str
    kind: Literal[
        "INDICATOR",
        "CAUSE",
        "COMPONENT",
        "INSPECTION",
        "REPAIR",
        "ESCALATION",
        "CONDITION",
        "EXPECTED",
        "WARNING",
        "PREREQUISITE",
        "ORDER",
        "OUTCOME",
        "REFERENCE",
    ]
    evidence_ref_ids: list[str]
    text: str
    status: Literal[
        "UNASSESSED",
        "REPRESENTED",
        "PARTIAL",
        "MISSING",
        "UNRESOLVED",
        "REJECTED_PROPOSAL",
        "NOT_ASSERTED_BY_SOURCE",
        "OUT_OF_SCHEMA",
    ] = "UNASSESSED"
    assertion_ids: list[str] = Field(default_factory=list)
    inventory_exhaustiveness: Literal["STRUCTURAL", "REVIEWED", "PARTIAL"] = "PARTIAL"


class ReviewRequest(QualityContract):
    request_id: str
    trigger: str
    entry_id: str = ""
    branch_id: str = ""
    target_item_ids: list[str] = Field(default_factory=list)
    target_assertion_ids: list[str] = Field(default_factory=list)
    source_fingerprint: str
    local_scope_fingerprint: str
    priority: int = 0
    severity: int = 0
    status: Literal["PENDING", "PROCESSED", "DEFERRED", "FAILED", "UNRESOLVED"] = "PENDING"
    retrieval_query: str = ""
    retrieved_evidence_ids: list[str] = Field(default_factory=list)
    attempts: list[dict[str, Any]] = Field(default_factory=list)
    round: int = 0
    parent_request_id: str = ""
    required_capabilities: list[str] = Field(default_factory=list)
    result_reason: str = ""
    audit: bool = False


class PageRoute(QualityContract):
    page: int = Field(ge=1)
    routes: list[Literal["TEXT", "TABLE", "VISUAL_REVIEW", "OCR_REVIEW"]]
    relevance: Literal["DIAGNOSTIC", "OTHER", "UNRESOLVED"] = "UNRESOLVED"
    reasons: list[str]
    confidence_class: str = "CANDIDATE"
    evidence_ref_ids: list[str] = Field(default_factory=list)
    native_text_unreadable: bool = False


class QualityConfig(QualityContract):
    profile: Literal["base_safe", "quality_v1"] = "base_safe"
    branch_identity: bool = False
    semantic_merge_review: bool = False
    completeness_review: bool = False
    reference_retrieval: bool = False
    graph_review: bool = False
    visual_routing: bool = False
    max_review_rounds: int = Field(default=2, ge=0, le=2)
    max_review_requests_per_document: int = Field(default=24, ge=0)
    audit_requests_per_document: int = Field(default=2, ge=0)
    max_evidence_chars_per_request: int = Field(default=18000, gt=0)
    max_images_per_request: int = Field(default=6, gt=0)
    max_retrieved_pages_per_request: int = Field(default=4, gt=0)
    review_model: str | None = None
    review_reasoning: str = "medium"
    verify_model: str | None = None
    verify_reasoning: str = "medium"
    vision_model: str | None = None
    vision_reasoning: str = "medium"
    inference_policy: Literal["source_only"] = "source_only"
    export_projection: bool = True
    visual_image_area_threshold: float = Field(default=0.15, ge=0, le=1)
    visual_drawing_threshold: int = Field(default=8, ge=0)

    @model_validator(mode="after")
    def prerequisites(self):
        if (
            any(
                (
                    self.semantic_merge_review,
                    self.completeness_review,
                    self.reference_retrieval,
                    self.graph_review,
                    self.visual_routing,
                )
            )
            and not self.branch_identity
        ):
            raise ValueError("quality extensions require branch_identity and the evidence catalog")
        if self.profile == "base_safe" and self.branch_identity:
            raise ValueError("P1 requires the opt-in quality_v1 profile")
        if self.audit_requests_per_document > self.max_review_requests_per_document:
            raise ValueError("audit slots exceed the total request cap")
        return self

    @classmethod
    def quality_v1(cls, **overrides):
        return cls(
            **{
                "profile": "quality_v1",
                "branch_identity": True,
                "semantic_merge_review": True,
                "completeness_review": True,
                "reference_retrieval": True,
                "graph_review": True,
                "visual_routing": True,
                **overrides,
            }
        )
