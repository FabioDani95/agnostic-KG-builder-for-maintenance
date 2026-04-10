"""Deterministic, non-intrusive supervisor audit for Phases 2 and 3."""

from __future__ import annotations

from hashlib import sha1
import json
from typing import Any

from backend.graph.store import append_supervisor_log, ensure_graph_state
from backend.graph.state import GraphPhase, utc_now_iso


def _phase_token_agent(phase_from: str) -> str:
    return {
        GraphPhase.SCOPING.value: "scoping_agent",
        GraphPhase.ONTOLOGY_DRAFT.value: "ontology_draft_agent",
        GraphPhase.EXTRACTION.value: "extraction_agent",
        GraphPhase.VALIDATION.value: "validation_agent",
        GraphPhase.COVERAGE.value: "coverage_agent",
        GraphPhase.GROUNDING.value: "grounding_agent",
        GraphPhase.CONFLICT_RESOLUTION.value: "conflict_resolution_agent",
        GraphPhase.REFINEMENT.value: "refiner_agent",
        GraphPhase.EXPORT.value: "export",
    }.get(phase_from, "")


def _first_advanced_step(
    *,
    coverage_enabled: bool,
    grounding_enabled: bool,
    conflict_enabled: bool,
    refiner_enabled: bool,
    has_refinement_candidates: bool,
) -> str:
    if coverage_enabled:
        return "coverage_agent"
    if grounding_enabled:
        return "grounding_agent"
    if refiner_enabled and has_refinement_candidates:
        return "refiner_agent"
    if conflict_enabled:
        return "conflict_resolution_agent"
    return "triplet_review"


def _state_snapshot_hash(state: dict[str, Any]) -> str:
    payload = {
        "current_phase": state.get("current_phase"),
        "selected_pages": state.get("selected_pages", []),
        "validation_summary": state.get("validation_summary", {}),
        "export_base": state.get("export_base"),
        "phase_history_count": len(state.get("phase_history", [])),
    }
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return sha1(encoded).hexdigest()[:12]


def _route_summary(
    *,
    state: dict[str, Any],
    phase_from: str,
    phase_to: str,
    condition_met: str,
    reasoning: str,
    entities_affected: list[str] | None = None,
) -> dict[str, Any]:
    validation_summary = state.get("validation_summary", {})
    return {
        "timestamp": utc_now_iso(),
        "run_id": state.get("run_id"),
        "phase_from": phase_from,
        "phase_to": phase_to,
        "decision_type": "deterministic",
        "condition_met": condition_met,
        "entities_affected": list(entities_affected or []),
        "reasoning": reasoning,
        "state_snapshot_hash": _state_snapshot_hash(state),
        "next_agent": phase_to,
        "token_budget_used_this_phase": int(
            state.get("token_ledger", {}).get(_phase_token_agent(phase_from), {}).get("total_tokens", 0) or 0
        ),
        "validation_summary": validation_summary,
    }


def record_scoping_route(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.SCOPING.value,
        phase_to="cut_plan_review",
        condition_met="phase1_and_phase2_preserve_sequential_operator_flow",
        reasoning="Scoping completed; operator cut-plan review remains the next step.",
    )
    append_supervisor_log(store, entry, run_status="awaiting_operator", next_step="cut_plan_review")
    return entry


def record_cut_plan_approval_route(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    entry = _route_summary(
        state=state,
        phase_from="cut_plan_review",
        phase_to="ontology_draft_agent",
        condition_met="operator_approved_cut_plan",
        reasoning="Approved pages are available; ontology drafting is the next deterministic step.",
    )
    append_supervisor_log(store, entry, run_status="in_progress", next_step="ontology_draft_agent")
    return entry


def record_ontology_route(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.ONTOLOGY_DRAFT.value,
        phase_to="ontology_review",
        condition_met="preserve_existing_ontology_review_screen",
        reasoning="Ontology draft completed; operator review remains mandatory in the current flow.",
    )
    append_supervisor_log(store, entry, run_status="awaiting_operator", next_step="ontology_review")
    return entry


def record_ontology_review_route(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    entry = _route_summary(
        state=state,
        phase_from="ontology_review",
        phase_to="extraction_agent",
        condition_met="ontology_review_state_saved",
        reasoning="The reviewed ontology context is stored; triplet extraction is the next deterministic step.",
    )
    append_supervisor_log(store, entry, run_status="in_progress", next_step="extraction_agent")
    return entry


def record_extraction_route(
    store: dict[str, Any],
    *,
    validation_enabled: bool,
    coverage_enabled: bool = False,
    grounding_enabled: bool = False,
    conflict_enabled: bool = False,
    refiner_enabled: bool = False,
) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    next_step = (
        "validation_agent"
        if validation_enabled
        else _first_advanced_step(
            coverage_enabled=coverage_enabled,
            grounding_enabled=grounding_enabled,
            conflict_enabled=conflict_enabled,
            refiner_enabled=refiner_enabled,
            has_refinement_candidates=bool(state.get("validation_summary", {}).get("needs_refinement", 0)),
        )
    )
    if validation_enabled:
        condition = "validation_enabled=true"
        reasoning = "Extraction completed; run the advisory ValidationAgent before the triplet review screen."
    elif next_step != "triplet_review":
        enabled_flags = ",".join([
            name for name, enabled in (
                ("coverage", coverage_enabled),
                ("grounding", grounding_enabled),
                ("conflict_resolution", conflict_enabled),
            )
            if enabled
        ])
        condition = f"validation_enabled=false,advanced_agents_enabled={enabled_flags}"
        reasoning = (
            "Extraction completed; ValidationAgent is disabled, so continue through the enabled Phase 3 "
            "advisory agents before returning to triplet review."
        )
    else:
        condition = "validation_enabled=false"
        reasoning = "Extraction completed; proceed directly to the existing triplet review screen."
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.EXTRACTION.value,
        phase_to=next_step,
        condition_met=condition,
        reasoning=reasoning,
    )
    append_supervisor_log(
        store,
        entry,
        run_status="in_progress" if validation_enabled else "awaiting_operator",
        next_step=next_step,
    )
    return entry


def record_validation_route(
    store: dict[str, Any],
    *,
    coverage_enabled: bool = False,
    grounding_enabled: bool = False,
    conflict_enabled: bool = False,
    refiner_enabled: bool = False,
) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    flagged_ids = list(state.get("validation_summary", {}).get("flagged_entity_ids", []))
    has_refinement_candidates = bool(state.get("validation_summary", {}).get("needs_refinement", 0))
    next_step = _first_advanced_step(
        coverage_enabled=coverage_enabled,
        grounding_enabled=grounding_enabled,
        conflict_enabled=conflict_enabled,
        refiner_enabled=refiner_enabled,
        has_refinement_candidates=has_refinement_candidates,
    )
    if next_step == "triplet_review":
        condition_met = "phase2_validation_is_advisory_only"
        reasoning = (
            "Validation flags are recorded for operator visibility, but the pipeline preserves the "
            "existing triplet review flow and does not auto-refine or auto-export."
        )
    else:
        enabled_flags = ",".join([
            name for name, enabled in (
                ("coverage", coverage_enabled),
                ("grounding", grounding_enabled),
                ("conflict_resolution", conflict_enabled),
                ("refiner", refiner_enabled and has_refinement_candidates),
            )
            if enabled
        ])
        condition_met = f"advanced_agents_enabled={enabled_flags}"
        reasoning = (
            "Validation completed; continue through the enabled Phase 3 advisory agents before returning "
            "to the existing triplet review screen."
        )
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.VALIDATION.value,
        phase_to=next_step,
        condition_met=condition_met,
        reasoning=reasoning,
        entities_affected=flagged_ids,
    )
    append_supervisor_log(
        store,
        entry,
        run_status="awaiting_operator" if next_step == "triplet_review" else "in_progress",
        next_step=next_step,
    )
    return entry


def record_coverage_route(
    store: dict[str, Any],
    *,
    grounding_enabled: bool = False,
    conflict_enabled: bool = False,
    refiner_enabled: bool = False,
) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    next_step = _first_advanced_step(
        coverage_enabled=False,
        grounding_enabled=grounding_enabled,
        conflict_enabled=conflict_enabled,
        refiner_enabled=refiner_enabled,
        has_refinement_candidates=bool(state.get("validation_summary", {}).get("needs_refinement", 0)),
    )
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.COVERAGE.value,
        phase_to=next_step,
        condition_met="coverage_completed",
        reasoning=(
            "Coverage gaps are logged; continue through the remaining enabled advisory agents before operator review."
            if next_step != "triplet_review"
            else "Coverage analysis is complete; return to the existing triplet review step."
        ),
    )
    append_supervisor_log(
        store,
        entry,
        run_status="awaiting_operator" if next_step == "triplet_review" else "in_progress",
        next_step=next_step,
    )
    return entry


def record_grounding_route(
    store: dict[str, Any],
    *,
    conflict_enabled: bool = False,
    refiner_enabled: bool = False,
) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    next_step = _first_advanced_step(
        coverage_enabled=False,
        grounding_enabled=False,
        conflict_enabled=conflict_enabled,
        refiner_enabled=refiner_enabled,
        has_refinement_candidates=bool(state.get("validation_summary", {}).get("needs_refinement", 0)),
    )
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.GROUNDING.value,
        phase_to=next_step,
        condition_met="grounding_completed",
        reasoning=(
            "Grounding evidence has been recorded; continue with the remaining enabled advisory steps."
            if next_step != "triplet_review"
            else "Grounding completed; return to the operator triplet review screen."
        ),
        entities_affected=list(state.get("validation_summary", {}).get("flagged_entity_ids", [])),
    )
    append_supervisor_log(
        store,
        entry,
        run_status="awaiting_operator" if next_step == "triplet_review" else "in_progress",
        next_step=next_step,
    )
    return entry


def record_conflict_route(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    next_step = "triplet_review"
    conflict_ids = [
        entity_id
        for item in state.get("conflicts", [])
        for entity_id in item.get("entity_ids", []) or []
    ]
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.CONFLICT_RESOLUTION.value,
        phase_to=next_step,
        condition_met="conflict_analysis_completed",
        reasoning="Conflict analysis completed; return to the operator triplet review screen.",
        entities_affected=conflict_ids,
    )
    append_supervisor_log(
        store,
        entry,
        run_status="awaiting_operator" if next_step == "triplet_review" else "in_progress",
        next_step=next_step,
    )
    return entry


def record_refinement_route(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    affected_ids = [item.get("entity_id", "") for item in state.get("refinement_log", []) if item.get("entity_id")]
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.REFINEMENT.value,
        phase_to="validation_agent",
        condition_met="targeted_refinement_applied",
        reasoning=(
            "Targeted refinement updated advisory extraction output; re-run validation before returning "
            "to the operator review screen."
        ),
        entities_affected=affected_ids,
    )
    append_supervisor_log(store, entry, run_status="in_progress", next_step="validation_agent")
    return entry


def record_export_route(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    entry = _route_summary(
        state=state,
        phase_from=GraphPhase.EXPORT.value,
        phase_to=GraphPhase.COMPLETED.value,
        condition_met="export_generated_successfully",
        reasoning="Export is complete; mark the run as completed without changing the existing file output behavior.",
    )
    append_supervisor_log(store, entry, run_status="completed", next_step=None, completed=True)
    return entry
