"""Rebuild a saved V3 graph with the back half of the connected-graph pipeline. No model call.

What it answers: with exactly what V3 already extracted from a manual, how much of the
island problem do the new rules alone remove? The saved graph is read as mentions and facts,
then assembled by backend/kg_v4:

* names equal in canonical form (plural, article, number word) become one node, and false
  friends stay apart;
* a placeholder cause ("Unspecified cause of ...") is replaced by a direct link from the
  problem to its remedy;
* an item whose own name names a component is linked to it (marked ``name_mention``);
* with ``--keep-excluded``, relations V3 had excluded are kept with low confidence instead of
  being dropped, to show how much the gates removed.

The result is an estimate on old extractions: it has no survey, no catalogue, no descriptions,
no gap search and no new verification. It is not a run of the new pipeline and its numbers
must not be reported as such.

Usage:
    .venv/bin/python scripts/kg_rebuild_from_v3.py --manual grizzly_g0872 \\
        --run campaign/grizzly_g0872/runs/v3_r1 --out experiments/my_rebuild/grizzly
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.kg_v3.contracts import ContextItem  # noqa: E402
from backend.kg_v4.model import Evidence, Fact, Mention  # noqa: E402

PLACEHOLDER = "unspecified cause of"
DIRECT = {"Symptom": "ADDRESSED_BY", "ErrorCode": "CLEARED_BY"}
VERDICT = {"green": "supported", "yellow": "unclear"}


def convert(graph: dict, doc, sections, *, keep_excluded: bool) -> tuple[list[Mention], list[Fact], dict]:
    """Mentions and facts of a saved graph; placeholder causes become direct links."""

    def evidence(segment_ids: list[str]) -> Evidence:
        known = [cite for cite in segment_ids if doc.segment(cite)]
        if known:
            page = doc.segment(known[0]).page
            return Evidence(page=page, section=sections.section(known[0], page), segment_ids=known, anchor="cited")
        return Evidence(page=1, anchor="unit")

    nodes = {node["id"]: node for node in graph["nodes"] if node["type"] != "Asset"}
    placeholders = {key for key, node in nodes.items()
                    if node["type"] == "FailureMode" and node["name"].casefold().startswith(PLACEHOLDER)}
    mentions: dict[str, Mention] = {}
    by_name: dict[tuple[str, str], str] = {}

    def mention(node: dict) -> Mention:
        if node["id"] not in mentions:
            properties = node.get("properties", {})
            mentions[node["id"]] = Mention(
                key=node["id"], type=node["type"], name=node["name"], code=str(properties.get("code") or ""),
                kind=str(properties.get("action_kind") or ""), stated=node.get("stated_in_source", True),
                evidence=evidence([item["segment_id"] for item in node.get("evidence", [])]), unit_id="v3")
            by_name[(node["type"], node["name"])] = node["id"]
        return mentions[node["id"]]

    facts: list[Fact] = []
    incoming: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    outgoing: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    stats = {"placeholder_causes_removed": len(placeholders), "direct_links": 0, "excluded_kept": 0}

    def add(relation: str, source: str, target: str, occurrence: dict, number: int, verdict: str) -> None:
        cites = [item["segment_id"] for item in occurrence.get("evidence", [])] or occurrence.get("segment_ids", [])
        conditions = []
        for item in occurrence.get("conditions", []):
            try:
                conditions.append(ContextItem.model_validate({key: item[key] for key in ("kind", "text") if key in item}))
            except (ValueError, TypeError, KeyError):
                continue
        facts.append(Fact(fact_id=f"v3/{relation}/{source}/{target}/{number}", relation=relation, source=source,
                          target=target, record=str(occurrence.get("record") or "v3"), conditions=conditions,
                          evidence=evidence(cites), origin="import", verdict=verdict))

    for edge in graph["edges"]:
        if edge.get("derived") or edge["from"] not in nodes or edge["to"] not in nodes:
            continue
        for number, occurrence in enumerate(edge["occurrences"]):
            verdict = VERDICT.get(occurrence.get("tier", edge.get("tier")), "unclear")
            if edge["to"] in placeholders:
                incoming[edge["to"]].append((edge, occurrence))
            elif edge["from"] in placeholders:
                outgoing[edge["from"]].append((edge, occurrence))
            else:
                add(edge["type"], mention(nodes[edge["from"]]).key, mention(nodes[edge["to"]]).key, occurrence,
                    number, verdict)
    for placeholder in sorted(placeholders):
        for number, (problem_edge, _) in enumerate(incoming[placeholder]):
            problem = nodes[problem_edge["from"]]
            for position, (action_edge, occurrence) in enumerate(outgoing[placeholder]):
                target = nodes[action_edge["to"]]
                if problem["type"] not in DIRECT or target["type"] != "CorrectiveAction":
                    continue
                verdict = VERDICT.get(occurrence.get("tier", action_edge.get("tier")), "unclear")
                add(DIRECT[problem["type"]], mention(problem).key, mention(target).key, occurrence,
                    number * 1000 + position, verdict)
                stats["direct_links"] += 1
    # Without --keep-excluded the relations V3 excluded stay out, as in the graph it exported.
    for number, item in enumerate(graph.get("excluded_relations", []) if keep_excluded else []):
        ends = []
        for key in ("source", "target"):
            kind, _, name = item[key].partition(":")
            if (kind, name) not in by_name:
                node = {"id": f"v3x/{kind}/{name}", "type": kind, "name": name, "properties": {},
                        "evidence": [{"segment_id": cite} for cite in item.get("certificate", {}).get("segment_ids", [])]}
                if kind == "FailureMode" and name.casefold().startswith(PLACEHOLDER):
                    ends = []
                    break
                mention(node)
            ends.append(by_name[(kind, name)])
        if len(ends) == 2:
            stats["excluded_kept"] += 1
            add(item["relation"], ends[0], ends[1], {"segment_ids": item.get("certificate", {}).get("segment_ids", [])},
                number, "unclear")
    return list(mentions.values()), facts, stats


def rebuild(manual: str, run: Path, *, keep_excluded: bool = False, pdf: Path | None = None) -> dict:
    from backend.kg_v3.ontology import load_ontology
    from backend.kg_v4.export import graph_counts, graph_json
    from backend.kg_v4.gaps import find_gaps, link_named_parts
    from backend.kg_v4.metrics import scorecard
    from backend.kg_v4.resolve import assemble, candidates
    from backend.kg_v4.survey import machine_words
    from scripts.kg_build import read
    from scripts.kg_v3 import manual_source

    source = json.loads((run / "graph.json").read_text())
    if pdf is None:
        pdf, asset = manual_source(manual)
    else:
        asset = dict(source["nodes"][0].get("properties", {}), name=source["nodes"][0]["name"])
    doc, sections, _ = read(pdf, asset)
    mentions, facts, stats = convert(source, doc, sections, keep_excluded=keep_excluded)
    graph, _ = assemble(mentions, facts)
    named = link_named_parts(graph, mentions, machine_words(asset))
    graph, _ = assemble(mentions, [*facts, *named])
    ask, apart = candidates(mentions)
    report = {"pipeline": "kg-v4", "status": "rebuilt", "rebuilt_from": str(run), "keep_excluded": keep_excluded,
              "note": "V3 extraction assembled by the kg_v4 rules without a model; not a kg_v4 run",
              "conversion": {**stats, "name_mention_links": len(named), "close_names_left_to_a_model": len(ask),
                             "false_friends_kept_apart": len(apart), "merged_nodes": len(graph.merges)},
              "open_gaps": {kind: sum(gap.kind == kind for gap in find_gaps(graph))
                            for kind in ("cause_without_remedy", "problem_without_diagnosis", "cause_without_problem")}}
    document = graph_json(graph, doc, asset=asset, source_title=source.get("source_title", pdf.name),
                          status="rebuilt", report=report, spec=load_ontology(full=True))
    report["graph"] = graph_counts(document)
    report["scorecard"] = {key: value for key, value in scorecard(document).items() if key != "cost"}
    report["before"] = {key: value for key, value in scorecard(source).items() if key != "cost"}
    document["report"] = report
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manual", required=True, help="manual ID (campaign/<id>) or a label when --pdf is given")
    parser.add_argument("--run", required=True, help="saved V3 run directory with graph.json")
    parser.add_argument("--pdf", help="the manual's PDF, when it is not a campaign manual")
    parser.add_argument("--keep-excluded", action="store_true",
                        help="keep the relations V3 excluded, with low confidence")
    parser.add_argument("--out", required=True, help="directory for the rebuilt graph.json")
    args = parser.parse_args()
    run = Path(args.run)
    run = run if run.is_absolute() else ROOT / run
    document = rebuild(args.manual, run, keep_excluded=args.keep_excluded, pdf=Path(args.pdf) if args.pdf else None)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(json.dumps(document, ensure_ascii=False) + "\n")
    before, after = document["report"]["before"]["connectivity"], document["report"]["scorecard"]["connectivity"]
    keys = ("nodes", "edges", "components", "largest_component_share", "causes_with_action_share",
            "causes_reachable_share", "entries_with_complete_chain_share")
    print(json.dumps({"manual": args.manual, "conversion": document["report"]["conversion"],
                      "before": {key: before[key] for key in keys}, "after": {key: after[key] for key in keys},
                      "after_extracted_only": after["variants"]["extracted_only"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
