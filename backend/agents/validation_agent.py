"""Conservative, advisory validation for Phase 2."""

from __future__ import annotations

import time
from typing import Any

from backend.app_config import get_validation_config
from backend.graph.state import EntityVerdict
from backend.graph.store import update_validation_state
from backend.services.llm_service import _fragment_supported_by_page
from backend.services.ontology_semantics import (
    corrective_actions_match,
    informative_instruction_steps,
    instruction_steps,
    is_corrective_action_candidate,
    is_failure_mode_candidate,
    normalize_semantic_text,
    semantically_equivalent,
    symptoms_match,
)
from backend.services.run_metrics import record_stage_metrics


def _page_text_by_page(store: dict[str, Any], selected_pages: list[int]) -> dict[int, str]:
    selected = set(selected_pages)
    return {
        int(page["page_number"]): str(page.get("text", "") or "")
        for page in store.get("pages", [])
        if not selected or int(page["page_number"]) in selected
    }


def _ontology_supports_symptom(ontology_draft: dict[str, Any] | None, symptom: dict[str, Any]) -> bool:
    node_list = ((ontology_draft or {}).get("nodes") or {}).get("Symptom") or []
    if not node_list:
        return True
    for node in node_list:
        if symptoms_match(
            str(symptom.get("name", "")),
            str(symptom.get("description", "")),
            str(node.get("name", "")),
            str(node.get("description", "")),
        ):
            return True
    return False


def _ontology_supports_failure_mode(ontology_draft: dict[str, Any] | None, failure_mode: dict[str, Any]) -> bool:
    node_list = ((ontology_draft or {}).get("nodes") or {}).get("FailureMode") or []
    if not node_list:
        return True
    for node in node_list:
        if is_failure_mode_candidate(
            str(failure_mode.get("name", "")),
            str(failure_mode.get("description", "")),
            str(failure_mode.get("material_context", "")),
        ) and semantically_equivalent(
            " ".join([
                str(failure_mode.get("name", "")),
                str(failure_mode.get("description", "")),
                str(failure_mode.get("material_context", "")),
            ]),
            " ".join([
                str(node.get("name", "")),
                str(node.get("description", "")),
                str(node.get("material_context", "")),
            ]),
            min_ratio=0.74,
            min_overlap=0.60,
        ):
            return True
    return False


def _ontology_supports_action(ontology_draft: dict[str, Any] | None, action: dict[str, Any]) -> bool:
    node_list = ((ontology_draft or {}).get("nodes") or {}).get("CorrectiveAction") or []
    if not node_list:
        return True
    for node in node_list:
        if corrective_actions_match(
            str(action.get("name", "")),
            str(action.get("description", "")),
            str(action.get("instruction_text", "")),
            str(node.get("name", "")),
            str(node.get("description", "")),
            str(node.get("instruction_text", "")),
        ):
            return True
    return False


def _score_support(fragment: str, page_texts: dict[int, str]) -> float:
    normalized = normalize_semantic_text(fragment)
    if not normalized:
        return 0.0
    for page_text in page_texts.values():
        if _fragment_supported_by_page(fragment, page_text):
            return 1.0
    return 0.0


def _relevant_page_numbers(triplet: dict[str, Any], selected_pages: list[int]) -> list[int]:
    action_pages = [
        int(action.get("source_page", 0) or 0)
        for action in triplet.get("corrective_actions", [])
        if int(action.get("source_page", 0) or 0) > 0
    ]
    if action_pages:
        return sorted(set(action_pages))
    return list(selected_pages)


def _verdict_for_score(score: float, reasons: list[str], cfg: dict[str, Any]) -> EntityVerdict:
    accept_threshold = float(cfg.get("grounding_accept_threshold", 0.8))
    refine_threshold = float(cfg.get("grounding_refine_threshold", 0.5))
    if score >= accept_threshold and not reasons:
        return EntityVerdict.ACCEPTED
    if score >= refine_threshold:
        return EntityVerdict.NEEDS_REFINEMENT
    return EntityVerdict.NEEDS_HUMAN


def _validate_symptom(
    triplet: dict[str, Any],
    ontology_draft: dict[str, Any] | None,
    page_texts: dict[int, str],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    symptom = triplet.get("symptom", {})
    relevant_pages = _relevant_page_numbers(triplet, list(page_texts.keys()))
    relevant_texts = {page: page_texts.get(page, "") for page in relevant_pages if page in page_texts} or page_texts
    name_score = _score_support(str(symptom.get("name", "")), relevant_texts)
    description_score = _score_support(str(symptom.get("description", "")), relevant_texts)
    ontology_supported = _ontology_supports_symptom(ontology_draft, symptom)

    score = (0.45 * name_score) + (0.35 * description_score) + (0.20 * (1.0 if ontology_supported else 0.0))
    reasons: list[str] = []
    if not name_score and not description_score:
        reasons.append("symptom text is weakly grounded in selected pages")
    if bool(cfg.get("check_ontology_chain", True)) and not ontology_supported:
        reasons.append("symptom has no clear match in ontology draft")

    verdict = _verdict_for_score(score, reasons, cfg)
    return {
        "entity_id": symptom.get("symptom_id", ""),
        "entity_type": "Symptom",
        "entity_name": symptom.get("name", ""),
        "verdict": verdict.value,
        "reasons": reasons,
        "source_page": relevant_pages[0] if relevant_pages else 0,
        "source_pages": relevant_pages,
        "grounding_score": round(score, 3),
        "agent": "ValidationAgent",
        "advisory_only": True,
    }


def _validate_failure_mode(
    triplet: dict[str, Any],
    failure_mode: dict[str, Any],
    ontology_draft: dict[str, Any] | None,
    page_texts: dict[int, str],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    relevant_pages = _relevant_page_numbers(triplet, list(page_texts.keys()))
    relevant_texts = {page: page_texts.get(page, "") for page in relevant_pages if page in page_texts} or page_texts
    name_score = _score_support(str(failure_mode.get("name", "")), relevant_texts)
    description_score = _score_support(str(failure_mode.get("description", "")), relevant_texts)
    context_score = _score_support(str(failure_mode.get("material_context", "")), relevant_texts)
    ontology_supported = _ontology_supports_failure_mode(ontology_draft, failure_mode)
    candidate = is_failure_mode_candidate(
        str(failure_mode.get("name", "")),
        str(failure_mode.get("description", "")),
        str(failure_mode.get("material_context", "")),
    )

    score = (
        (0.30 * name_score)
        + (0.25 * description_score)
        + (0.20 * context_score)
        + (0.15 * (1.0 if ontology_supported else 0.0))
        + (0.10 * (1.0 if candidate else 0.0))
    )
    reasons: list[str] = []
    if not candidate:
        reasons.append("failure mode resembles an observation or procedure outcome more than a cause")
    if not name_score and not description_score and not context_score:
        reasons.append("failure mode text is weakly grounded in selected pages")
    if bool(cfg.get("check_ontology_chain", True)) and not ontology_supported:
        reasons.append("failure mode has no clear match in ontology draft")

    verdict = _verdict_for_score(score, reasons, cfg)
    return {
        "entity_id": failure_mode.get("failure_mode_id", ""),
        "entity_type": "FailureMode",
        "entity_name": failure_mode.get("name", ""),
        "verdict": verdict.value,
        "reasons": reasons,
        "source_page": relevant_pages[0] if relevant_pages else 0,
        "source_pages": relevant_pages,
        "grounding_score": round(score, 3),
        "agent": "ValidationAgent",
        "advisory_only": True,
    }


def _validate_action(
    action: dict[str, Any],
    ontology_draft: dict[str, Any] | None,
    page_texts: dict[int, str],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    source_page = int(action.get("source_page", 0) or 0)
    page_text = page_texts.get(source_page, "")
    name_supported = _fragment_supported_by_page(str(action.get("name", "")), page_text) if page_text else False
    description_supported = _fragment_supported_by_page(str(action.get("description", "")), page_text) if page_text else False
    raw_steps = instruction_steps(str(action.get("instruction_text", "")))
    informative_steps = informative_instruction_steps(str(action.get("instruction_text", "")))
    supported_steps = [
        step for step in informative_steps
        if page_text and _fragment_supported_by_page(step, page_text)
    ]
    step_support_ratio = (len(supported_steps) / len(informative_steps)) if informative_steps else 0.0
    actionable = is_corrective_action_candidate(
        str(action.get("name", "")),
        str(action.get("description", "")),
        str(action.get("instruction_text", "")),
    )
    ontology_supported = _ontology_supports_action(ontology_draft, action)

    score = 0.0
    score += 0.20 if source_page > 0 else 0.0
    score += 0.20 if bool(page_text) else 0.0
    score += 0.25 if actionable else 0.0
    score += 0.20 if (name_supported or description_supported) else 0.0
    score += 0.10 if ontology_supported else 0.0
    score += 0.05 if not raw_steps else min(0.25, 0.25 * step_support_ratio)
    score = min(score, 1.0)

    reasons: list[str] = []
    if source_page <= 0:
        reasons.append("corrective action is missing a cited source page")
    elif bool(cfg.get("check_page_attribution", True)) and not page_text:
        reasons.append("cited source page is not present in the selected document scope")
    if not actionable:
        reasons.append("corrective action is inspection-only or not clearly actionable")
    if page_text and raw_steps and not supported_steps and not (name_supported or description_supported):
        reasons.append("corrective action steps are weakly grounded in the cited page")
    if bool(cfg.get("check_ontology_chain", True)) and not ontology_supported:
        reasons.append("corrective action has no clear match in ontology draft")

    verdict = _verdict_for_score(score, reasons, cfg)
    return {
        "entity_id": action.get("action_id", ""),
        "entity_type": "CorrectiveAction",
        "entity_name": action.get("name", ""),
        "verdict": verdict.value,
        "reasons": reasons,
        "source_page": source_page,
        "source_pages": [source_page] if source_page else [],
        "grounding_score": round(score, 3),
        "agent": "ValidationAgent",
        "advisory_only": True,
    }


def run_validation_agent(store: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Produce advisory validation verdicts without blocking the operator review flow."""
    t0 = time.perf_counter()
    cfg = get_validation_config()
    graph_state = store.get("graph_state") or {}
    selected_pages = list(graph_state.get("selected_pages") or [])
    page_texts = _page_text_by_page(store, selected_pages)
    ontology_draft = graph_state.get("ontology_draft")
    triplets = list(graph_state.get("cleaned_triplets") or [])

    entity_verdicts: list[dict[str, Any]] = []
    for triplet in triplets:
        entity_verdicts.append(_validate_symptom(triplet, ontology_draft, page_texts, cfg))
        for failure_mode in triplet.get("failure_modes", []):
            entity_verdicts.append(_validate_failure_mode(
                triplet,
                failure_mode,
                ontology_draft,
                page_texts,
                cfg,
            ))
        for action in triplet.get("corrective_actions", []):
            entity_verdicts.append(_validate_action(action, ontology_draft, page_texts, cfg))

    summary = {
        "total_entities": len(entity_verdicts),
        "accepted": sum(1 for item in entity_verdicts if item["verdict"] == EntityVerdict.ACCEPTED.value),
        "needs_refinement": sum(1 for item in entity_verdicts if item["verdict"] == EntityVerdict.NEEDS_REFINEMENT.value),
        "needs_human": sum(1 for item in entity_verdicts if item["verdict"] == EntityVerdict.NEEDS_HUMAN.value),
        "flagged_entities": sum(
            1 for item in entity_verdicts if item["verdict"] != EntityVerdict.ACCEPTED.value
        ),
        "flagged_entity_ids": [
            item["entity_id"] for item in entity_verdicts if item["verdict"] != EntityVerdict.ACCEPTED.value
        ],
        "advisory_only": True,
    }

    record_stage_metrics(
        store,
        "validation",
        {
            "stage": "validation",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            "llm_calls": 0,
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "non_cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "models": [],
            "operations": ["validation"],
            "details": summary,
        },
    )
    update_validation_state(store, entity_verdicts=entity_verdicts, validation_summary=summary)
    return entity_verdicts, summary
