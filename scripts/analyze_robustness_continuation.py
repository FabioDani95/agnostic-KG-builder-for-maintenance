"""Read-only C11/C12 metrics. Source-case judgements remain separate audit files."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from analyze_extraction_experiment import grounding, historical_probe, historical_tools, read, write

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--continuation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    events = [json.loads(x) for x in (args.campaign / "real_call_budget.jsonl").read_text().splitlines()]
    reserved = {e["call_id"]: e for e in events if e["event"] == "call_reserved"}
    finalized = {e["call_id"]: e for e in events if e["event"] == "call_finalized"}
    costs = defaultdict(lambda: {"new_api_attempts": 0, "charged_usd": Decimal(0), "unknown_usage_attempts": 0})
    for call, e in finalized.items():
        row = costs[reserved[call]["run_id"]]
        row["new_api_attempts"] += 1
        row["charged_usd"] += Decimal(str(e["charged_cost_usd"]))
        row["unknown_usage_attempts"] += e.get("actual_usage") is None
    for row in costs.values():
        row["charged_usd"] = float(row["charged_usd"])
    wrapped, analyzer = historical_tools()
    specs = {
        s["manual_id"]: s
        for s in read(ROOT / "artifacts/acceptance/g3/diagnostic_benchmark_20260812/golden.json")["manuals"]
    }
    rows = []
    for path in sorted(args.continuation.glob("c12r1_*")):
        if not path.is_dir():
            continue
        profile = read(path / "runtime_profile.json")
        state = read(path / "continuation.json")
        original = Path(profile["source_run"])
        manual = read(original / "runtime_profile.json")["manual_id"]
        row = {
            "run_id": path.name,
            "manual_id": manual,
            "status": state["status"],
            "mode": profile["mode"],
            "cached_request_count": len(state.get("cached_exchanges", [])),
            "new_request_count": len(state.get("new_requests", [])),
            "blocked_requests": state.get("blocked_requests", []),
            "unused_exchanges": state.get("unused_exchanges"),
            "new_cost": costs.get(path.name, {"new_api_attempts": 0, "charged_usd": 0.0, "unknown_usage_attempts": 0}),
            "elapsed_seconds": state.get("elapsed_seconds"),
        }
        if (path / "graph.json").exists():
            graph = read(path / "graph.json")
            old = read(original / "graph.json")
            ledger = graph["diagnostic_compilation_ledger"]
            paths = wrapped._branch_aware_paths(graph)
            branches = {p["branch_lineage_id"] for p in paths}
            old_branches = {p["branch_lineage_id"] for p in wrapped._branch_aware_paths(old)}
            row.update(
                review=graph["review_summary"],
                approval_eligible=graph["approval_eligible"],
                candidate_count=ledger["candidate_count"],
                publish_count=ledger["publish_count"],
                unresolved_count=ledger["unresolved_count"],
                distinct_graph_branches=len(branches),
                branches_added=sorted(branches - old_branches),
                branches_lost=sorted(old_branches - branches),
                canonical_grounding=grounding(graph, original),
                supplemental_procedure_pages=ledger.get("supplemental_procedure_pages", []),
                supplemental_procedure_packet_count=ledger.get("supplemental_procedure_packet_count", 0),
                graph_nodes_identical_to_c11=graph["nodes"] == old["nodes"],
                graph_relations_identical_to_c11=graph["relations"] == old["relations"],
                semantic_precision=None,
                semantic_recall=None,
            )
            if manual in specs:
                probe = historical_probe(graph, specs[manual], paths, analyzer)
                row["historical_probe"] = {
                    k: v for k, v in probe.items() if k not in {"witnesses", "one_to_one_assignments"}
                }
        rows.append(row)
    budget = {
        "cap_usd": 20,
        "charged_usd": float(sum((Decimal(str(e["charged_cost_usd"])) for e in finalized.values()), Decimal(0))),
        "reservations": len(reserved),
        "finalized": len(finalized),
        "active_call_ids": sorted(reserved.keys() - finalized.keys()),
    }
    write(
        args.output,
        {
            "status": "development_not_independent_gold",
            "c12": rows,
            "budget": budget,
            "new_run_costs": {k: v for k, v in costs.items() if k.startswith(("c9", "c10", "c11", "c12"))},
            "cost_note": "Cached token usage in graph metrics belongs to original runs. New API costs come only from ledger.",
        },
    )
    print(
        json.dumps(
            {"budget": budget, "runs": [(r["run_id"], r["status"], r.get("distinct_graph_branches")) for r in rows]}
        )
    )


if __name__ == "__main__":
    main()
