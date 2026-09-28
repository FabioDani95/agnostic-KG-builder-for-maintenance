"""Scoring of a graph against a campaign gold: position candidates and a meaning judge.

Used by scripts/kg_v3_kpi.py. A gold relation (problem -> cause, cause -> action)
is matched to trusted extracted relations cited on the same segments or with
similar names; an LLM judge with three votes decides whether they state the same
fact. v22 graphs saved in the campaign can be scored with the same rules.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections import defaultdict
from pathlib import Path

from backend.kg_v3.contracts import context_text

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
contradictory context is different. The reference context is the annotator's note for the whole
branch and may concern only one of its steps: do not require it on every extracted step, answer
different only when the extracted fact contradicts it. Extracted section notes apply to a whole
table or procedure: they are compatible extra context, never a condition of the step.
A prohibition represented as a typed [warning] on an action can match the same prohibition
represented as a separate reference action, provided its cause, scope and polarity agree.
Never match an affirmative command to a prohibition. Never borrow a remedy or context from
another entry. Extracted occurrences are alternatives: do not conjoin their conditions or
use a condition on one occurrence to repair a missing condition on another. When the
reference action itself states its condition (for example "if the problem persists, contact
service"), the extracted action must carry that condition in its own step context. Only steps in
the same source record can jointly express a reference action.
"""


def _locator_index(evidence) -> dict:
    index = {}
    for unit in evidence:
        locator = unit.locator
        if locator.table_index is not None and locator.row_index is not None:
            index[(locator.page, "t", locator.table_index, locator.row_index)] = unit.evidence_id
        elif locator.block_index is not None:
            index[(locator.page, "b", locator.block_index)] = unit.evidence_id
    return index


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
        for occurrence in edge["occurrences"]:
            segments = {item["segment_id"] for item in occurrence["evidence"]}
            edges.append({"type": edge["type"], "source": edge["from"], "target": edge["to"],
                          "source_name": names[edge["from"]], "target_name": names[edge["to"]],
                          "source_stated": stated[edge["from"]], "target_stated": stated[edge["to"]],
                          "conditions": occurrence.get('conditions', edge.get('conditions', [])),
                          "record": occurrence.get('record', ''),
                          "segments": segments,
                          "trusted": occurrence.get('tier', edge.get('tier')) == 'green'})
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
        lexical = min(token_f1(edge["source_name"], relation["left"]),
                      token_f1(edge["target_name"] + " " + context_text(edge.get("conditions", [])), relation["right"]))
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

    raw_context = relation.get('conditions') or []
    context = (f" Reference branch context: "
               f"{context_text([raw_context] if isinstance(raw_context, str) else raw_context) or '(none)'}.")
    location = f" Reference segments: {', '.join(sorted(relation.get('segments', [])))}."
    context += location
    if relation["kind"] == "indicator":
        edge = group[0]
        cause = f"the cause '{relation['right']}'" if relation["right"] else "a cause the manual does not name"
        extracted = ("a cause the manual does not name" if not relation["right"] and not edge.get("target_stated", True)
                     else f"'{edge['target_name']}'")
        return (f"{pair_id}: reference '{relation['left']}' may indicate {cause} | "
                f"extracted '{edge['source_name']}' may indicate {extracted}" +
                (f". Extracted context: {context_text(edge.get('conditions', []), scope='relation') or '(none)'}. "
                 f"Extracted segments: {', '.join(sorted(edge.get('segments', [])))}.") + context)
    remedies = "; ".join(f"'{edge['target_name']}' (step context: "
                         f"{context_text(edge.get('conditions', []), scope='relation') or '(none)'}; "
                         f"section notes: {context_text(edge.get('conditions', []), scope='section') or '(none)'}; "
                         f"source record: {edge.get('record', '')}; segments: {', '.join(sorted(edge.get('segments', [])))})"
                         for edge in group)
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
            else:  # Only remedies on the same source occurrence can form a compound action.
                by_cause: dict[str, list[int]] = defaultdict(list)
                for index in found:
                    by_cause[(edges[index]["source"], edges[index].get("record", ""))].append(index)
                groups = [sorted({i for i, edge in enumerate(edges) if edge["type"] == "RESOLVED_BY"
                                  and edge["trusted"] and (edge["source"], edge.get("record", "")) == cause}) for cause in by_cause]
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

    witnesses = {}
    for claim in claims:
        cid = claim["claim_id"]
        causes = {edges[i]["target"] for i in same[(cid, "indicator")]}
        if claim.get("action"):
            causes &= {edges[i]["source"] for i in same[(cid, "action")]}
        witnesses[cid] = {"FailureMode": sorted(causes), "Symptom": sorted({
            edges[i]["source"] for i in same[(cid, "indicator")] if edges[i]["target"] in causes})}

    matched = [(relation, edge) for (_, _, group), verdict, (relation, group_edges) in zip(keys, verdicts, pairs)
               if verdict for edge in group_edges]
    return {
        "judged_pairs": len(pairs),
        "matched_nodes_with_own_actions": witnesses,
        # Of the relations judged right, the share citing where the gold says the fact is written.
        "evidence_on_gold_segments": round(sum(bool(edge["segments"] & relation["segments"])
                                               for relation, edge in matched) / len(matched), 3) if matched else None,
        "recovered_meaning": sorted(claim["claim_id"] for claim in claims if recovered(claim, same)),
        "recovered_position_only": sorted(claim["claim_id"] for claim in claims if recovered(claim, positional)),
    }
