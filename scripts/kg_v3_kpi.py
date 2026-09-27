"""KPI of the V3 evaluation protocol for any annotated manual (paper/evaluation/PROTOCOLLO_V3.md).

Layout: <runs>/<manual>/runs/ (campaign) or <runs>/<manual>/ holds V3 runs (v3_r1, ...)
and the optional v22 baseline (v22). The gold is campaign/<manual>/gold/gold.json, or
paper/evaluation/gold_segments_v1 for the historical cases. Usually called through
scripts/campaign.py kpi.

Usage:
    .venv/bin/python scripts/kg_v3_kpi.py --manuals genie_scissor,grundfos_paco --runs campaign \\
        --out campaign/results/kpi.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.kg_v3 import DEFAULT_BUDGET, DEFAULT_LEDGER, load_evidence, manual_source  # noqa: E402
from scripts.kg_v3_compare import token_f1  # noqa: E402
from scripts.kg_v3_evaluate import score_system, v3_edges, v22_edges_from  # noqa: E402

CAMPAIGN = ROOT / "campaign"
GOLD_V1 = ROOT / "paper/evaluation/gold_segments_v1"


def wilson(successes: int, total: int) -> list[float]:
    if not total:
        return [0.0, 0.0]
    z, p = 1.96, successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return [round(centre - margin, 3), round(centre + margin, 3)]


def load_gold(manual: str) -> tuple[list[dict], list[int]]:
    path = CAMPAIGN / manual / "gold" / "gold.json"
    if path.exists():
        data = json.loads(path.read_text())
        return data["claims"], data.get("pages", [])
    data = json.loads((GOLD_V1 / f"{manual}.json").read_text())
    claims = [{**claim, "branch_id": claim["claim_id"]} for claim in data["claims"] if not claim.get("excluded")]
    return claims, sorted({page for claim in claims for page in claim["pages"]})


def v3_run_facts(run: Path) -> dict:
    report = json.loads((run / "report.json").read_text())
    graph = json.loads((run / "graph.json").read_text())
    # Causes the system names from a check or remedy, marked as not written in the manual.
    derived = sum(node["type"] == "FailureMode" and not node.get("stated_in_source", True)
                  and not node["name"].startswith("Unspecified cause of") for node in graph["nodes"])
    usage = report["usage"]["estimated_cost_usd"] + ((report.get("agent_usage") or {}).get("estimated_cost_usd") or 0)
    return {
        "diagnostic_pages": report.get("diagnostic_pages", []),
        "person_questions": sum(report["gates"].get(gate, {}).get("pending", 0) for gate in ("map", "doubts")),
        "agent_answers": report.get("answers_by_reviewer", {}).get("agent", 0),
        "failed_reads": report.get("failed_reads", 0),
        "seconds": report["seconds"]["total"], "cost_usd": round(usage, 5),
        "green": report["graph"]["edges_by_tier"].get("green", 0),
        "derived_causes": derived,
    }


async def evaluate(manuals: list[str], runs_root: Path) -> dict:
    from backend.kg_v3.llm import ModelClient
    from backend.kg_v3.reader import read_document

    llm = ModelClient(model="gpt-6-luna", reasoning_effort="low")
    results: dict = {"manuals": {}}
    for manual in manuals:
        claims, gold_pages = load_gold(manual)
        # A branch with neither cause nor action only defines a code or indication: it is
        # measured as code coverage, not as a diagnostic chain.
        indicator_only = [claim for claim in claims if not claim.get("failure") and not claim.get("action")]
        claims = [claim for claim in claims if claim not in indicator_only]
        # A gold re-linked from another reading of the PDF is valid for positions only once verified.
        gold_dir = CAMPAIGN / manual / "gold"
        positions_valid = not (gold_dir / "remap_ids.json").exists() or (gold_dir / "remap_ids_verified.json").exists()
        pdf, asset = manual_source(manual)
        evidence, page_count, _ = load_evidence(pdf, asset)
        doc = read_document(list(evidence), page_count=page_count)
        branches = defaultdict(list)
        for claim in claims:
            branches[claim["branch_id"]].append(claim["claim_id"])
        folder = runs_root / manual / "runs" if (runs_root / manual / "runs").exists() else runs_root / manual
        systems = {}
        for run in sorted(item for item in folder.iterdir() if item.is_dir()) if folder.exists() else []:
            if run.name == "v22" and (run / "graph.json").exists():
                systems["v22"] = (v22_edges_from(run / "graph.json", doc, evidence), json.loads(
                    (run / "timing.json").read_text()) if (run / "timing.json").exists() else {})
            elif (run / "graph.json").exists() and (run / "report.json").exists():
                name = run.name if run.name.startswith("v3_") else f"v3_{run.name}"
                systems[name] = (v3_edges(run), v3_run_facts(run))
        rows = {}
        for name, (edges, facts) in systems.items():
            score = await score_system(llm, claims, edges)
            found = set(score["recovered_meaning"])
            branch_hits = sum(all(claim in found for claim in members) for members in branches.values())
            names = [" ".join([edge["source_name"], edge["target_name"]]) for edge in edges]
            covered = sum(any(token_f1(claim["indicator"], name) >= 0.5 or (claim.get("code") and claim["code"] in name)
                              for name in names) for claim in indicator_only)
            row = {
                "branch_recall": [branch_hits, len(branches)], "claim_recall": [len(found), len(claims)],
                "code_coverage": [covered, len(indicator_only)],
                "evidence_on_gold_segments": score["evidence_on_gold_segments"] if positions_valid else "not valid",
                "missing_claims": sorted(set(claim["claim_id"] for claim in claims) - found),
            }
            if name.startswith("v3_"):
                read = set(facts["diagnostic_pages"])
                row.update(facts, map_coverage=[len(set(gold_pages) & read), len(gold_pages)])
                row.pop("diagnostic_pages")
            else:
                row["seconds"] = facts.get("seconds")
            rows[name] = row
        v3_rows = [row for name, row in rows.items() if name.startswith("v3_")]
        stability = [row["branch_recall"][0] / max(1, row["branch_recall"][1]) for row in v3_rows]
        results["manuals"][manual] = {
            "branches": len(branches), "claims": len(claims), "gold_pages": gold_pages, "systems": rows,
            "v3_branch_recall_min_max": [round(min(stability), 3), round(max(stability), 3)] if stability else None,
        }
    totals = defaultdict(lambda: [0, 0])
    for manual in results["manuals"].values():
        for name, row in manual["systems"].items():
            family = "v22" if name == "v22" else "v3"
            totals[family][0] += row["branch_recall"][0]
            totals[family][1] += row["branch_recall"][1]
    results["micro_branch_recall"] = {name: {"value": [hits, total], "wilson95": wilson(hits, total)}
                                      for name, (hits, total) in totals.items()}
    results["judge_usage"] = llm.usage.as_dict()
    return results


def markdown(results: dict) -> str:
    lines = ["| Manuale | Sistema | Rami | Asserzioni | Codici | Prove sul gold | Mappa | Domande a persona | Secondi | USD |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for manual, data in results["manuals"].items():
        for name, row in data["systems"].items():
            branch, claim = row["branch_recall"], row["claim_recall"]
            mapping = f"{row['map_coverage'][0]}/{row['map_coverage'][1]}" if "map_coverage" in row else "-"
            codes = row["code_coverage"]
            lines.append(f"| {manual} | {name} | {branch[0]}/{branch[1]} | {claim[0]}/{claim[1]} | {codes[0]}/{codes[1]} | "
                         f"{row['evidence_on_gold_segments']} | {mapping} | {row.get('person_questions', '-')} | "
                         f"{row.get('seconds', '-')} | {row.get('cost_usd', '-')} |")
    for name, total in results["micro_branch_recall"].items():
        lines.append(f"\nRecall dei rami {name}: {total['value'][0]}/{total['value'][1]}, IC95 {total['wilson95']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manuals", required=True, help="comma-separated manual IDs")
    parser.add_argument("--runs", required=True, help="folder with one sub-folder per manual")
    parser.add_argument("--out", required=True)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--budget", default=DEFAULT_BUDGET)
    args = parser.parse_args()
    os.chdir(ROOT)
    Path(args.ledger).resolve().parent.mkdir(parents=True, exist_ok=True)
    os.environ.update({"KG_LLM_MODE": "real", "KG_REAL_CALL_BUDGET_LEDGER": str(Path(args.ledger).resolve()),
                       "KG_REAL_CALL_BUDGET_USD": args.budget, "KG_REAL_CALL_RUN_ID": "v3_kpi_judge",
                       "KG_REAL_CALL_PDF_ID": "evaluation",
                       "KG_LLM_TRACE_DIR": str(ROOT / "eval_runs/v3_kpi/provider")})
    results = asyncio.run(evaluate([item.strip() for item in args.manuals.split(",") if item.strip()],
                                   (ROOT / args.runs).resolve()))
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1) + "\n")
    out.with_suffix(".md").write_text(markdown(results))
    print(markdown(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
