"""Phase 3 RefinerAgent: targeted, entity-level corrections for advisory refinement candidates."""

from __future__ import annotations

from copy import deepcopy
import re
import time
from difflib import SequenceMatcher
from typing import Any

from backend.app_config import get_agent_config
from backend.graph.state import EntityVerdict
from backend.graph.store import update_refinement_state
from backend.models import CorrectiveAction
from backend.services.llm_service import _normalize_action_against_source
from backend.services.ontology_semantics import normalize_semantic_text, prefer_more_informative_text, semantic_tokens
from backend.services.run_metrics import record_stage_metrics

_SEGMENT_SPLIT_RE = re.compile(r"[\n.;:]+")


def _raw_segments(page_text: str) -> list[str]:
    return [segment.strip() for segment in _SEGMENT_SPLIT_RE.split(str(page_text or "")) if segment.strip()]


def _best_segment(query_parts: list[str], page_texts: dict[int, str], candidate_pages: list[int]) -> str:
    query = " ".join(str(part or "") for part in query_parts if str(part or "").strip()).strip()
    query_norm = normalize_semantic_text(query)
    if not query_norm:
        return ""
    query_tokens = set(semantic_tokens(query_norm))
    best_score = 0.0
    best_segment = ""
    pages = candidate_pages or list(page_texts.keys())
    for page in pages:
        for segment in _raw_segments(page_texts.get(int(page), "")):
            segment_norm = normalize_semantic_text(segment)
            if not segment_norm:
                continue
            segment_tokens = set(semantic_tokens(segment_norm))
            overlap = (
                len(query_tokens & segment_tokens) / len(query_tokens)
                if query_tokens else 0.0
            )
            ratio = SequenceMatcher(a=query_norm, b=segment_norm).ratio()
            score = max(overlap, ratio)
            if score > best_score:
                best_score = score
                best_segment = segment
    return best_segment if best_score >= 0.45 else ""


def _relevant_pages_for_triplet(triplet: dict[str, Any], fallback_pages: list[int]) -> list[int]:
    action_pages = [
        int(action.get("source_page", 0) or 0)
        for action in triplet.get("corrective_actions", [])
        if int(action.get("source_page", 0) or 0) > 0
    ]
    return sorted(set(action_pages)) if action_pages else list(fallback_pages)


def _page_text_by_page(store: dict[str, Any], selected_pages: list[int]) -> dict[int, str]:
    selected = set(int(page) for page in selected_pages)
    return {
        int(page["page_number"]): str(page.get("text", "") or "")
        for page in store.get("pages", [])
        if not selected or int(page["page_number"]) in selected
    }


def _refine_action(action: dict[str, Any], page_texts: dict[int, str]) -> tuple[dict[str, Any], str]:
    source_page = int(action.get("source_page", 0) or 0)
    page_text = page_texts.get(source_page, "")
    if not page_text:
        return action, "skipped: cited source page text is unavailable"
    normalized = _normalize_action_against_source(
        CorrectiveAction.model_validate(action),
        {source_page: page_text},
    )
    if normalized is not None:
        updated = normalized.model_dump()
        if updated != action:
            return updated, "updated action fields from grounded source-page steps"
    segment = _best_segment(
        [str(action.get("instruction_text", "")), str(action.get("description", "")), str(action.get("name", ""))],
        page_texts,
        [source_page],
    )
    if not segment:
        return action, "skipped: no stronger grounded procedural segment found"
    updated = dict(action)
    updated["instruction_text"] = segment
    updated["description"] = prefer_more_informative_text(str(updated.get("description", "")), segment)
    if updated != action:
        return updated, "updated corrective action from best matching grounded segment"
    return action, "skipped: grounded segment did not improve the entity"


def _refine_text_entity(
    entity: dict[str, Any],
    *,
    query_parts: list[str],
    page_texts: dict[int, str],
    candidate_pages: list[int],
    description_field: str = "description",
) -> tuple[dict[str, Any], str]:
    segment = _best_segment(query_parts, page_texts, candidate_pages)
    if not segment:
        return entity, "skipped: no grounded supporting segment found"
    updated = dict(entity)
    updated[description_field] = prefer_more_informative_text(str(updated.get(description_field, "")), segment)
    if updated != entity:
        return updated, "updated descriptive text from best matching grounded segment"
    return entity, "skipped: grounded segment did not improve the entity"


def _refine_entity_in_triplets(
    triplets: list[dict[str, Any]],
    verdict: dict[str, Any],
    page_texts: dict[int, str],
    fallback_pages: list[int],
) -> tuple[bool, str]:
    entity_id = str(verdict.get("entity_id", "") or "")
    entity_type = str(verdict.get("entity_type", "") or "")
    candidate_pages = [
        int(page or 0)
        for page in (verdict.get("source_pages") or [verdict.get("source_page", 0)])
        if int(page or 0) > 0
    ]
    for triplet in triplets:
        relevant_pages = candidate_pages or _relevant_pages_for_triplet(triplet, fallback_pages)
        symptom = triplet.get("symptom", {})
        if entity_type == "Symptom" and str(symptom.get("symptom_id", "") or "") == entity_id:
            updated, reasoning = _refine_text_entity(
                symptom,
                query_parts=[str(symptom.get("name", "")), str(symptom.get("description", ""))],
                page_texts=page_texts,
                candidate_pages=relevant_pages,
            )
            if updated != symptom:
                triplet["symptom"] = updated
                return True, reasoning
            return False, reasoning

        for index, failure_mode in enumerate(triplet.get("failure_modes", [])):
            if entity_type != "FailureMode" or str(failure_mode.get("failure_mode_id", "") or "") != entity_id:
                continue
            updated, reasoning = _refine_text_entity(
                failure_mode,
                query_parts=[
                    str(failure_mode.get("name", "")),
                    str(failure_mode.get("description", "")),
                    str(failure_mode.get("material_context", "")),
                ],
                page_texts=page_texts,
                candidate_pages=relevant_pages,
            )
            if updated != failure_mode:
                triplet["failure_modes"][index] = updated
                return True, reasoning
            return False, reasoning

        for index, action in enumerate(triplet.get("corrective_actions", [])):
            if entity_type != "CorrectiveAction" or str(action.get("action_id", "") or "") != entity_id:
                continue
            updated, reasoning = _refine_action(action, page_texts)
            if updated != action:
                triplet["corrective_actions"][index] = updated
                return True, reasoning
            return False, reasoning
    return False, "skipped: entity not found in current cleaned triplets"


def run_refiner_agent(store: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    cfg = get_agent_config("refiner")
    max_retries = int(cfg.get("max_retries_per_entity", 2) or 2)
    graph_state = store.get("graph_state") or {}
    selected_pages = list(graph_state.get("selected_pages") or [])
    triplets = deepcopy(list(graph_state.get("cleaned_triplets") or []))
    verdicts = list(graph_state.get("entity_verdicts") or [])
    refinement_attempts = dict(graph_state.get("refinement_attempts") or {})
    refinement_log = list(graph_state.get("refinement_log") or [])
    page_texts = _page_text_by_page(store, selected_pages)
    changed_entity_ids: list[str] = []

    for verdict in verdicts:
        if str(verdict.get("verdict", "") or "") != EntityVerdict.NEEDS_REFINEMENT.value:
            continue
        entity_id = str(verdict.get("entity_id", "") or "")
        attempts = int(refinement_attempts.get(entity_id, 0) or 0)
        if attempts >= max_retries:
            refinement_log.append({
                "entity_id": entity_id,
                "attempt": attempts,
                "result": "exhausted",
                "reasoning": f"max retries reached ({max_retries})",
            })
            continue
        changed, reasoning = _refine_entity_in_triplets(triplets, verdict, page_texts, selected_pages)
        refinement_attempts[entity_id] = attempts + 1
        if changed:
            changed_entity_ids.append(entity_id)
        refinement_log.append({
            "entity_id": entity_id,
            "attempt": attempts + 1,
            "result": "updated" if changed else "skipped",
            "reasoning": reasoning,
        })

    record_stage_metrics(
        store,
        "refinement",
        {
            "stage": "refinement",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            "llm_calls": 0,
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "non_cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "models": [],
            "operations": ["refinement"],
            "details": {
                "attempted_entities": len([
                    verdict for verdict in verdicts
                    if str(verdict.get("verdict", "") or "") == EntityVerdict.NEEDS_REFINEMENT.value
                ]),
                "updated_entities": len(changed_entity_ids),
                "exhausted_entities": sum(1 for item in refinement_log if item.get("result") == "exhausted"),
            },
        },
    )
    model_name = str(cfg.get("model") or "")
    update_refinement_state(
        store,
        cleaned_triplets=triplets,
        refinement_attempts=refinement_attempts,
        refinement_log=refinement_log,
        model_name=model_name or None,
    )
    attempted_entity_ids = [
        str(verdict.get("entity_id", "") or "")
        for verdict in verdicts
        if str(verdict.get("verdict", "") or "") == EntityVerdict.NEEDS_REFINEMENT.value
        and str(verdict.get("entity_id", "") or "")
    ]
    exhausted_entity_ids = [
        str(item.get("entity_id", "") or "")
        for item in refinement_log
        if item.get("result") == "exhausted" and str(item.get("entity_id", "") or "")
    ]
    return {
        "attempted_entity_ids": attempted_entity_ids,
        "changed_entity_ids": changed_entity_ids,
        "exhausted_entity_ids": exhausted_entity_ids,
        "refinement_log": refinement_log,
    }
