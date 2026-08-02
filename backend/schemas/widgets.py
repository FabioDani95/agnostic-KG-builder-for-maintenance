from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class WidgetType(StrEnum):
    SECTIONS = "sections"
    ONTOLOGY_REVIEW = "ontology_review"
    TRIPLET = "triplet"
    TRIPLET_REVIEW_START = "triplet_review_start"
    REQUIRED_FIELDS = "required_fields"
    EXTRACTION_GRAPH = "extraction_graph"
    EXPORT = "export"
    RUN_METRICS = "run_metrics"


class _WidgetPayloadBase(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str | None = None


class SectionsWidgetPayload(_WidgetPayloadBase):
    widget: Literal[WidgetType.SECTIONS]
    sections: list[dict[str, Any]] = Field(default_factory=list)
    pages_to_keep: list[int] = Field(default_factory=list)
    total_pages: int | None = None


class OntologyReviewWidgetPayload(_WidgetPayloadBase):
    widget: Literal[WidgetType.ONTOLOGY_REVIEW]
    node_count: int = 0
    node_type_counts: dict[str, int] = Field(default_factory=dict)
    human_required_fields: list[dict[str, Any]] = Field(default_factory=list)
    review_queue: list[dict[str, Any]] = Field(default_factory=list)


class TripletWidgetPayload(_WidgetPayloadBase):
    widget: Literal[WidgetType.TRIPLET]
    index: int | None = None
    total: int | None = None
    triplet: dict[str, Any] | None = None
    graph: dict[str, Any] | None = None
    logic_assessment: dict[str, Any] | list[str] | None = None


class TripletReviewStartWidgetPayload(_WidgetPayloadBase):
    widget: Literal[WidgetType.TRIPLET_REVIEW_START]
    total: int | None = None
    message: str | None = None


class RequiredFieldsWidgetPayload(_WidgetPayloadBase):
    widget: Literal[WidgetType.REQUIRED_FIELDS]
    fields: list[dict[str, Any]] = Field(default_factory=list)


class ExtractionGraphWidgetPayload(_WidgetPayloadBase):
    widget: Literal[WidgetType.EXTRACTION_GRAPH]
    graph: dict[str, Any] | None = None


class ExportWidgetPayload(_WidgetPayloadBase):
    widget: Literal[WidgetType.EXPORT]
    exported: bool | None = None
    output_path: str | None = None
    total: int | None = None
    validated: int | None = None


class RunMetricsWidgetPayload(_WidgetPayloadBase):
    widget: Literal[WidgetType.RUN_METRICS]
    metrics: dict[str, Any] = Field(default_factory=dict)


WidgetPayload = Annotated[
    SectionsWidgetPayload
    | OntologyReviewWidgetPayload
    | TripletWidgetPayload
    | TripletReviewStartWidgetPayload
    | RequiredFieldsWidgetPayload
    | ExtractionGraphWidgetPayload
    | ExportWidgetPayload
    | RunMetricsWidgetPayload,
    Field(discriminator="widget"),
]

_WIDGET_PAYLOAD_ADAPTER = TypeAdapter(WidgetPayload)


def validate_widget_payload(payload: dict[str, Any]):
    return _WIDGET_PAYLOAD_ADAPTER.validate_python(payload)
