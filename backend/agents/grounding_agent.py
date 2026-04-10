"""Phase 3 GroundingAgent: focused text-level verification for extracted entities."""

from __future__ import annotations

import re
import time
from difflib import SequenceMatcher
from typing import Any

from backend.app_config import get_agents_config, get_validation_config
from backend.graph.state import EntityVerdict
from backend.graph.store import update_grounding_state
from backend.services.llm_service import _fragment_supported_by_page
from backend.services.ontology_semantics import (
    informative_instruction_steps,
    normalize_semantic_text,
    semantic_tokens,
)
from backend.services.run_metrics import record_stage_metrics

_SEGMENT_SPLIT_RE = re.compile(r"[\n.;:]+")
_VERDICT_ORDER = {
    EntityVerdict.ACCEPTED.value: 0,
    EntityVerdict.NEEDS_REFINEMENT.value: 1,
    EntityVerdict.NEEDS_HUMAN.value: 2,
}


def _page_text_by_page(store: dict[str, Any], selected_pages: list[int]) -> dict[int, str]:
    selected = set(int(page) for page in selected_pages)
    return {
        int(page["page_number"]): str(page.get("text", "") or "")
        for page in store.get("pages", [])
        if not selected or int(page["page_number"]) in selected
    }


def _relevant_pages(triplet: dict[str, Any], selected_pages: list[int]) -> list[int]:
    action_pages = [
        int(action.get("source_page", 0) or 0)
        for action in triplet.get("corrective_actions", [])
        if int(action.get("source_page", 0) or 0) > 0
    ]
    return sorted(set(action_pages)) if action_pages else list(selected_pages)


def _raw_segments(page_text: str) -> list[str]:
    return [segment.strip() for segment in _SEGMENT_SPLIT_RE.split(str(page_text or "")) if segment.strip()]


def _best_support(fragment: str, page_text: str) -> tuple[float, str]:
    fragment_norm = normalize_semantic_text(fragment)
    if not fragment_norm or not page_text:
        return 0.0, ""
    if _fragment_supported_by_page(fragment, page_text):
        for segment in _raw_segments(page_text):
            if _fragment_supported_by_page(fragment, segment):
                return 1.0, segment
        return 1.0, str(page_text or "").strip()[:240]

    fragment_tokens = set(semantic_tokens(fragment_norm))
    best_score = 0.0
    best_segment = ""
    for segment in _raw_segments(page_text):
        segment_norm = normalize_semantic_text(segment)
        if not segment_norm:
            continue
        ratio = SequenceMatcher(a=fragment_norm, b=segment_norm).ratio()
        segment_tokens = set(semantic_tokens(segment_norm))
        overlap = (
            len(fragment_tokens & segment_tokens) / len(fragment_tokens)
            if fragment_tokens else 0.0
        )
        score = max(ratio, overlap)
        if score > best_score:
            best_score = score
            best_segment = segment
    return round(best_score, 3), best_segment


def _ground_symptom(triplet: dict[str, Any], page_texts: dict[int, str], selected_pages: list[int]) -> dict[str, Any]:
    symptom = triplet.get("symptom", {})
    relevant_pages = _relevant_pages(triplet, selected_pages)
    best_name = (0.0, "")
    best_description = (0.0, "")
    source_page = relevant_pages[0] if relevant_pages else 0
    for page in relevant_pages:
        page_text = page_texts.get(page, "")
        candidate_name = _best_support(str(symptom.get("name", "")), page_text)
        candidate_description = _best_support(str(symptom.get("description", "")), page_text)
        if candidate_name[0] > best_name[0]:
            best_name = candidate_name
            source_page = page
        if candidate_description[0] > best_description[0]:
            best_description = candidate_description
            if candidate_description[0] >= best_name[0]:
                source_page = page

    score = round((0.55 * best_name[0]) + (0.45 * best_description[0]), 3)
    issues: list[str] = []
    if score < 0.8:
        issues.append("symptom text is not strongly supported by source-page wording")
    supporting_text = best_name[1] or best_description[1]
    return {
        "entity_id": str(symptom.get("symptom_id", "") or ""),
        "entity_type": "Symptom",
        "source_page": source_page,
        "grounding_score": score,
        "supporting_text": supporting_text,
        "issues": issues,
    }


def _ground_failure_mode(
    triplet: dict[str, Any],
    failure_mode: dict[str, Any],
    page_texts: dict[int, str],
    selected_pages: list[int],
) -> dict[str, Any]:
    relevant_pages = _relevant_pages(triplet, selected_pages)
    best_name = (0.0, "")
    best_description = (0.0, "")
    best_context = (0.0, "")
    source_page = relevant_pages[0] if relevant_pages else 0
    for page in relevant_pages:
        page_text = page_texts.get(page, "")
        candidate_name = _best_support(str(failure_mode.get("name", "")), page_text)
        candidate_description = _best_support(str(failure_mode.get("description", "")), page_text)
        candidate_context = _best_support(str(failure_mode.get("material_context", "")), page_text)
        if max(candidate_name[0], candidate_description[0], candidate_context[0]) >= max(
            best_name[0], best_description[0], best_context[0],
        ):
            source_page = page
        if candidate_name[0] > best_name[0]:
            best_name = candidate_name
        if candidate_description[0] > best_description[0]:
            best_description = candidate_description
        if candidate_context[0] > best_context[0]:
            best_context = candidate_context

    score = round(
        (0.35 * best_name[0]) + (0.35 * best_description[0]) + (0.30 * best_context[0]),
        3,
    )
    issues: list[str] = []
    if best_context[0] < 0.55:
        issues.append("failure mode material context is weakly supported by the cited pages")
    if score < 0.8:
        issues.append("failure mode wording is only partially grounded in source text")
    supporting_text = best_name[1] or best_description[1] or best_context[1]
    return {
        "entity_id": str(failure_mode.get("failure_mode_id", "") or ""),
        "entity_type": "FailureMode",
        "source_page": source_page,
        "grounding_score": score,
        "supporting_text": supporting_text,
        "issues": issues,
    }


def _ground_action(action: dict[str, Any], page_texts: dict[int, str]) -> dict[str, Any]:
    source_page = int(action.get("source_page", 0) or 0)
    page_text = page_texts.get(source_page, "")
    issues: list[str] = []
    if source_page <= 0:
        issues.append("corrective action has no cited source page")
    if source_page > 0 and not page_text:
        issues.append("cited source page is unavailable for grounding")
    name_score, name_support = _best_support(str(action.get("name", "")), page_text)
    description_score, description_support = _best_support(str(action.get("description", "")), page_text)
    steps = informative_instruction_steps(str(action.get("instruction_text", "")))
    step_scores: list[float] = []
    step_support = ""
    for step in steps:
        score, support = _best_support(step, page_text)
        step_scores.append(score)
        if score >= 0.8 and support and not step_support:
            step_support = support
    step_score = (sum(step_scores) / len(step_scores)) if step_scores else 0.0
    score = round((0.25 * name_score) + (0.20 * description_score) + (0.55 * step_score), 3)
    if steps and step_score < 0.65:
        issues.append("corrective action steps are weakly supported by the cited page")
    if score < 0.8:
        issues.append("corrective action grounding is below the advisory accept threshold")
    supporting_text = step_support or description_support or name_support
    return {
        "entity_id": str(action.get("action_id", "") or ""),
        "entity_type": "CorrectiveAction",
        "source_page": source_page,
        "grounding_score": score,
        "supporting_text": supporting_text,
        "issues": issues,
    }


def _verdict_for_score(score: float, cfg: dict[str, Any]) -> str:
    accept_threshold = float(cfg.get("grounding_accept_threshold", 0.8))
    refine_threshold = float(cfg.get("grounding_refine_threshold", 0.5))
    if score >= accept_threshold:
        return EntityVerdict.ACCEPTED.value
    if score >= refine_threshold:
        return EntityVerdict.NEEDS_REFINEMENT.value
    return EntityVerdict.NEEDS_HUMAN.value


def _base_verdicts_from_triplets(triplets: list[dict[str, Any]], selected_pages: list[int]) -> list[dict[str, Any]]:
    base_verdicts: list[dict[str, Any]] = []
    for triplet in triplets:
        relevant_pages = _relevant_pages(triplet, selected_pages)
        symptom = triplet.get("symptom", {})
        base_verdicts.append({
            "entity_id": str(symptom.get("symptom_id", "") or ""),
            "entity_type": "Symptom",
            "entity_name": str(symptom.get("name", "") or ""),
            "verdict": EntityVerdict.ACCEPTED.value,
            "reasons": [],
            "source_page": relevant_pages[0] if relevant_pages else 0,
            "source_pages": relevant_pages,
            "grounding_score": 1.0,
            "agent": "GroundingAgent",
            "advisory_only": True,
        })
        for failure_mode in triplet.get("failure_modes", []):
            base_verdicts.append({
                "entity_id": str(failure_mode.get("failure_mode_id", "") or ""),
                "entity_type": "FailureMode",
                "entity_name": str(failure_mode.get("name", "") or ""),
                "verdict": EntityVerdict.ACCEPTED.value,
                "reasons": [],
                "source_page": relevant_pages[0] if relevant_pages else 0,
                "source_pages": relevant_pages,
                "grounding_score": 1.0,
                "agent": "GroundingAgent",
                "advisory_only": True,
            })
        for action in triplet.get("corrective_actions", []):
            source_page = int(action.get("source_page", 0) or 0)
            base_verdicts.append({
                "entity_id": str(action.get("action_id", "") or ""),
                "entity_type": "CorrectiveAction",
                "entity_name": str(action.get("name", "") or ""),
                "verdict": EntityVerdict.ACCEPTED.value,
                "reasons": [],
                "source_page": source_page,
                "source_pages": [source_page] if source_page else [],
                "grounding_score": 1.0,
                "agent": "GroundingAgent",
                "advisory_only": True,
            })
    return base_verdicts


def _merge_verdicts(
    entity_verdicts: list[dict[str, Any]],
    grounding_results: list[dict[str, Any]],
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    results_by_id = {
        str(item.get("entity_id", "") or ""): item
        for item in grounding_results
        if str(item.get("entity_id", "") or "")
    }
    merged: list[dict[str, Any]] = []
    for verdict in entity_verdicts:
        entity_id = str(verdict.get("entity_id", "") or "")
        grounding = results_by_id.get(entity_id)
        if grounding is None:
            merged.append(dict(verdict))
            continue
        updated = dict(verdict)
        updated["agent"] = "GroundingAgent"
        updated["advisory_only"] = True
        updated["grounding_score"] = round(
            min(
                float(verdict.get("grounding_score", 1.0) or 1.0),
                float(grounding.get("grounding_score", 0.0) or 0.0),
            ),
            3,
        )
        existing_reasons = [str(reason) for reason in verdict.get("reasons", [])]
        for issue in grounding.get("issues", []) or []:
            if issue not in existing_reasons:
                existing_reasons.append(issue)
        updated["reasons"] = existing_reasons
        target_verdict = _verdict_for_score(float(grounding.get("grounding_score", 0.0) or 0.0), cfg)
        current_verdict = str(verdict.get("verdict", EntityVerdict.ACCEPTED.value) or EntityVerdict.ACCEPTED.value)
        updated["verdict"] = (
            target_verdict
            if _VERDICT_ORDER[target_verdict] > _VERDICT_ORDER[current_verdict]
            else current_verdict
        )
        if grounding.get("source_page"):
            updated["source_page"] = int(grounding.get("source_page", 0) or 0)
        merged.append(updated)
    return merged


def run_grounding_agent(store: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    t0 = time.perf_counter()
    cfg = get_validation_config()
    graph_state = store.get("graph_state") or {}
    selected_pages = list(graph_state.get("selected_pages") or [])
    page_texts = _page_text_by_page(store, selected_pages)
    triplets = list(graph_state.get("cleaned_triplets") or [])
    entity_verdicts = list(graph_state.get("entity_verdicts") or [])
    if not entity_verdicts:
        entity_verdicts = _base_verdicts_from_triplets(triplets, selected_pages)

    grounding_results: list[dict[str, Any]] = []
    for triplet in triplets:
        grounding_results.append(_ground_symptom(triplet, page_texts, selected_pages))
        for failure_mode in triplet.get("failure_modes", []):
            grounding_results.append(_ground_failure_mode(triplet, failure_mode, page_texts, selected_pages))
        for action in triplet.get("corrective_actions", []):
            grounding_results.append(_ground_action(action, page_texts))

    updated_verdicts = _merge_verdicts(entity_verdicts, grounding_results, cfg)
    weak_entities = sum(1 for item in grounding_results if float(item.get("grounding_score", 0.0) or 0.0) < 0.5)
    average_score = (
        sum(float(item.get("grounding_score", 0.0) or 0.0) for item in grounding_results) / len(grounding_results)
        if grounding_results else 0.0
    )
    record_stage_metrics(
        store,
        "grounding",
        {
            "stage": "grounding",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            "llm_calls": 0,
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "non_cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "models": [],
            "operations": ["grounding"],
            "details": {
                "total_entities": len(grounding_results),
                "weak_grounding_entities": weak_entities,
                "average_grounding_score": round(average_score, 3),
            },
        },
    )
    model_name = str((get_agents_config().get("grounding") or {}).get("model") or "")
    update_grounding_state(
        store,
        grounding_results=grounding_results,
        entity_verdicts=updated_verdicts,
        model_name=model_name or None,
    )
    return grounding_results, updated_verdicts
