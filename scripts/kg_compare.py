"""Compare pipeline versions on the same manuals, from saved graphs and saved judgements.

Offline and read-only. Each system is a set of run directories, one per manual; a system may
have a saved judgement of branch recall. The tool puts the measures of every system side by
side and, against a baseline, says for each measure whether the system is better, the same or
worse. "The same" is a band, not a point: two values closer than the tolerance are not told
apart, because replicas of one system differ by that much.

Recall is shown three ways, from strict to tolerant, all computed from the same saved judgement:

    branches   branches whose claims were all found          (all or nothing)
    coverage   mean share of claims found per branch         (partial credit)
    claims     claims found over all claims

Usage:
    .venv/bin/python scripts/kg_compare.py --manuals grizzly_g0872,lg_lmh2235st \\
        --system "V3 F=campaign/{manual}/runs/v3_r1" --recall "V3 F=campaign/results/kpi_F.json:v3_r1" \\
        --system "kg_v4=experiments/kg4_trial/runs/{manual}/r1" --recall "kg_v4=experiments/kg4_trial/kpi.json:v3_r1" \\
        --baseline "V3 F" --out experiments/kg4_trial/comparison
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.kg_v4.metrics import scorecard  # noqa: E402
from scripts.kg_loss_analysis import recovered_claims  # noqa: E402

TOLERANCE = 0.03
# (key, label, higher is better, shown as a share)
MEASURES = (
    ("recall_branches", "Recall: branches fully found", True, True),
    ("recall_coverage", "Recall: mean coverage per branch", True, True),
    ("recall_claims", "Recall: claims found", True, True),
    ("largest_component", "Nodes in the largest grounded component", True, True),
    ("largest_component_read", "  the same, only links read from the manual", True, True),
    ("causes_with_action", "Causes with an action or a declared absence", True, True),
    ("causes_reachable", "Causes reachable from a symptom or code", True, True),
    ("complete_chains", "Symptoms and codes with a complete chain", True, True),
    ("excluded", "Relations excluded", False, True),
    ("real_descriptions", "Descriptions that say more than the name", True, True),
    ("attributes_from_manual", "Required attributes filled from the manual", True, True),
    ("generic_bridges", "Generic nodes used as bridges", False, False),
    ("duplicate_candidates", "Duplicate candidates (lexical screen)", False, False),
    ("suspect_merges", "Suspect merges (false-friend screen)", False, False),
    ("with_section", "Facts with page and section", True, True),
    ("nodes", "Nodes", None, False),
    ("cost_usd", "Estimated cost, USD", False, False),
    ("seconds", "Seconds", False, False),
)


def gold_claims(manual: str) -> list[dict]:
    path = ROOT / "campaign" / manual / "gold" / "gold.json"
    if not path.exists():
        return []
    return [claim for claim in json.loads(path.read_text())["claims"] if claim.get("failure") or claim.get("action")]


def recall(claims: list[dict], found: set[str]) -> dict[str, float | list[int] | None]:
    """Strict, partial-credit and claim-level recall of one judged graph."""

    branches: dict[str, list[str]] = defaultdict(list)
    for claim in claims:
        branches[claim["branch_id"]].append(claim["claim_id"])
    if not branches:
        return {"recall_branches": None, "recall_coverage": None, "recall_claims": None}
    full = sum(all(item in found for item in members) for members in branches.values())
    coverage = sum(sum(item in found for item in members) / len(members) for members in branches.values())
    hits = sum(claim["claim_id"] in found for claim in claims)
    return {"recall_branches": round(full / len(branches), 4), "recall_coverage": round(coverage / len(branches), 4),
            "recall_claims": round(hits / len(claims), 4), "branch_counts": [full, len(branches)],
            "claim_counts": [hits, len(claims)]}


def measures(graph: dict) -> dict:
    card = scorecard(graph)
    links, quality = card["connectivity"], card["node_quality"]
    return {
        "nodes": links["nodes"], "largest_component": links["largest_component_share"],
        "largest_component_read": links["variants"]["extracted_only"]["largest_component_share"],
        "causes_with_action": links["causes_with_action_or_declared_share"],
        "causes_reachable": links["causes_reachable_where_manual_gives_entry_share"],
        "complete_chains": links["entries_with_complete_chain_share"], "excluded": links["excluded_share"],
        "real_descriptions": quality["real_description_share"],
        "attributes_from_manual": quality["required_attributes_from_manual_share"],
        "generic_bridges": quality["generic_nodes_used_as_bridge"],
        "duplicate_candidates": quality["duplicate_candidates"], "suspect_merges": quality["suspect_merges"],
        "with_section": card["provenance"]["with_section_share"],
        "cost_usd": card["cost"]["estimated_cost_usd"] or None, "seconds": card["cost"]["seconds"],
    }


def verdict(key: str, value, base, tolerance: float = TOLERANCE) -> str:
    """better, same or worse than the baseline; '' when the measure has no direction or a value is missing."""

    higher, share = next((item[2], item[3]) for item in MEASURES if item[0] == key)
    if higher is None or value is None or base is None:
        return ""
    band = tolerance if share else tolerance * max(abs(base), 1)
    if abs(value - base) <= band:
        return "same"
    return "better" if (value > base) == higher else "worse"


def compare(manuals: list[str], systems: dict[str, str], judgements: dict[str, tuple[Path, str]],
            baseline: str | None) -> dict:
    table: dict[str, dict[str, dict]] = {}
    for manual in manuals:
        claims = gold_claims(manual)
        table[manual] = {}
        for name, pattern in systems.items():
            run = ROOT / pattern.format(manual=manual)
            graph_path = run if run.name == "graph.json" else run / "graph.json"
            if not graph_path.exists():
                continue
            row = measures(json.loads(graph_path.read_text()))
            row["graph"] = str(graph_path.relative_to(ROOT))
            if name in judgements and claims:
                path, system = judgements[name]
                try:
                    row.update(recall(claims, recovered_claims(path, manual, system)))
                    row["judgement"] = str(path)
                except (KeyError, StopIteration, SystemExit):
                    pass  # this manual has no complete saved judgement for this system
            table[manual][name] = row
    summary: dict[str, dict[str, int]] = {}
    if baseline:
        for name in systems:
            if name == baseline:
                continue
            counts: dict[str, int] = defaultdict(int)
            for rows in table.values():
                if name in rows and baseline in rows:
                    rows[name]["versus_baseline"] = {key: verdict(key, rows[name].get(key), rows[baseline].get(key))
                                                     for key, *_ in MEASURES}
                    for value in rows[name]["versus_baseline"].values():
                        counts[value] += bool(value)
            summary[name] = dict(counts)
    return {"baseline": baseline, "tolerance": TOLERANCE, "manuals": table, "versus_baseline": summary}


def _show(value, share: bool) -> str:
    if value is None:
        return "n.m."
    return f"{round(100 * value)}%" if share else str(round(value, 3) if isinstance(value, float) else value)


def markdown(result: dict) -> str:
    marks = {"better": " ▲", "worse": " ▼", "same": " ＝", "": ""}
    lines = ["# Pipeline comparison", "",
             f"Baseline: **{result['baseline'] or 'none'}**. ▲ better, ▼ worse, ＝ within ±{round(100 * result['tolerance'])} "
             "points (or 3% for counts) of the baseline. n.m. = not measured: no saved judgement or no value.",
             "Every column describes one saved graph file; recall comes from a saved judgement by an LLM judge.", ""]
    for manual, rows in result["manuals"].items():
        if not rows:
            continue
        names = list(rows)
        lines += [f"## {manual}", "", "| Measure | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
        for key, label, _, share in MEASURES:
            cells = [_show(rows[name].get(key), share) + marks[rows[name].get("versus_baseline", {}).get(key, "")]
                     for name in names]
            lines.append(f"| {label} | " + " | ".join(cells) + " |")
        lines.append("")
    if result["versus_baseline"]:
        lines += ["## Against the baseline, over all manuals and measures", "", "| System | Better | Same | Worse |",
                  "|---|---:|---:|---:|"]
        for name, counts in result["versus_baseline"].items():
            lines.append(f"| {name} | {counts.get('better', 0)} | {counts.get('same', 0)} | {counts.get('worse', 0)} |")
        lines.append("")
    return "\n".join(lines)


def _pairs(values: list[str], what: str) -> dict[str, str]:
    out = {}
    for value in values:
        name, separator, rest = value.partition("=")
        if not separator or not rest:
            raise SystemExit(f"--{what} takes NAME=VALUE, got {value!r}")
        out[name.strip()] = rest.strip()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manuals", required=True, help="comma-separated manual IDs")
    parser.add_argument("--system", action="append", default=[], required=True,
                        help="NAME=run directory pattern with {manual}; repeat for each system")
    parser.add_argument("--recall", action="append", default=[],
                        help="NAME=judgement file:run name in it (a campaign kpi JSON, or the pilot scores with Bsafe/r1)")
    parser.add_argument("--baseline", help="system the others are compared with")
    parser.add_argument("--out", required=True, help="directory for comparison.json and COMPARISON.md")
    args = parser.parse_args()
    systems = _pairs(args.system, "system")
    judgements = {}
    for name, value in _pairs(args.recall, "recall").items():
        path, _, system = value.rpartition(":")
        judgements[name] = (ROOT / path, system)
    if args.baseline and args.baseline not in systems:
        parser.error(f"--baseline {args.baseline!r} is not one of the systems")
    result = compare([item for item in args.manuals.split(",") if item], systems, judgements, args.baseline)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    (out / "COMPARISON.md").write_text(markdown(result) + "\n")
    print(markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
