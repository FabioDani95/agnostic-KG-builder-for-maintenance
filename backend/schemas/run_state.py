from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunState(BaseModel):
    """Persistable typed wrapper for the in-memory multi-agent run state."""

    model_config = ConfigDict(extra="allow")

    pdf_id: str
    run_id: str
    current_phase: str
    run_status: str = "loaded"
    next_step: str | None = None
    started_at: str
    updated_at: str
    completed_at: str | None = None
    phase_history: list[dict[str, Any]] = Field(default_factory=list)
    filename: str = ""
    total_pages: int = 0
    source_type: str = ""
    source_title: str = ""
    selected_pages: list[int] = Field(default_factory=list)
    cut_plan: dict[str, Any] | None = None
    ontology_pipeline: dict[str, Any] | None = None
    ontology_draft: dict[str, Any] | None = None
    ontology_issues: list[dict[str, Any]] = Field(default_factory=list)
    human_required_fields: list[dict[str, Any]] = Field(default_factory=list)
    suggested_relations: list[dict[str, Any]] = Field(default_factory=list)
    schema_compliant: bool = False
    raw_triplets: list[dict[str, Any]] = Field(default_factory=list)
    cleaned_triplets: list[dict[str, Any]] = Field(default_factory=list)
    extraction_chunks: list[dict[str, Any]] = Field(default_factory=list)
    entity_verdicts: list[dict[str, Any]] = Field(default_factory=list)
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    coverage_map: dict[Any, Any] | None = None
    grounding_results: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    refinement_attempts: dict[str, int] = Field(default_factory=dict)
    refinement_log: list[dict[str, Any]] = Field(default_factory=list)
    supervisor_log: list[dict[str, Any]] = Field(default_factory=list)
    export_base: str | None = None
    final_json: dict[str, Any] | None = None
    token_ledger: dict[str, Any] = Field(default_factory=dict)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
    selected_models: dict[str, str | None] = Field(default_factory=dict)
