"""Reduced GraphState for the Phase 1 migration layer."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, TypedDict
from uuid import uuid4


class GraphPhase(str, Enum):
    LOADED = "loaded"
    SCOPING = "scoping"
    ONTOLOGY_DRAFT = "ontology_draft"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    COVERAGE = "coverage"
    GROUNDING = "grounding"
    CONFLICT_RESOLUTION = "conflict_resolution"
    REFINEMENT = "refinement"
    EXPORT = "export"
    COMPLETED = "completed"


class EntityVerdict(str, Enum):
    ACCEPTED = "accepted"
    NEEDS_REFINEMENT = "needs_refinement"
    NEEDS_HUMAN = "needs_human"


class GraphState(TypedDict, total=False):
    pdf_id: str
    run_id: str
    current_phase: str
    run_status: str
    next_step: str | None
    started_at: str
    updated_at: str
    completed_at: str | None
    phase_history: list[dict[str, Any]]
    filename: str
    total_pages: int
    source_type: str
    source_title: str
    source_language: str
    selected_pages: list[int]
    cut_plan: dict[str, Any] | None
    scoping_metadata: dict[str, Any]
    ontology_pipeline: dict[str, Any] | None
    ontology_draft: dict[str, Any] | None
    ontology_issues: list[dict[str, Any]]
    human_required_fields: list[dict[str, Any]]
    suggested_relations: list[dict[str, Any]]
    schema_compliant: bool
    raw_triplets: list[dict[str, Any]]
    cleaned_triplets: list[dict[str, Any]]
    extraction_chunks: list[dict[str, Any]]
    entity_verdicts: list[dict[str, Any]]
    validation_summary: dict[str, Any]
    coverage_map: dict[str, Any] | None
    grounding_results: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    refinement_attempts: dict[str, int]
    refinement_log: list[dict[str, Any]]
    supervisor_log: list[dict[str, Any]]
    export_base: str | None
    final_json: dict[str, Any] | None
    token_ledger: dict[str, Any]
    config_snapshot: dict[str, Any]
    selected_models: dict[str, str | None]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_initial_graph_state(
    *,
    pdf_id: str,
    filename: str,
    total_pages: int,
    source_type: str = "",
    source_title: str = "",
    config_snapshot: dict[str, Any] | None = None,
    selected_models: dict[str, str | None] | None = None,
) -> GraphState:
    now = utc_now_iso()
    return GraphState(
        pdf_id=pdf_id,
        run_id=f"run_{uuid4().hex}",
        current_phase=GraphPhase.LOADED.value,
        run_status="loaded",
        next_step=None,
        started_at=now,
        updated_at=now,
        completed_at=None,
        phase_history=[],
        filename=filename,
        total_pages=total_pages,
        source_type=source_type,
        source_title=source_title,
        source_language="",
        selected_pages=[],
        cut_plan=None,
        scoping_metadata={},
        ontology_pipeline=None,
        ontology_draft=None,
        ontology_issues=[],
        human_required_fields=[],
        suggested_relations=[],
        schema_compliant=False,
        raw_triplets=[],
        cleaned_triplets=[],
        extraction_chunks=[],
        entity_verdicts=[],
        validation_summary={
            "total_entities": 0,
            "accepted": 0,
            "needs_refinement": 0,
            "needs_human": 0,
            "flagged_entities": 0,
            "advisory_only": True,
        },
        coverage_map=None,
        grounding_results=[],
        conflicts=[],
        refinement_attempts={},
        refinement_log=[],
        supervisor_log=[],
        export_base=None,
        final_json=None,
        token_ledger={},
        config_snapshot=config_snapshot or {},
        selected_models=selected_models or {
            "scoping": None,
            "ontology_draft": None,
            "extraction": None,
        },
    )
