"""Bridge between GraphState and the existing in-memory pdf_store entries."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.graph.config_snapshot import build_config_snapshot, default_selected_models
from backend.graph.state import GraphPhase, GraphState, create_initial_graph_state, utc_now_iso
from backend.runstore import snapshot_store
from backend.schemas.run_state import RunState
from backend.services.run_metrics import project_agent_token_ledger

def persist_graph_state(store: dict[str, Any], state: GraphState) -> GraphState:
    RunState.model_validate(state)
    state["updated_at"] = utc_now_iso()
    store["graph_state"] = state
    store["run_id"] = state["run_id"]
    store["config_snapshot"] = deepcopy(state.get("config_snapshot", {}))
    store["selected_models"] = deepcopy(state.get("selected_models", {}))
    snapshot_store(store)
    return state


def seed_conversation_state(store: dict[str, Any]) -> dict[str, Any]:
    """Initialise store['conversation'] if not already present."""
    if "conversation" not in store:
        store["conversation"] = {
            "messages": [],
            "tool_calls": [],
            "critiques": [],
        }
    return store["conversation"]


def seed_graph_state(store: dict[str, Any], pdf_id: str) -> GraphState:
    """Create the initial GraphState for a freshly loaded manual."""
    existing = store.get("graph_state")
    if existing:
        return existing

    state = create_initial_graph_state(
        pdf_id=pdf_id,
        filename=store.get("filename", ""),
        total_pages=int(store.get("page_count") or len(store.get("pages", [])) or 0),
        source_type=store.get("source_type", ""),
        source_title=store.get("source_title", ""),
        config_snapshot=build_config_snapshot(),
        selected_models=deepcopy(store.get("selected_models") or default_selected_models()),
    )
    return persist_graph_state(store, state)


def ensure_graph_state(store: dict[str, Any], pdf_id: str | None = None) -> GraphState:
    if store.get("graph_state"):
        return store["graph_state"]
    if not pdf_id:
        raise ValueError("pdf_id is required when seeding GraphState for the first time.")
    return seed_graph_state(store, pdf_id)


def refresh_token_ledger(store: dict[str, Any]) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state["token_ledger"] = project_agent_token_ledger(store)
    return persist_graph_state(store, state)


def _record_phase(
    store: dict[str, Any],
    *,
    phase: GraphPhase,
    agent: str,
    decision: str,
    stage_name: str | None = None,
    details: dict[str, Any] | None = None,
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    stage_summary = (store.get("run_metrics") or {}).get("stages", {}).get(stage_name or phase.value, {})
    state["current_phase"] = phase.value
    state.setdefault("phase_history", []).append({
        "phase": phase.value,
        "agent": agent,
        "timestamp": utc_now_iso(),
        "decision": decision,
        "tokens_used": int(stage_summary.get("total_tokens", 0) or 0),
        "llm_calls": int(stage_summary.get("llm_calls", 0) or 0),
        "details": details or {},
    })
    return persist_graph_state(store, state)


def update_scoping_state(store: dict[str, Any], cut_plan, *, model_name: str) -> GraphState:
    state = ensure_graph_state(store, pdf_id=cut_plan.pdf_id)
    state.setdefault("selected_models", {})["scoping"] = model_name
    product_info = cut_plan.product_info.model_dump() if cut_plan.product_info else {}
    state["source_type"] = product_info.get("document_type") or store.get("source_type", "")
    state["source_title"] = product_info.get("product_name") or store.get("source_title", "")
    state["source_language"] = product_info.get("language") or state.get("source_language", "")
    state["selected_pages"] = list(cut_plan.pages_to_keep)
    state["cut_plan"] = cut_plan.model_dump()
    state["scoping_metadata"] = {
        "product_info": product_info,
        "toc": cut_plan.toc.model_dump() if cut_plan.toc else None,
        "page_offset": cut_plan.page_offset,
        "skipped": cut_plan.skipped,
    }
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    return _record_phase(
        store,
        phase=GraphPhase.SCOPING,
        agent="ScopingAgent",
        decision=f"selected {len(cut_plan.pages_to_keep)} pages",
        stage_name="scoping",
        details={
            "total_pages": cut_plan.total_pages,
            "selected_sections": len(cut_plan.sections),
            "skipped": cut_plan.skipped,
        },
    )


def update_cut_plan_approval(
    store: dict[str, Any],
    *,
    pages_to_keep: list[int],
    page_offset: int,
    sections: list[dict[str, Any]],
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state["selected_pages"] = sorted(pages_to_keep)
    state["cut_plan"] = {
        "pdf_id": state["pdf_id"],
        "total_pages": state.get("total_pages", 0),
        "sections": sections,
        "pages_to_keep": sorted(pages_to_keep),
        "page_offset": page_offset,
        "toc": (state.get("cut_plan") or {}).get("toc"),
        "skipped": (state.get("scoping_metadata") or {}).get("skipped", False),
        "product_info": (state.get("scoping_metadata") or {}).get("product_info"),
    }
    metadata = dict(state.get("scoping_metadata", {}))
    metadata["approved"] = True
    state["scoping_metadata"] = metadata
    return persist_graph_state(store, state)


def update_ontology_state(store: dict[str, Any], result, *, model_name: str) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state.setdefault("selected_models", {})["ontology_draft"] = model_name
    state["ontology_pipeline"] = result.model_dump()
    state["ontology_draft"] = result.ontology.model_dump()
    state["ontology_issues"] = [
        issue.model_dump() for issue in (
            list(result.semantic_issues) + list(result.schema_issues) + list(result.graph_issues)
        )
    ]
    state["human_required_fields"] = [field.model_dump() for field in result.human_required_fields]
    state["suggested_relations"] = [relation.model_dump() for relation in result.suggested_relations]
    state["schema_compliant"] = bool(result.is_schema_compliant)
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    return _record_phase(
        store,
        phase=GraphPhase.ONTOLOGY_DRAFT,
        agent="OntologyDraftAgent",
        decision=f"status={result.status}",
        stage_name="ontology",
        details={
            "schema_issue_count": len(result.schema_issues),
            "human_required_count": len(result.human_required_fields),
            "suggested_relation_count": len(result.suggested_relations),
        },
    )


def sync_ontology_pipeline_state(store: dict[str, Any]) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    pipeline_state = deepcopy(store.get("ontology_pipeline") or {})
    state["ontology_pipeline"] = pipeline_state
    state["ontology_draft"] = deepcopy(pipeline_state.get("ontology") or None)
    state["human_required_fields"] = deepcopy(pipeline_state.get("human_required_fields") or [])
    state["suggested_relations"] = deepcopy(pipeline_state.get("suggested_relations") or [])
    state["schema_compliant"] = bool(pipeline_state.get("is_schema_compliant"))
    semantic_issues = pipeline_state.get("semantic_issues") or []
    schema_issues = pipeline_state.get("schema_issues") or []
    graph_issues = pipeline_state.get("graph_issues") or []
    state["ontology_issues"] = deepcopy(semantic_issues + schema_issues + graph_issues)
    return persist_graph_state(store, state)


def update_extraction_state(
    store: dict[str, Any],
    result,
    *,
    model_name: str,
    chunk_metadata: list[dict[str, Any]],
    pages_to_keep: list[int],
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state.setdefault("selected_models", {})["extraction"] = model_name
    serialized_triplets = [triplet.model_dump() for triplet in result.triplets]
    state["selected_pages"] = list(pages_to_keep)
    state["raw_triplets"] = serialized_triplets
    state["cleaned_triplets"] = serialized_triplets
    state["extraction_chunks"] = deepcopy(chunk_metadata)
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    return _record_phase(
        store,
        phase=GraphPhase.EXTRACTION,
        agent="ExtractionAgent",
        decision=f"extracted {len(result.triplets)} triplets",
        stage_name="extraction",
        details={
            "selected_pages": len(pages_to_keep),
            "chunk_count": len(chunk_metadata),
        },
    )


def update_export_state(
    store: dict[str, Any],
    *,
    ontology_payload: dict[str, Any],
    export_base: str,
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state["export_base"] = export_base
    state["final_json"] = deepcopy(ontology_payload)
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    return _record_phase(
        store,
        phase=GraphPhase.EXPORT,
        agent="Export",
        decision=f"exported via {export_base}",
        stage_name="export",
        details={"export_base": export_base},
    )


def update_validation_state(
    store: dict[str, Any],
    *,
    entity_verdicts: list[dict[str, Any]],
    validation_summary: dict[str, Any],
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state["entity_verdicts"] = deepcopy(entity_verdicts)
    state["validation_summary"] = deepcopy(validation_summary)
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    return _record_phase(
        store,
        phase=GraphPhase.VALIDATION,
        agent="ValidationAgent",
        decision=(
            f"accepted={validation_summary.get('accepted', 0)} "
            f"needs_refinement={validation_summary.get('needs_refinement', 0)} "
            f"needs_human={validation_summary.get('needs_human', 0)}"
        ),
        stage_name="validation",
        details=validation_summary,
    )


def _validation_summary_from_verdicts(entity_verdicts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_entities": len(entity_verdicts),
        "accepted": sum(1 for item in entity_verdicts if item.get("verdict") == "accepted"),
        "needs_refinement": sum(1 for item in entity_verdicts if item.get("verdict") == "needs_refinement"),
        "needs_human": sum(1 for item in entity_verdicts if item.get("verdict") == "needs_human"),
        "flagged_entities": sum(1 for item in entity_verdicts if item.get("verdict") != "accepted"),
        "flagged_entity_ids": [
            str(item.get("entity_id", ""))
            for item in entity_verdicts
            if item.get("verdict") != "accepted" and str(item.get("entity_id", ""))
        ],
        "advisory_only": True,
    }


def update_coverage_state(
    store: dict[str, Any],
    *,
    coverage_map: dict[str, Any],
    model_name: str | None = None,
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    if model_name:
        state.setdefault("selected_models", {})["coverage"] = model_name
    state["coverage_map"] = deepcopy(coverage_map)
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    gap_counts: dict[str, int] = {}
    for details in coverage_map.values():
        gap_type = str((details or {}).get("gap_type", "") or "")
        if not gap_type:
            continue
        gap_counts[gap_type] = gap_counts.get(gap_type, 0) + 1
    return _record_phase(
        store,
        phase=GraphPhase.COVERAGE,
        agent="CoverageAgent",
        decision=f"analyzed {len(coverage_map)} selected pages",
        stage_name="coverage",
        details={
            "selected_pages": len(coverage_map),
            "gap_counts": gap_counts,
        },
    )


def update_grounding_state(
    store: dict[str, Any],
    *,
    grounding_results: list[dict[str, Any]],
    entity_verdicts: list[dict[str, Any]],
    model_name: str | None = None,
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    if model_name:
        state.setdefault("selected_models", {})["grounding"] = model_name
    state["grounding_results"] = deepcopy(grounding_results)
    state["entity_verdicts"] = deepcopy(entity_verdicts)
    state["validation_summary"] = _validation_summary_from_verdicts(entity_verdicts)
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    avg_score = (
        sum(float(item.get("grounding_score", 0.0) or 0.0) for item in grounding_results) / len(grounding_results)
        if grounding_results else 0.0
    )
    return _record_phase(
        store,
        phase=GraphPhase.GROUNDING,
        agent="GroundingAgent",
        decision=f"grounded {len(grounding_results)} entities",
        stage_name="grounding",
        details={
            "total_entities": len(grounding_results),
            "average_grounding_score": round(avg_score, 3),
            "flagged_entities": state["validation_summary"].get("flagged_entities", 0),
        },
    )


def update_conflict_state(
    store: dict[str, Any],
    *,
    conflicts: list[dict[str, Any]],
    cleaned_triplets: list[dict[str, Any]] | None = None,
    model_name: str | None = None,
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    if model_name:
        state.setdefault("selected_models", {})["conflict_resolution"] = model_name
    state["conflicts"] = deepcopy(conflicts)
    if cleaned_triplets is not None:
        state["cleaned_triplets"] = deepcopy(cleaned_triplets)
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    resolved = sum(1 for item in conflicts if str(item.get("resolution") or "") not in {"", "escalate"})
    return _record_phase(
        store,
        phase=GraphPhase.CONFLICT_RESOLUTION,
        agent="ConflictResolutionAgent",
        decision=f"conflicts={len(conflicts)} resolved={resolved}",
        stage_name="conflict_resolution",
        details={
            "total_conflicts": len(conflicts),
            "resolved_conflicts": resolved,
            "unresolved_conflicts": max(0, len(conflicts) - resolved),
        },
    )


def update_refinement_state(
    store: dict[str, Any],
    *,
    cleaned_triplets: list[dict[str, Any]],
    refinement_attempts: dict[str, int],
    refinement_log: list[dict[str, Any]],
    model_name: str | None = None,
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    if model_name:
        state.setdefault("selected_models", {})["refiner"] = model_name
    state["cleaned_triplets"] = deepcopy(cleaned_triplets)
    state["refinement_attempts"] = deepcopy(refinement_attempts)
    state["refinement_log"] = deepcopy(refinement_log)
    persist_graph_state(store, state)
    refresh_token_ledger(store)
    updated = sum(1 for item in refinement_log if item.get("result") == "updated")
    exhausted = sum(1 for item in refinement_log if item.get("result") == "exhausted")
    return _record_phase(
        store,
        phase=GraphPhase.REFINEMENT,
        agent="RefinerAgent",
        decision=f"attempted={len(refinement_log)} updated={updated}",
        stage_name="refinement",
        details={
            "attempted_entities": len(refinement_log),
            "updated_entities": updated,
            "exhausted_entities": exhausted,
        },
    )


def set_run_progress(
    store: dict[str, Any],
    *,
    run_status: str,
    next_step: str | None,
    completed: bool = False,
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state["run_status"] = run_status
    state["next_step"] = next_step
    if completed:
        state["completed_at"] = utc_now_iso()
        state["current_phase"] = GraphPhase.COMPLETED.value
    return persist_graph_state(store, state)


def append_supervisor_log(
    store: dict[str, Any],
    entry: dict[str, Any],
    *,
    run_status: str | None = None,
    next_step: str | None = None,
    completed: bool = False,
) -> GraphState:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state.setdefault("supervisor_log", []).append(deepcopy(entry))
    if run_status is not None:
        state["run_status"] = run_status
    if next_step is not None:
        state["next_step"] = next_step
    if completed:
        state["completed_at"] = utc_now_iso()
        state["current_phase"] = GraphPhase.COMPLETED.value
    return persist_graph_state(store, state)


def find_store_by_run_id(store_map: dict[str, dict[str, Any]], run_id: str) -> dict[str, Any] | None:
    for store in store_map.values():
        graph_state = store.get("graph_state") or {}
        if graph_state.get("run_id") == run_id:
            return store
    return None
