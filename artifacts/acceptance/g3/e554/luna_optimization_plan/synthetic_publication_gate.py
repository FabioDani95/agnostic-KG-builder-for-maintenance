#!/usr/bin/env python3
"""Manual-agnostic executable specification for the proposed publication gate.

This is analysis code, not application code.  It uses only the configured
ontology's node/relation names, domains and ranges.  The fixtures deliberately
cover several generic asset domains and prove the intended projection behavior:
complete grounded diagnostic chains are published, structural components stay
available in a separate view, and incomplete or unsupported claims become gaps.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def load_contract(path: Path) -> tuple[set[str], dict[str, tuple[str, str]]]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    node_types = {item["name"] for item in schema["nodes"]}
    relation_contract = {
        item["name"]: (item["domain"], item["range"])
        for item in schema["relations"]
    }
    return node_types, relation_contract


def relation_is_grounded(relation: dict[str, Any], evidence: dict[str, str]) -> bool:
    claims = relation.get("evidence") or []
    if not claims:
        return False
    for claim in claims:
        anchor = str(claim.get("source_anchor") or "").strip()
        quote = normalize(claim.get("quote") or "")
        source = normalize(evidence.get(anchor, ""))
        if anchor and quote and source and quote in source:
            return True
    return False


def project_case(
    case: dict[str, Any],
    *,
    node_types: set[str],
    relation_contract: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    nodes = case["nodes"]
    evidence = case["evidence"]
    node_by_id = {node["node_id"]: node for node in nodes}
    assert len(node_by_id) == len(nodes)
    assert all(node["node_type"] in node_types for node in nodes)

    valid_relations: list[dict[str, Any]] = []
    rejected_relations: list[dict[str, Any]] = []
    for relation in case["relations"]:
        expected = relation_contract.get(relation["relation_type"])
        source = node_by_id.get(relation["from_id"])
        target = node_by_id.get(relation["to_id"])
        reasons: list[str] = []
        if expected is None:
            reasons.append("unknown_relation")
        elif source is None or target is None:
            reasons.append("missing_endpoint")
        elif (source["node_type"], target["node_type"]) != expected:
            reasons.append("domain_range")
        if not relation_is_grounded(relation, evidence):
            reasons.append("claim_evidence_unresolved")
        if reasons:
            rejected_relations.append({
                "relation_id": relation["relation_id"],
                "reasons": reasons,
            })
        else:
            valid_relations.append(relation)

    out: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    incoming: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for relation in valid_relations:
        out[relation["relation_type"]][relation["from_id"]].add(relation["to_id"])
        incoming[relation["relation_type"]][relation["to_id"]].add(relation["from_id"])

    failure_ids = {
        node["node_id"] for node in nodes if node["node_type"] == "FailureMode"
    }
    complete_failures = {
        failure_id
        for failure_id in failure_ids
        if out["RESOLVED_BY"].get(failure_id)
        and (
            incoming["MAY_INDICATE"].get(failure_id)
            or incoming["INDICATES"].get(failure_id)
        )
    }
    symptom_ids = {
        symptom_id
        for failure_id in complete_failures
        for symptom_id in incoming["MAY_INDICATE"].get(failure_id, set())
    }
    error_ids = {
        error_id
        for failure_id in complete_failures
        for error_id in incoming["INDICATES"].get(failure_id, set())
    }
    action_ids = {
        action_id
        for failure_id in complete_failures
        for action_id in out["RESOLVED_BY"].get(failure_id, set())
    }
    diagnostic_component_ids = {
        component_id
        for failure_id in complete_failures
        for component_id in out["AFFECTS"].get(failure_id, set())
    }
    asset_ids = {node["node_id"] for node in nodes if node["node_type"] == "Asset"}
    diagnostic_ids = (
        complete_failures | symptom_ids | error_ids | action_ids | diagnostic_component_ids
    )

    diagnostic_relations = [
        relation
        for relation in valid_relations
        if (
            relation["relation_type"] in {"MAY_INDICATE", "INDICATES", "RESOLVED_BY", "AFFECTS"}
            and relation["from_id"] in diagnostic_ids
            and relation["to_id"] in diagnostic_ids
        )
        or (
            relation["relation_type"] == "HAS_COMPONENT"
            and relation["from_id"] in asset_ids
            and relation["to_id"] in diagnostic_component_ids
        )
        or (
            relation["relation_type"] == "GENERATES_ERROR"
            and relation["from_id"] in asset_ids
            and relation["to_id"] in error_ids
        )
    ]
    diagnostic_touched = {
        endpoint
        for relation in diagnostic_relations
        for endpoint in (relation["from_id"], relation["to_id"])
    }
    diagnostic_nodes = [node for node in nodes if node["node_id"] in diagnostic_touched]

    structural_relations = [
        relation for relation in valid_relations
        if relation["relation_type"] == "HAS_COMPONENT"
    ]
    structural_touched = {
        endpoint
        for relation in structural_relations
        for endpoint in (relation["from_id"], relation["to_id"])
    }
    structural_nodes = [node for node in nodes if node["node_id"] in structural_touched]

    canonical_ids = diagnostic_touched | structural_touched
    canonical_relations = {
        relation["relation_id"]: relation
        for relation in [*diagnostic_relations, *structural_relations]
    }
    canonical_nodes = [node for node in nodes if node["node_id"] in canonical_ids]
    degrees = Counter(
        endpoint
        for relation in canonical_relations.values()
        for endpoint in (relation["from_id"], relation["to_id"])
    )

    gaps: list[dict[str, str]] = []
    for node in nodes:
        node_id = node["node_id"]
        node_type = node["node_type"]
        if node_type == "Symptom" and node_id not in symptom_ids:
            gaps.append({"target_id": node_id, "code": "incomplete_symptom_chain"})
        elif node_type == "ErrorCode" and node_id not in error_ids:
            gaps.append({"target_id": node_id, "code": "incomplete_error_chain"})
        elif node_type == "CorrectiveAction" and node_id not in action_ids:
            gaps.append({"target_id": node_id, "code": "unlinked_or_noncorrective_action"})
        elif node_type == "FailureMode" and node_id not in complete_failures:
            gaps.append({"target_id": node_id, "code": "incomplete_failure_chain"})

    metrics = {
        "canonical_nodes": len(canonical_nodes),
        "canonical_relations": len(canonical_relations),
        "canonical_isolated_nodes": sum(degrees[node["node_id"]] == 0 for node in canonical_nodes),
        "diagnostic_nodes_by_type": dict(sorted(Counter(
            node["node_type"] for node in diagnostic_nodes
        ).items())),
        "structural_nodes_by_type": dict(sorted(Counter(
            node["node_type"] for node in structural_nodes
        ).items())),
        "published_symptoms": len(symptom_ids),
        "published_complete_failure_modes": len(complete_failures),
        "published_actions": len(action_ids),
        "published_actions_without_failure_mode": sum(
            not incoming["RESOLVED_BY"].get(action_id) for action_id in action_ids
        ),
        "grounded_relations_published": len(canonical_relations),
        "ungrounded_relations_published": 0,
        "rejected_relations": len(rejected_relations),
        "gaps": len(gaps),
    }
    return {
        "case_id": case["case_id"],
        "metrics": metrics,
        "gaps": gaps,
        "rejected_relations": rejected_relations,
        "published_node_ids": sorted(canonical_ids),
    }


def relation(
    relation_id: str,
    relation_type: str,
    source: str,
    target: str,
    anchor: str,
    quote: str,
) -> dict[str, Any]:
    return {
        "relation_id": relation_id,
        "relation_type": relation_type,
        "from_id": source,
        "to_id": target,
        "evidence": [{"source_anchor": anchor, "quote": quote}],
    }


def cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "grounded_pump_chain_with_structural_component",
            "evidence": {
                "ev1": "Low outlet flow may be caused by a clogged inlet filter.",
                "ev2": "If the inlet filter is clogged, clean or replace the inlet filter.",
                "ev3": "The pump assembly includes an inlet filter.",
            },
            "nodes": [
                {"node_id": "asset_pump", "node_type": "Asset", "label": "Pump"},
                {"node_id": "comp_filter", "node_type": "Component", "label": "Inlet filter"},
                {"node_id": "sym_low_flow", "node_type": "Symptom", "label": "Low outlet flow"},
                {"node_id": "fm_clogged_filter", "node_type": "FailureMode", "label": "Inlet filter clogged"},
                {"node_id": "ca_clean_filter", "node_type": "CorrectiveAction", "label": "Clean or replace filter"},
            ],
            "relations": [
                relation("r1", "MAY_INDICATE", "sym_low_flow", "fm_clogged_filter", "ev1", "Low outlet flow may be caused by a clogged inlet filter"),
                relation("r2", "RESOLVED_BY", "fm_clogged_filter", "ca_clean_filter", "ev2", "If the inlet filter is clogged, clean or replace the inlet filter"),
                relation("r3", "AFFECTS", "fm_clogged_filter", "comp_filter", "ev2", "inlet filter is clogged"),
                relation("r4", "HAS_COMPONENT", "asset_pump", "comp_filter", "ev3", "pump assembly includes an inlet filter"),
            ],
            "expect": {"published_symptoms": 1, "published_actions": 1, "gaps": 0},
        },
        {
            "case_id": "preventive_safety_install_actions_do_not_publish",
            "evidence": {
                "ev1": "Inspect guards weekly. Wear eye protection. Level the machine before installation.",
                "ev2": "Motor overheating can result from a blocked cooling fan.",
                "ev3": "Clean the fan guard monthly to prevent dust accumulation.",
                "ev4": "The machine includes a cooling fan.",
            },
            "nodes": [
                {"node_id": "asset_machine", "node_type": "Asset", "label": "Machine"},
                {"node_id": "comp_fan", "node_type": "Component", "label": "Cooling fan"},
                {"node_id": "sym_hot", "node_type": "Symptom", "label": "Motor overheating"},
                {"node_id": "fm_blocked_fan", "node_type": "FailureMode", "label": "Cooling fan blocked"},
                {"node_id": "ca_inspect", "node_type": "CorrectiveAction", "label": "Inspect guards weekly"},
                {"node_id": "ca_ppe", "node_type": "CorrectiveAction", "label": "Wear eye protection"},
                {"node_id": "ca_level", "node_type": "CorrectiveAction", "label": "Level machine before installation"},
                {"node_id": "ca_preventive", "node_type": "CorrectiveAction", "label": "Clean fan guard monthly"},
            ],
            "relations": [
                relation("r1", "MAY_INDICATE", "sym_hot", "fm_blocked_fan", "ev2", "Motor overheating can result from a blocked cooling fan"),
                # The evidence is real text but does not state that the monthly task
                # resolves the explicit failure, so claim-level grounding fails.
                relation("r2", "RESOLVED_BY", "fm_blocked_fan", "ca_preventive", "ev3", "If the cooling fan is blocked clean it now"),
                relation("r3", "HAS_COMPONENT", "asset_machine", "comp_fan", "ev4", "machine includes a cooling fan"),
            ],
            "expect": {"published_symptoms": 0, "published_actions": 0, "gaps": 6},
        },
        {
            "case_id": "incomplete_conveyor_symptom_becomes_gap",
            "evidence": {
                "ev1": "Belt drift may indicate that the tracking roller is misaligned.",
                "ev2": "The conveyor includes a tracking roller.",
            },
            "nodes": [
                {"node_id": "asset_conveyor", "node_type": "Asset", "label": "Conveyor"},
                {"node_id": "comp_roller", "node_type": "Component", "label": "Tracking roller"},
                {"node_id": "sym_drift", "node_type": "Symptom", "label": "Belt drift"},
                {"node_id": "fm_misaligned", "node_type": "FailureMode", "label": "Tracking roller misaligned"},
            ],
            "relations": [
                relation("r1", "MAY_INDICATE", "sym_drift", "fm_misaligned", "ev1", "Belt drift may indicate that the tracking roller is misaligned"),
                relation("r2", "HAS_COMPONENT", "asset_conveyor", "comp_roller", "ev2", "conveyor includes a tracking roller"),
            ],
            "expect": {"published_symptoms": 0, "published_actions": 0, "gaps": 2},
        },
        {
            "case_id": "error_code_chain_without_symptom_is_valid",
            "evidence": {
                "ev1": "Alarm E42 indicates loss of encoder feedback.",
                "ev2": "For loss of encoder feedback, reconnect the encoder cable.",
                "ev3": "The controller generates Alarm E42 when feedback is lost.",
            },
            "nodes": [
                {"node_id": "asset_controller", "node_type": "Asset", "label": "Controller"},
                {"node_id": "err_e42", "node_type": "ErrorCode", "label": "Alarm E42"},
                {"node_id": "fm_feedback", "node_type": "FailureMode", "label": "Encoder feedback lost"},
                {"node_id": "ca_reconnect", "node_type": "CorrectiveAction", "label": "Reconnect encoder cable"},
            ],
            "relations": [
                relation("r1", "INDICATES", "err_e42", "fm_feedback", "ev1", "Alarm E42 indicates loss of encoder feedback"),
                relation("r2", "RESOLVED_BY", "fm_feedback", "ca_reconnect", "ev2", "For loss of encoder feedback, reconnect the encoder cable"),
                relation("r3", "GENERATES_ERROR", "asset_controller", "err_e42", "ev3", "controller generates Alarm E42"),
            ],
            "expect": {"published_symptoms": 0, "published_actions": 1, "gaps": 0},
        },
        {
            "case_id": "affects_optional_but_asset_remains_structurally_owned",
            "evidence": {
                "ev1": "Unstable temperature may indicate an invalid control parameter.",
                "ev2": "If the control parameter is invalid, restore the documented default.",
                "ev3": "The thermal system includes a controller module.",
            },
            "nodes": [
                {"node_id": "asset_thermal", "node_type": "Asset", "label": "Thermal system"},
                {"node_id": "comp_controller", "node_type": "Component", "label": "Controller module"},
                {"node_id": "sym_unstable", "node_type": "Symptom", "label": "Unstable temperature"},
                {"node_id": "fm_parameter", "node_type": "FailureMode", "label": "Control parameter invalid"},
                {"node_id": "ca_restore", "node_type": "CorrectiveAction", "label": "Restore documented default"},
            ],
            "relations": [
                relation("r1", "MAY_INDICATE", "sym_unstable", "fm_parameter", "ev1", "Unstable temperature may indicate an invalid control parameter"),
                relation("r2", "RESOLVED_BY", "fm_parameter", "ca_restore", "ev2", "If the control parameter is invalid, restore the documented default"),
                relation("r3", "HAS_COMPONENT", "asset_thermal", "comp_controller", "ev3", "thermal system includes a controller module"),
            ],
            "expect": {"published_symptoms": 1, "published_actions": 1, "gaps": 0},
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=Path("ontology_schema.JSON"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    node_types, relation_contract = load_contract(args.schema)
    results = []
    for case in cases():
        result = project_case(
            case,
            node_types=node_types,
            relation_contract=relation_contract,
        )
        for metric, expected in case["expect"].items():
            actual = result["metrics"][metric]
            assert actual == expected, (
                f"{case['case_id']} expected {metric}={expected}, got {actual}"
            )
        assert result["metrics"]["canonical_isolated_nodes"] == 0
        assert result["metrics"]["published_actions_without_failure_mode"] == 0
        assert result["metrics"]["ungrounded_relations_published"] == 0
        results.append(result)

    payload = {
        "analysis_kind": "manual_agnostic_synthetic_publication_gate_spec",
        "ontology_source": str(args.schema),
        "ontology_node_types": sorted(node_types),
        "ontology_relation_contract": {
            name: {"domain": domain, "range": range_type}
            for name, (domain, range_type) in sorted(relation_contract.items())
        },
        "case_count": len(results),
        "all_assertions_passed": True,
        "cases": results,
    }
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
