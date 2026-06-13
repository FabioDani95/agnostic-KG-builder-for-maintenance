"""Deterministic evidence grounding for ontology relations.

Every relation extracted by the LLM carries evidence entries with a cited page
and a verbatim quote. This pass verifies each quote against the text of the
cited page (no extra LLM calls) and flags relations whose evidence cannot be
found. Ungrounded relations lower the confidence score of the nodes they touch
so the adaptive HITL queue surfaces them for human review instead of
auto-approving fabricated provenance.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.models import OntologyInstance, PipelineIssue

logger = logging.getLogger(__name__)

_ID_FIELD_BY_TYPE: dict[str, str] = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}

# Relations whose endpoints both exist are trusted even without quotes;
# only structurally derived relations are exempt from quote checks entirely.
_DERIVED_RELATIONS = {"HAS_COMPONENT"}


def _node_label_index(ontology: OntologyInstance) -> dict[str, tuple[str, str]]:
    """Map node_id → (node_type, display name)."""
    index: dict[str, tuple[str, str]] = {}
    for node_type, items in (ontology.nodes or {}).items():
        id_field = _ID_FIELD_BY_TYPE.get(node_type, f"{node_type.lower()}_id")
        for item in items or []:
            if not isinstance(item, dict):
                continue
            node_id = str(item.get(id_field, "")).strip()
            if node_id:
                index[node_id] = (node_type, str(item.get("name", node_id)))
    return index


def ground_relation_evidence(
    ontology: OntologyInstance,
    page_text_by_page: dict[int, str],
) -> tuple[list[PipelineIssue], set[tuple[str, str]], dict[str, Any]]:
    """Verify relation evidence quotes against their cited pages.

    Returns (issues, ungrounded_node_keys, stats):
    - issues: one warning PipelineIssue per node involved in ungrounded relations
    - ungrounded_node_keys: {(node_type, node_id)} for confidence penalties
    - stats: counters for metrics/telemetry
    """
    from backend.services.llm_service import _fragment_supported_by_page

    checked = 0
    grounded = 0
    ungrounded_relations: list[Any] = []

    for relation in ontology.relations or []:
        if relation.name in _DERIVED_RELATIONS:
            continue
        quotes = [
            (int(getattr(ev, "source_page", 0) or 0), str(getattr(ev, "quote", "") or "").strip())
            for ev in (relation.evidence or [])
        ]
        quotes = [(page, quote) for page, quote in quotes if quote]
        if not quotes:
            continue
        checked += 1
        supported = False
        for page, quote in quotes:
            page_text = page_text_by_page.get(page, "")
            if page_text and _fragment_supported_by_page(quote, page_text):
                supported = True
                break
        if supported:
            grounded += 1
        else:
            ungrounded_relations.append(relation)

    issues: list[PipelineIssue] = []
    ungrounded_node_keys: set[tuple[str, str]] = set()
    if ungrounded_relations:
        label_index = _node_label_index(ontology)
        relations_by_node: dict[tuple[str, str], list[str]] = {}
        for relation in ungrounded_relations:
            for node_id in (relation.from_id, relation.to_id):
                node_type, _ = label_index.get(node_id, ("", ""))
                if not node_type:
                    continue
                key = (node_type, node_id)
                ungrounded_node_keys.add(key)
                relations_by_node.setdefault(key, []).append(
                    f"{relation.name}({relation.from_id} → {relation.to_id})"
                )
        for (node_type, node_id), relation_labels in relations_by_node.items():
            issues.append(PipelineIssue(
                severity="warning",
                code="ungrounded_evidence",
                message=(
                    f"{node_type} '{node_id}' participates in relation(s) whose evidence quote "
                    f"was not found on the cited page: {', '.join(sorted(set(relation_labels)))}."
                ),
                target_type=node_type,
                target_id=node_id,
                fix_hint=(
                    "Verify the relation against the manual: fix the cited page/quote, "
                    "or remove the relation if the manual does not support it."
                ),
            ))

    stats = {
        "relations_checked": checked,
        "relations_grounded": grounded,
        "relations_ungrounded": len(ungrounded_relations),
        "nodes_flagged": len(ungrounded_node_keys),
    }
    if ungrounded_relations:
        logger.info(
            "[grounding] %d/%d relation evidence quote(s) NOT found on cited pages — %d node(s) flagged",
            len(ungrounded_relations),
            checked,
            len(ungrounded_node_keys),
        )
    else:
        logger.info("[grounding] All %d relation evidence quote(s) verified", checked)
    return issues, ungrounded_node_keys, stats
