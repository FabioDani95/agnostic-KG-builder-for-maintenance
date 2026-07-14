"""Schema-aware confidence scoring — Step 3 of the agentic roadmap.

Assigns a 0.0–1.0 confidence score to every extracted ontology node using signals
that are computed from:
1. the node's own payload (required properties, evidence)
2. the live OntologySchemaDefinition (required props, expected relations)
3. the reflective-loop state (retries, semantic/schema issues, human bindings)

The scorer is deliberately schema-driven: weights and thresholds live in
config.yaml, and signals never reference specific node type names. Changing
ontology_schema.JSON therefore requires no code change in this module — the
"which relations should a FailureMode have?" question is answered by reading
the schema's OntologyRelationDefinition list at runtime.

Every scoring run is pure: it reads inputs and returns a ConfidenceReport
without mutating the OntologyInstance. This keeps the core pipeline's
payloads backward-compatible and makes the layer cheap to unit-test.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.app_config import get_confidence_config
from backend.models import (
    ConfidenceEntry,
    ConfidenceReport,
    HumanRequiredField,
    OntologyInstance,
    OntologyRelationInstance,
    OntologySchemaDefinition,
    PipelineIssue,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ID_FIELD_BY_TYPE: dict[str, str] = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}


def _node_id(node_type: str, item: dict[str, Any]) -> str:
    """Extract the canonical id for a node dict, matching graph_reasoning conventions."""
    # Prefer the schema's type-specific key, then fall back to any *_id field.
    expected = _ID_FIELD_BY_TYPE.get(node_type, f"{node_type.lower()}_id")
    val = str(item.get(expected, "") or "").strip()
    if val:
        return val
    for key, value in item.items():
        if key.endswith("_id") and value:
            return str(value).strip()
    return ""


def _required_property_names(
    schema: OntologySchemaDefinition, node_type: str
) -> list[str]:
    for node_def in schema.nodes:
        if node_def.name == node_type:
            return [prop.name for prop in node_def.properties if prop.required]
    return []


def _expected_relations_for_type(
    schema: OntologySchemaDefinition, node_type: str
) -> tuple[set[str], set[str]]:
    """Return (outgoing_relation_names, incoming_relation_names) declared in schema."""
    outgoing: set[str] = set()
    incoming: set[str] = set()
    for rel in schema.relations:
        if rel.domain == node_type:
            outgoing.add(rel.name)
        if rel.range == node_type:
            incoming.add(rel.name)
    return outgoing, incoming


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _normalized_weights(raw_weights: dict[str, Any]) -> dict[str, float]:
    cleaned: dict[str, float] = {}
    for key, value in raw_weights.items():
        try:
            cleaned[key] = max(0.0, float(value))
        except (TypeError, ValueError):
            continue
    total = sum(cleaned.values())
    if total <= 0.0:
        # Avoid division by zero: fall back to uniform weighting over whatever keys are present.
        if not cleaned:
            return {}
        uniform = 1.0 / len(cleaned)
        return {k: uniform for k in cleaned}
    return {k: v / total for k, v in cleaned.items()}


# ---------------------------------------------------------------------------
# Per-signal scorers (each returns a float in [0, 1])
# ---------------------------------------------------------------------------

def _collect_node_pages(node_item: dict[str, Any]) -> set[int]:
    """Collect source_page values from the node's own evidence list."""
    pages: set[int] = set()
    evidence = node_item.get("evidence")
    if not isinstance(evidence, list):
        return pages
    for ev in evidence:
        if not isinstance(ev, dict):
            continue
        try:
            page = int(ev.get("source_page") or 0)
        except (TypeError, ValueError):
            continue
        if page > 0:
            pages.add(page)
    return pages


def _build_relation_page_index(
    relations: list[OntologyRelationInstance],
) -> dict[str, set[int]]:
    """Build a mapping from node_id → set of source_pages inferred from its incident relations.

    Relations in the current prompt always carry evidence; nodes do not. A node that
    appears as from_id or to_id in a relation with evidence on page P was mentioned
    on page P — so that page becomes provenance for the node.

    This enables evidence_present and corroboration signals even when the LLM prompt
    does not explicitly ask for node-level evidence objects.
    """
    index: dict[str, set[int]] = {}
    for rel in relations or []:
        if not isinstance(rel, OntologyRelationInstance):
            continue
        # Collect pages from relation evidence
        rel_pages: set[int] = set()
        for ev in rel.evidence or []:
            try:
                page = int(getattr(ev, "source_page", 0) or 0)
            except (TypeError, ValueError):
                continue
            if page > 0:
                rel_pages.add(page)
        if not rel_pages:
            continue
        for node_id in (rel.from_id, rel.to_id):
            if node_id:
                index.setdefault(node_id, set()).update(rel_pages)
    return index


def _signal_evidence_present(
    node_item: dict[str, Any],
    relation_pages: set[int] | None = None,
) -> float:
    """1.0 if the node has provenance: either from its own evidence or from incident relations."""
    own_pages = _collect_node_pages(node_item)
    if own_pages:
        return 1.0
    if relation_pages:
        return 1.0
    return 0.0


def _signal_corroboration(
    node_item: dict[str, Any],
    relation_pages: set[int] | None = None,
) -> float:
    """Saturating score based on distinct source pages (own + propagated from relations).

    1 page → ~0.50, 2 → ~0.83, 3+ → 1.0.
    Relation-propagated pages are weighted at 0.5 relative to own-evidence pages,
    because a page cited in a relation mentioning this node is weaker provenance than
    a page where the node itself is explicitly evidenced.
    """
    own_pages = _collect_node_pages(node_item)
    propagated = (relation_pages or set()) - own_pages
    # Effective page count: own pages count fully, propagated pages count at half weight
    effective = len(own_pages) + 0.5 * len(propagated)
    if effective == 0:
        return 0.0
    return min(1.0, effective / 3.0 + 0.17)


def _signal_required_props_complete(
    node_item: dict[str, Any], required_props: list[str]
) -> float:
    if not required_props:
        return 1.0
    present = 0
    for prop in required_props:
        value = node_item.get(prop)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        present += 1
    return present / len(required_props)


def _signal_chain_participation(
    node_id: str,
    outgoing_expected: set[str],
    incoming_expected: set[str],
    outgoing_actual: dict[str, set[str]],
    incoming_actual: dict[str, set[str]],
) -> float:
    """Fraction of schema-expected relations that are actually attached to this node.

    If the schema declares no expected relations for this type (e.g. leaf nodes),
    the signal is vacuously satisfied (1.0).
    """
    expected_total = len(outgoing_expected) + len(incoming_expected)
    if expected_total == 0:
        return 1.0

    actual_out = outgoing_actual.get(node_id, set())
    actual_in = incoming_actual.get(node_id, set())
    satisfied = len(outgoing_expected & actual_out) + len(incoming_expected & actual_in)
    return satisfied / expected_total


def _signal_clean_extraction(
    node_type: str,
    node_id: str,
    semantic_issues: list[PipelineIssue],
    schema_issues: list[PipelineIssue],
) -> float:
    """Grades per-node extraction cleanliness:

    1.0 — this node was not directly targeted by any semantic or schema issue
    0.0 — this node was directly targeted by at least one semantic or schema issue
          (even after re-extraction the issue may remain, so trust is low)

    The global retry signal is intentionally NOT folded in here: it is applied
    once, uniformly, via the per_retry penalty. With the reflective loop enabled
    by default a single self-correcting retry would otherwise blanket-discount
    every node and flood the human-review queue, hurting the validation UX.
    """
    is_direct_target = any(
        issue.target_type == node_type and issue.target_id == node_id
        for issue in list(semantic_issues) + list(schema_issues)
    )
    if is_direct_target:
        return 0.0
    return 1.0


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def score_ontology(
    ontology: OntologyInstance,
    schema: OntologySchemaDefinition,
    *,
    semantic_issues: list[PipelineIssue] | None = None,
    schema_issues: list[PipelineIssue] | None = None,
    human_required_fields: list[HumanRequiredField] | None = None,
    retry_count: int = 0,
    config: dict[str, Any] | None = None,
    ungrounded_node_keys: set[tuple[str, str]] | None = None,
) -> ConfidenceReport:
    """Score every node in the ontology and classify it for adaptive HITL."""
    cfg = config or get_confidence_config()
    if not cfg.get("enabled", True):
        return ConfidenceReport(
            theta_high=float(cfg.get("theta_high", 0.80)),
            theta_low=float(cfg.get("theta_low", 0.45)),
            auto_reject_enabled=bool(cfg.get("auto_reject_enabled", False)),
        )

    theta_high = float(cfg.get("theta_high", 0.80))
    theta_low = float(cfg.get("theta_low", 0.45))
    auto_reject_enabled = bool(cfg.get("auto_reject_enabled", False))

    weights = _normalized_weights(cfg.get("weights", {}) or {})
    penalties_cfg = cfg.get("penalties", {}) or {}
    penalty_human = float(penalties_cfg.get("human_binding_required", 0.0) or 0.0)
    penalty_retry = float(penalties_cfg.get("per_retry", 0.0) or 0.0)
    penalty_ungrounded = float(penalties_cfg.get("ungrounded_evidence", 0.0) or 0.0)

    semantic_issues = semantic_issues or []
    schema_issues = schema_issues or []
    human_required_fields = human_required_fields or []
    ungrounded_node_keys = ungrounded_node_keys or set()

    # Pre-compute per-node incoming/outgoing relation sets (by relation name)
    outgoing_actual: dict[str, set[str]] = {}
    incoming_actual: dict[str, set[str]] = {}
    for rel in ontology.relations:
        if not isinstance(rel, OntologyRelationInstance):
            continue
        if rel.from_id:
            outgoing_actual.setdefault(rel.from_id, set()).add(rel.name)
        if rel.to_id:
            incoming_actual.setdefault(rel.to_id, set()).add(rel.name)

    # Propagate relation evidence to nodes (Soluzione B):
    # Relations carry source_page evidence; nodes typically do not (prompt limitation).
    # A node that appears in a relation citing page P was referenced on that page,
    # so P counts as weak provenance for the node.
    relation_page_index = _build_relation_page_index(ontology.relations)

    # Pre-index human-required fields for O(1) lookup per (type, id).
    human_required_index: set[tuple[str, str]] = {
        (field.target_type, field.target_id)
        for field in human_required_fields
        if field.target_type and field.target_id
    }

    entries: list[ConfidenceEntry] = []
    counts: dict[str, int] = {
        "auto_approve": 0,
        "human_review": 0,
        "auto_reject": 0,
    }

    for node_type, items in (ontology.nodes or {}).items():
        required_props = _required_property_names(schema, node_type)
        outgoing_expected, incoming_expected = _expected_relations_for_type(schema, node_type)

        for item in items or []:
            if not isinstance(item, dict):
                continue
            node_id = _node_id(node_type, item)
            if not node_id:
                continue

            node_relation_pages = relation_page_index.get(node_id)
            signals: dict[str, float] = {
                "evidence_present": _signal_evidence_present(item, node_relation_pages),
                "corroboration": _signal_corroboration(item, node_relation_pages),
                "required_props_complete": _signal_required_props_complete(
                    item, required_props
                ),
                "chain_participation": _signal_chain_participation(
                    node_id,
                    outgoing_expected,
                    incoming_expected,
                    outgoing_actual,
                    incoming_actual,
                ),
                "clean_extraction": _signal_clean_extraction(
                    node_type,
                    node_id,
                    semantic_issues,
                    schema_issues,
                ),
            }

            weighted = sum(
                signals.get(name, 0.0) * weight for name, weight in weights.items()
            )

            applied_penalties: dict[str, float] = {}
            if (node_type, node_id) in human_required_index and penalty_human > 0:
                applied_penalties["human_binding_required"] = penalty_human
            if retry_count > 0 and penalty_retry > 0:
                # Cap retry penalty at 3× to avoid runaway deductions on long loops.
                applied_penalties["per_retry"] = min(3.0, float(retry_count)) * penalty_retry
            if (node_type, node_id) in ungrounded_node_keys and penalty_ungrounded > 0:
                applied_penalties["ungrounded_evidence"] = penalty_ungrounded

            final_score = _clamp(weighted - sum(applied_penalties.values()))

            if final_score >= theta_high:
                classification = "auto_approve"
            elif final_score < theta_low and auto_reject_enabled:
                classification = "auto_reject"
            else:
                classification = "human_review"

            reasons: list[str] = []
            if signals["evidence_present"] == 0.0:
                reasons.append("no evidence attached")
            elif not _collect_node_pages(item) and node_relation_pages:
                reasons.append("evidence inferred from relations only")
            if signals["required_props_complete"] < 1.0:
                reasons.append("missing required properties")
            if signals["chain_participation"] < 1.0 and (outgoing_expected or incoming_expected):
                reasons.append("incomplete schema-expected relations")
            if signals["clean_extraction"] < 1.0:
                reasons.append("validation issues or retries")
            if "human_binding_required" in applied_penalties:
                reasons.append("human binding required")
            if "ungrounded_evidence" in applied_penalties:
                reasons.append("evidence quote not found on cited page")

            entries.append(ConfidenceEntry(
                node_type=node_type,
                node_id=node_id,
                score=round(final_score, 4),
                classification=classification,
                signals={k: round(v, 4) for k, v in signals.items()},
                penalties={k: round(v, 4) for k, v in applied_penalties.items()},
                reasons=reasons,
            ))
            counts[classification] = counts.get(classification, 0) + 1

    logger.info(
        "[confidence] Scored %d nodes — auto_approve=%d, human_review=%d, auto_reject=%d",
        len(entries),
        counts.get("auto_approve", 0),
        counts.get("human_review", 0),
        counts.get("auto_reject", 0),
    )

    return ConfidenceReport(
        entries=entries,
        theta_high=theta_high,
        theta_low=theta_low,
        auto_reject_enabled=auto_reject_enabled,
        counts=counts,
    )
