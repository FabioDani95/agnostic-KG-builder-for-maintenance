"""Join review notifications to immutable candidates, graph branches and PDF sources.

Families are mechanical triage, not semantic adjudication. A case is an exact
target (or exact record window); connected components are deliberately avoided:
one general component notification must not collapse all its diagnostic branches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path


def inventory(graph, evidence):
    records = graph.get("diagnostic_compilation_ledger", {}).get("records", [])
    nodes = {n["node_id"]: n for n in graph["nodes"]}
    by_id = {e["evidence_id"]: e for e in evidence}
    rows = []
    for item in graph.get("review_queue", []):
        target = item.get("target_id", "")
        exact = [r for r in records if target and target in {r.get("branch_lineage_id"), r.get("record_lineage_id"), r.get("record_window_id")}]
        anchors = set(item.get("evidence_ids", []))
        related = [r for r in records if r in exact or anchors.intersection(r.get("evidence_ids", [])) or target in r.get("emitted_node_ids", [])]
        codes = {reason["code"] for r in exact for reason in r.get("drop_reasons", [])} | {item["code"]}
        if any("quote" in c or "anchor" in c or "provenance" in c or "ocr" in c or "schema" in c for c in codes):
            family = "technical_evidence"
        elif any("ambiguous" in c or "canonical" in c for c in codes):
            family = "pairing_or_identity_unjudged"
        elif any("endpoint_support" in c for c in codes):
            family = "missing_relation_context"
        elif any("unaccounted" in c or "undisposed" in c for c in codes):
            family = "omission"
        elif exact and all(r.get("source_gap_verified") for r in exact):
            family = "verified_source_gap"
        else:
            family = "content_requires_source_audit"
        window_ids = sorted({r["record_window_id"] for r in exact if r.get("record_window_id")})
        case = "window:" + window_ids[0] if len(window_ids) == 1 else "target:" + target if target else "notification:" + item["item_id"]
        source_ids = sorted(anchors | {a for r in exact for a in r.get("evidence_ids", [])} | set(nodes.get(target, {}).get("evidence_ids", [])))
        sources = [{"evidence_id": a, "locator": by_id[a]["locator"], "attributes": by_id[a].get("attributes", {})} for a in source_ids if a in by_id]
        rows.append({"original": item, "case_id": case, "triage_family": family,
                     "exact_record_ids": [r["branch_lineage_id"] for r in exact],
                     "related_record_ids": [r["branch_lineage_id"] for r in related],
                     "window_ids": window_ids, "sources": sources,
                     "pages": sorted({s["locator"]["page"] for s in sources if "page" in s["locator"]}),
                     "reason_codes": sorted(codes), "judgement": "not_semantically_adjudicated"})
    cases = {}
    for row in rows:
        cases.setdefault(row["case_id"], []).append(row)
    return {"notification_count": len(rows), "exact_target_case_count": len(cases),
            "case_definition": "Exact target/window identity; not unique semantic chains or measured human workload.",
            "family_counts_notifications": dict(Counter(r["triage_family"] for r in rows)),
            "family_counts_cases": dict(Counter(sorted({r["triage_family"] for r in group})[0] if len({r["triage_family"] for r in group}) == 1 else "mixed" for group in cases.values())),
            "notifications": rows, "records": records,
            "canonicalization": graph.get("canonicalization_report", {}),
            "cases": {key: [r["original"]["item_id"] for r in group] for key, group in cases.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    graph = json.loads(args.graph.read_text())
    with sqlite3.connect(args.database.resolve().as_uri() + "?mode=ro", uri=True) as conn:
        evidence = [json.loads(r[0]) for r in conn.execute("SELECT payload_json FROM evidence_units")]
    result = inventory(graph, evidence)
    result["graph_sha256"] = hashlib.sha256(args.graph.read_bytes()).hexdigest()
    with args.output.open("x") as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k.endswith("count") or k.startswith("family_counts")}))


if __name__ == "__main__":
    main()
