"""Compare V3 runs with the frozen v22 graphs on the same manuals and the same scorer.

The scorer is deliberately independent of the V3 code: a gold claim counts as
recovered when the graph holds a chain symptom or code -> failure -> action or
check whose names share enough content words with the gold text (token F1).
It is a lexical development probe, not a validated semantic metric, and it is
applied identically to both systems.

Usage:
    .venv/bin/python scripts/kg_v3_compare.py --v3 eval_runs/v3_dev/final_r1 [--v3 ...] --out report.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "artifacts/acceptance/g3/diagnostic_benchmark_20260812/golden.json"
V22 = ROOT / "paper/experiments/robustness_continuation_20260926"
LEDGER = ROOT / "paper/experiments/robustness_20260925/real_call_budget.jsonl"
MANUALS = ("eastman_e554", "danfoss_apf", "graco_check_mate_200", "hypertherm_powermax30_air")
# Wall time of the complete v22 extraction runs (C11 report); C12 reused them.
V22_SECONDS = {"eastman_e554": 1013.237, "danfoss_apf": 110.729, "graco_check_mate_200": 161.615,
               "hypertherm_powermax30_air": 1615.165}
MATCH = 0.5
_STOP = {"the", "a", "an", "of", "or", "and", "is", "are", "to", "in", "on", "be", "if", "for", "with", "not"}


def words(text: str) -> list[str]:
    return [item for item in re.findall(r"[a-z0-9]+", str(text).lower()) if item not in _STOP]


def token_f1(left: str, right: str) -> float:
    a, b = words(left), words(right)
    if not a or not b:
        return 0.0
    common = sum(min(a.count(item), b.count(item)) for item in set(a))
    if not common:
        return 0.0
    precision, recall = common / len(a), common / len(b)
    return 2 * precision * recall / (precision + recall)


class Graph:
    def __init__(self, names: dict[str, list[str]], edges: list[tuple[str, str, str, bool]], human_items: int):
        self.names = names
        self.out: dict[str, list[tuple[str, str, bool]]] = defaultdict(list)
        for relation, source, target, trusted in edges:
            self.out[source].append((relation, target, trusted))
        self.human_items = human_items

    def best(self, node: str, text: str) -> float:
        return max((token_f1(name, text) for name in self.names.get(node, [])), default=0.0)

    def recovered(self, claim: dict, *, trusted_only: bool) -> bool:
        indicator = claim.get("symptom") or ""
        code = str(claim.get("error_code") or "")
        action = claim.get("corrective_action") or claim.get("inspection_step") or ""
        for start in self.names:
            if self.best(start, indicator) < MATCH and not (code and any(code == name.strip() for name in self.names[start])):
                continue
            for relation, failure, trusted in self.out.get(start, []):
                if relation not in {"MAY_INDICATE", "INDICATES"} or (trusted_only and not trusted):
                    continue
                if self.best(failure, claim["failure_mode"]) < MATCH:
                    continue
                if not action:
                    return True
                for relation2, target, trusted2 in self.out.get(failure, []):
                    if relation2 == "RESOLVED_BY" and (trusted2 or not trusted_only) and self.best(target, action) >= MATCH:
                        return True
        return False


def load_v22(manual: str) -> Graph:
    data = json.loads((V22 / f"c12r1_{manual}" / "graph.json").read_text())
    names = {}
    for node in data["nodes"]:
        attributes = node.get("attributes") or {}
        names[node["node_id"]] = [node["label"], *(str(attributes[key]) for key in ("code", "name") if attributes.get(key))]
    edges = [(item["relation_type"], item["from_id"], item["to_id"], True) for item in data["relations"]]
    return Graph(names, edges, len(data.get("review_queue") or []))


def load_v3(run: Path) -> tuple[Graph, dict]:
    data = json.loads((run / "graph.json").read_text())
    names = {node["id"]: [node["name"], *node.get("aliases", []), *(
        [node["properties"]["code"]] if node.get("properties", {}).get("code") else [])] for node in data["nodes"]}
    edges = [(item["type"], item["from"], item["to"], item["trusted"]) for item in data["edges"]]
    report = data["report"]
    # What a person would still have to answer: questions no agent settled.
    human = sum(report["gates"].get(gate, {}).get("pending", 0) for gate in ("map", "doubts"))
    return Graph(names, edges, human), report


def ledger_costs() -> dict[str, float]:
    runs, costs = {}, defaultdict(float)
    for line in LEDGER.read_text().splitlines():
        event = json.loads(line)
        if event.get("event") == "call_reserved":
            runs[event["call_id"]] = event.get("run_id", "")
        elif event.get("event") == "call_finalized":
            costs[runs.get(event["call_id"], "")] += float(event.get("charged_cost_usd") or 0)
    return costs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--v3", action="append", required=True, help="directory holding <manual>/ run folders")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    gold = {item["manual_id"]: item["expected_claims"] for item in json.loads(GOLD.read_text())["manuals"]}
    costs = ledger_costs()
    rows = []
    for manual in MANUALS:
        v22 = load_v22(manual)
        claims = gold.get(manual, [])
        row = {"manual": manual, "gold_claims": len(claims), "v22": {
            "recovered": sum(v22.recovered(claim, trusted_only=False) for claim in claims),
            "human_items": v22.human_items, "seconds": V22_SECONDS[manual],
            "cost_usd": round(costs.get(f"c11_full_{manual}", 0.0), 5),
            "relations": sum(len(items) for items in v22.out.values()),
        }, "v3": []}
        for folder in args.v3:
            run = Path(folder) / manual
            if not (run / "graph.json").exists():
                continue
            graph, report = load_v3(run)
            row["v3"].append({
                "run": str(run.relative_to(ROOT)) if run.is_absolute() else str(run),
                "recovered_trusted": sum(graph.recovered(claim, trusted_only=True) for claim in claims),
                "recovered_any": sum(graph.recovered(claim, trusted_only=False) for claim in claims),
                "human_items": graph.human_items,
                "questions_answered_by_agent": report.get("answers_by_reviewer", {}).get("agent", 0),
                "relations": report["graph"]["edges"], "relations_by_tier": report["graph"]["edges_by_tier"],
                "seconds": report["seconds"]["total"], "cost_usd": report["usage"]["estimated_cost_usd"]
                + ((report.get("agent_usage") or {}).get("estimated_cost_usd") or 0),
                "failed_reads": report["failed_reads"]
            })
        rows.append(row)
    Path(args.out).write_text(json.dumps(rows, indent=1) + "\n")
    for row in rows:
        v3 = row["v3"]
        recovered = [item["recovered_trusted"] for item in v3]
        print(f"{row['manual']:28s} gold {row['gold_claims']:2d} | v22 {row['v22']['recovered']:2d} rec, "
              f"{row['v22']['human_items']:3d} items, {row['v22']['seconds']:7.1f}s | v3 rec {recovered}, "
              f"items {[item['human_items'] for item in v3]}, s {[round(item['seconds']) for item in v3]}, "
              f"$ {[round(item['cost_usd'], 4) for item in v3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
