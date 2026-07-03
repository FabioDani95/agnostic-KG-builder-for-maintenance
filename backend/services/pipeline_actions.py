"""Single-source-of-truth wrappers for pipeline mutations.

Routers call these functions. The chat orchestrator also calls these
directly, so logic is never duplicated between the two entry points.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.app_config import get_confidence_config
from backend.graph.store import sync_ontology_pipeline_state
from backend.graph.supervisor import record_ontology_review_route
from backend.models import (
    OntologyInstance,
    OntologyPipelineResponse,
    SuggestedRelation,
)
from backend.services.confidence import score_ontology
from backend.services.graph_reasoning import run_graph_analysis
from backend.services.ontology_pipeline import validate_ontology_instance
from backend.services.ontology_schema_service import load_ontology_schema


def apply_ontology_suggestions(
    store: dict,
    accepted_suggestions: list[SuggestedRelation],
) -> OntologyPipelineResponse:
    """Merge accepted graph-reasoning suggestions into the live ontology."""
    pipeline_state = store.get("ontology_pipeline")
    if not pipeline_state:
        raise ValueError("Ontology pipeline has not been run yet.")

    existing = OntologyPipelineResponse.model_validate(pipeline_state)
    ontology_data = deepcopy(existing.ontology.model_dump())

    existing_edges: set[tuple[str, str, str]] = {
        (r["name"], r["from_id"], r["to_id"])
        for r in ontology_data.get("relations", [])
    }

    for suggestion in accepted_suggestions:
        edge_key = (suggestion.relation_name, suggestion.from_id, suggestion.to_id)
        if edge_key in existing_edges:
            continue
        ontology_data["relations"].append({
            "name": suggestion.relation_name,
            "from_type": suggestion.from_type,
            "from_id": suggestion.from_id,
            "to_type": suggestion.to_type,
            "to_id": suggestion.to_id,
            "evidence": [],
        })
        existing_edges.add(edge_key)

    updated_ontology = OntologyInstance.model_validate(ontology_data)
    schema = load_ontology_schema()
    schema_issues, human_fields = validate_ontology_instance(updated_ontology)
    graph_issues, suggested_relations = run_graph_analysis(updated_ontology, schema)

    confidence_cfg = get_confidence_config()
    confidence_report = None
    if confidence_cfg.get("enabled", True):
        confidence_report = score_ontology(
            ontology=updated_ontology,
            schema=schema,
            semantic_issues=existing.semantic_issues,
            schema_issues=schema_issues,
            human_required_fields=human_fields,
            retry_count=existing.retry_count,
            config=confidence_cfg,
        )

    result = OntologyPipelineResponse(
        status="blocked" if schema_issues else ("needs_human" if human_fields else "ready"),
        ontology=updated_ontology,
        semantic_issues=existing.semantic_issues,
        schema_issues=schema_issues,
        human_required_fields=human_fields,
        is_schema_compliant=not schema_issues and not human_fields,
        is_ready_for_human_review=not schema_issues,
        retry_count=existing.retry_count,
        graph_issues=graph_issues,
        suggested_relations=suggested_relations,
        confidence_report=confidence_report,
    )
    store["ontology_pipeline"] = result.model_dump()
    sync_ontology_pipeline_state(store)
    record_ontology_review_route(store)
    return result


def get_current_ontology(store: dict) -> OntologyPipelineResponse | None:
    """Return the current ontology pipeline state, or None."""
    pipeline_state = store.get("ontology_pipeline")
    if not pipeline_state:
        return None
    return OntologyPipelineResponse.model_validate(pipeline_state)


def get_run_phase(store: dict) -> str:
    """Return the current graph phase string."""
    gs = store.get("graph_state") or {}
    return str(gs.get("current_phase") or "loaded")


def get_triplets_from_store(store: dict) -> list[dict[str, Any]]:
    """Return cleaned triplets as dicts (empty list if not yet extracted)."""
    gs = store.get("graph_state") or {}
    return list(gs.get("cleaned_triplets") or store.get("triplets") or [])
