"""Graph reasoning module — Step 2 of the agentic roadmap.

Uses NetworkX to perform structural analysis on the extracted ontology instance:
- Detect incomplete diagnostic chains (Symptom → FailureMode → CorrectiveAction)
- Find orphaned nodes not reachable from the root Asset
- Identify FailureModes with no RESOLVED_BY relation
- Check that every Component referenced in AFFECTS actually exists
- Detect invalid cycles in the relation graph
- Suggest missing relations using semantic similarity

Produces structured GraphIssue and SuggestedRelation objects consumed by the
LangGraph pipeline node and surfaced to the operator in the frontend.
"""
from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from backend.models import (
    GraphIssue,
    OntologyInstance,
    OntologySchemaDefinition,
    SuggestedRelation,
)
from backend.services.ontology_semantics import semantic_tokens

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_nx_graph(ontology: OntologyInstance) -> nx.DiGraph:
    """Build a directed NetworkX graph from an OntologyInstance.

    Each node has attributes: node_type, label (name or id).
    Each edge has attributes: relation_name.
    """
    G = nx.DiGraph()

    for node_type, items in ontology.nodes.items():
        for item in items:
            node_id = _item_id(node_type, item)
            if not node_id:
                continue
            G.add_node(
                node_id,
                node_type=node_type,
                label=str(item.get("name", node_id)),
                data=item,
            )

    for rel in ontology.relations:
        if rel.from_id and rel.to_id:
            G.add_edge(rel.from_id, rel.to_id, relation_name=rel.name)

    return G


_ID_KEY: dict[str, str] = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}


def _item_id(node_type: str, item: dict[str, Any]) -> str:
    id_key = _ID_KEY.get(node_type, f"{node_type.lower()}_id")
    # Fallback: look for any key ending in _id
    val = str(item.get(id_key, "")).strip()
    if not val:
        for k, v in item.items():
            if k.endswith("_id") and v:
                return str(v).strip()
    return val


# ---------------------------------------------------------------------------
# Issue detection
# ---------------------------------------------------------------------------

def detect_chain_gaps(
    G: nx.DiGraph,
    ontology: OntologyInstance,
    schema: OntologySchemaDefinition,
) -> list[GraphIssue]:
    """Detect incomplete Symptom → FailureMode → CorrectiveAction chains."""
    issues: list[GraphIssue] = []
    symptoms = ontology.nodes.get("Symptom", [])
    failure_modes = ontology.nodes.get("FailureMode", [])
    error_codes = ontology.nodes.get("ErrorCode", [])

    # Build quick sets of existing relation pairs
    resolved_by_sources: set[str] = set()
    indicates_targets_by_error: dict[str, set[str]] = {}
    for rel in ontology.relations:
        if rel.name == "RESOLVED_BY":
            resolved_by_sources.add(rel.from_id)
        if rel.name == "INDICATES" and rel.from_id and rel.to_id:
            indicates_targets_by_error.setdefault(rel.from_id, set()).add(rel.to_id)

    # Symptoms with no outgoing MAY_INDICATE
    for symptom in symptoms:
        sid = _item_id("Symptom", symptom)
        if not sid:
            continue
        has_indicate = any(
            rel.from_id == sid and rel.name == "MAY_INDICATE"
            for rel in ontology.relations
        )
        if not has_indicate:
            issues.append(GraphIssue(
                issue_type="broken_chain",
                affected_nodes=[sid],
                description=f"Symptom '{symptom.get('name', sid)}' has no MAY_INDICATE relation to a FailureMode.",
                suggested_fix="Link this symptom to the most semantically similar FailureMode via MAY_INDICATE.",
                auto_fixable=False,
            ))

    # FailureModes with no RESOLVED_BY
    for fm in failure_modes:
        fid = _item_id("FailureMode", fm)
        if not fid:
            continue
        if fid not in resolved_by_sources:
            issues.append(GraphIssue(
                issue_type="missing_relation",
                affected_nodes=[fid],
                description=f"FailureMode '{fm.get('name', fid)}' has no RESOLVED_BY relation to a CorrectiveAction.",
                suggested_fix="Link this failure mode to the appropriate CorrectiveAction via RESOLVED_BY.",
                auto_fixable=False,
            ))

    # ErrorCodes should either identify a FailureMode that is resolved, or be
    # escalated to targeted retrieval/HITL. Manuals usually explain the remedy
    # near the code table, but the relation may require a second pass.
    for error_code in error_codes:
        eid = _item_id("ErrorCode", error_code)
        if not eid:
            continue
        indicated_failure_modes = indicates_targets_by_error.get(eid, set())
        if not indicated_failure_modes:
            issues.append(GraphIssue(
                issue_type="missing_relation",
                affected_nodes=[eid],
                description=(
                    f"ErrorCode '{error_code.get('name', eid)}' has no INDICATES "
                    "relation to a FailureMode."
                ),
                suggested_fix=(
                    "Use targeted retrieval around the error-code pages to link this "
                    "code to the failure condition it signals."
                ),
                auto_fixable=False,
            ))
            continue

        unresolved_failure_modes = [
            failure_mode_id
            for failure_mode_id in sorted(indicated_failure_modes)
            if failure_mode_id not in resolved_by_sources
        ]
        if unresolved_failure_modes:
            issues.append(GraphIssue(
                issue_type="broken_chain",
                affected_nodes=[eid, *unresolved_failure_modes],
                description=(
                    f"ErrorCode '{error_code.get('name', eid)}' indicates FailureMode(s) "
                    f"{', '.join(unresolved_failure_modes)} without a RESOLVED_BY "
                    "CorrectiveAction."
                ),
                suggested_fix=(
                    "Run targeted corrective-action retrieval for the indicated "
                    "failure mode(s), then add RESOLVED_BY relation(s)."
                ),
                auto_fixable=False,
            ))

    return issues


def detect_orphans(
    G: nx.DiGraph,
    ontology: OntologyInstance,
) -> list[GraphIssue]:
    """Find nodes not reachable from any Asset node (weakly connected)."""
    issues: list[GraphIssue] = []
    asset_ids = {
        _item_id("Asset", a)
        for a in ontology.nodes.get("Asset", [])
        if _item_id("Asset", a)
    }

    if not asset_ids:
        return issues

    # Build undirected version for reachability check
    UG = G.to_undirected()

    # Collect all nodes reachable from any asset
    reachable: set[str] = set()
    for asset_id in asset_ids:
        if asset_id in UG:
            reachable |= nx.node_connected_component(UG, asset_id)

    for node_id, attrs in G.nodes(data=True):
        if node_id in reachable:
            continue
        if attrs.get("node_type") == "Asset":
            continue
        issues.append(GraphIssue(
            issue_type="orphan",
            affected_nodes=[node_id],
            description=(
                f"{attrs.get('node_type', 'Node')} '{attrs.get('label', node_id)}' "
                f"is not connected to any Asset in the graph."
            ),
            suggested_fix="Connect this node to the asset graph via the appropriate relation, or remove it if spurious.",
            auto_fixable=False,
        ))

    return issues


def detect_invalid_cycles(G: nx.DiGraph) -> list[GraphIssue]:
    """Detect cycles in the directed relation graph (should be a DAG).

    Uses strongly connected components instead of simple-cycle enumeration:
    nx.simple_cycles is exponential in the worst case, while every cycle lives
    inside a non-trivial SCC (or a self-loop) and one issue per SCC is what the
    operator needs anyway.
    """
    issues: list[GraphIssue] = []
    try:
        non_trivial_sccs = [
            sorted(component)
            for component in nx.strongly_connected_components(G)
            if len(component) > 1
        ]
        self_loops = sorted(nx.nodes_with_selfloops(G))
    except Exception:
        return issues

    for component in sorted(non_trivial_sccs):
        issues.append(GraphIssue(
            issue_type="cycle",
            affected_nodes=component,
            description=f"Cycle detected among nodes: {', '.join(component)}.",
            suggested_fix="Review the relations forming this cycle and remove the incorrect edge.",
            auto_fixable=False,
        ))
    for node in self_loops:
        issues.append(GraphIssue(
            issue_type="cycle",
            affected_nodes=[node],
            description=f"Self-referencing relation detected on node: {node}.",
            suggested_fix="Remove the relation pointing the node at itself.",
            auto_fixable=False,
        ))
    return issues


def detect_affects_missing_components(
    G: nx.DiGraph,
    ontology: OntologyInstance,
) -> list[GraphIssue]:
    """Check that every Component referenced via AFFECTS actually exists in the graph."""
    issues: list[GraphIssue] = []
    existing_component_ids = {
        _item_id("Component", c)
        for c in ontology.nodes.get("Component", [])
        if _item_id("Component", c)
    }
    for rel in ontology.relations:
        if rel.name == "AFFECTS" and rel.to_type == "Component":
            if rel.to_id not in existing_component_ids:
                issues.append(GraphIssue(
                    issue_type="missing_relation",
                    affected_nodes=[rel.from_id, rel.to_id],
                    description=(
                        f"FailureMode '{rel.from_id}' has AFFECTS relation pointing to "
                        f"Component '{rel.to_id}' which does not exist in the ontology."
                    ),
                    suggested_fix=f"Add Component '{rel.to_id}' to the ontology or remove the dangling AFFECTS relation.",
                    auto_fixable=False,
                ))
    return issues


# ---------------------------------------------------------------------------
# Relation suggestions
# ---------------------------------------------------------------------------

_SUGGESTION_PAIRS: list[tuple[str, str, str]] = [
    # (relation_name, from_type, to_type)
    ("MAY_INDICATE", "Symptom", "FailureMode"),
    ("RESOLVED_BY", "FailureMode", "CorrectiveAction"),
    ("AFFECTS", "FailureMode", "Component"),
    ("HAS_COMPONENT", "Asset", "Component"),
]

# Minimum token-overlap ratio to propose a suggestion
_SIMILARITY_THRESHOLD = 0.20
# Maximum suggestions per (source node, relation type). Real diagnostic graphs
# are multi-cause/multi-target: proposing only the single best candidate hid
# legitimate parallel links from the operator.
_MAX_SUGGESTIONS_PER_SOURCE = 3


def suggest_missing_relations(
    ontology: OntologyInstance,
    schema: OntologySchemaDefinition,
) -> list[SuggestedRelation]:
    """Suggest missing relations based on semantic text similarity between nodes.

    Only proposes relations that do not already exist in the ontology.
    Uses token_overlap from ontology_semantics as the similarity signal.
    Returns up to _MAX_SUGGESTIONS_PER_SOURCE candidates per source node.
    """
    suggestions: list[SuggestedRelation] = []

    existing_edges: set[tuple[str, str, str]] = {
        (rel.name, rel.from_id, rel.to_id) for rel in ontology.relations
    }

    for rel_name, from_type, to_type in _SUGGESTION_PAIRS:
        from_items = ontology.nodes.get(from_type, [])
        to_items = ontology.nodes.get(to_type, [])
        if not from_items or not to_items:
            continue

        for from_item in from_items:
            from_id = _item_id(from_type, from_item)
            if not from_id:
                continue
            from_text = _node_text(from_item)
            from_label = from_item.get("name", from_id)

            scored: list[tuple[float, str, str]] = []
            for to_item in to_items:
                to_id = _item_id(to_type, to_item)
                if not to_id or (rel_name, from_id, to_id) in existing_edges:
                    continue
                score = _token_overlap(from_text, _node_text(to_item))
                if score >= _SIMILARITY_THRESHOLD:
                    scored.append((score, to_id, to_item.get("name", to_id)))

            scored.sort(key=lambda item: (-item[0], item[1]))
            for score, to_id, to_label in scored[:_MAX_SUGGESTIONS_PER_SOURCE]:
                suggestions.append(SuggestedRelation(
                    relation_name=rel_name,
                    from_type=from_type,
                    from_id=from_id,
                    from_label=from_label,
                    to_type=to_type,
                    to_id=to_id,
                    to_label=to_label,
                    confidence=round(score, 3),
                    rationale=(
                        f"Token overlap {score:.2f} between "
                        f"'{from_label}' and '{to_label}'."
                    ),
                ))

    # Sort by confidence descending
    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    return suggestions


def _token_overlap(text_a: str, text_b: str) -> float:
    """Jaccard-like token overlap between two text strings."""
    tokens_a = set(semantic_tokens(text_a))
    tokens_b = set(semantic_tokens(text_b))
    if not tokens_a or not tokens_b:
        return 0.0
    shared = tokens_a & tokens_b
    return len(shared) / max(1, min(len(tokens_a), len(tokens_b)))


def _node_text(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("name", "")),
        str(item.get("description", "")),
        str(item.get("material_context", "")),
        str(item.get("instruction_text", "")),
    ]
    return " ".join(p for p in parts if p).lower()


# ---------------------------------------------------------------------------
# Top-level analysis entry point
# ---------------------------------------------------------------------------

def run_graph_analysis(
    ontology: OntologyInstance,
    schema: OntologySchemaDefinition,
) -> tuple[list[GraphIssue], list[SuggestedRelation]]:
    """Run all graph analyses and return issues + suggestions.

    Called by the LangGraph graph_validate node.
    """
    G = build_nx_graph(ontology)

    issues: list[GraphIssue] = []
    issues += detect_chain_gaps(G, ontology, schema)
    issues += detect_orphans(G, ontology)
    issues += detect_affects_missing_components(G, ontology)
    issues += detect_invalid_cycles(G)

    suggestions = suggest_missing_relations(ontology, schema)

    logger.info(
        "[graph_reasoning] %d issue(s), %d suggestion(s)",
        len(issues),
        len(suggestions),
    )
    return issues, suggestions
