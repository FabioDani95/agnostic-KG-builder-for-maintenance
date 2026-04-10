"""Phase 3 CoverageAgent: page-level gap analysis for selected pages."""

from __future__ import annotations

import re
import time
from typing import Any

from backend.app_config import get_agents_config
from backend.graph.store import update_coverage_state
from backend.services.run_metrics import record_stage_metrics

_DIAGNOSTIC_HINT_RE = re.compile(
    r"(?i)\b("
    r"error|fault|failure|alarm|warning|does not|cannot|won't|will not|"
    r"replace|repair|clean|tighten|adjust|reset|reboot|restart|install|"
    r"check|inspect|diagnostic|troubleshoot|troubleshooting"
    r")\b"
)


def _page_text_by_page(store: dict[str, Any], selected_pages: list[int]) -> dict[int, str]:
    selected = set(int(page) for page in selected_pages)
    return {
        int(page["page_number"]): str(page.get("text", "") or "")
        for page in store.get("pages", [])
        if not selected or int(page["page_number"]) in selected
    }


def _page_has_diagnostic_content(page_text: str) -> bool:
    return bool(_DIAGNOSTIC_HINT_RE.search(str(page_text or "")))


def run_coverage_agent(store: dict[str, Any]) -> dict[int, dict[str, Any]]:
    t0 = time.perf_counter()
    graph_state = store.get("graph_state") or {}
    selected_pages = list(graph_state.get("selected_pages") or [])
    page_texts = _page_text_by_page(store, selected_pages)
    triplets = list(graph_state.get("cleaned_triplets") or [])
    verdicts = list(graph_state.get("entity_verdicts") or [])
    verdicts_by_page: dict[int, list[dict[str, Any]]] = {}
    for verdict in verdicts:
        for page in verdict.get("source_pages") or [verdict.get("source_page", 0)]:
            page_num = int(page or 0)
            if page_num <= 0:
                continue
            verdicts_by_page.setdefault(page_num, []).append(verdict)

    coverage_map: dict[int, dict[str, Any]] = {}
    for page_num, page_text in sorted(page_texts.items()):
        symptom_ids: list[str] = []
        failure_ids: list[str] = []
        action_ids: list[str] = []
        entity_names: list[str] = []
        for triplet in triplets:
            action_pages = {
                int(action.get("source_page", 0) or 0)
                for action in triplet.get("corrective_actions", [])
                if int(action.get("source_page", 0) or 0) > 0
            }
            if page_num not in action_pages:
                continue
            symptom = triplet.get("symptom", {})
            symptom_id = str(symptom.get("symptom_id", "") or "")
            if symptom_id:
                symptom_ids.append(symptom_id)
                entity_names.append(str(symptom.get("name", "") or symptom_id))
            for failure_mode in triplet.get("failure_modes", []):
                failure_id = str(failure_mode.get("failure_mode_id", "") or "")
                if failure_id:
                    failure_ids.append(failure_id)
                    entity_names.append(str(failure_mode.get("name", "") or failure_id))
            for action in triplet.get("corrective_actions", []):
                if int(action.get("source_page", 0) or 0) != page_num:
                    continue
                action_id = str(action.get("action_id", "") or "")
                if action_id:
                    action_ids.append(action_id)
                    entity_names.append(str(action.get("name", "") or action_id))

        diagnostic = _page_has_diagnostic_content(page_text)
        review_required = any(
            str(verdict.get("verdict", "") or "") != "accepted"
            for verdict in verdicts_by_page.get(page_num, [])
        )
        missing_types = [
            entity_type
            for entity_type, values in (
                ("Symptom", symptom_ids),
                ("FailureMode", failure_ids),
                ("CorrectiveAction", action_ids),
            )
            if not values
        ]
        if not diagnostic:
            gap_type = "no_diagnostic_content"
            recommendation = "No targeted re-extraction needed for this selected page."
        elif not entity_names:
            gap_type = "missing_extraction"
            recommendation = "Consider targeted re-extraction for this page before operator review."
        elif missing_types or review_required:
            gap_type = "partially_covered"
            recommendation = "Coverage is partial; review flagged entities and missing diagnostic types."
        else:
            gap_type = "fully_covered"
            recommendation = "No immediate action required."

        coverage_map[page_num] = {
            "has_content": diagnostic,
            "extracted_entities": sorted(dict.fromkeys(entity_names)),
            "entity_ids": sorted(dict.fromkeys(symptom_ids + failure_ids + action_ids)),
            "gap_type": gap_type,
            "missing_entity_types": missing_types,
            "review_required": review_required,
            "recommendation": recommendation,
        }

    record_stage_metrics(
        store,
        "coverage",
        {
            "stage": "coverage",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            "llm_calls": 0,
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "non_cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "models": [],
            "operations": ["coverage"],
            "details": {
                "selected_pages": len(coverage_map),
                "missing_extraction_pages": sum(
                    1 for details in coverage_map.values() if details.get("gap_type") == "missing_extraction"
                ),
            },
        },
    )
    model_name = str((get_agents_config().get("coverage") or {}).get("model") or "")
    update_coverage_state(store, coverage_map=coverage_map, model_name=model_name or None)
    return coverage_map
