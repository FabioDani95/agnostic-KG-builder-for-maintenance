"""Evaluate V3 and v22 graphs by position and meaning instead of shared words.

1. Position: the historical gold claims are mapped to segment IDs of the manual
   (``--map-gold`` writes the mapping for review). A predicted relation is a
   candidate for a gold relation when it has a compatible type and cites the
   segments where the gold ends are written.
2. Meaning: a separate model judge decides whether candidate and gold state the
   same fact; paraphrases count, different causes, remedies or rows do not.

A gold claim is recovered when its problem -> cause relation and its cause ->
action relation are both matched through the same cause node. The old lexical
probe is reported alongside. All systems use the same gold, candidates and judge.

Usage:
    .venv/bin/python scripts/kg_v3_evaluate.py --map-gold
    .venv/bin/python scripts/kg_v3_evaluate.py --v3 paper/experiments/v3_dev_20260926/r1 \\
        --v3 paper/experiments/v3_dev_20260926/r2 --out paper/experiments/v3_dev_20260926/evaluation_v2.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.kg_v3.contracts import context_text  # noqa: E402
from scripts.kg_v3_compare import GOLD, V22, load_v3, load_v22, token_f1, words  # noqa: E402

MANIFEST = ROOT / "paper/experiments/robustness_20260925/manifest.json"
GOLD_SEGMENTS = ROOT / "paper/evaluation/gold_segments_v1"
LEDGER = ROOT / "paper/experiments/robustness_20260925/real_call_budget.jsonl"
GOLD_MANUALS = ("eastman_e554", "danfoss_apf", "graco_check_mate_200")
INDICATOR_TYPES = {"MAY_INDICATE", "INDICATES"}
MAX_CANDIDATES = 8
JUDGE_VOTES = 3
JUDGE_PROMPT = """You compare facts extracted from a maintenance manual with reference facts written by a person.
For each pair answer same when the extracted fact states the same thing as the reference: the
same problem (or code) with the same cause, or the same cause with the same remedy or check.
Different wording, extra detail or a shorter name are fine. Answer different when the problem,
the cause, the remedy, a number, a direction or a negation differs, or when it only partly
overlaps with a different meaning. When the reference says the manual names no cause, answer same
if the extracted problem is the same and the extracted cause is only a placeholder (such as
"unspecified cause of ...") rather than a specific cause the manual does not state.
When context is supplied, respect antecedents, prerequisites, prohibitions, expected outcomes
and sequence. An expected outcome is not a precondition. Extra compatible context is allowed;
contradictory context or missing required context is different.
"""


def manual_spec(manual: str) -> dict:
    return next(item for item in json.loads(MANIFEST.read_text())["manuals"] if item["manual_id"] == manual)


def load_doc(manual: str):
    from backend.kg_v3.reader import read_document
    from scripts.kg_v3 import load_evidence

    spec = manual_spec(manual)
    evidence, page_count, _ = load_evidence(ROOT / "paper/manuals/files" / spec["file_name"], spec["asset"])
    return read_document(list(evidence), page_count=page_count), list(evidence)


def _cells(segment) -> list[str]:
    return segment.text.split(" | ") if segment.table else [segment.text]


def containment(text: str, segment_text: str) -> float:
    """Share of the reference words found in the segment, with a small wording tie-break."""

    reference = set(words(text))
    if not reference:
        return 0.0
    return len(reference & set(words(segment_text))) / len(reference) + 0.01 * token_f1(text, segment_text)


def best_segments(doc, pages: list[int], text: str) -> tuple[list[str], float]:
    scored = sorted(((max(containment(text, cell) for cell in _cells(segment)), segment.segment_id)
                     for page in pages for segment in doc.pages.get(page, [])), reverse=True)
    if not scored or scored[0][0] < 0.5:
        return [], round(scored[0][0], 3) if scored else 0.0
    top = scored[0][0]
    return [segment_id for score, segment_id in scored if score >= top - 0.02][:2], round(top, 3)


def best_row(doc, pages: list[int], fields: list[str]) -> tuple[str, float] | None:
    """The single table row that holds all fields of a claim together."""

    rows = [segment for page in pages for segment in doc.pages.get(page, []) if segment.table]
    scored = sorted(((sum(containment(field, segment.text) for field in fields) / len(fields), segment.segment_id)
                     for segment in rows), reverse=True)
    return (scored[0][1], round(scored[0][0], 3)) if scored and scored[0][0] >= 0.6 else None


def map_gold() -> None:
    GOLD_SEGMENTS.mkdir(parents=True, exist_ok=True)
    gold = {item["manual_id"]: item["expected_claims"] for item in json.loads(GOLD.read_text())["manuals"]}
    for manual in GOLD_MANUALS:
        doc, _ = load_doc(manual)
        claims = []
        for claim in gold[manual]:
            pages = list(claim["pages"])
            action = claim.get("corrective_action") or claim.get("inspection_step") or ""
            entry = {"claim_id": claim["claim_id"], "pages": pages, "indicator": claim["symptom"],
                     "code": claim.get("error_code") or "", "failure": claim["failure_mode"], "action": action,
                     "action_kind": "inspection" if claim.get("inspection_step") else ("repair" if action else "")}
            fields = [value for value in (entry["indicator"], entry["failure"], entry["action"]) if value]
            row = best_row(doc, pages, fields)
            for field in ("indicator", "failure", "action"):
                if not entry[field]:
                    continue
                if row:
                    entry[f"{field}_segments"], entry[f"{field}_score"] = [row[0]], row[1]
                else:
                    entry[f"{field}_segments"], entry[f"{field}_score"] = best_segments(doc, pages, entry[field])
            claims.append(entry)
        payload = {
            "manual_id": manual, "status": "agent_mapped_from_historical_gold",
            "note": "Segment IDs located automatically from the historical gold text; a technician must confirm.",
            "claims": claims,
        }
        (GOLD_SEGMENTS / f"{manual}.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
        for item in claims:
            print(manual, item["claim_id"], item.get("indicator_segments"), item.get("failure_segments"),
                  item.get("action_segments"), item.get("failure_score"), item.get("action_score"))


def _locator_index(evidence) -> dict:
    index = {}
    for unit in evidence:
        locator = unit.locator
        if locator.table_index is not None and locator.row_index is not None:
            index[(locator.page, "t", locator.table_index, locator.row_index)] = unit.evidence_id
        elif locator.block_index is not None:
            index[(locator.page, "b", locator.block_index)] = unit.evidence_id
    return index


def v22_edges(manual: str, doc, evidence) -> list[dict]:
    """v22 relations of the frozen C12 graphs, located on the segments V3 uses."""

    return v22_edges_from(V22 / f"c12r1_{manual}" / "graph.json", doc, evidence)


def v22_edges_from(path: Path, doc, evidence) -> list[dict]:
    """v22 relations of any revision file, located on the same segments V3 uses."""

    data = json.loads(Path(path).read_text())
    names = {node["node_id"]: node["label"] for node in data["nodes"]}
    by_evidence = defaultdict(list)
    for segment in doc.segments():
        by_evidence[segment.evidence_id].append(segment)
    index = _locator_index(evidence)
    edges = []
    for relation in data["relations"]:
        segments = set()
        for ref in relation.get("evidence_refs") or []:
            locator = ref["locator"]
            key = ((locator["page"], "t", locator.get("table_index"), locator.get("row_index"))
                   if locator.get("row_index") else (locator["page"], "b", locator.get("block_index")))
            candidates = by_evidence.get(index.get(key, ""), [])
            quote = ref.get("quote") or ""
            if not candidates or not any(token_f1(quote, item.text) > 0.3 or quote in item.text for item in candidates):
                candidates = [item for item in doc.pages.get(locator["page"], [])
                              if quote and (quote in item.text or token_f1(quote, item.text) >= 0.6)]
            segments.update(item.segment_id for item in candidates)
        edges.append({"type": relation["relation_type"], "source": relation["from_id"], "target": relation["to_id"],
                      "source_name": names.get(relation["from_id"], ""), "target_name": names.get(relation["to_id"], ""),
                      "segments": segments, "trusted": True})
    return edges


def v3_edges(run: Path) -> list[dict]:
    data = json.loads((run / "graph.json").read_text())
    names = {node["id"]: node["name"] for node in data["nodes"]}
    stated = {node["id"]: node.get("stated_in_source", True) for node in data["nodes"]}
    edges = []
    for edge in data["edges"]:
        if edge.get("derived"):
            continue
        segments = {item["segment_id"] for occurrence in edge["occurrences"] for item in occurrence["evidence"]}
        edges.append({"type": edge["type"], "source": edge["from"], "target": edge["to"],
                      "source_name": names[edge["from"]], "target_name": names[edge["to"]],
                      "source_stated": stated[edge["from"]], "target_stated": stated[edge["to"]],
                      "conditions": edge.get('conditions', []),
                      "segments": segments, "trusted": edge["trusted"]})
    return edges


def gold_relations(claim: dict) -> list[dict]:
    relations = [{"kind": "indicator", "types": INDICATOR_TYPES, "left": claim["indicator"], "right": claim["failure"],
                  "segments": set(claim.get("indicator_segments", []) + claim.get("failure_segments", [])),
                  "conditions": claim.get('conditions', '')}]
    if claim.get("action"):
        relations.append({"kind": "action", "types": {"RESOLVED_BY"}, "left": claim["failure"],
                          "right": claim["action"],
                          "conditions": claim.get('conditions', ''),
                          "segments": set(claim.get("failure_segments", []) + claim.get("action_segments", []))})
    return relations


def candidates(relation: dict, edges: list[dict]) -> list[int]:
    scored = []
    for index, edge in enumerate(edges):
        if edge["type"] not in relation["types"] or not edge["trusted"]:
            continue
        positional = bool(edge["segments"] & relation["segments"])
        lexical = min(token_f1(edge["source_name"], relation["left"]), token_f1(edge["target_name"], relation["right"]))
        if positional or lexical >= 0.3:
            scored.append((positional, lexical, index))
    scored.sort(reverse=True)
    return [index for _, _, index in scored[:MAX_CANDIDATES]]


def pair_line(pair_id: str, relation: dict, group: list[dict]) -> str:
    """One reference fact and the extracted fact it is compared with.

    Where the manual names no cause (the reference) and the system marks its cause
    as not written in the manual, the extracted cause is shown unnamed too: the
    pair is then judged on the problem and the remedy. A cause the system presents
    as written in the manual keeps its name and is judged as such.
    """

    context = f" Reference context: {relation['conditions']}." if relation.get('conditions') else ''
    if relation["kind"] == "indicator":
        edge = group[0]
        cause = f"the cause '{relation['right']}'" if relation["right"] else "a cause the manual does not name"
        extracted = ("a cause the manual does not name" if not relation["right"] and not edge.get("target_stated", True)
                     else f"'{edge['target_name']}'")
        return (f"{pair_id}: reference '{relation['left']}' may indicate {cause} | "
                f"extracted '{edge['source_name']}' may indicate {extracted}" +
                (f". Extracted context: {context_text(edge['conditions'])}." if edge.get('conditions') else '') + context)
    remedies = "; ".join(f"'{edge['target_name']}' ({context_text(edge.get('conditions', []))})" for edge in group)
    reference_cause = relation["left"] or "(not named in the manual)"
    extracted_cause = ("(not named in the manual)" if not relation["left"] and not group[0].get("source_stated", True)
                       else group[0]["source_name"])
    return (f"{pair_id}: reference cause {reference_cause!r} is resolved or checked by "
            f"'{relation['right']}' | extracted cause {extracted_cause!r} is resolved or "
            f"checked by these steps together: {remedies}.{context}")


async def judge(llm, pairs: list[tuple[dict, list[dict]]]) -> list[bool]:
    """One verdict per pair; a pair holds one extracted relation or all remedies of one cause."""

    verdicts: list[bool] = []
    for start in range(0, len(pairs), 40):
        batch = pairs[start:start + 40]
        ids = [f"P{index}" for index in range(1, len(batch) + 1)]
        lines = [pair_line(pair_id, relation, group) for pair_id, (relation, group) in zip(ids, batch)]
        schema = {"type": "object", "additionalProperties": False, "required": ["answers"], "properties": {
            "answers": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                                   "required": ["id", "answer"], "properties": {
                                                       "id": {"type": "string", "enum": ids},
                                                       "answer": {"type": "string", "enum": ["same", "different"]}}}}}}
        # Three independent votes, majority wins: one judge call is not stable enough.
        votes = await asyncio.gather(*(
            llm.json(system=JUDGE_PROMPT, user="\n".join(lines), schema=schema, name="kg_v3_eval_judge",
                     max_output_tokens=4000) for _ in range(JUDGE_VOTES)))
        counts: dict[str, int] = defaultdict(int)
        for data in votes:
            for item in data.get("answers") or []:
                counts[item["id"]] += item["answer"] == "same"
        verdicts.extend(counts[pair_id] * 2 > JUDGE_VOTES for pair_id in ids)
    return verdicts


async def score_system(llm, claims: list[dict], edges: list[dict]) -> dict:
    pairs, keys = [], []
    for claim in claims:
        for relation in gold_relations(claim):
            found = candidates(relation, edges)
            if relation["kind"] == "indicator":
                groups = [[index] for index in found]
            else:  # every remedy of the same cause is judged together
                by_cause: dict[str, list[int]] = defaultdict(list)
                for index in found:
                    by_cause[edges[index]["source"]].append(index)
                groups = [sorted({i for i, edge in enumerate(edges) if edge["type"] == "RESOLVED_BY"
                                  and edge["trusted"] and edge["source"] == cause}) for cause in by_cause]
            for group in groups:
                pairs.append((relation, [edges[index] for index in group]))
                keys.append((claim["claim_id"], relation["kind"], group))
    verdicts = await judge(llm, pairs) if pairs else []
    same = defaultdict(set)
    positional = defaultdict(set)
    for (claim_id, kind, group), verdict, (relation, group_edges) in zip(keys, verdicts, pairs):
        if verdict:
            same[(claim_id, kind)].update(group)
        positional[(claim_id, kind)].update(
            index for index, edge in zip(group, group_edges) if edge["segments"] & relation["segments"])

    def recovered(claim, table) -> bool:
        causes = {edges[index]["target"] for index in table[(claim["claim_id"], "indicator")]}
        if not claim.get("action"):
            return bool(causes)
        return any(edges[index]["source"] in causes for index in table[(claim["claim_id"], "action")])

    matched = [(relation, edge) for (_, _, group), verdict, (relation, group_edges) in zip(keys, verdicts, pairs)
               if verdict for edge in group_edges]
    return {
        "judged_pairs": len(pairs),
        # Of the relations judged right, the share citing where the gold says the fact is written.
        "evidence_on_gold_segments": round(sum(bool(edge["segments"] & relation["segments"])
                                               for relation, edge in matched) / len(matched), 3) if matched else None,
        "recovered_meaning": sorted(claim["claim_id"] for claim in claims if recovered(claim, same)),
        "recovered_position_only": sorted(claim["claim_id"] for claim in claims if recovered(claim, positional)),
    }


async def evaluate(v3_runs: list[Path]) -> list[dict]:
    from backend.kg_v3.llm import ModelClient

    llm = ModelClient(model="gpt-6-luna", reasoning_effort="low")
    gold = {item["manual_id"]: item["expected_claims"] for item in json.loads(GOLD.read_text())["manuals"]}
    rows = []
    for manual in GOLD_MANUALS:
        claims = [claim for claim in json.loads((GOLD_SEGMENTS / f"{manual}.json").read_text())["claims"]
                  if not claim.get("excluded")]
        doc, evidence = load_doc(manual)
        systems = {"v22": (v22_edges(manual, doc, evidence), load_v22(manual))}
        for run in v3_runs:
            graph, _ = load_v3(run / manual)
            systems[f"v3_{run.name}"] = (v3_edges(run / manual), graph)
        row = {"manual": manual, "claims": len(claims), "systems": {}}
        for name, (edges, lexical_graph) in systems.items():
            result = await score_system(llm, claims, edges)
            result["recovered_lexical"] = sorted(
                item["claim_id"] for item in gold[manual]
                if item["claim_id"] in {claim["claim_id"] for claim in claims}
                and lexical_graph.recovered(item, trusted_only=name != "v22"))
            row["systems"][name] = result
        rows.append(row)
    rows.append({"judge_usage": llm.usage.as_dict()})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--map-gold", action="store_true")
    parser.add_argument("--v3", action="append", default=[])
    parser.add_argument("--out")
    parser.add_argument("--budget", default="20")
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.map_gold:
        map_gold()
        return 0
    os.environ.update({"KG_LLM_MODE": "real", "KG_REAL_CALL_BUDGET_LEDGER": str(LEDGER),
                       "KG_REAL_CALL_BUDGET_USD": args.budget, "KG_REAL_CALL_RUN_ID": "v3eval_judge",
                       "KG_REAL_CALL_PDF_ID": "evaluation", "KG_LLM_TRACE_DIR": str(ROOT / "eval_runs/v3_eval/provider")})
    rows = asyncio.run(evaluate([Path(item).resolve() for item in args.v3]))
    Path(args.out).write_text(json.dumps(rows, indent=1) + "\n")
    for row in rows[:-1]:
        print(row["manual"], row["claims"])
        for name, result in row["systems"].items():
            print(f"  {name:10s} lexical {len(result['recovered_lexical']):2d}  position {len(result['recovered_position_only']):2d}"
                  f"  meaning {len(result['recovered_meaning']):2d}  missing(meaning) "
                  f"{sorted(set(c['claim_id'] for c in json.loads((GOLD_SEGMENTS / (row['manual'] + '.json')).read_text())['claims']) - set(result['recovered_meaning']))}")
    print(rows[-1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
