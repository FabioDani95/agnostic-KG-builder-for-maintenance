from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.config import DEFAULT_MODEL_NAME


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Symptom(BaseModel):
    symptom_id: str
    name: str
    description: str
    severity: Severity


class FailureMode(BaseModel):
    failure_mode_id: str
    name: str
    description: str
    material_context: str
    linked_symptom_id: str


class CorrectiveAction(BaseModel):
    action_id: str
    name: str
    description: str
    instruction_text: str
    source_type: str
    source_title: str
    source_page: int
    linked_failure_mode_id: str


class Triplet(BaseModel):
    symptom: Symptom
    failure_modes: list[FailureMode]
    corrective_actions: list[CorrectiveAction]


class ExtractionResult(BaseModel):
    triplets: list[Triplet]
    raw_symptom_table: str
    raw_failure_mode_table: str
    raw_corrective_action_table: str


class UploadResponse(BaseModel):
    pdf_id: str
    filename: str
    page_count: int


class ExtractRequest(BaseModel):
    pdf_id: str
    source_type: str
    source_title: str
    model_name: str = DEFAULT_MODEL_NAME
    pages_to_keep: list[int] | None = None
    target_language: str = "en"


class GenerateJsonRequest(BaseModel):
    pdf_id: str | None = None
    validated_triplets: list[Triplet]
    target_language: str = "en"


class OntologyPropertyDefinition(BaseModel):
    name: str
    type: str
    required: bool = False
    unique: bool = False
    items: str | None = None


class OntologyNodeDefinition(BaseModel):
    name: str
    description: str
    properties: list[OntologyPropertyDefinition]


class OntologyRelationDefinition(BaseModel):
    name: str
    domain: str
    range: str
    description: str


class OntologySchemaDefinition(BaseModel):
    ontology_name: str
    version: str
    language: str
    description: str
    design_principles: list[str] = []
    nodes: list[OntologyNodeDefinition]
    relations: list[OntologyRelationDefinition]


class OntologyEvidence(BaseModel):
    source_page: int = 0
    source_reference: str = ""
    quote: str = ""


class OntologyRelationInstance(BaseModel):
    name: str
    from_type: str
    from_id: str
    to_type: str
    to_id: str
    evidence: list[OntologyEvidence] = []


class OntologyInstance(BaseModel):
    ontology_name: str
    version: str
    language: str
    source_type: str
    source_title: str
    nodes: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    relations: list[OntologyRelationInstance] = Field(default_factory=list)


class ExportOntologyMetadata(BaseModel):
    product_name: str
    product_short_name: str
    product_type: str
    domain_topics: list[str]
    version: str = ""
    file_version: str = ""
    total_nodes: int = 0
    total_relationships: int = 0


class ExportOntologyRelationship(BaseModel):
    type: str
    from_id: str
    to_id: str
    evidence: list[OntologyEvidence] = Field(default_factory=list)


class ExportOntologyInstance(BaseModel):
    metadata: ExportOntologyMetadata
    nodes: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    relationships: list[ExportOntologyRelationship] = Field(default_factory=list)


class PipelineIssue(BaseModel):
    severity: str
    code: str
    message: str
    target_type: str = ""
    target_id: str = ""
    property_name: str = ""
    fix_hint: str = ""


class HumanRequiredField(BaseModel):
    field_key: str
    prompt: str
    target_type: str
    target_id: str
    property_name: str
    reason: str
    expected_type: str = "string"
    suggested_value: str = ""
    allowed_values: list[str] = []


class HumanBindingAnswer(BaseModel):
    field_key: str
    value: str


class OntologyDraftRequest(BaseModel):
    pdf_id: str
    source_type: str
    source_title: str
    model_name: str = DEFAULT_MODEL_NAME
    pages_to_keep: list[int] | None = None
    target_language: str = "en"


class OntologyReviewRequest(BaseModel):
    pdf_id: str
    answers: list[HumanBindingAnswer] = []
    model_name: str = DEFAULT_MODEL_NAME


class GraphIssue(BaseModel):
    issue_type: str  # orphan | missing_relation | broken_chain | cycle
    affected_nodes: list[str] = []
    description: str
    suggested_fix: str = ""
    auto_fixable: bool = False


class SuggestedRelation(BaseModel):
    relation_name: str
    from_type: str
    from_id: str
    from_label: str
    to_type: str
    to_id: str
    to_label: str
    confidence: float
    rationale: str = ""


class ApplySuggestionsRequest(BaseModel):
    pdf_id: str
    accepted_suggestions: list[SuggestedRelation] = []


class OntologyPipelineResponse(BaseModel):
    status: str
    ontology: OntologyInstance
    semantic_issues: list[PipelineIssue] = []
    schema_issues: list[PipelineIssue] = []
    human_required_fields: list[HumanRequiredField] = []
    is_schema_compliant: bool = False
    is_ready_for_human_review: bool = False
    retry_count: int = 0
    graph_issues: list[GraphIssue] = []
    suggested_relations: list[SuggestedRelation] = []


class OntologyExportRequest(BaseModel):
    pdf_id: str


# ─── Cut Plan Models ───


class PageRange(BaseModel):
    start: int  # physical page number (1-based)
    end: int    # physical page number (1-based, inclusive)


class TocEntry(BaseModel):
    title: str
    manual_page: int  # page number as printed in the manual


class StructuredToc(BaseModel):
    entries: list[TocEntry]
    toc_start_page: int  # absolute PDF page where ToC starts
    toc_end_page: int    # absolute PDF page where ToC ends


class SectionInfo(BaseModel):
    name: str
    page_range: PageRange                      # absolute PDF pages
    manual_page_range: PageRange | None = None  # manual pages (for display)
    source: str                                # "rule" | "llm" | "keyword" | "user"
    keyword_matches: list[str] = []
    reasoning: str = ""


class ProductInfo(BaseModel):
    product_name: str = ""
    document_type: str = ""
    language: str = ""
    page_count: int = 0


class CutPlan(BaseModel):
    pdf_id: str
    total_pages: int
    sections: list[SectionInfo]
    pages_to_keep: list[int]
    page_offset: int = 0
    toc: StructuredToc | None = None
    skipped: bool = False
    product_info: ProductInfo | None = None


class CutPlanRequest(BaseModel):
    pdf_id: str
    model_name: str = DEFAULT_MODEL_NAME
    page_offset: int = 0


class CutPlanApprovalSection(BaseModel):
    """Lightweight section info sent back from the frontend during approve."""
    name: str
    page_range: PageRange
    source: str = ""

class CutPlanApproval(BaseModel):
    pdf_id: str
    pages_to_keep: list[int]
    page_offset: int = 0
    sections: list[CutPlanApprovalSection] = []


class LoadManualRequest(BaseModel):
    filename: str
