#!/usr/bin/env python3
"""Run the one authorized post-fix diagnostic micro-benchmark."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.adapters.pdf import evidence_units_to_legacy_pages  # noqa: E402
from backend.services.llm_gateway import llm_mode  # noqa: E402
from backend.services.ontology_canonicalization_service import (  # noqa: E402
    canonicalize_ontology_instance,
)
from backend.services.ontology_pipeline import build_initial_ontology  # noqa: E402
from backend.services.pdf_service import format_text_with_pages  # noqa: E402
from backend.storage.repositories.evidence import EvidenceRepository  # noqa: E402
from backend.storage.repositories.workspaces import WorkspaceRepository  # noqa: E402

ROOT = Path(__file__).resolve().parent
MICRO_LEDGER_PATH = ROOT / "microbenchmark_ledger.json"
ACTIVITY_LEDGER_PATH = ROOT / "real_api_ledger.json"
RESULT_PATH = ROOT / "v6_diagnostic_microbenchmark.json"
WORKSPACE_ID = "ws_PFJFoXKzA2TjEW4pUS8Yqg"
SOURCE_ID = "src_SZQuae1zPnJcWZbJpblu4w"
PAGES = {37, 38, 39}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _similarity(left: str, right: str) -> float:
    left_norm = _normalize(left)
    right_norm = _normalize(right)
    if not left_norm or not right_norm:
        return 0.0
    left_tokens = set(left_norm.split())
    right_tokens = set(right_norm.split())
    containment = len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))
    sequence = SequenceMatcher(None, left_norm, right_norm).ratio()
    return round(0.7 * containment + 0.3 * sequence, 4)


def _id(item: dict[str, Any], node_type: str) -> str:
    field = {
        "Symptom": "symptom_id",
        "FailureMode": "failure_mode_id",
        "CorrectiveAction": "action_id",
    }[node_type]
    return str(item.get(field, "") or "")


def _acceptance(ontology_payload: dict[str, Any]) -> dict[str, Any]:
    gold = json.loads((REPOSITORY_ROOT / "artifacts/acceptance/g3/e554/gold.json").read_text())
    baseline = json.loads(
        (REPOSITORY_ROOT / "artifacts/acceptance/g3/e554/luna_validation/result.json").read_text()
    )
    nodes = ontology_payload.get("nodes") or {}
    labels = {
        node_type: {
            _id(item, node_type): str(item.get("name", "") or "")
            for item in nodes.get(node_type, [])
            if isinstance(item, dict)
        }
        for node_type in ("Symptom", "FailureMode", "CorrectiveAction")
    }
    relations = ontology_payload.get("relations") or []
    symptom_failure = {
        (item["from_id"], item["to_id"])
        for item in relations
        if item.get("name") == "MAY_INDICATE"
    }
    failure_action = {
        (item["from_id"], item["to_id"])
        for item in relations
        if item.get("name") == "RESOLVED_BY"
    }
    paths = [
        (symptom_id, failure_id, action_id)
        for symptom_id, failure_id in sorted(symptom_failure)
        for source_failure_id, action_id in sorted(failure_action)
        if failure_id == source_failure_id
    ]

    expected = baseline["gold_evaluation"]["matches"]
    matches = []
    for witness in expected:
        scored = []
        for symptom_id, failure_id, action_id in paths:
            scores = {
                "symptom": _similarity(witness["symptom"], labels["Symptom"].get(symptom_id, "")),
                "failure_mode": _similarity(
                    witness["failure_mode"], labels["FailureMode"].get(failure_id, "")
                ),
                "corrective_action": _similarity(
                    witness["corrective_action"], labels["CorrectiveAction"].get(action_id, "")
                ),
            }
            scored.append((sum(scores.values()) / 3, min(scores.values()), scores, (symptom_id, failure_id, action_id)))
        best = max(scored, default=(0.0, 0.0, {}, ("", "", "")))
        average, minimum, scores, path = best
        matches.append({
            "gold": witness["gold"],
            "present": minimum >= 0.55 and average >= 0.65,
            "average_similarity": round(average, 4),
            "minimum_similarity": round(minimum, 4),
            "field_similarity": scores,
            "actual": {
                "symptom": labels["Symptom"].get(path[0], ""),
                "failure_mode": labels["FailureMode"].get(path[1], ""),
                "corrective_action": labels["CorrectiveAction"].get(path[2], ""),
            },
        })

    forbidden_results = []
    for forbidden in gold["forbidden_cross_pairings"]:
        found = False
        actual = None
        for symptom_id, failure_id in symptom_failure:
            symptom_label = labels["Symptom"].get(symptom_id, "")
            failure_label = labels["FailureMode"].get(failure_id, "")
            if (
                _similarity(forbidden["symptom"], symptom_label) >= 0.60
                and _similarity(forbidden["failure_mode"], failure_label) >= 0.60
            ):
                found = True
                actual = {"symptom": symptom_label, "failure_mode": failure_label}
                break
        forbidden_results.append({**forbidden, "found": found, "actual": actual})

    return {
        "method": (
            "acceptance-only semantic witness over explicit MAY_INDICATE/RESOLVED_BY paths; "
            "thresholds fixed before inspecting output: each field >=0.55 and mean >=0.65"
        ),
        "gold_chains_present": sum(item["present"] for item in matches),
        "gold_chains_total": len(matches),
        "matches": matches,
        "forbidden_pairings_found": sum(item["found"] for item in forbidden_results),
        "forbidden_pairings_total": len(forbidden_results),
        "forbidden_pairings": forbidden_results,
    }


def main() -> int:
    micro_ledger = json.loads(MICRO_LEDGER_PATH.read_text(encoding="utf-8"))
    activity_ledger = json.loads(ACTIVITY_LEDGER_PATH.read_text(encoding="utf-8"))
    if int(micro_ledger.get("calls_started", 0) or 0) != 0:
        raise RuntimeError("The one-shot micro-benchmark call has already been started")
    if llm_mode() != "real":
        raise RuntimeError("The micro-benchmark requires real mode")
    if float(activity_ledger.get("actual_spend_usd", 0) or 0) >= 0.47:
        raise RuntimeError("Insufficient activity budget for the conservative $0.03 envelope")

    workspace = WorkspaceRepository().get_by_id(WORKSPACE_ID)
    if workspace is None:
        raise RuntimeError("Experimental workspace not found")
    evidence = EvidenceRepository().list_evidence(workspace_id=WORKSPACE_ID, source_id=SOURCE_ID)
    selected_pages = [
        page for page in evidence_units_to_legacy_pages(evidence)
        if int(page["page_number"]) in PAGES
    ]
    if {int(page["page_number"]) for page in selected_pages} != PAGES:
        raise RuntimeError("The three diagnostic pages are not available in canonical evidence")

    micro_ledger["calls_started"] = 1
    micro_ledger["status"] = "call_started"
    _write_json(MICRO_LEDGER_PATH, micro_ledger)

    result, metrics = build_initial_ontology(
        text_with_pages=format_text_with_pages(selected_pages),
        source_type="technical PDF",
        source_title="E-554.pdf",
        target_language="en",
        model_name="gpt-5.6-luna",
        reasoning_effort="medium",
        asset_identity=workspace.asset.model_dump(mode="json"),
        extraction_role="diagnostic",
        relation_first=True,
    )
    if int(metrics.get("llm_calls", 0) or 0) != 1:
        raise RuntimeError("Micro-benchmark violated its one-call envelope")

    canonical, canonicalization = canonicalize_ontology_instance(result.ontology)
    ontology_payload = canonical.model_dump(mode="json")
    evidence_by_id = {item.evidence_id: item for item in evidence}
    grounding = []
    for relation in ontology_payload.get("relations") or []:
        if relation.get("name") in {"HAS_COMPONENT", "GENERATES_ERROR"} and not relation.get("evidence"):
            continue
        resolved = []
        for ref in relation.get("evidence") or []:
            item = evidence_by_id.get(str(ref.get("source_anchor") or ""))
            quote = _normalize(str(ref.get("quote") or ""))
            excerpt = _normalize(str(getattr(getattr(item, "locator", None), "quote", "") or ""))
            resolved.append(bool(item and quote and (quote in excerpt or excerpt in quote)))
        grounding.append(all(resolved) and bool(resolved))

    analysis = {
        "kind": "measured_real_single_call_post_fix_microbenchmark",
        "production_pipeline_version": "pdf-g3-relation-first-publication-v6",
        "input_pages": sorted(PAGES),
        "gold_used_in_prompt": False,
        "status": result.status,
        "is_schema_compliant": result.is_schema_compliant,
        "is_ready_for_human_review": result.is_ready_for_human_review,
        "metrics": metrics,
        "node_counts": {
            node_type: len(items)
            for node_type, items in ontology_payload.get("nodes", {}).items()
        },
        "relation_counts": {
            relation_type: sum(
                item.get("name") == relation_type
                for item in ontology_payload.get("relations") or []
            )
            for relation_type in sorted({
                item.get("name") for item in ontology_payload.get("relations") or []
            })
        },
        "relation_grounding": {
            "total": len(grounding),
            "resolved": sum(grounding),
            "ratio": round(sum(grounding) / len(grounding), 4) if grounding else None,
            "status": "measured" if grounding else "not_available_no_direct_relations",
        },
        "canonicalization": canonicalization,
        "acceptance": _acceptance(ontology_payload),
        "ontology": ontology_payload,
        "schema_issues": [item.model_dump(mode="json") for item in result.schema_issues],
        "semantic_issues": [item.model_dump(mode="json") for item in result.semantic_issues],
        "graph_issues": [item.model_dump(mode="json") for item in result.graph_issues],
    }
    _write_json(RESULT_PATH, analysis)

    call_cost = float(metrics.get("estimated_cost_usd", 0) or 0)
    call = {
        "stage": "post_fix_v6_microbenchmark",
        "global_call_index": len(activity_ledger.get("calls") or []) + 1,
        "operation": "ontology_draft",
        "model": "gpt-5.6-luna",
        "reasoning_effort": "medium",
        "input_pages": sorted(PAGES),
        "prompt": int(metrics.get("prompt_tokens", 0) or 0),
        "cached_prompt": int(metrics.get("cached_prompt_tokens", 0) or 0),
        "non_cached_prompt": int(metrics.get("non_cached_prompt_tokens", 0) or 0),
        "completion": int(metrics.get("completion_tokens", 0) or 0),
        "total": int(metrics.get("total_tokens", 0) or 0),
        "estimated_cost_usd": round(call_cost, 6),
    }
    micro_ledger.update({
        "status": "completed",
        "calls_completed": 1,
        "call": call,
        "actual_spend_usd": round(call_cost, 6),
        "activity_spend_after_usd": round(
            float(activity_ledger.get("actual_spend_usd", 0) or 0) + call_cost, 6
        ),
    })
    _write_json(MICRO_LEDGER_PATH, micro_ledger)

    activity_ledger.setdefault("calls", []).append(call)
    activity_ledger["actual_spend_usd"] = micro_ledger["activity_spend_after_usd"]
    activity_ledger["remaining_budget_usd"] = round(
        0.5 - activity_ledger["actual_spend_usd"], 6
    )
    activity_ledger["microbenchmarks_completed"] = 1
    _write_json(ACTIVITY_LEDGER_PATH, activity_ledger)

    print(json.dumps({
        "status": "completed",
        "cost_usd": round(call_cost, 6),
        "activity_spend_usd": activity_ledger["actual_spend_usd"],
        "nodes": sum(analysis["node_counts"].values()),
        "relations": sum(analysis["relation_counts"].values()),
        "grounding": analysis["relation_grounding"],
        "acceptance": analysis["acceptance"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
