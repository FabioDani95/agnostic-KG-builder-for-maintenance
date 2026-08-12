#!/usr/bin/env python3
"""Read-only acceptance analysis of the autonomous E-554 v7 revision."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "v7_real_run"
RESPONSE_PATH = RUN_ROOT / "generation_response.json"
LEDGER_PATH = RUN_ROOT / "real_api_ledger.json"
STATE_PATH = RUN_ROOT / "run_state.json"
GOLD_PATH = ROOT.parents[1] / "gold.json"
OUTPUT_PATH = RUN_ROOT / "acceptance_analysis.json"


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(value: str) -> set[str]:
    return {token for token in _normalize(value).split() if len(token) > 1}


def _similarity(expected: str, actual: str) -> float:
    expected_tokens = _tokens(expected)
    actual_tokens = _tokens(actual)
    if not expected_tokens or not actual_tokens:
        return 0.0
    overlap = expected_tokens & actual_tokens
    containment = len(overlap) / len(expected_tokens)
    jaccard = len(overlap) / len(expected_tokens | actual_tokens)
    phrase = float(_normalize(expected) in _normalize(actual) or _normalize(actual) in _normalize(expected))
    return round(max(containment * 0.8 + jaccard * 0.2, phrase), 6)


def _components(node_ids: set[str], relations: list[dict[str, Any]]) -> list[list[str]]:
    adjacent: dict[str, set[str]] = defaultdict(set)
    for relation in relations:
        left, right = relation["from_id"], relation["to_id"]
        if left in node_ids and right in node_ids:
            adjacent[left].add(right)
            adjacent[right].add(left)
    remaining = set(node_ids)
    groups: list[list[str]] = []
    while remaining:
        root = min(remaining)
        queue = deque([root])
        group: set[str] = set()
        while queue:
            current = queue.popleft()
            if current in group:
                continue
            group.add(current)
            queue.extend(adjacent[current] - group)
        remaining -= group
        groups.append(sorted(group))
    return sorted(groups, key=lambda group: (-len(group), group))


def main() -> None:
    response = json.loads(RESPONSE_PATH.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    revision = next(item["subgraph"] for item in response["sources"] if item.get("subgraph"))
    nodes = revision["nodes"]
    relations = revision["relations"]
    evidence = {item["evidence_id"]: item for item in revision["evidence"]}
    node_by_id = {node["node_id"]: node for node in nodes}
    incident = {
        endpoint
        for relation in relations
        for endpoint in (relation["from_id"], relation["to_id"])
    }
    outgoing: dict[tuple[str, str], list[str]] = defaultdict(list)
    for relation in relations:
        outgoing[(relation["relation_type"], relation["from_id"])].append(
            relation["to_id"]
        )

    published_paths: list[dict[str, Any]] = []
    for indicator in nodes:
        if indicator["node_type"] not in {"Symptom", "ErrorCode"}:
            continue
        relation_type = "MAY_INDICATE" if indicator["node_type"] == "Symptom" else "INDICATES"
        for failure_id in outgoing[(relation_type, indicator["node_id"])]:
            for action_id in outgoing[("RESOLVED_BY", failure_id)]:
                published_paths.append(
                    {
                        "indicator": indicator["label"],
                        "indicator_id": indicator["node_id"],
                        "failure": node_by_id[failure_id]["label"],
                        "failure_id": failure_id,
                        "action": node_by_id[action_id]["label"],
                        "action_id": action_id,
                    }
                )

    witnesses: list[dict[str, Any]] = []
    for index, expected in enumerate(gold["minimum_expected_manual_chains"], start=1):
        candidates = []
        for path in published_paths:
            scores = {
                "symptom": _similarity(expected["symptom"], path["indicator"]),
                "failure_mode": _similarity(expected["failure_mode"], path["failure"]),
                "corrective_action": _similarity(expected["corrective_action"], path["action"]),
            }
            candidates.append((min(scores.values()), sum(scores.values()), scores, path))
        best = max(candidates, default=(0.0, 0.0, {}, {}), key=lambda item: (item[0], item[1]))
        present = bool(best[0] >= 0.55)
        witnesses.append(
            {
                "gold_chain": index,
                "expected": expected,
                "present": present,
                "best_min_field_score": best[0],
                "field_scores": best[2],
                "matched_path": best[3],
            }
        )

    forbidden: list[dict[str, Any]] = []
    for expected in gold["forbidden_cross_pairings"]:
        matches = [
            path
            for path in published_paths
            if _similarity(expected["symptom"], path["indicator"]) >= 0.55
            and _similarity(expected["failure_mode"], path["failure"]) >= 0.55
        ]
        forbidden.append({**expected, "found": bool(matches), "matches": matches})

    exact_edge_refs = 0
    total_edge_refs = 0
    unresolved_edge_refs: list[dict[str, str]] = []
    for relation in relations:
        for ref in relation.get("evidence_refs") or []:
            total_edge_refs += 1
            anchor = ref.get("source_anchor") or ref.get("evidence_id")
            unit = evidence.get(str(anchor))
            canonical = ((unit or {}).get("locator") or {}).get("canonical_text") or (
                (unit or {}).get("locator") or {}
            ).get("quote", "")
            quote = str(ref.get("quote") or "")
            if unit and _normalize(quote) and _normalize(quote) in _normalize(canonical):
                exact_edge_refs += 1
            else:
                unresolved_edge_refs.append(
                    {"relation_id": relation["relation_id"], "anchor": str(anchor), "quote": quote}
                )

    node_ids = set(node_by_id)
    component_groups = _components(node_ids, relations)
    diagnostic_ids = {
        node["node_id"]
        for node in nodes
        if node["node_type"] in {"Symptom", "ErrorCode", "FailureMode", "CorrectiveAction"}
    }
    diagnostic_groups = _components(diagnostic_ids, relations)
    calls = ledger["calls"]
    gold_present = sum(item["present"] for item in witnesses)
    forbidden_found = sum(item["found"] for item in forbidden)
    validation_passed = bool(revision["validation"].get("passed"))
    grounding_exact = exact_edge_refs == total_edge_refs
    topology_clean = not (node_ids - incident) and bool(published_paths)
    acceptance_passed = (
        gold_present == len(witnesses)
        and forbidden_found == 0
        and validation_passed
        and grounding_exact
        and topology_clean
    )
    if acceptance_passed:
        verdict_reason = (
            "All frozen E-554 chains are represented without forbidden cross-pairings; "
            "the graph passes schema, topology and exact evidence-grounding checks."
        )
    else:
        verdict_reason = (
            f"Frozen E-554 coverage is {gold_present}/{len(witnesses)} with "
            f"{forbidden_found}/{len(forbidden)} forbidden cross-pairings; "
            "schema/topology/grounding results are reported independently below."
        )
    result = {
        "verdict": {
            "status": "go" if acceptance_passed else "no_go",
            "reason": verdict_reason,
        },
        "integrity": {
            "workspace_id": state["workspace_id"],
            "source_id": state["source_id"],
            "revision_id": state["revision_id"],
            "revision_status": state["revision_status"],
            "approval_decision_taken": state["approval_decision_taken"],
            "merge_started": state["merge_started"],
            "csv_processed": state["csv_processed"],
            "manual_sha256": state["manual_sha256"],
            "pipeline_version": revision["pipeline_version"],
        },
        "budget": {
            "authorized_ceiling_usd": ledger["authorized_ceiling_usd"],
            "prior_attempt_reserved_usd": ledger["prior_attempt_reserved_usd"],
            "run_hard_ceiling_usd": ledger["run_hard_ceiling_usd"],
            "cumulative_maximum_usd": ledger["cumulative_maximum_usd"],
            "run_measured_cost_usd": ledger["actual_spend_usd"],
            "run_preflight_ceiling_usd": ledger["preflight"].get("conservative_max_cost_usd"),
            "call_count": ledger["call_count"],
            "models": dict(sorted(Counter(call["model"] for call in calls).items())),
            "terra_escalations": sum(call.get("call_role") == "escalation" for call in calls),
        },
        "scope": revision["pdf_extraction_scope"],
        "graph": {
            "nodes": len(nodes),
            "nodes_by_type": dict(sorted(Counter(node["node_type"] for node in nodes).items())),
            "relations": len(relations),
            "relations_by_type": dict(
                sorted(Counter(relation["relation_type"] for relation in relations).items())
            ),
            "isolated_nodes": len(node_ids - incident),
            "weakly_connected_components": len(component_groups),
            "weak_component_sizes": [len(group) for group in component_groups],
            "diagnostic_weakly_connected_components": len(diagnostic_groups),
            "diagnostic_weak_component_sizes": [len(group) for group in diagnostic_groups],
            "published_complete_paths": len(published_paths),
            "published_paths": published_paths,
        },
        "validation": revision["validation"],
        "publication_metrics": revision["publication_metrics"],
        "acceptance": {
            "method": "post-run fuzzy witness matching; gold was never available to production",
            "minimum_field_score": 0.55,
            "gold_chains_present": gold_present,
            "gold_chains_total": len(witnesses),
            "witnesses": witnesses,
            "forbidden_pairings_found": forbidden_found,
            "forbidden_pairings_total": len(forbidden),
            "forbidden": forbidden,
        },
        "grounding_audit": {
            "relation_evidence_refs_exact": exact_edge_refs,
            "relation_evidence_refs_total": total_edge_refs,
            "unresolved": unresolved_edge_refs,
        },
        "review": {
            "approval_eligible": revision["approval_eligible"],
            "review_summary": revision["review_summary"],
            "blocking_gaps": [
                gap for gap in revision["knowledge_gaps"] if gap.get("blocking")
            ],
        },
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "verdict": result["verdict"],
        "budget": result["budget"],
        "graph": {key: value for key, value in result["graph"].items() if key != "published_paths"},
        "validation": result["validation"],
        "acceptance": {
            key: value for key, value in result["acceptance"].items() if key not in {"witnesses", "forbidden"}
        },
        "grounding_audit": result["grounding_audit"],
        "review_summary": result["review"]["review_summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
