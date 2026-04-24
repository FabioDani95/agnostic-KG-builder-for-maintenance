"""Compute coverage and clarity KPIs for an extracted ontology.

These KPIs describe how complete and diagnostically usable the graph is,
on top of the raw node/relationship counts already emitted in metrics.

The helpers accept either the internal pipeline representation
(``{"nodes": {...}, "relations": [...]}``) or the exported contract shape
(``{"nodes": {...}, "relationships": [...]}``). The output is a flat JSON-safe
dict ready to be embedded in ``metrics.json`` and the KPI widget.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

_NODE_ID_FIELDS = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}

_SCHEMA_RELATIONS = {
    "HAS_COMPONENT": ("Asset", "Component"),
    "MAY_INDICATE": ("Symptom", "FailureMode"),
    "AFFECTS": ("FailureMode", "Component"),
    "RESOLVED_BY": ("FailureMode", "CorrectiveAction"),
    "GENERATES_ERROR": ("Asset", "ErrorCode"),
    "INDICATES": ("ErrorCode", "FailureMode"),
}


def _ratio(numerator: int, denominator: int) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator, 4)


def _iter_relations(ontology: dict[str, Any]) -> Iterable[dict[str, Any]]:
    rels = ontology.get("relationships")
    if isinstance(rels, list):
        return rels
    rels = ontology.get("relations")
    if isinstance(rels, list):
        return rels
    return []


def _relation_endpoints(rel: dict[str, Any]) -> tuple[str, str, str]:
    rel_type = str(rel.get("type") or "").strip()
    from_id = str(rel.get("from_id") or rel.get("from") or "").strip()
    to_id = str(rel.get("to_id") or rel.get("to") or "").strip()
    return rel_type, from_id, to_id


def compute_graph_coverage(ontology: dict[str, Any]) -> dict[str, Any]:
    """Return a KPI dict describing coverage/clarity of the extracted graph."""

    nodes_by_type = ontology.get("nodes") or {}
    if not isinstance(nodes_by_type, dict):
        nodes_by_type = {}

    id_by_label: dict[str, str] = {}
    ids_by_label: dict[str, set[str]] = {label: set() for label in _NODE_ID_FIELDS}
    for label, id_field in _NODE_ID_FIELDS.items():
        items = nodes_by_type.get(label) or []
        for node in items:
            if not isinstance(node, dict):
                continue
            node_id = str(node.get(id_field) or "").strip()
            if not node_id:
                continue
            ids_by_label[label].add(node_id)
            id_by_label[node_id] = label

    # relationship index: (type) -> from -> {to}; (type) -> to -> {from}
    out_edges: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    in_edges: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    rel_type_counts: dict[str, int] = defaultdict(int)
    dangling_refs = 0
    domain_range_violations = 0

    for rel in _iter_relations(ontology):
        if not isinstance(rel, dict):
            continue
        rel_type, from_id, to_id = _relation_endpoints(rel)
        if not rel_type or not from_id or not to_id:
            continue
        rel_type_counts[rel_type] += 1
        fl = id_by_label.get(from_id)
        tl = id_by_label.get(to_id)
        if fl is None or tl is None:
            dangling_refs += 1
            continue
        expected = _SCHEMA_RELATIONS.get(rel_type)
        if expected and (fl != expected[0] or tl != expected[1]):
            domain_range_violations += 1
        out_edges[rel_type][from_id].add(to_id)
        in_edges[rel_type][to_id].add(from_id)

    symptom_ids = ids_by_label["Symptom"]
    failure_ids = ids_by_label["FailureMode"]
    action_ids = ids_by_label["CorrectiveAction"]
    component_ids = ids_by_label["Component"]
    error_ids = ids_by_label["ErrorCode"]

    # Upstream/downstream coverage
    sym_with_fm = {s for s in symptom_ids if out_edges["MAY_INDICATE"].get(s)}
    fm_with_action = {f for f in failure_ids if out_edges["RESOLVED_BY"].get(f)}
    fm_with_component = {f for f in failure_ids if out_edges["AFFECTS"].get(f)}
    fm_reachable_from_symptom = {f for f in failure_ids if in_edges["MAY_INDICATE"].get(f)}
    action_used = {a for a in action_ids if in_edges["RESOLVED_BY"].get(a)}
    components_in_fm = {c for c in component_ids if in_edges["AFFECTS"].get(c)}
    error_with_generates = {e for e in error_ids if in_edges["GENERATES_ERROR"].get(e)}
    error_with_indicates = {e for e in error_ids if out_edges["INDICATES"].get(e)}

    # End-to-end diagnostic chain: Symptom -> FailureMode -> CorrectiveAction
    chain_complete_symptoms = 0
    for sid in symptom_ids:
        reached = False
        for fid in out_edges["MAY_INDICATE"].get(sid, ()):
            if out_edges["RESOLVED_BY"].get(fid):
                reached = True
                break
        if reached:
            chain_complete_symptoms += 1

    # Breadth metrics
    ca_counts_per_fm = [
        len(out_edges["RESOLVED_BY"].get(fid, ())) for fid in failure_ids
    ]
    symptoms_per_fm = [
        len(in_edges["MAY_INDICATE"].get(fid, ())) for fid in failure_ids
    ]
    avg_actions_per_fm = (
        round(sum(ca_counts_per_fm) / len(ca_counts_per_fm), 3) if ca_counts_per_fm else 0.0
    )
    avg_symptoms_per_fm = (
        round(sum(symptoms_per_fm) / len(symptoms_per_fm), 3) if symptoms_per_fm else 0.0
    )

    total_nodes = sum(len(v) for v in ids_by_label.values())
    total_rels = sum(rel_type_counts.values())
    non_asset_nodes = max(0, total_nodes - len(ids_by_label["Asset"]))
    relationship_density = (
        round(total_rels / non_asset_nodes, 3) if non_asset_nodes else 0.0
    )

    schema_rel_types_present = {
        rt for rt in _SCHEMA_RELATIONS if rel_type_counts.get(rt, 0) > 0
    }
    missing_schema_rel_types = sorted(set(_SCHEMA_RELATIONS) - schema_rel_types_present)

    # Health score: unweighted average of the most critical ratios.
    health_components = [
        _ratio(len(sym_with_fm), len(symptom_ids)),
        _ratio(len(fm_with_action), len(failure_ids)),
        _ratio(len(fm_with_component), len(failure_ids)),
        _ratio(len(fm_reachable_from_symptom), len(failure_ids)),
        _ratio(len(action_used), len(action_ids)),
        _ratio(chain_complete_symptoms, len(symptom_ids)),
    ]
    health_components = [c for c in health_components if c is not None]
    health_score = (
        round(sum(health_components) / len(health_components), 4)
        if health_components
        else 0.0
    )

    return {
        "node_totals": {
            "Asset": len(ids_by_label["Asset"]),
            "Component": len(ids_by_label["Component"]),
            "Symptom": len(ids_by_label["Symptom"]),
            "FailureMode": len(ids_by_label["FailureMode"]),
            "CorrectiveAction": len(ids_by_label["CorrectiveAction"]),
            "ErrorCode": len(ids_by_label["ErrorCode"]),
        },
        "relationship_totals": dict(rel_type_counts),
        "diagnostic_chain": {
            "symptoms_total": len(symptom_ids),
            "symptoms_with_failure_mode": len(sym_with_fm),
            "symptoms_with_failure_mode_ratio": _ratio(len(sym_with_fm), len(symptom_ids)),
            "symptoms_end_to_end_resolved": chain_complete_symptoms,
            "symptoms_end_to_end_ratio": _ratio(chain_complete_symptoms, len(symptom_ids)),
            "orphan_symptoms": len(symptom_ids) - len(sym_with_fm),
        },
        "failure_mode_coverage": {
            "failure_modes_total": len(failure_ids),
            "with_corrective_action": len(fm_with_action),
            "with_corrective_action_ratio": _ratio(len(fm_with_action), len(failure_ids)),
            "with_component_anchor": len(fm_with_component),
            "with_component_anchor_ratio": _ratio(len(fm_with_component), len(failure_ids)),
            "reachable_from_symptom": len(fm_reachable_from_symptom),
            "reachable_from_symptom_ratio": _ratio(len(fm_reachable_from_symptom), len(failure_ids)),
            "without_corrective_action": len(failure_ids) - len(fm_with_action),
            "without_component_anchor": len(failure_ids) - len(fm_with_component),
            "orphan_upstream": len(failure_ids) - len(fm_reachable_from_symptom),
            "avg_corrective_actions_per_failure_mode": avg_actions_per_fm,
            "avg_symptoms_per_failure_mode": avg_symptoms_per_fm,
        },
        "corrective_action_coverage": {
            "corrective_actions_total": len(action_ids),
            "used_by_failure_mode": len(action_used),
            "used_by_failure_mode_ratio": _ratio(len(action_used), len(action_ids)),
            "orphan_corrective_actions": len(action_ids) - len(action_used),
        },
        "component_coverage": {
            "components_total": len(component_ids),
            "components_in_failure_chain": len(components_in_fm),
            "components_in_failure_chain_ratio": _ratio(len(components_in_fm), len(component_ids)),
            "components_only_structural": len(component_ids) - len(components_in_fm),
        },
        "error_code_coverage": {
            "error_codes_total": len(error_ids),
            "with_asset_link": len(error_with_generates),
            "with_failure_mode_link": len(error_with_indicates),
            "fully_wired": len(error_with_generates & error_with_indicates),
            "fully_wired_ratio": _ratio(len(error_with_generates & error_with_indicates), len(error_ids)),
        },
        "schema_integrity": {
            "dangling_references": dangling_refs,
            "domain_range_violations": domain_range_violations,
            "missing_relationship_types": missing_schema_rel_types,
            "relationship_density": relationship_density,
        },
        "health_score": health_score,
    }
