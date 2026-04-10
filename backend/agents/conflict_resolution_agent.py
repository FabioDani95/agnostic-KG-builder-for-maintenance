"""Phase 3 ConflictResolutionAgent: detect duplicates and contradictions across extracted triplets."""

from __future__ import annotations

import time
from typing import Any

from backend.app_config import get_agent_config
from backend.graph.store import update_conflict_state
from backend.services.ontology_semantics import corrective_actions_match, failure_modes_match, symptoms_match
from backend.services.run_metrics import record_stage_metrics


def _grounding_score_by_entity(graph_state: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for item in graph_state.get("grounding_results", []) or []:
        entity_id = str(item.get("entity_id", "") or "")
        if not entity_id:
            continue
        scores[entity_id] = float(item.get("grounding_score", 0.0) or 0.0)
    for verdict in graph_state.get("entity_verdicts", []) or []:
        entity_id = str(verdict.get("entity_id", "") or "")
        if not entity_id or entity_id in scores:
            continue
        scores[entity_id] = float(verdict.get("grounding_score", 0.0) or 0.0)
    return scores


def _recommended_resolution(left_id: str, right_id: str, scores: dict[str, float]) -> tuple[str, dict[str, Any] | None]:
    left_score = scores.get(left_id, 0.0)
    right_score = scores.get(right_id, 0.0)
    if abs(left_score - right_score) >= 0.15:
        preferred = left_id if left_score >= right_score else right_id
        return "prefer_higher_confidence", {
            "preferred_entity_id": preferred,
            "preferred_grounding_score": max(left_score, right_score),
        }
    return "merge", {
        "candidate_entity_ids": [left_id, right_id],
        "grounding_scores": {left_id: left_score, right_id: right_score},
    }


def run_conflict_resolution_agent(store: dict[str, Any]) -> list[dict[str, Any]]:
    t0 = time.perf_counter()
    graph_state = store.get("graph_state") or {}
    triplets = list(graph_state.get("cleaned_triplets") or [])
    scores = _grounding_score_by_entity(graph_state)
    conflicts: list[dict[str, Any]] = []

    for left_index, left_triplet in enumerate(triplets):
        left_symptom = left_triplet.get("symptom", {})
        for right_triplet in triplets[left_index + 1:]:
            right_symptom = right_triplet.get("symptom", {})
            if not symptoms_match(
                str(left_symptom.get("name", "") or ""),
                str(left_symptom.get("description", "") or ""),
                str(right_symptom.get("name", "") or ""),
                str(right_symptom.get("description", "") or ""),
            ):
                continue

            left_symptom_id = str(left_symptom.get("symptom_id", "") or "")
            right_symptom_id = str(right_symptom.get("symptom_id", "") or "")
            if str(left_symptom.get("severity", "") or "") != str(right_symptom.get("severity", "") or ""):
                conflicts.append({
                    "entity_ids": [left_symptom_id, right_symptom_id],
                    "conflict_type": "contradictory_severity",
                    "resolution": None,
                    "resolved_entity": None,
                })
            else:
                resolution, resolved_entity = _recommended_resolution(left_symptom_id, right_symptom_id, scores)
                conflicts.append({
                    "entity_ids": [left_symptom_id, right_symptom_id],
                    "conflict_type": "duplicate_symptom",
                    "resolution": resolution,
                    "resolved_entity": resolved_entity,
                })

            for left_failure in left_triplet.get("failure_modes", []):
                for right_failure in right_triplet.get("failure_modes", []):
                    if not failure_modes_match(
                        str(left_failure.get("name", "") or ""),
                        str(left_failure.get("description", "") or ""),
                        str(left_failure.get("material_context", "") or ""),
                        str(right_failure.get("name", "") or ""),
                        str(right_failure.get("description", "") or ""),
                        str(right_failure.get("material_context", "") or ""),
                    ):
                        continue
                    left_failure_id = str(left_failure.get("failure_mode_id", "") or "")
                    right_failure_id = str(right_failure.get("failure_mode_id", "") or "")
                    resolution, resolved_entity = _recommended_resolution(left_failure_id, right_failure_id, scores)
                    conflicts.append({
                        "entity_ids": [left_failure_id, right_failure_id],
                        "conflict_type": "duplicate_failure_mode",
                        "resolution": resolution,
                        "resolved_entity": resolved_entity,
                    })

            for left_action in left_triplet.get("corrective_actions", []):
                for right_action in right_triplet.get("corrective_actions", []):
                    if not corrective_actions_match(
                        str(left_action.get("name", "") or ""),
                        str(left_action.get("description", "") or ""),
                        str(left_action.get("instruction_text", "") or ""),
                        str(right_action.get("name", "") or ""),
                        str(right_action.get("description", "") or ""),
                        str(right_action.get("instruction_text", "") or ""),
                    ):
                        continue
                    left_action_id = str(left_action.get("action_id", "") or "")
                    right_action_id = str(right_action.get("action_id", "") or "")
                    resolution, resolved_entity = _recommended_resolution(left_action_id, right_action_id, scores)
                    conflicts.append({
                        "entity_ids": [left_action_id, right_action_id],
                        "conflict_type": "overlapping_corrective_action",
                        "resolution": resolution,
                        "resolved_entity": resolved_entity,
                    })

    deduped_conflicts: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for conflict in conflicts:
        key = (
            str(conflict.get("conflict_type", "") or ""),
            tuple(sorted(str(entity_id) for entity_id in conflict.get("entity_ids", []) or [])),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped_conflicts.append(conflict)

    record_stage_metrics(
        store,
        "conflict_resolution",
        {
            "stage": "conflict_resolution",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            "llm_calls": 0,
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "non_cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "models": [],
            "operations": ["conflict_resolution"],
            "details": {
                "total_conflicts": len(deduped_conflicts),
                "unresolved_conflicts": sum(1 for item in deduped_conflicts if not item.get("resolution")),
            },
        },
    )
    cfg = get_agent_config("conflict_resolution")
    model_name = str(cfg.get("model") or "")
    update_conflict_state(
        store,
        conflicts=deduped_conflicts,
        cleaned_triplets=list(graph_state.get("cleaned_triplets") or []),
        model_name=model_name or None,
    )
    return deduped_conflicts
