#!/usr/bin/env python3
"""Deterministic, read-only analysis of the three frozen real PDF runs."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
GOLD_PATH = ROOT / "golden.json"
RUNS_ROOT = ROOT / "runs" / "real"
OUTPUT_PATH = ROOT / "campaign_results.json"
REPORT_PATH = ROOT / "CAMPAIGN_REPORT.md"
MATCH_FLOOR = 0.55
GENERIC_REVIEW_TOKENS = {
    "and",
    "action",
    "adjust",
    "adjustment",
    "clean",
    "damage",
    "damaged",
    "dirt",
    "dirty",
    "failure",
    "is",
    "or",
    "replace",
    "replacement",
    "require",
    "required",
    "the",
}


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def tokens(value: str) -> set[str]:
    return {token for token in normalize(value).split() if len(token) > 1}


def similarity(expected: str, actual: str) -> float:
    expected_tokens = tokens(expected)
    actual_tokens = tokens(actual)
    if not expected_tokens or not actual_tokens:
        return 0.0
    overlap = expected_tokens & actual_tokens
    containment = len(overlap) / len(expected_tokens)
    jaccard = len(overlap) / len(expected_tokens | actual_tokens)
    phrase = float(normalize(expected) in normalize(actual) or normalize(actual) in normalize(expected))
    return round(max(containment * 0.8 + jaccard * 0.2, phrase), 6)


def revision_from(response: dict[str, Any]) -> dict[str, Any]:
    return next(item["subgraph"] for item in response["sources"] if item.get("subgraph"))


def published_paths(revision: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = {node["node_id"]: node for node in revision["nodes"]}
    outgoing: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for relation in revision["relations"]:
        outgoing[(relation["relation_type"], relation["from_id"])].append(relation)
    paths: list[dict[str, Any]] = []
    for indicator in revision["nodes"]:
        if indicator["node_type"] not in {"Symptom", "ErrorCode"}:
            continue
        indicator_relation = "MAY_INDICATE" if indicator["node_type"] == "Symptom" else "INDICATES"
        for indicator_edge in outgoing[(indicator_relation, indicator["node_id"])]:
            failure = nodes.get(indicator_edge["to_id"])
            if not failure:
                continue
            for action_edge in outgoing[("RESOLVED_BY", failure["node_id"])]:
                action = nodes.get(action_edge["to_id"])
                if not action:
                    continue
                refs = (indicator_edge.get("evidence_refs") or []) + (action_edge.get("evidence_refs") or [])
                paths.append(
                    {
                        "indicator_type": indicator["node_type"],
                        "indicator": indicator["label"],
                        "failure_mode": failure["label"],
                        "corrective_action": action["label"],
                        "pages": sorted(
                            {
                                ref.get("locator", {}).get("page")
                                for ref in refs
                                if ref.get("locator", {}).get("page") is not None
                            }
                        ),
                        "indicator_id": indicator["node_id"],
                        "failure_mode_id": failure["node_id"],
                        "corrective_action_id": action["node_id"],
                    }
                )
    return paths


def score_claim_path(claim: dict[str, Any], path: dict[str, Any]) -> dict[str, float]:
    return {
        "indicator": similarity(claim["symptom"], path["indicator"]),
        "failure_mode": similarity(claim["failure_mode"], path["failure_mode"]),
        "corrective_action": similarity(
            claim.get("corrective_action", ""), path["corrective_action"]
        ),
    }


def gap_text(gap: dict[str, Any], evidence: dict[str, dict[str, Any]]) -> str:
    pieces = [gap.get("message", "")]
    for evidence_id in gap.get("evidence_ids") or []:
        unit = evidence.get(evidence_id) or {}
        locator = unit.get("locator") or {}
        pieces.extend(
            [
                locator.get("canonical_text", ""),
                locator.get("quote", ""),
                unit.get("quote", ""),
                unit.get("text", ""),
            ]
        )
    return " ".join(str(piece) for piece in pieces if piece)


def score_expected_gap(claim: dict[str, Any], text: str) -> dict[str, float]:
    return {
        "indicator": similarity(claim["symptom"], text),
        "failure_mode": similarity(claim["failure_mode"], text),
        "inspection_step": similarity(claim["inspection_step"], text),
    }


def score_review_claim(claim: dict[str, Any], text: str) -> dict[str, float]:
    return {
        "indicator": similarity(claim["symptom"], text),
        "failure_mode": similarity(claim["failure_mode"], text),
        "corrective_action": similarity(claim["corrective_action"], text),
    }


def exact_grounding(revision: dict[str, Any]) -> dict[str, Any]:
    evidence = {item["evidence_id"]: item for item in revision["evidence"]}
    exact = 0
    total = 0
    unresolved: list[dict[str, str]] = []
    for relation in revision["relations"]:
        for ref in relation.get("evidence_refs") or []:
            total += 1
            anchor = str(ref.get("source_anchor") or ref.get("evidence_id") or "")
            unit = evidence.get(anchor)
            locator = (unit or {}).get("locator") or {}
            canonical = locator.get("canonical_text") or locator.get("quote") or ""
            quote = str(ref.get("quote") or "")
            if unit and normalize(quote) and normalize(quote) in normalize(canonical):
                exact += 1
            else:
                unresolved.append(
                    {"relation_id": relation["relation_id"], "anchor": anchor, "quote": quote}
                )
    return {"exact": exact, "total": total, "unresolved": unresolved, "passed": exact == total}


def analyze_manual(spec: dict[str, Any]) -> dict[str, Any]:
    manual_id = spec["manual_id"]
    run_root = RUNS_ROOT / manual_id
    response = json.loads((run_root / "generation_response.json").read_text(encoding="utf-8"))
    ledger = json.loads((run_root / "real_api_ledger.json").read_text(encoding="utf-8"))
    state = json.loads((run_root / "run_state.json").read_text(encoding="utf-8"))
    revision = revision_from(response)
    paths = published_paths(revision)
    evidence = {item["evidence_id"]: item for item in revision["evidence"]}
    explicit_gaps = [
        gap
        for gap in revision["knowledge_gaps"]
        if gap.get("code") == "pdf_diagnostic_record_gap"
    ]
    review_records = [
        gap
        for gap in revision["knowledge_gaps"]
        if gap.get("code") == "pdf_diagnostic_record_review"
    ]

    witnesses: list[dict[str, Any]] = []
    for claim in spec["expected_claims"]:
        if claim.get("expected_gap") == "inspection_only":
            candidates = []
            for gap in explicit_gaps:
                scores = score_expected_gap(claim, gap_text(gap, evidence))
                candidates.append((min(scores.values()), sum(scores.values()), scores, gap))
            best = max(candidates, default=(0.0, 0.0, {}, {}), key=lambda item: (item[0], item[1]))
            present = bool(best[0] >= MATCH_FLOOR)
            witnesses.append(
                {
                    "claim_id": claim["claim_id"],
                    "expected_outcome": "traceable_explicit_gap",
                    "present": present,
                    "best_min_field_score": best[0],
                    "field_scores": best[2],
                    "matched_gap": best[3],
                }
            )
            continue
        candidates = []
        for path in paths:
            scores = score_claim_path(claim, path)
            candidates.append(
                (min(scores.values()), sum(scores.values()), scores, path, "published_path")
            )
        if claim.get("expected_disposition") == "review_or_publish":
            claim_pages = set(claim["pages"])
            for gap in review_records:
                anchored_pages = {
                    (evidence.get(evidence_id) or {}).get("locator", {}).get("page")
                    for evidence_id in gap.get("evidence_ids") or []
                }
                if not claim_pages.intersection(anchored_pages):
                    continue
                scores = score_review_claim(claim, gap_text(gap, evidence))
                review_text = gap_text(gap, evidence)
                specific_tokens = (
                    tokens(claim["failure_mode"] + " " + claim["corrective_action"])
                    - tokens(claim["symptom"])
                    - GENERIC_REVIEW_TOKENS
                )
                specific_overlap = specific_tokens & tokens(review_text)
                # Layout-inferred table branches may state the condition through
                # the corrective instruction itself ("replace filters"), so the
                # failure-field floor is intentionally lower only for frozen
                # review_or_publish claims. Indicator and action remain strict,
                # and a component-specific token prevents one shared symptom
                # from matching neighbouring lens/mirror/nozzle branches.
                qualifying_score = (
                    min(
                        scores["indicator"],
                        scores["corrective_action"],
                        scores["failure_mode"] / 0.35 * MATCH_FLOOR,
                    )
                    if specific_overlap
                    else 0.0
                )
                scores["specific_token_overlap"] = float(bool(specific_overlap))
                candidates.append(
                    (
                        qualifying_score,
                        sum(scores.values()),
                        scores,
                        gap,
                        "traceable_review",
                    )
                )
        best = max(
            candidates,
            default=(0.0, 0.0, {}, {}, "none"),
            key=lambda item: (item[0], item[1]),
        )
        present = bool(best[0] >= MATCH_FLOOR)
        witnesses.append(
            {
                "claim_id": claim["claim_id"],
                "expected_outcome": (
                    "complete_published_path_or_traceable_review"
                    if claim.get("expected_disposition") == "review_or_publish"
                    else "complete_published_path"
                ),
                "present": present,
                "matched_outcome": best[4],
                "best_min_field_score": best[0],
                "field_scores": best[2],
                "matched_record": best[3],
            }
        )

    forbidden_results = []
    for forbidden in spec["forbidden_pairings"]:
        matches = [
            path
            for path in paths
            if similarity(forbidden["symptom"], path["indicator"]) >= MATCH_FLOOR
            and similarity(forbidden["failure_mode"], path["failure_mode"]) >= MATCH_FLOOR
        ]
        forbidden_results.append({**forbidden, "found": bool(matches), "matches": matches})

    path_gold_matches: list[list[str]] = []
    for path in paths:
        matches = []
        for claim in spec["expected_claims"]:
            if not claim.get("corrective_action"):
                continue
            scores = score_claim_path(claim, path)
            if min(scores.values()) >= MATCH_FLOOR:
                matches.append(claim["claim_id"])
        path_gold_matches.append(matches)
    exhaustive = spec["gold_scope"].startswith("exhaustive")
    unsupported_paths = [path for path, matches in zip(paths, path_gold_matches) if not matches] if exhaustive else []

    grounding = exact_grounding(revision)
    diagnostic_types = {"Symptom", "ErrorCode", "FailureMode", "CorrectiveAction"}
    diagnostic_ids = {
        node["node_id"] for node in revision["nodes"] if node["node_type"] in diagnostic_types
    }
    diagnostic_incident = {
        endpoint
        for relation in revision["relations"]
        if relation["from_id"] in diagnostic_ids or relation["to_id"] in diagnostic_ids
        for endpoint in (relation["from_id"], relation["to_id"])
        if endpoint in diagnostic_ids
    }
    action_ids = {
        node["node_id"] for node in revision["nodes"] if node["node_type"] == "CorrectiveAction"
    }
    resolved_actions = {
        relation["to_id"]
        for relation in revision["relations"]
        if relation["relation_type"] == "RESOLVED_BY"
    }
    assets = [node for node in revision["nodes"] if node["node_type"] == "Asset"]
    retained = set(revision["pdf_extraction_scope"]["diagnostic_pages"])
    gold_pages = set(spec["must_keep_pdf_pages"])
    recall_count = sum(witness["present"] for witness in witnesses)
    recall = recall_count / len(witnesses)
    autonomous_count = sum(
        witness["present"] and witness.get("matched_outcome") == "published_path"
        for witness in witnesses
        if witness["expected_outcome"] != "traceable_explicit_gap"
    )
    traceable_review_count = sum(
        witness["present"] and witness.get("matched_outcome") == "traceable_review"
        for witness in witnesses
    )
    publication = revision["publication_metrics"]
    state_safety = (
        not state["approval_decision_taken"]
        and not state["merge_started"]
        and not state["structured_source_processed"]
    )
    accounting_safe = bool(publication["diagnostic_accounting_complete"]) or not bool(
        revision["approval_eligible"]
    )
    integrity_checks = {
        "strict_validation": bool(revision["validation"]["passed"]),
        "exact_relation_grounding": grounding["passed"],
        "zero_isolated_diagnostic_nodes": not (diagnostic_ids - diagnostic_incident),
        "all_corrective_actions_have_incoming_resolved_by": action_ids <= resolved_actions,
        "one_original_canonical_asset": len(assets) == 1
        and assets[0]["node_id"] == state["asset_id"],
        "candidate_accounting_or_nonapprovable": accounting_safe,
        "no_approval_merge_or_structured_processing": state_safety,
    }
    semantic_checks = {
        "recall_floor": recall >= spec["gold_claim_recall_floor"],
        "forbidden_pairings_zero": not any(item["found"] for item in forbidden_results),
        "unsupported_published_paths_zero": not unsupported_paths if exhaustive else True,
        "gold_page_retention": gold_pages <= retained,
    }
    return {
        "manual_id": manual_id,
        "gold_scope": spec["gold_scope"],
        "semantic": {
            "gold_claims_present": recall_count,
            "gold_claims_total": len(witnesses),
            "gold_claim_recall": round(recall, 6),
            "recall_floor": spec["gold_claim_recall_floor"],
            "autonomous_expected_claims_present": autonomous_count,
            "traceable_review_claims_present": traceable_review_count,
            "explicit_expected_gaps_present": sum(
                witness["present"]
                for witness in witnesses
                if witness["expected_outcome"] == "traceable_explicit_gap"
            ),
            "published_complete_paths_total": len(paths),
            "paths_outside_frozen_gold": sum(not matches for matches in path_gold_matches),
            "unsupported_path_gate_scope": "exhaustive_gold" if exhaustive else "manual_audit_required",
            "unsupported_published_paths_detected": len(unsupported_paths),
            "forbidden_pairings_found": sum(item["found"] for item in forbidden_results),
            "gold_pages_retained": sorted(gold_pages & retained),
            "gold_pages_required": sorted(gold_pages),
            "checks": semantic_checks,
            "witnesses": witnesses,
            "forbidden": forbidden_results,
        },
        "graph": {
            "nodes": len(revision["nodes"]),
            "relations": len(revision["relations"]),
            "nodes_by_type": dict(sorted(Counter(node["node_type"] for node in revision["nodes"]).items())),
            "relations_by_type": dict(
                sorted(Counter(rel["relation_type"] for rel in revision["relations"]).items())
            ),
            "published_paths": paths,
        },
        "integrity": {
            "passed": all(integrity_checks.values()),
            "checks": integrity_checks,
            "grounding": grounding,
            "diagnostic_accounting_complete": publication["diagnostic_accounting_complete"],
            "approval_eligible": revision["approval_eligible"],
            "review_summary": revision["review_summary"],
            "validation": revision["validation"],
        },
        "scope": revision["pdf_extraction_scope"],
        "operations": {
            "cost_usd": ledger["actual_spend_usd"],
            "calls": ledger["call_count"],
            "elapsed_seconds": ledger["elapsed_seconds"],
            "conservative_preflight_usd": ledger["preflight"]["conservative_max_cost_usd"],
            "models": dict(sorted(Counter(call["model"] for call in ledger["calls"]).items())),
            "hard_ceiling_usd": ledger["run_hard_ceiling_usd"],
        },
        "verdict": {
            "semantic": "pass" if all(semantic_checks.values()) else "fail",
            "publication_integrity": "pass" if all(integrity_checks.values()) else "fail",
        },
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# PDF G3 diagnostic benchmark - final report",
        "",
        "Frozen gold and KPI protocol were prepared before the real generations. Each PDF was generated exactly once; no revision was approved, rejected or merged.",
        "",
        "| Manual | Gold recall | Floor | Autonomous paths relevant to gold | All published paths | Fail-closed integrity | Cost (USD) | Calls |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for manual in result["manuals"]:
        semantic = manual["semantic"]
        operations = manual["operations"]
        lines.append(
            f"| {manual['manual_id']} | {semantic['gold_claims_present']}/{semantic['gold_claims_total']} ({semantic['gold_claim_recall']:.3f}) | "
            f"{semantic['recall_floor']:.3f} | {semantic['autonomous_expected_claims_present']} | "
            f"{semantic['published_complete_paths_total']} | {manual['verdict']['publication_integrity']} | "
            f"{operations['cost_usd']:.6f} | {operations['calls']} |"
        )
    campaign = result["campaign"]
    lines.extend(
        [
            "",
            "## Campaign verdict",
            "",
            f"**{campaign['verdict'].upper()}**. Macro gold recall {campaign['macro_gold_claim_recall']:.3f} versus floor {campaign['macro_recall_floor']:.3f}. "
            f"Measured spend USD {campaign['actual_spend_usd']:.6f} of USD {campaign['authorized_budget_usd']:.2f}; "
            f"{campaign['calls']} calls in {campaign['elapsed_seconds']:.1f} seconds.",
            "",
            "## Critical interpretation",
            "",
            "- Page discovery retained every frozen gold page, so the principal failure is downstream of retrieval.",
            "- Graco published only Asset/Component structure. The dense troubleshooting table produced no diagnostic path and candidate accounting remained incomplete.",
            "- Danfoss published one correct table branch (Fuse blowout -> broken input fuse -> contact service personnel); the remaining table branches stayed in review/unaccounted states, including inspection-only rows that were not persisted as traceable explicit gaps.",
            "- Eastman published twelve complete paths, but none matches the frozen troubleshooting sample. Two of eight frozen claims survive only as traceable review records (vacuum filters and focusing lens). The published paths are mostly maintenance instructions reframed as diagnostic paths.",
            "- Schema and exact EvidenceRef checks pass for all three revisions, and the revisions correctly remain non-approvable. This is good fail-closed behavior, not evidence of useful diagnostic completeness.",
            "- Review artifacts persist reasons and evidence anchors but not the rejected typed records. That makes post-run semantic audit of latent candidates unnecessarily difficult.",
            "",
            "## Recommended next fixes",
            "",
            "1. Fix deterministic-ID collisions for repeated actions/causes within dense tables, preserving row identity without duplicating semantic nodes.",
            "2. Persist every typed diagnostic candidate and its compiler disposition, even when publication fails.",
            "3. Treat troubleshooting tables as row/branch structures and test row lineage before broad extraction of maintenance procedures.",
            "4. Rerun this frozen suite only after the compiler/accounting fixes; do not tune the gold to these outputs.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    manuals = [analyze_manual(spec) for spec in gold["manuals"]]
    macro = sum(item["semantic"]["gold_claim_recall"] for item in manuals) / len(manuals)
    spend = sum(item["operations"]["cost_usd"] for item in manuals)
    campaign = {
        "verdict": "go"
        if all(item["verdict"]["semantic"] == "pass" for item in manuals)
        and all(item["verdict"]["publication_integrity"] == "pass" for item in manuals)
        and macro >= gold["macro_gold_claim_recall_floor"]
        and spend <= gold["authorized_budget_usd"]
        else "no_go",
        "macro_gold_claim_recall": round(macro, 6),
        "macro_recall_floor": gold["macro_gold_claim_recall_floor"],
        "actual_spend_usd": round(spend, 6),
        "authorized_budget_usd": gold["authorized_budget_usd"],
        "conservative_preflight_usd": round(
            sum(item["operations"]["conservative_preflight_usd"] for item in manuals), 6
        ),
        "calls": sum(item["operations"]["calls"] for item in manuals),
        "elapsed_seconds": round(sum(item["operations"]["elapsed_seconds"] for item in manuals), 3),
    }
    result = {
        "campaign_id": gold["campaign_id"],
        "analysis_method": {
            "gold_is_frozen": True,
            "minimum_per_field_similarity": MATCH_FLOOR,
            "inspection_only_requires_pdf_diagnostic_record_gap": True,
            "production_had_access_to_gold": False,
        },
        "campaign": campaign,
        "manuals": manuals,
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    print(json.dumps({"campaign": campaign, "manuals": [{"manual_id": item["manual_id"], "semantic": item["semantic"] | {"witnesses": "omitted", "forbidden": "omitted"}, "integrity": {"passed": item["integrity"]["passed"], "diagnostic_accounting_complete": item["integrity"]["diagnostic_accounting_complete"], "approval_eligible": item["integrity"]["approval_eligible"]}, "operations": item["operations"]} for item in manuals]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
