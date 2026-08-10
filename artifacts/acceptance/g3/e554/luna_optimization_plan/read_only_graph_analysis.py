#!/usr/bin/env python3
"""Read-only forensic analysis of the retained E-554 Luna revision.

The script opens SQLite with ``mode=ro`` and never imports application services
that could mutate operational state.  It computes topology and deterministic
view/projection metrics from the immutable SourceSubgraphRevision payload.
Gold witnesses are used only after projection as acceptance assertions.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


EXPECTED_REVISION_ID = "sgrev_OR8HyabEt7ntt0Z00LZEoA"
EXPECTED_WORKSPACE_ID = "ws_ebXgqKWDDgsjKdrGbFDiQQ"
EXPECTED_ASSET_ID = "asset_mF-1RBkvmra24woUH3T6iQ"
EXPECTED_CONFIG_HASH = "a56332c883f2ab0f6372aabad39c2e49c568bd0d8efc9a58bcff695af3b871e6"

ID_FIELD = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}

CAUSAL_RELATIONS = {"MAY_INDICATE", "RESOLVED_BY", "INDICATES"}
STRUCTURAL_RELATIONS = {"HAS_COMPONENT", "GENERATES_ERROR"}


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _simple_singular(value: str) -> str:
    words = _normalize(value).split()
    normalized: list[str] = []
    for word in words:
        if len(word) > 4 and word.endswith("ies"):
            word = f"{word[:-3]}y"
        elif len(word) > 4 and word.endswith("es") and not word.endswith(("ses", "xes")):
            word = word[:-2]
        elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        normalized.append(word)
    return " ".join(normalized)


def _node_pages(node: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]]) -> list[int]:
    pages: set[int] = set()
    for evidence_id in node.get("evidence_ids") or []:
        locator = (evidence_by_id.get(evidence_id) or {}).get("locator") or {}
        try:
            page = int(locator.get("page") or locator.get("page_number") or 0)
        except (TypeError, ValueError):
            page = 0
        if page > 0:
            pages.add(page)
    return sorted(pages)


def _relation_pages(relation: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]]) -> list[int]:
    pages: set[int] = set()
    for evidence_id in relation.get("evidence_ids") or []:
        locator = (evidence_by_id.get(evidence_id) or {}).get("locator") or {}
        try:
            page = int(locator.get("page") or locator.get("page_number") or 0)
        except (TypeError, ValueError):
            page = 0
        if page > 0:
            pages.add(page)
    return sorted(pages)


def _fanout_summary(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "minimum": 0, "median": 0, "maximum": 0, "sum": 0}
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2
    )
    return {
        "count": len(ordered),
        "minimum": min(ordered),
        "median": median,
        "maximum": max(ordered),
        "sum": sum(ordered),
    }


def _build_indexes(nodes: list[dict[str, Any]], relations: list[dict[str, Any]]) -> dict[str, Any]:
    node_by_id = {node["node_id"]: node for node in nodes}
    out_by_type: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    in_by_type: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    rels_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relation in relations:
        relation_type = relation["relation_type"]
        from_id = relation["from_id"]
        to_id = relation["to_id"]
        out_by_type[relation_type][from_id].add(to_id)
        in_by_type[relation_type][to_id].add(from_id)
        rels_by_type[relation_type].append(relation)
    return {
        "node_by_id": node_by_id,
        "out": out_by_type,
        "in": in_by_type,
        "relations_by_type": rels_by_type,
    }


def _topology_metrics(
    nodes: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    indexes = _build_indexes(nodes, relations)
    node_by_id = indexes["node_by_id"]
    out_by_type = indexes["out"]
    in_by_type = indexes["in"]
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    evidence_ids = set(evidence_by_id)

    all_out: dict[str, set[str]] = defaultdict(set)
    all_in: dict[str, set[str]] = defaultdict(set)
    for relation in relations:
        all_out[relation["from_id"]].add(relation["to_id"])
        all_in[relation["to_id"]].add(relation["from_id"])

    isolated = [
        node for node in nodes
        if not all_out.get(node["node_id"]) and not all_in.get(node["node_id"])
    ]
    symptoms = [node for node in nodes if node["node_type"] == "Symptom"]
    failure_modes = [node for node in nodes if node["node_type"] == "FailureMode"]
    actions = [node for node in nodes if node["node_type"] == "CorrectiveAction"]
    components = [node for node in nodes if node["node_type"] == "Component"]

    complete_symptoms: set[str] = set()
    complete_failure_modes: set[str] = set()
    complete_actions: set[str] = set()
    complete_paths: list[tuple[str, str, str]] = []
    for symptom in symptoms:
        symptom_id = symptom["node_id"]
        for failure_id in sorted(out_by_type["MAY_INDICATE"].get(symptom_id, set())):
            for action_id in sorted(out_by_type["RESOLVED_BY"].get(failure_id, set())):
                if failure_id in node_by_id and action_id in node_by_id:
                    complete_symptoms.add(symptom_id)
                    complete_failure_modes.add(failure_id)
                    complete_actions.add(action_id)
                    complete_paths.append((symptom_id, failure_id, action_id))

    symptoms_without_failure = {
        node["node_id"] for node in symptoms
        if not out_by_type["MAY_INDICATE"].get(node["node_id"])
    }
    symptoms_with_failure_without_complete_path = {
        node["node_id"] for node in symptoms
        if out_by_type["MAY_INDICATE"].get(node["node_id"])
        and node["node_id"] not in complete_symptoms
    }

    failure_with_symptom = {
        node["node_id"] for node in failure_modes
        if in_by_type["MAY_INDICATE"].get(node["node_id"])
    }
    failure_with_action = {
        node["node_id"] for node in failure_modes
        if out_by_type["RESOLVED_BY"].get(node["node_id"])
    }
    failure_with_component = {
        node["node_id"] for node in failure_modes
        if out_by_type["AFFECTS"].get(node["node_id"])
    }
    action_with_failure = {
        node["node_id"] for node in actions
        if in_by_type["RESOLVED_BY"].get(node["node_id"])
    }
    topology_problem_target_ids = (
        symptoms_without_failure
        | symptoms_with_failure_without_complete_path
        | ({node["node_id"] for node in failure_modes} - failure_with_symptom)
        | ({node["node_id"] for node in failure_modes} - failure_with_action)
        | ({node["node_id"] for node in actions} - action_with_failure)
    )
    diagnostic_component_ids = {
        component_id
        for failure_id in complete_failure_modes
        for component_id in out_by_type["AFFECTS"].get(failure_id, set())
        if component_id in node_by_id
    }

    referenced_evidence = {
        evidence_id
        for node in nodes
        for evidence_id in node.get("evidence_ids") or []
    } | {
        evidence_id
        for relation in relations
        for evidence_id in relation.get("evidence_ids") or []
    }

    def describe(node: dict[str, Any]) -> dict[str, Any]:
        return {
            "node_id": node["node_id"],
            "node_type": node["node_type"],
            "label": node.get("label", ""),
            "pages": _node_pages(node, evidence_by_id),
        }

    return {
        "nodes_total": len(nodes),
        "nodes_by_type": dict(sorted(Counter(node["node_type"] for node in nodes).items())),
        "relations_total": len(relations),
        "relations_by_type": dict(sorted(Counter(rel["relation_type"] for rel in relations).items())),
        "evidence_total": len(evidence),
        "referenced_evidence_total": len(referenced_evidence),
        "referenced_evidence_resolvable": len(referenced_evidence & evidence_ids),
        "referenced_evidence_unresolved": sorted(referenced_evidence - evidence_ids),
        "isolated_total": len(isolated),
        "isolated_by_type": dict(sorted(Counter(node["node_type"] for node in isolated).items())),
        "isolated_nodes": [describe(node) for node in isolated],
        "symptoms_total": len(symptoms),
        "symptoms_with_complete_path": len(complete_symptoms),
        "symptoms_without_complete_path": len(symptoms) - len(complete_symptoms),
        "symptoms_without_failure_mode": len(symptoms_without_failure),
        "symptoms_reaching_only_failure_modes_without_action": len(
            symptoms_with_failure_without_complete_path
        ),
        "failure_modes_total": len(failure_modes),
        "failure_modes_without_symptom": len(failure_modes) - len(failure_with_symptom),
        "failure_modes_without_action": len(failure_modes) - len(failure_with_action),
        "failure_modes_without_component": len(failure_modes) - len(failure_with_component),
        "failure_modes_with_component": len(failure_with_component),
        "failure_modes_with_complete_path": len(complete_failure_modes),
        "complete_failure_modes_with_component": len(
            complete_failure_modes & failure_with_component
        ),
        "complete_failure_modes_without_component": len(
            complete_failure_modes - failure_with_component
        ),
        "actions_total": len(actions),
        "actions_without_failure_mode": len(actions) - len(action_with_failure),
        "components_total": len(components),
        "components_diagnostic_in_complete_paths": len(diagnostic_component_ids),
        "components_structural_only_or_non_complete": len(components) - len(diagnostic_component_ids),
        "complete_path_count": len(complete_paths),
        "complete_path_node_ids": [list(path) for path in complete_paths],
        "unique_topology_problem_targets": len(topology_problem_target_ids),
    }


def _project_remove_isolated(
    nodes: list[dict[str, Any]], relations: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    touched = {
        endpoint
        for relation in relations
        for endpoint in (relation["from_id"], relation["to_id"])
    }
    return [node for node in nodes if node["node_id"] in touched], list(relations)


def _project_complete_diagnostic_view(
    nodes: list[dict[str, Any]], relations: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Project complete diagnostic chains plus their explicitly affected components.

    This is a simulation of a publish gate/view over the existing graph.  It does
    not claim that the upstream extractor would produce the same candidate set.
    """
    indexes = _build_indexes(nodes, relations)
    node_by_id = indexes["node_by_id"]
    out_by_type = indexes["out"]

    symptom_ids = {node["node_id"] for node in nodes if node["node_type"] == "Symptom"}
    error_code_ids = {node["node_id"] for node in nodes if node["node_type"] == "ErrorCode"}
    complete_symptoms: set[str] = set()
    complete_failure_modes: set[str] = set()
    complete_actions: set[str] = set()
    for symptom_id in symptom_ids:
        for failure_id in out_by_type["MAY_INDICATE"].get(symptom_id, set()):
            actions = out_by_type["RESOLVED_BY"].get(failure_id, set())
            if not actions:
                continue
            complete_symptoms.add(symptom_id)
            complete_failure_modes.add(failure_id)
            complete_actions.update(action_id for action_id in actions if action_id in node_by_id)

    complete_error_codes: set[str] = set()
    for error_code_id in error_code_ids:
        for failure_id in out_by_type["INDICATES"].get(error_code_id, set()):
            actions = out_by_type["RESOLVED_BY"].get(failure_id, set())
            if not actions:
                continue
            complete_error_codes.add(error_code_id)
            complete_failure_modes.add(failure_id)
            complete_actions.update(action_id for action_id in actions if action_id in node_by_id)

    diagnostic_components = {
        component_id
        for failure_id in complete_failure_modes
        for component_id in out_by_type["AFFECTS"].get(failure_id, set())
        if component_id in node_by_id
    }
    asset_ids = {node["node_id"] for node in nodes if node["node_type"] == "Asset"}
    error_codes = complete_error_codes
    keep_ids = (
        asset_ids
        | complete_symptoms
        | complete_failure_modes
        | complete_actions
        | diagnostic_components
        | error_codes
    )

    keep_relation_keys: set[tuple[str, str, str]] = set()
    for relation in relations:
        relation_type = relation["relation_type"]
        from_id = relation["from_id"]
        to_id = relation["to_id"]
        keep = False
        if relation_type == "MAY_INDICATE":
            keep = from_id in complete_symptoms and to_id in complete_failure_modes
        elif relation_type == "RESOLVED_BY":
            keep = from_id in complete_failure_modes and to_id in complete_actions
        elif relation_type == "AFFECTS":
            keep = from_id in complete_failure_modes and to_id in diagnostic_components
        elif relation_type == "HAS_COMPONENT":
            keep = from_id in asset_ids and to_id in diagnostic_components
        elif relation_type == "INDICATES":
            keep = from_id in error_codes and to_id in complete_failure_modes
        elif relation_type == "GENERATES_ERROR":
            keep = from_id in asset_ids and to_id in error_codes
        if keep:
            keep_relation_keys.add((relation_type, from_id, to_id))

    projected_relations = [
        relation for relation in relations
        if (relation["relation_type"], relation["from_id"], relation["to_id"])
        in keep_relation_keys
    ]
    touched = {
        endpoint
        for relation in projected_relations
        for endpoint in (relation["from_id"], relation["to_id"])
    }
    # The canonical Asset must remain in the graph. If no diagnostic component
    # exists, leaving the Asset isolated would violate the publication invariant;
    # report that as an infeasible projection instead of silently dropping it.
    projected_nodes = [node for node in nodes if node["node_id"] in keep_ids and node["node_id"] in touched]
    infeasible_asset_ids = sorted(asset_ids - touched)
    return projected_nodes, projected_relations, {
        "candidate_nodes_excluded": len(nodes) - len(projected_nodes),
        "candidate_relations_excluded": len(relations) - len(projected_relations),
        "canonical_asset_unconnected": infeasible_asset_ids,
        "diagnostic_component_ids": sorted(diagnostic_components),
    }


def _project_union(
    *projections: tuple[list[dict[str, Any]], list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Union compatible views by stable IDs without changing canonical claims."""
    nodes_by_id: dict[str, dict[str, Any]] = {}
    relations_by_id: dict[str, dict[str, Any]] = {}
    for nodes, relations in projections:
        nodes_by_id.update({node["node_id"]: node for node in nodes})
        relations_by_id.update({relation["relation_id"]: relation for relation in relations})
    return list(nodes_by_id.values()), list(relations_by_id.values())


def _project_structural_view(
    nodes: list[dict[str, Any]], relations: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    keep_types = {"Asset", "Component"}
    keep_ids = {node["node_id"] for node in nodes if node["node_type"] in keep_types}
    keep_relations = [
        relation for relation in relations
        if relation["relation_type"] == "HAS_COMPONENT"
        and relation["from_id"] in keep_ids
        and relation["to_id"] in keep_ids
    ]
    touched = {
        endpoint
        for relation in keep_relations
        for endpoint in (relation["from_id"], relation["to_id"])
    }
    return [node for node in nodes if node["node_id"] in touched], keep_relations


def _exact_label_id(nodes: Iterable[dict[str, Any]], label: str, node_type: str) -> str:
    target = _normalize(label)
    matches = [
        node["node_id"]
        for node in nodes
        if node["node_type"] == node_type and _normalize(node.get("label", "")) == target
    ]
    return sorted(matches)[0] if matches else ""


def _acceptance_witnesses(
    nodes: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    validation_result: dict[str, Any],
) -> dict[str, Any]:
    """Verify frozen baseline witnesses after projection (acceptance use only)."""
    edge_keys = {
        (relation["relation_type"], relation["from_id"], relation["to_id"])
        for relation in relations
    }
    matches: list[dict[str, Any]] = []
    for witness in validation_result["gold_evaluation"]["matches"]:
        symptom_id = _exact_label_id(nodes, witness["symptom"], "Symptom")
        failure_id = _exact_label_id(nodes, witness["failure_mode"], "FailureMode")
        action_id = _exact_label_id(nodes, witness["corrective_action"], "CorrectiveAction")
        present = bool(
            symptom_id
            and failure_id
            and action_id
            and ("MAY_INDICATE", symptom_id, failure_id) in edge_keys
            and ("RESOLVED_BY", failure_id, action_id) in edge_keys
        )
        matches.append({
            "gold": witness["gold"],
            "present": present,
            "symptom_id": symptom_id,
            "failure_mode_id": failure_id,
            "corrective_action_id": action_id,
        })

    forbidden: list[dict[str, Any]] = []
    for witness in validation_result["gold_evaluation"]["forbidden_pairings"]:
        symptom_id = _exact_label_id(nodes, witness["symptom"], "Symptom")
        failure_id = _exact_label_id(nodes, witness["failure_mode"], "FailureMode")
        found = bool(
            symptom_id
            and failure_id
            and ("MAY_INDICATE", symptom_id, failure_id) in edge_keys
        )
        forbidden.append({
            "symptom": witness["symptom"],
            "failure_mode": witness["failure_mode"],
            "found": found,
        })
    return {
        "gold_chains_present": sum(item["present"] for item in matches),
        "gold_chains_total": len(matches),
        "gold_witnesses": matches,
        "forbidden_pairings_found": sum(item["found"] for item in forbidden),
        "forbidden_pairings_total": len(forbidden),
        "forbidden_witnesses": forbidden,
        "method": "exact node-label witnesses frozen in luna_validation/result.json; acceptance-only",
    }


def _near_duplicate_candidates(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Conservative candidate generation; never an automatic merge decision."""
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        if node["node_type"] != "Asset":
            by_type[node["node_type"]].append(node)

    candidates: list[dict[str, Any]] = []
    for node_type, items in sorted(by_type.items()):
        for index, left in enumerate(items):
            left_norm = _normalize(left.get("label", ""))
            left_singular = _simple_singular(left_norm)
            left_tokens = set(left_singular.split())
            if not left_tokens:
                continue
            for right in items[index + 1 :]:
                right_norm = _normalize(right.get("label", ""))
                if left_norm == right_norm:
                    continue
                right_singular = _simple_singular(right_norm)
                right_tokens = set(right_singular.split())
                if not right_tokens:
                    continue
                shared = left_tokens & right_tokens
                containment = len(shared) / max(1, min(len(left_tokens), len(right_tokens)))
                union_score = len(shared) / max(1, len(left_tokens | right_tokens))
                singular_equal = left_singular == right_singular
                # Keep only strong lexical candidates. Single generic tokens such
                # as "filter" contained in a more specific component are not a
                # sufficient candidate signal. Context and incident-edge
                # compatibility must still be checked before any eventual merge.
                strong_multitoken_overlap = (
                    len(shared) >= 2 and containment >= 0.80 and union_score >= 0.60
                )
                if not (singular_equal or union_score >= 0.78 or strong_multitoken_overlap):
                    continue
                candidates.append({
                    "node_type": node_type,
                    "left_id": left["node_id"],
                    "left_label": left.get("label", ""),
                    "right_id": right["node_id"],
                    "right_label": right.get("label", ""),
                    "singular_equal": singular_equal,
                    "token_containment": round(containment, 4),
                    "token_jaccard": round(union_score, 4),
                })
    return sorted(
        candidates,
        key=lambda item: (
            item["node_type"],
            -int(item["singular_equal"]),
            -item["token_containment"],
            item["left_label"],
            item["right_label"],
        ),
    )


def _load_revision(database_path: Path, revision_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    uri = f"file:{database_path.resolve()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            """
            SELECT source_subgraph_revision_id, workspace_id, source_id,
                   input_config_hash, preparation_fingerprint, payload_json,
                   supersedes, created_at
            FROM source_subgraph_revisions
            WHERE source_subgraph_revision_id = ?
            """,
            (revision_id,),
        ).fetchone()
        if row is None:
            raise SystemExit(f"Revision not found: {revision_id}")
        decision_count = int(connection.execute(
            "SELECT COUNT(*) FROM source_subgraph_decisions WHERE source_subgraph_revision_id = ?",
            (revision_id,),
        ).fetchone()[0])
        source_row = connection.execute(
            "SELECT source_id, workspace_id, source_kind, authority, file_name, status, sha256 "
            "FROM sources WHERE source_id = ?",
            (row["source_id"],),
        ).fetchone()
        payload = json.loads(row["payload_json"])
        metadata = {
            "source_subgraph_revision_id": row["source_subgraph_revision_id"],
            "workspace_id": row["workspace_id"],
            "source_id": row["source_id"],
            "input_config_hash": row["input_config_hash"],
            "preparation_fingerprint": row["preparation_fingerprint"],
            "supersedes": row["supersedes"],
            "created_at": row["created_at"],
            "decision_count": decision_count,
            "derived_status": "reviewing" if decision_count == 0 else "decided",
            "database_open_mode": "read_only",
            "source": dict(source_row) if source_row is not None else None,
        }
        return payload, metadata
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=Path("data/operational.db"))
    parser.add_argument("--revision-id", default=EXPECTED_REVISION_ID)
    parser.add_argument(
        "--validation-result",
        type=Path,
        default=Path("artifacts/acceptance/g3/e554/luna_validation/result.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload, metadata = _load_revision(args.database, args.revision_id)
    assert metadata["source_subgraph_revision_id"] == EXPECTED_REVISION_ID
    assert metadata["workspace_id"] == EXPECTED_WORKSPACE_ID
    assert metadata["input_config_hash"] == EXPECTED_CONFIG_HASH
    assert metadata["decision_count"] == 0

    validation_result = json.loads(args.validation_result.read_text(encoding="utf-8"))
    nodes = payload.get("nodes") or []
    relations = payload.get("relations") or []
    evidence = payload.get("evidence") or []
    asset_nodes = [node for node in nodes if node["node_type"] == "Asset"]
    assert len(asset_nodes) == 1 and asset_nodes[0]["node_id"] == EXPECTED_ASSET_ID

    baseline_metrics = _topology_metrics(nodes, relations, evidence)
    baseline_acceptance = _acceptance_witnesses(nodes, relations, validation_result)

    no_isolated_nodes, no_isolated_relations = _project_remove_isolated(nodes, relations)
    no_isolated_metrics = _topology_metrics(no_isolated_nodes, no_isolated_relations, evidence)

    diagnostic_nodes, diagnostic_relations, diagnostic_notes = _project_complete_diagnostic_view(
        nodes, relations
    )
    diagnostic_metrics = _topology_metrics(diagnostic_nodes, diagnostic_relations, evidence)
    diagnostic_acceptance = _acceptance_witnesses(
        diagnostic_nodes, diagnostic_relations, validation_result
    )

    structural_nodes, structural_relations = _project_structural_view(nodes, relations)
    structural_metrics = _topology_metrics(structural_nodes, structural_relations, evidence)
    canonical_nodes, canonical_relations = _project_union(
        (diagnostic_nodes, diagnostic_relations),
        (structural_nodes, structural_relations),
    )
    canonical_metrics = _topology_metrics(canonical_nodes, canonical_relations, evidence)

    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    gaps = payload.get("knowledge_gaps") or []
    node_evidence_fanout = {
        node_type: _fanout_summary([
            len(node.get("evidence_ids") or [])
            for node in nodes
            if node["node_type"] == node_type
        ])
        for node_type in sorted(ID_FIELD)
    }
    relation_evidence_fanout = {
        relation_type: _fanout_summary([
            len(relation.get("evidence_ids") or [])
            for relation in relations
            if relation["relation_type"] == relation_type
        ])
        for relation_type in sorted({relation["relation_type"] for relation in relations})
    }
    result = {
        "analysis_kind": "offline_read_only_simulation",
        "revision_integrity": metadata,
        "payload_contract": {
            "node_count": len(nodes),
            "relation_count": len(relations),
            "evidence_count": len(evidence),
            "knowledge_gap_count": len(gaps),
            "validation": payload.get("validation"),
            "approval_eligible": payload.get("approval_eligible"),
            "generation_metrics": payload.get("generation_metrics"),
            "pdf_extraction_scope": payload.get("pdf_extraction_scope"),
        },
        "baseline": {
            "measurement_status": "measured_from_immutable_revision",
            "metrics": baseline_metrics,
            "acceptance": baseline_acceptance,
            "knowledge_gaps_by_code": dict(sorted(Counter(gap["code"] for gap in gaps).items())),
            "knowledge_gaps": gaps,
            "provenance_fanout": {
                "node_evidence_ids": node_evidence_fanout,
                "relation_evidence_ids": relation_evidence_fanout,
                "asset_referenced_evidence_count": sum(
                    len(node.get("evidence_ids") or [])
                    for node in nodes
                    if node["node_type"] == "Asset"
                ),
                "persisted_relation_claim_quote_available": False,
                "note": (
                    "SourceGraphRelation stores evidence_ids only. Exact relation quote and "
                    "source_anchor are discarded by the adapter, so claim-level provenance "
                    "precision cannot be reconstructed from this revision."
                ),
            },
        },
        "simulations": {
            "remove_only_completely_isolated_nodes": {
                "measurement_status": "simulated_deterministic_projection",
                "metrics": no_isolated_metrics,
                "acceptance": _acceptance_witnesses(
                    no_isolated_nodes, no_isolated_relations, validation_result
                ),
                "limitation": (
                    "Removes degree-zero nodes only; incomplete chains and structural-view clutter remain."
                ),
            },
            "complete_diagnostic_view": {
                "measurement_status": "simulated_deterministic_projection_of_existing_claims",
                "metrics": diagnostic_metrics,
                "acceptance": diagnostic_acceptance,
                "notes": diagnostic_notes,
                "grounding_limitation": (
                    "The persisted SourceGraphRelation retains canonical evidence_ids but not the exact "
                    "relation quote/source_anchor tuple. Resolvability is measurable; the two known "
                    "ungrounded relation identities are not recoverable from this payload."
                ),
            },
            "structural_component_view": {
                "measurement_status": "simulated_deterministic_projection",
                "metrics": structural_metrics,
                "acceptance": "not_applicable_structural_view",
            },
            "canonical_publishable_union": {
                "measurement_status": (
                    "simulated_union_of_complete_diagnostic_and_structural_projections"
                ),
                "metrics": canonical_metrics,
                "acceptance": _acceptance_witnesses(
                    canonical_nodes, canonical_relations, validation_result
                ),
                "grounding_limitation": (
                    "This preserves only existing relation evidence IDs. The persisted contract "
                    "does not retain the exact quote/source_anchor tuple needed to prove the "
                    "future 100% claim-level grounding gate."
                ),
            },
        },
        "near_duplicate_analysis": {
            "measurement_status": "offline_lexical_candidates_not_merge_decisions",
            "exact_normalized_duplicate_groups": sum(
                1
                for node_type in ID_FIELD
                for count in Counter(
                    _normalize(node.get("label", ""))
                    for node in nodes
                    if node["node_type"] == node_type
                ).values()
                if count > 1
            ),
            "candidate_pairs": _near_duplicate_candidates(nodes),
        },
        "relation_evidence_pages": [
            {
                "relation_id": relation["relation_id"],
                "relation_type": relation["relation_type"],
                "from_id": relation["from_id"],
                "to_id": relation["to_id"],
                "evidence_ids": relation.get("evidence_ids") or [],
                "pages": _relation_pages(relation, evidence_by_id),
            }
            for relation in relations
        ],
        "api_budget_ledger": {
            "authorized_budget_usd": 0.50,
            "calls_made": 0,
            "actual_spend_usd": 0.0,
            "remaining_budget_usd": 0.50,
            "reason": "Offline evidence is sufficient for diagnosis and implementation planning.",
        },
    }

    serialized = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
