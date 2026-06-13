"""Grounded graph closure — Fase A1.

The graph reasoning step already proposes missing relations (token-overlap
similarity), but historically none were ever applied automatically: they were
only shown to the operator. This pass closes the structural gaps the system can
verify on its own, so the human queue only contains genuinely open or
ambiguous links.

Closure is intentionally conservative — the golden rule of the architecture is
"only promote to green what is grounded; everything else degrades to the human
gate, never to auto-accept":

- Only association-style relations are auto-applied here: MAY_INDICATE
  (Symptom → FailureMode) and AFFECTS (FailureMode → Component). RESOLVED_BY is
  deliberately excluded — "FM and CA share tokens" does not prove the action
  remedies the fault, so resolution stays with the LLM retrieval pass
  (resolution_completion) which verifies remediation against the text.
- A candidate is applied only when (a) its similarity confidence clears a
  threshold AND (b) it is grounded: both endpoints are evidenced on a common
  page, or both node names co-occur on a page of the source text.

Everything that is not auto-applied remains in suggested_relations for the
operator to accept or reject.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.models import (
    OntologyEvidence,
    OntologyInstance,
    OntologyRelationInstance,
    SuggestedRelation,
)

logger = logging.getLogger(__name__)

_ID_FIELD_BY_TYPE: dict[str, str] = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}

# Relations safe to auto-apply from similarity + grounding alone.
_AUTO_CLOSE_RELATIONS = {"MAY_INDICATE", "AFFECTS"}

# Minimum similarity confidence before a grounded candidate is auto-applied.
# Kept above the suggestion floor (0.20) so weak token coincidences stay in the
# human queue rather than entering the graph.
_DEFAULT_MIN_CONFIDENCE = 0.35


def _node_pages_index(ontology: OntologyInstance) -> dict[str, set[int]]:
    """node_id → set of source pages inferred from incident relation evidence."""
    index: dict[str, set[int]] = {}
    for rel in ontology.relations or []:
        pages: set[int] = set()
        for ev in rel.evidence or []:
            try:
                page = int(getattr(ev, "source_page", 0) or 0)
            except (TypeError, ValueError):
                continue
            if page > 0:
                pages.add(page)
        if not pages:
            continue
        for node_id in (rel.from_id, rel.to_id):
            if node_id:
                index.setdefault(node_id, set()).update(pages)
    return index


def _node_name_index(ontology: OntologyInstance) -> dict[str, str]:
    names: dict[str, str] = {}
    for node_type, items in (ontology.nodes or {}).items():
        id_field = _ID_FIELD_BY_TYPE.get(node_type, f"{node_type.lower()}_id")
        for item in items or []:
            if not isinstance(item, dict):
                continue
            node_id = str(item.get(id_field, "")).strip()
            if node_id:
                names[node_id] = str(item.get("name", "")).strip()
    return names


def _grounding_page(
    from_id: str,
    to_id: str,
    node_pages: dict[str, set[int]],
    node_names: dict[str, str],
    page_text_by_page: dict[int, str],
) -> int:
    """Return a page that grounds the from→to link, or 0 if none found.

    Priority 1: a page where both endpoints already carry evidence.
    Priority 2: a page of source text where both node names co-occur.
    """
    shared = node_pages.get(from_id, set()) & node_pages.get(to_id, set())
    if shared:
        return min(shared)

    from backend.services.llm_service import _fragment_supported_by_page

    from_name = node_names.get(from_id, "")
    to_name = node_names.get(to_id, "")
    if not from_name or not to_name:
        return 0
    for page in sorted(page_text_by_page):
        page_text = page_text_by_page[page]
        if not page_text:
            continue
        if _fragment_supported_by_page(from_name, page_text) and _fragment_supported_by_page(
            to_name, page_text
        ):
            return page
    return 0


def close_grounded_gaps(
    ontology: OntologyInstance,
    suggested_relations: list[SuggestedRelation],
    page_text_by_page: dict[int, str],
    *,
    min_confidence: float = _DEFAULT_MIN_CONFIDENCE,
) -> tuple[OntologyInstance, list[SuggestedRelation], dict[str, Any]]:
    """Auto-apply grounded association relations; return (ontology, remaining, report).

    `remaining` are the suggestions NOT auto-applied — they stay in the operator
    queue. The returned ontology is a new instance when anything changed.
    """
    if not suggested_relations:
        return ontology, suggested_relations, {"considered": 0, "applied": 0}

    node_pages = _node_pages_index(ontology)
    node_names = _node_name_index(ontology)
    existing = {
        (rel.name, rel.from_id, rel.to_id) for rel in ontology.relations or []
    }

    data = ontology.model_dump()
    relations = [
        OntologyRelationInstance.model_validate(rel)
        for rel in data.get("relations", [])
        if isinstance(rel, dict)
    ]

    applied: list[tuple[str, str, str, int]] = []
    remaining: list[SuggestedRelation] = []
    considered = 0

    for suggestion in suggested_relations:
        if suggestion.relation_name not in _AUTO_CLOSE_RELATIONS:
            remaining.append(suggestion)
            continue
        considered += 1
        key = (suggestion.relation_name, suggestion.from_id, suggestion.to_id)
        if key in existing or suggestion.confidence < min_confidence:
            remaining.append(suggestion)
            continue
        page = _grounding_page(
            suggestion.from_id,
            suggestion.to_id,
            node_pages,
            node_names,
            page_text_by_page,
        )
        if not page:
            remaining.append(suggestion)
            continue
        relations.append(OntologyRelationInstance(
            name=suggestion.relation_name,
            from_type=suggestion.from_type,
            from_id=suggestion.from_id,
            to_type=suggestion.to_type,
            to_id=suggestion.to_id,
            evidence=[OntologyEvidence(source_page=page, source_reference=f"PAGE {page}", quote="")],
        ))
        existing.add(key)
        applied.append(key)

    if not applied:
        return ontology, remaining, {"considered": considered, "applied": 0}

    data["relations"] = [rel.model_dump() for rel in relations]
    updated = OntologyInstance.model_validate(data)
    by_relation: dict[str, int] = {}
    for name, _from_id, _to_id in applied:
        by_relation[name] = by_relation.get(name, 0) + 1
    logger.info(
        "[graph_closure] Auto-applied %d/%d grounded association relation(s): %s",
        len(applied),
        considered,
        by_relation,
    )
    return updated, remaining, {
        "considered": considered,
        "applied": len(applied),
        "by_relation": by_relation,
    }
