"""Where a saved run lost each gold claim: before reading, in extraction, at a gate or in the graph.

Offline and read-only: it uses the gold, the run's saved state and graph, and the recovered
claims of a saved judgement. No model is called.

Each gold claim asks for a problem-to-cause link and, when it has one, a cause-to-action link.
For each link the tool finds how far a candidate got. A candidate is a relation of the right
type cited on a gold segment or with similar names: the rule the historical scorer uses to
choose what the judge sees. The stages, in order:

    page_not_read          no page of the claim was among the pages read
    never_extracted        no read proposed a candidate
    lost_after_extraction  proposed, but neither in the graph nor among the excluded relations
    discarded_by_gate      only among the excluded relations (with the gate that excluded it)
    in_graph_untrusted     in the graph, never trusted (yellow)
    in_graph_not_matched   trusted in the graph, yet the judge did not find the claim
    recovered              the judge found the claim

A claim takes the stage of its weakest link. "Candidate" does not mean correct: stages before
"recovered" are upper bounds of how far the right fact got, so "never_extracted" and
"page_not_read" are firm and the later losses may hide more extraction errors.

Usage:
    .venv/bin/python scripts/kg_loss_analysis.py --manual grizzly_g0872 \\
        --run campaign/grizzly_g0872/runs/v3_r1 --kpi campaign/results/kpi_F.json --system v3_r1 \\
        --out experiments/kg_restructure/losses/grizzly_F_r1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.kg_v3_evaluate import gold_relations, token_f1  # noqa: E402

STAGES = ("page_not_read", "never_extracted", "lost_after_extraction", "discarded_by_gate", "in_graph_untrusted",
          "in_graph_not_matched", "recovered")
LEXICAL = 0.3


def _page(segment_id: str) -> int:
    return int(segment_id.split(".", 1)[0][1:])


def _matches(relation: dict, kind: str, source: str, target: str, segments: set[str]) -> bool:
    if kind not in relation["types"]:
        return False
    if segments & relation["segments"]:
        return True
    return min(token_f1(source, relation["left"]), token_f1(target, relation["right"])) >= LEXICAL


def load_run(run: Path) -> dict:
    """Proposals, graph occurrences and excluded relations of a saved run of either pipeline, in one shape.

    A remedy the connected-graph pipeline links directly to a problem is compared with the gold
    through the same projection the scorer uses (an unnamed cause between problem and action).
    """

    graph = json.loads((run / "graph.json").read_text())
    report = json.loads((run / "report.json").read_text())
    proposals = []
    for path in sorted((run / "state").glob("extract_*.json")):
        for item in json.loads(path.read_text()).get("proposals", []):
            cites = {*item.get("cites", []), *item["source"].get("cites", []), *item["target"].get("cites", [])}
            proposals.append((item["relation_type"], item["source"]["name"], item["target"]["name"], cites))
    # Runs of the connected-graph pipeline keep what each passage yielded as mentions and facts.
    for path in sorted((run / "state").glob("records_*.json")):
        records = json.loads(path.read_text())
        mentions = {item["key"]: item for item in records.get("mentions", [])}
        for fact in records.get("facts", []):
            source, target = mentions.get(fact["source"]), mentions.get(fact["target"])
            if source and target:
                proposals.append((fact["relation"], source["name"], target["name"],
                                  set(fact.get("evidence", {}).get("segment_ids", []))))
    names = {node["id"]: node["name"] for node in graph["nodes"]}
    kept = []
    if graph.get("pipeline") == "kg-v4":
        from backend.kg_v4.scoring import historical_edges

        kept = [(edge["type"], edge["source_name"], edge["target_name"], edge["segments"], edge["trusted"])
                for edge in historical_edges(graph)]
    else:
        for edge in graph["edges"]:
            if edge.get("derived"):
                continue
            for occurrence in edge["occurrences"]:
                segments = {item["segment_id"] for item in occurrence.get("evidence", [])}
                kept.append((edge["type"], names[edge["from"]], names[edge["to"]], segments,
                             occurrence.get("tier", edge.get("tier")) == "green"))
    excluded = []
    for item in graph.get("excluded_relations", []):
        certificate = item.get("certificate", {})
        if item.get("reason"):  # connected-graph pipeline: the problem of meaning the verifier named
            gate = "meaning:" + str(item["reason"]).split(":", 1)[0]
        elif certificate.get("rejected_by"):
            gate = "reviewer_rejection"
        elif "CROSS_BRANCH_CONTAMINATION" in certificate.get("validation_issues", []):
            gate = "cross_branch_rule"
        elif certificate.get("verifier_verdict") == "not_supported":
            gate = "verifier_not_supported"
        else:
            gate = "other_rule"
        excluded.append((item["relation"], item["source"].split(":", 1)[-1], item["target"].split(":", 1)[-1],
                         set(certificate.get("segment_ids", [])), gate))
    return {"read_pages": set(report.get("read_pages") or report.get("diagnostic_pages") or []),
            "proposals": proposals, "kept": kept, "excluded": excluded}


def link_stage(relation: dict, run: dict) -> tuple[str, str]:
    """How far the best candidate of one gold link got, and the gate when one stopped it."""

    trusted = untrusted = False
    for kind, source, target, segments, is_trusted in run["kept"]:
        if _matches(relation, kind, source, target, segments):
            trusted, untrusted = trusted or is_trusted, True
    if trusted:
        return "in_graph_trusted", ""
    if untrusted:
        return "in_graph_untrusted", ""
    gates = Counter(gate for kind, source, target, segments, gate in run["excluded"]
                    if _matches(relation, kind, source, target, segments))
    if gates:
        return "discarded_by_gate", gates.most_common(1)[0][0]
    if any(_matches(relation, kind, source, target, segments) for kind, source, target, segments in run["proposals"]):
        return "lost_after_extraction", ""
    pages = {_page(segment) for segment in relation["segments"]}
    if pages and run["read_pages"] and not pages & run["read_pages"]:
        return "page_not_read", ""
    return "never_extracted", ""


def analyse(claims: list[dict], run: dict, recovered: set[str]) -> dict:
    order = {**{stage: index for index, stage in enumerate(STAGES)}, "in_graph_trusted": STAGES.index("in_graph_not_matched")}
    rows = []
    for claim in claims:
        if not claim.get("failure") and not claim.get("action"):
            continue  # an indication without cause or action is code coverage, not a chain
        stages = [link_stage(relation, run) for relation in gold_relations(claim)]
        stage, gate = min(stages, key=lambda item: order[item[0]])
        if claim["claim_id"] in recovered:
            stage, gate = "recovered", ""
        elif stage == "in_graph_trusted":
            stage = "in_graph_not_matched"
        pages = sorted({_page(segment) for relation in gold_relations(claim) for segment in relation["segments"]})
        rows.append({"claim_id": claim["claim_id"], "branch_id": claim["branch_id"], "stage": stage, "gate": gate,
                     "pages": pages, "indicator": claim["indicator"][:90], "failure": claim.get("failure", "")[:90],
                     "action": claim.get("action", "")[:90],
                     "weakest_link": ("indicator" if order[stages[0][0]] <= min(order[item[0]] for item in stages)
                                      else "action")})
    branches: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        branches[row["branch_id"]].append(row)
    index = {stage: position for position, stage in enumerate(STAGES)}
    branch_stage = {key: min((row["stage"] for row in items), key=index.__getitem__) for key, items in branches.items()}
    lost_pages = Counter(page for row in rows if row["stage"] in {"never_extracted", "page_not_read"} for page in row["pages"][:1])
    return {
        "claims": len(rows), "branches": len(branches),
        "claims_by_stage": {stage: sum(row["stage"] == stage for row in rows) for stage in STAGES},
        "branches_by_stage": {stage: sum(value == stage for value in branch_stage.values()) for stage in STAGES},
        "gates": dict(Counter(row["gate"] for row in rows if row["gate"])),
        "weakest_link_of_lost_claims": dict(Counter(row["weakest_link"] for row in rows if row["stage"] != "recovered")),
        "pages_with_unextracted_claims": dict(sorted(lost_pages.items())),
        "rows": rows,
    }


def recovered_claims(path: Path, manual: str, system: str) -> set[str]:
    """Claims a saved judgement found: a campaign KPI file, or the pilot's historical scores."""

    data = json.loads(path.read_text())
    if "manuals" in data:
        row = data["manuals"][manual]["systems"][system]
        gold = json.loads((ROOT / "campaign" / manual / "gold" / "gold.json").read_text())["claims"]
        scored = {claim["claim_id"] for claim in gold if claim.get("failure") or claim.get("action")}
        return scored - set(row["missing_claims"])
    condition, replica = system.rsplit("/r", 1)
    row = next(item for item in data["rows"] if item["manual"] == manual and item["condition"] == condition
               and str(item["replica"]) == replica)
    if row.get("recovered_claims_lower") != row.get("recovered_claims_upper"):
        raise SystemExit(f"{manual} {system}: the saved judgement is partial; its recovered claims are not determined")
    return set(row["recovered_claims_lower"])


def markdown(title: str, result: dict) -> str:
    lines = [f"### {title}", "", "| Stage | Claims | Branches |", "|---|---:|---:|"]
    for stage in STAGES:
        lines.append(f"| {stage} | {result['claims_by_stage'][stage]} | {result['branches_by_stage'][stage]} |")
    lines.append(f"| total | {result['claims']} | {result['branches']} |")
    if result["gates"]:
        lines += ["", "Gates that excluded candidates: " + ", ".join(f"{key} {value}" for key, value in result["gates"].items())]
    if result["pages_with_unextracted_claims"]:
        lines += ["", "PDF pages of claims never extracted: " + ", ".join(
            f"p{page} ({count})" for page, count in result["pages_with_unextracted_claims"].items())]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manual", required=True)
    parser.add_argument("--run", required=True, help="saved run directory with state/, graph.json and report.json")
    parser.add_argument("--kpi", required=True, help="saved judgement: a campaign kpi_*.json or the pilot historical_scores.json")
    parser.add_argument("--system", required=True, help="run name in the judgement: v3_r1, or Bsafe/r1 for the pilot")
    parser.add_argument("--out", help="write the full result as JSON")
    args = parser.parse_args()
    run_dir = Path(args.run)
    run_dir = run_dir if run_dir.is_absolute() else ROOT / run_dir
    claims = json.loads((ROOT / "campaign" / args.manual / "gold" / "gold.json").read_text())["claims"]
    result = analyse(claims, load_run(run_dir), recovered_claims(Path(args.kpi), args.manual, args.system))
    result.update(manual=args.manual, run=str(args.run), judgement=str(args.kpi), system=args.system)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    print(markdown(f"{args.manual} {args.system}", result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
