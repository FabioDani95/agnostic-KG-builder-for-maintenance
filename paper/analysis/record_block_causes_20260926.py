"""Classify why diagnostic records of the frozen C12 graphs were not published.

Offline, read-only analysis of the four final C12 revisions produced by
generator ``pdf-g3-structured-recovery-v22``. It groups each non-excluded
record of the compilation ledger by its drop reasons, groups review items by
kind and counts how many extraction calls read each diagnostic page.

Record counts include duplicate extractions of the same source passage. The
categories describe the compiler's stated reasons; they are not a semantic
judgement of whether a record was correct.

Usage: python paper/analysis/record_block_causes_20260926.py
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "paper/experiments/robustness_continuation_20260926"
MANUALS = ("eastman_e554", "danfoss_apf", "graco_check_mate_200", "hypertherm_powermax30_air")
OUTPUT = Path(__file__).with_suffix(".json")

# Failures of evidence bookkeeping, record parsing, redundant accounting or
# lexical support rules. None of them states that the source lacks the claim.
MECHANICAL = {
    "quote_not_in_anchored_evidence", "source_anchor_outside_record_window",
    "unknown_source_anchor", "source_page_mismatch", "lineage_anchor_outside_bundle",
    "record_schema_invalid", "candidate_passage_missing_disposition",
    "relation_endpoint_support_unestablished", "missing_indicator_failure_evidence",
    "missing_resolution_evidence", "structured_response_error", "missing_affects_evidence",
}
# The source states only part of the symptom -> failure -> action chain.
PARTIAL_CHAIN = {
    "missing_actions", "missing_failure", "check_only", "no_action_stated",
    "action_without_failure", "component_without_failure",
    "failure_edge_without_failure", "inspection_only_action",
}
# Review items that ask for a decision about a diagnostic record or identity.
DECISION_REVIEW_CODES = {
    "pdf_diagnostic_record_review", "pdf_diagnostic_record_gap", "canonicalization_ambiguous",
}


def classify_records(records: list[dict]) -> dict[str, int]:
    counts: collections.Counter[str] = collections.Counter()
    for record in records:
        disposition = record.get("disposition")
        if disposition in {"publish", "exclude"}:
            counts[disposition] += 1
            continue
        codes = {reason.get("code") for reason in record.get("drop_reasons") or []}
        if codes & MECHANICAL:
            counts["blocked_mechanical_or_checker"] += 1
        elif codes & PARTIAL_CHAIN:
            counts["blocked_partial_chain_only"] += 1
        else:
            counts["blocked_other_content"] += 1
    return dict(counts)


def page_read_counts(chunks: list[dict]) -> dict[str, float]:
    reads: collections.Counter[int] = collections.Counter()
    for chunk in chunks:
        for page in chunk.get("input_pages") or []:
            reads[int(page)] += 1
    values = list(reads.values()) or [0]
    return {
        "extraction_calls": len(chunks),
        "pages_read": len(reads),
        "max_calls_reading_one_page": max(values),
        "mean_calls_per_page_read": round(sum(values) / len(values), 3),
    }


def main() -> int:
    per_manual: dict[str, dict] = {}
    totals: collections.Counter[str] = collections.Counter()
    for manual in MANUALS:
        graph = json.loads((CAMPAIGN / f"c12r1_{manual}" / "graph.json").read_text(encoding="utf-8"))
        ledger = graph["diagnostic_compilation_ledger"]
        records = classify_records(ledger["records"])
        review_codes = collections.Counter(item["code"] for item in graph["review_queue"])
        decision_items = sum(count for code, count in review_codes.items() if code in DECISION_REVIEW_CODES)
        node_types = collections.Counter(node["node_type"] for node in graph["nodes"])
        per_manual[manual] = {
            "records": records,
            "review_items_total": len(graph["review_queue"]),
            "review_items_record_or_identity": decision_items,
            "review_items_system_report": len(graph["review_queue"]) - decision_items,
            "review_codes": dict(review_codes.most_common()),
            "node_types": dict(node_types.most_common()),
            "page_reads": page_read_counts(ledger["chunks"]),
        }
        totals.update(records)
    non_excluded = sum(value for key, value in totals.items() if key != "exclude")
    result = {
        "source": str(CAMPAIGN.relative_to(ROOT)),
        "generator": "pdf-g3-structured-recovery-v22",
        "unit": "compilation-ledger record, duplicates included",
        "totals": dict(totals),
        "non_excluded_records": non_excluded,
        "share_of_non_excluded": {
            key: round(value / non_excluded, 3) for key, value in totals.items() if key != "exclude"
        },
        "per_manual": per_manual,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "share": result["share_of_non_excluded"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
