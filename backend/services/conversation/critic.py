"""Proactive critic for ontology nodes and triplets.

Called asynchronously after each entity is surfaced in chat.
If issues are found, emits a critique event so the chatbot can
prepend a proactive suggestion before showing the widget.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.services.conversation.events import critique_event

logger = logging.getLogger(__name__)

# Maximum number of proactive critiques per entity (avoid noise)
_MAX_CRITIQUES = 3


def _node_lookup(pipeline_state: dict[str, Any]) -> dict[str, dict[str, str]]:
    ontology = (pipeline_state.get("ontology") or {})
    nodes = ontology.get("nodes") or {}
    lookup: dict[str, dict[str, str]] = {}
    for node_type, items in nodes.items():
        for item in items or []:
            if not isinstance(item, dict):
                continue
            node_id = next(
                (str(value).strip() for key, value in item.items() if key.endswith("_id") and value),
                "",
            )
            if not node_id:
                continue
            lookup[node_id] = {
                "node_type": str(node_type),
                "label": str(item.get("name") or node_id),
            }
    return lookup


def _graph_issue_candidates(
    pipeline_state: dict[str, Any],
    graph_issue: dict[str, Any],
    *,
    limit: int = 4,
) -> list[dict[str, Any]]:
    affected_nodes = {str(node_id) for node_id in (graph_issue.get("affected_nodes") or []) if node_id}
    if not affected_nodes:
        return []

    candidates: list[dict[str, Any]] = []
    for index, suggestion in enumerate(pipeline_state.get("suggested_relations") or []):
        if not isinstance(suggestion, dict):
            continue
        from_id = str(suggestion.get("from_id") or "")
        to_id = str(suggestion.get("to_id") or "")
        if from_id not in affected_nodes and to_id not in affected_nodes:
            continue
        candidates.append({
            "index": index,
            "relation_name": str(suggestion.get("relation_name") or ""),
            "from_id": from_id,
            "from_label": str(suggestion.get("from_label") or from_id),
            "to_id": to_id,
            "to_label": str(suggestion.get("to_label") or to_id),
            "confidence": float(suggestion.get("confidence") or 0.0),
            "rationale": str(suggestion.get("rationale") or ""),
        })

    candidates.sort(key=lambda item: item["confidence"], reverse=True)
    return candidates[:limit]


def critique_triplet(
    triplet: dict[str, Any],
    store: dict[str, Any],
) -> list[dict[str, Any]]:
    """Check a triplet for common issues. Returns a list of critique event dicts."""
    issues: list[dict[str, Any]] = []

    symptom = triplet.get("symptom") or {}
    failure_modes = triplet.get("failure_modes") or []
    corrective_actions = triplet.get("corrective_actions") or []

    symptom_id = symptom.get("symptom_id", "")
    symptom_name = symptom.get("name", "")
    symptom_desc = symptom.get("description", "")
    evidence_page = symptom.get("evidence_page", 0)

    # 1. Missing description
    if not symptom_desc:
        issues.append(critique_event(
            message=f"Symptom '{symptom_name}' has no description — consider adding one for clarity.",
            entity_id=symptom_id,
            suggestion=f"Add a concise description for symptom '{symptom_name}'.",
        ))

    # 2. No failure modes linked
    if not failure_modes:
        issues.append(critique_event(
            message=f"Symptom '{symptom_name}' has no linked Failure Modes — this triplet is incomplete.",
            entity_id=symptom_id,
            suggestion="Add at least one Failure Mode linked to this symptom.",
        ))

    # 3. Failure modes without corrective actions
    for fm in failure_modes:
        fm_id = fm.get("failure_mode_id", "")
        fm_name = fm.get("name", "")
        linked_cas = [
            ca for ca in corrective_actions
            if ca.get("linked_failure_mode_id") == fm_id
        ]
        if not linked_cas:
            issues.append(critique_event(
                message=f"Failure Mode '{fm_name}' has no linked Corrective Action.",
                entity_id=fm_id,
                suggestion=f"Add at least one Corrective Action for '{fm_name}'.",
            ))

    # 4. Type-consistency check: highly similar Symptom name ↔ FailureMode name
    try:
        from backend.services.ontology_semantics import normalize_semantic_text, semantic_tokens
        sym_tokens = set(semantic_tokens(symptom_name))
        for fm in failure_modes:
            fm_tokens = set(semantic_tokens(fm.get("name", "")))
            if sym_tokens and fm_tokens:
                overlap = len(sym_tokens & fm_tokens) / max(len(sym_tokens | fm_tokens), 1)
                if overlap > 0.8:
                    issues.append(critique_event(
                        message=(
                            f"Symptom '{symptom_name}' and Failure Mode '{fm.get('name', '')}' "
                            f"look very similar ({overlap:.0%} token overlap). "
                            "Are they really distinct concepts?"
                        ),
                        entity_id=fm.get("failure_mode_id"),
                        suggestion="Consider merging them or refining their descriptions to clarify the distinction.",
                    ))
    except Exception:
        pass

    # 5. Evidence page sanity
    pages = store.get("pages") or []
    page_numbers = {p["page_number"] for p in pages}
    if evidence_page and evidence_page not in page_numbers:
        issues.append(critique_event(
            message=f"Symptom '{symptom_name}' cites evidence page {evidence_page}, which is not in the document.",
            entity_id=symptom_id,
            suggestion=f"Check the evidence page reference — it may be a page-offset error.",
        ))

    return issues[:_MAX_CRITIQUES]


def critique_ontology_draft(
    store: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run a quick post-draft critique: orphan nodes, missing required fields, type consistency."""
    issues: list[dict[str, Any]] = []
    pipeline_state = store.get("ontology_pipeline") or {}
    node_lookup = _node_lookup(pipeline_state)

    # 1. Schema issues
    for issue in (pipeline_state.get("schema_issues") or []):
        if isinstance(issue, dict) and issue.get("severity") in ("error", "critical", "High", "Critical"):
            issues.append(critique_event(
                message=f"Schema issue ({issue.get('code', '')}): {issue.get('message', '')}",
                entity_id=issue.get("target_id"),
                suggestion=issue.get("fix_hint", ""),
            ))
            if len(issues) >= _MAX_CRITIQUES:
                return issues

    # 2. Human-required fields
    human_fields = pipeline_state.get("human_required_fields") or []
    if human_fields:
        field_names = [f.get("property_name", "") for f in human_fields[:3] if isinstance(f, dict)]
        issues.append(critique_event(
            message=(
                f"{len(human_fields)} required field(s) were not filled automatically: "
                f"{', '.join(field_names)}{'…' if len(human_fields) > 3 else ''}."
            ),
            entity_id=None,
            suggestion="I'll prompt you to fill them one by one.",
        ))

    # 3. Graph issues (orphan nodes)
    for graph_issue in (pipeline_state.get("graph_issues") or []):
        if isinstance(graph_issue, dict):
            affected_nodes = [str(node_id) for node_id in (graph_issue.get("affected_nodes") or []) if node_id]
            first_node_id = affected_nodes[0] if affected_nodes else None
            first_node = node_lookup.get(first_node_id or "", {})
            issues.append(critique_event(
                message=f"Graph issue: {graph_issue.get('description', '')}",
                entity_id=first_node_id,
                suggestion=graph_issue.get("suggested_fix", ""),
                issue_type=graph_issue.get("issue_type"),
                affected_nodes=affected_nodes,
                entity_label=first_node.get("label"),
                entity_type=first_node.get("node_type"),
                candidates=_graph_issue_candidates(pipeline_state, graph_issue),
            ))
            if len(issues) >= _MAX_CRITIQUES:
                return issues

    return issues[:_MAX_CRITIQUES]
