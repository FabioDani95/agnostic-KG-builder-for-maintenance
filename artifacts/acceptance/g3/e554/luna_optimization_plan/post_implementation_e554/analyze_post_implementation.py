#!/usr/bin/env python3
"""Read-only measured comparison for the retained v5 run and v6 micro-test."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = Path(__file__).resolve().parents[6]


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _topology(nodes: list[dict[str, Any]], relations: list[dict[str, Any]]) -> dict[str, Any]:
    node_by_id = {item["node_id"]: item for item in nodes}
    incoming: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    outgoing: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    incident: set[str] = set()
    for relation in relations:
        outgoing[relation["relation_type"]][relation["from_id"]].add(relation["to_id"])
        incoming[relation["relation_type"]][relation["to_id"]].add(relation["from_id"])
        incident.update((relation["from_id"], relation["to_id"]))

    symptoms = {item["node_id"] for item in nodes if item["node_type"] == "Symptom"}
    failures = {item["node_id"] for item in nodes if item["node_type"] == "FailureMode"}
    actions = {item["node_id"] for item in nodes if item["node_type"] == "CorrectiveAction"}
    components = {item["node_id"] for item in nodes if item["node_type"] == "Component"}
    complete_symptoms = {
        symptom_id
        for symptom_id in symptoms
        if any(
            outgoing["RESOLVED_BY"].get(failure_id)
            for failure_id in outgoing["MAY_INDICATE"].get(symptom_id, set())
        )
    }
    return {
        "nodes": len(nodes),
        "nodes_by_type": dict(sorted(Counter(item["node_type"] for item in nodes).items())),
        "relations": len(relations),
        "relations_by_type": dict(sorted(Counter(item["relation_type"] for item in relations).items())),
        "isolated_nodes": len(set(node_by_id) - incident),
        "symptoms": len(symptoms),
        "symptoms_with_complete_path": len(complete_symptoms),
        "failure_modes": len(failures),
        "failure_modes_without_symptom": sum(
            not incoming["MAY_INDICATE"].get(item) for item in failures
        ),
        "failure_modes_without_action": sum(
            not outgoing["RESOLVED_BY"].get(item) for item in failures
        ),
        "failure_modes_without_component": sum(
            not outgoing["AFFECTS"].get(item) for item in failures
        ),
        "corrective_actions": len(actions),
        "corrective_actions_without_failure": sum(
            not incoming["RESOLVED_BY"].get(item) for item in actions
        ),
        "components": len(components),
        "diagnostically_involved_components": len({
            component_id
            for failure_id in failures
            for component_id in outgoing["AFFECTS"].get(failure_id, set())
        }),
    }


def _exact_acceptance(
    nodes: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline = _load(REPOSITORY_ROOT / "artifacts/acceptance/g3/e554/luna_validation/result.json")
    by_type_and_label = {
        (item["node_type"], _normalize(item.get("label", ""))): item["node_id"]
        for item in nodes
    }
    edges = {
        (item["relation_type"], item["from_id"], item["to_id"])
        for item in relations
    }
    matches = []
    for witness in baseline["gold_evaluation"]["matches"]:
        symptom_id = by_type_and_label.get(("Symptom", _normalize(witness["symptom"])), "")
        failure_id = by_type_and_label.get(("FailureMode", _normalize(witness["failure_mode"])), "")
        action_id = by_type_and_label.get(
            ("CorrectiveAction", _normalize(witness["corrective_action"])), ""
        )
        present = bool(
            symptom_id
            and failure_id
            and action_id
            and ("MAY_INDICATE", symptom_id, failure_id) in edges
            and ("RESOLVED_BY", failure_id, action_id) in edges
        )
        matches.append({"gold": witness["gold"], "present": present})

    forbidden = []
    for witness in baseline["gold_evaluation"]["forbidden_pairings"]:
        symptom_id = by_type_and_label.get(("Symptom", _normalize(witness["symptom"])), "")
        failure_id = by_type_and_label.get(("FailureMode", _normalize(witness["failure_mode"])), "")
        forbidden.append({
            **witness,
            "found": bool(
                symptom_id
                and failure_id
                and ("MAY_INDICATE", symptom_id, failure_id) in edges
            ),
        })
    return {
        "method": "exact normalized frozen witnesses; acceptance-only",
        "gold_chains_present": sum(item["present"] for item in matches),
        "gold_chains_total": len(matches),
        "matches": matches,
        "forbidden_pairings_found": sum(item["found"] for item in forbidden),
        "forbidden_pairings_total": len(forbidden),
        "forbidden_pairings": forbidden,
    }


def main() -> None:
    response = _load(ROOT / "generation_response.json")
    revision = next(item["subgraph"] for item in response["sources"] if item.get("subgraph"))
    state = _load(ROOT / "run_state.json")
    ledger = _load(ROOT / "real_api_ledger.json")
    micro = _load(ROOT / "v6_diagnostic_microbenchmark.json")
    micro_ledger = _load(ROOT / "microbenchmark_ledger.json")
    baseline = _load(REPOSITORY_ROOT / "artifacts/acceptance/g3/e554/luna_validation/result.json")

    projections = {}
    node_by_id = {item["node_id"]: item for item in revision["nodes"]}
    relation_by_id = {item["relation_id"]: item for item in revision["relations"]}
    for name, projection in revision["projections"].items():
        projection_nodes = [node_by_id[item] for item in projection["node_ids"] if item in node_by_id]
        projection_relations = [
            relation_by_id[item] for item in projection["relation_ids"] if item in relation_by_id
        ]
        projections[name] = _topology(projection_nodes, projection_relations)

    exact_duplicates = sum(
        count - 1
        for (_node_type, _label), count in Counter(
            (item["node_type"], _normalize(item.get("label", "")))
            for item in revision["nodes"]
        ).items()
        if count > 1
    )
    call_cost_sum = round(sum(float(item.get("estimated_cost_usd", 0) or 0) for item in ledger["calls"]), 6)
    full_metrics = revision["generation_metrics"]
    old_metrics = baseline["generation_metrics"]
    output = {
        "verdict": {
            "status": "no_go",
            "reason": (
                "Publication invariants, cost and grounding pass, but the retained full run lost all "
                "8 acceptance chains. The post-fix one-call micro-benchmark extracted the expected "
                "entities but emitted no causal relations after coercion, so v6 is not yet proven."
            ),
        },
        "measurement_status": {
            "v5_full_generation": "measured_real_persisted_revision",
            "v6_page_roles": "simulated_deterministically_on_same_persisted_scope_and_pdf_text",
            "v6_microbenchmark": "measured_real_single_call_not_a_full_generation",
        },
        "integrity": {
            "baseline_before": state["baseline_before"],
            "baseline_after": state["baseline_after"],
            "baseline_unchanged": state["baseline_unchanged"],
            "experimental_revision_id": revision["source_subgraph_revision_id"],
            "experimental_workspace_id": revision["workspace_id"],
            "experimental_status": revision["status"],
            "experimental_decision_id": revision.get("approval_decision_id"),
            "csv_processed": state["csv_processed"],
            "merge_started": state["merge_started"],
            "review_decision_taken": state["review_decision_taken"],
        },
        "v5_full_generation": {
            "pipeline_version": revision["pipeline_version"],
            "scope": revision["pdf_extraction_scope"],
            "projections": projections,
            "validation": revision["validation"],
            "publication_metrics": revision["publication_metrics"],
            "acceptance": _exact_acceptance(revision["nodes"], revision["relations"]),
            "exact_normalized_duplicates": exact_duplicates,
            "canonicalization": revision["canonicalization_report"],
            "knowledge_gaps_by_code": dict(sorted(Counter(
                item["code"] for item in revision["knowledge_gaps"]
            ).items())),
            "review_summary": revision["review_summary"],
            "generation_metrics": full_metrics,
            "preflight": full_metrics["stages"]["ontology"]["details"]["cost_preflight"],
            "baseline_delta": {
                "nodes": len(revision["nodes"]) - 399,
                "relations": len(revision["relations"]) - 369,
                "review_queue_items": len(revision["review_queue"]) - 250,
                "llm_calls": full_metrics["llm_calls"] - old_metrics["llm_calls"],
                "total_tokens": full_metrics["total_tokens"] - old_metrics["total_tokens"],
                "duration_seconds": round(full_metrics["duration_seconds"] - old_metrics["duration_seconds"], 3),
                "cost_usd": round(full_metrics["estimated_cost_usd"] - old_metrics["estimated_cost_usd"], 6),
                "gold_chains": -8,
            },
        },
        "v6_post_fix": {
            "offline_page_roles": {
                "diagnostic_pages": [37, 38, 39],
                "structural_pages_count": 27,
                "retrieval_pages_count": 54,
                "page_39_promoted_by_content_guard": True,
            },
            "microbenchmark": {
                key: micro[key]
                for key in (
                    "kind", "production_pipeline_version", "input_pages", "gold_used_in_prompt",
                    "status", "is_schema_compliant", "is_ready_for_human_review", "metrics",
                    "node_counts", "relation_counts", "relation_grounding", "acceptance",
                    "canonicalization", "schema_issues", "graph_issues",
                )
            },
            "interpretation": (
                "The role boundary fix recovers the correct diagnostic pages and the model extracted most, "
                "but not all, expected symptom/failure/action concepts; the generic relation contract/coercion "
                "still yielded only derived HAS_COMPONENT relations. This is a pipeline contract failure, "
                "not evidence that a stronger model is required."
            ),
        },
        "real_api_budget": {
            "authorized_usd": 0.5,
            "full_generation_cost_usd": full_metrics["estimated_cost_usd"],
            "microbenchmark_cost_usd": micro_ledger["actual_spend_usd"],
            "cumulative_spend_usd": ledger["actual_spend_usd"],
            "remaining_usd": ledger["remaining_budget_usd"],
            "calls": len(ledger["calls"]),
            "per_call_cost_sum_usd": call_cost_sum,
            "ledger_matches_call_sum": call_cost_sum == ledger["actual_spend_usd"],
            "full_generations_started": ledger["full_generations_started"],
            "full_generations_completed": ledger["full_generations_completed"],
            "microbenchmarks_completed": ledger["microbenchmarks_completed"],
        },
    }
    _write(ROOT / "post_implementation_analysis.json", output)


if __name__ == "__main__":
    main()
