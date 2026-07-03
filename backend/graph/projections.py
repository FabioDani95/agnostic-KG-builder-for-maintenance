"""Read-only projections for multi-agent run state."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.graph.state import GraphPhase
from backend.graph.store import ensure_graph_state


def _progress_percent_for_phase(current_phase: str) -> int:
    return {
        GraphPhase.LOADED.value: 0,
        GraphPhase.SCOPING.value: 20,
        GraphPhase.ONTOLOGY_DRAFT.value: 45,
        GraphPhase.EXTRACTION.value: 70,
        GraphPhase.VALIDATION.value: 85,
        GraphPhase.COVERAGE.value: 88,
        GraphPhase.GROUNDING.value: 90,
        GraphPhase.CONFLICT_RESOLUTION.value: 92,
        GraphPhase.REFINEMENT.value: 94,
        GraphPhase.EXPORT.value: 95,
        GraphPhase.COMPLETED.value: 100,
    }.get(str(current_phase or ""), 0)


def _coverage_summary(coverage_map: dict[str, Any] | None) -> dict[str, Any]:
    coverage_map = coverage_map or {}
    gap_counts: dict[str, int] = {}
    flagged_pages = 0
    for item in coverage_map.values():
        details = item or {}
        gap_type = str(details.get("gap_type", "") or "")
        if gap_type:
            gap_counts[gap_type] = gap_counts.get(gap_type, 0) + 1
        if details.get("review_required"):
            flagged_pages += 1
    return {
        "selected_pages": len(coverage_map),
        "gap_counts": gap_counts,
        "flagged_pages": flagged_pages,
    }


def _grounding_summary(grounding_results: list[dict[str, Any]] | None) -> dict[str, Any]:
    grounding_results = grounding_results or []
    total = len(grounding_results)
    weak = sum(1 for item in grounding_results if float(item.get("grounding_score", 0.0) or 0.0) < 0.5)
    average = (
        sum(float(item.get("grounding_score", 0.0) or 0.0) for item in grounding_results) / total
        if total else 0.0
    )
    return {
        "total_entities": total,
        "weak_grounding_entities": weak,
        "average_grounding_score": round(average, 3),
    }


def _conflict_summary(conflicts: list[dict[str, Any]] | None) -> dict[str, Any]:
    conflicts = conflicts or []
    resolved = sum(1 for item in conflicts if str(item.get("resolution") or "") not in {"", "escalate"})
    return {
        "total_conflicts": len(conflicts),
        "resolved_conflicts": resolved,
        "unresolved_conflicts": max(0, len(conflicts) - resolved),
    }


def _refinement_summary(refinement_log: list[dict[str, Any]] | None) -> dict[str, Any]:
    refinement_log = refinement_log or []
    return {
        "total_attempts": len(refinement_log),
        "updated_entities": sum(1 for item in refinement_log if item.get("result") == "updated"),
        "skipped_entities": sum(1 for item in refinement_log if item.get("result") == "skipped"),
        "exhausted_entities": sum(1 for item in refinement_log if item.get("result") == "exhausted"),
    }


def build_status_payload(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    supervisor_log = state.get("supervisor_log", [])
    return {
        "run_id": state.get("run_id"),
        "pdf_id": state.get("pdf_id"),
        "filename": state.get("filename", ""),
        "pipeline_mode": state.get("config_snapshot", {}).get("pipeline", {}).get("mode", "multi_agent"),
        "current_phase": state.get("current_phase"),
        "run_status": state.get("run_status", "loaded"),
        "next_step": state.get("next_step"),
        "progress_percent": _progress_percent_for_phase(state.get("current_phase", "")),
        "started_at": state.get("started_at"),
        "updated_at": state.get("updated_at"),
        "completed_at": state.get("completed_at"),
        "selected_pages": state.get("selected_pages", []),
        "validation_summary": deepcopy(state.get("validation_summary", {})),
        "coverage_summary": _coverage_summary(state.get("coverage_map")),
        "grounding_summary": _grounding_summary(state.get("grounding_results")),
        "conflict_summary": _conflict_summary(state.get("conflicts")),
        "refinement_summary": _refinement_summary(state.get("refinement_log")),
        "last_supervisor_decision": deepcopy(supervisor_log[-1]) if supervisor_log else None,
        "token_ledger": deepcopy(state.get("token_ledger", {})),
        "phase_history": deepcopy(state.get("phase_history", [])),
    }


def build_audit_payload(store: dict[str, Any]) -> dict[str, Any]:
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    return {
        "run_id": state.get("run_id"),
        "pdf_id": state.get("pdf_id"),
        "filename": state.get("filename", ""),
        "started_at": state.get("started_at"),
        "updated_at": state.get("updated_at"),
        "completed_at": state.get("completed_at"),
        "current_phase": state.get("current_phase"),
        "run_status": state.get("run_status", "loaded"),
        "next_step": state.get("next_step"),
        "phase_history": deepcopy(state.get("phase_history", [])),
        "supervisor_log": deepcopy(state.get("supervisor_log", [])),
        "validation_summary": deepcopy(state.get("validation_summary", {})),
        "entity_verdicts": deepcopy(state.get("entity_verdicts", [])),
        "coverage_map": deepcopy(state.get("coverage_map")),
        "grounding_results": deepcopy(state.get("grounding_results", [])),
        "conflicts": deepcopy(state.get("conflicts", [])),
        "refinement_attempts": deepcopy(state.get("refinement_attempts", {})),
        "refinement_log": deepcopy(state.get("refinement_log", [])),
        "token_ledger": deepcopy(state.get("token_ledger", {})),
        "export_base": state.get("export_base"),
    }
