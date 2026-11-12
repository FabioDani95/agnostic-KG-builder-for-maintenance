"""Stage 4, resolve: one node for each real thing of the manual, with its aliases and provenance.

Two levels. Names equal in canonical form (case, articles, plurals, number words) are the same
entity; this joins the same part, symptom or action written in different sections. Names that
are only close are proposed to a model that sees how the manual describes and uses each of them.
A pair that differs by a number, an axis, a side, an opposite or a negation is never merged,
whatever its similarity: such false friends are kept apart and listed.

Identity is global to the manual. The branch a fact belongs to stays on the fact (its record), so
a consumer can still walk one source entry at a time.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any

from pydantic import BaseModel, Field

from backend.kg_v4.model import CatalogueEntry, Edge, Evidence, Fact, Graph, Mention, Node
from backend.kg_v4.names import canonical, code_key, contrast, distinguishing_difference, similarity, tokens
from backend.kg_v4.prompts import RESOLVE_PROMPT
from backend.kg_v4.sections import SectionIndex
from backend.kg_v4.verify import statement

logger = logging.getLogger(__name__)

CANDIDATE_SIMILARITY = 0.78
MAX_JUDGED_PAIRS = 400
JUDGE_BATCH = 12
JUDGE_CONCURRENCY = 6
MAX_NODE_EVIDENCE = 8
_CODE_LABEL = re.compile(r"^(?:alarm|error|err|code|fault|warning|no\.?|number)\s*[:#]?\s*", re.I)
STRUCTURE_RELATIONS = {"PART_OF"}


class Pair(BaseModel):
    left: str
    right: str
    type: str
    left_name: str
    right_name: str
    note: str = ""
    reason: str = ""


class Resolution(BaseModel):
    """Decisions about close names; kept so that a resumed or extended run asks nothing twice."""

    same: list[Pair] = Field(default_factory=list)
    different: list[Pair] = Field(default_factory=list)
    unjudged: list[Pair] = Field(default_factory=list)

    def decided(self) -> set[frozenset[str]]:
        return {frozenset((pair.left, pair.right)) for pair in (*self.same, *self.different)}


def identity(mention: Mention) -> str:
    if mention.type == "ErrorCode" and mention.code:
        return f"ErrorCode|code:{code_key(_CODE_LABEL.sub('', mention.code))}"
    return f"{mention.type}|{canonical(mention.name)}"


def catalogue_mentions(catalogue: list[CatalogueEntry], sections: SectionIndex | None = None) -> tuple[list[Mention], list[Fact]]:
    """The catalogue as mentions and hierarchy facts, so that it resolves with everything else."""

    mentions: list[Mention] = []
    facts: list[Fact] = []
    keys: dict[str, str] = {}
    for entry in catalogue:
        page = entry.pages[0] if entry.pages else 1
        evidence = Evidence(page=page, section=sections.section(page=page) if sections else "", anchor="unit")
        attributes = {key: value for key, value in (("category", entry.category), ("part_number", entry.part_number))
                      if value}
        base = f"catalogue/{entry.type}/{code_key(entry.code) or canonical(entry.name)}/{canonical(entry.name)}"
        for position, name in enumerate([entry.name, *entry.aliases]):
            mention = Mention(key=f"{base}/{position}", type=entry.type, name=name, code=entry.code,
                              description=entry.description if position == 0 else "", attributes=attributes,
                              evidence=evidence, unit_id="catalogue")
            mentions.append(mention)
        keys[canonical(entry.name)] = f"{base}/0"
    for entry in catalogue:
        child, parent = keys.get(canonical(entry.name)), keys.get(canonical(entry.part_of))
        if entry.type == "Component" and entry.part_of and child and parent and child != parent:
            source = next(item for item in mentions if item.key == child)
            facts.append(Fact(fact_id=f"catalogue/part_of/{canonical(entry.name)}", relation="PART_OF", source=child,
                              target=parent, record="catalogue", evidence=source.evidence, origin="catalogue"))
    return mentions, facts


def _groups(mentions: list[Mention]) -> dict[str, list[Mention]]:
    groups: dict[str, list[Mention]] = defaultdict(list)
    for mention in mentions:
        groups[identity(mention)].append(mention)
    return groups


def _display(items: list[Mention]) -> str:
    names = Counter(item.name for item in items)
    return sorted(names, key=lambda value: (-names[value], len(value), value))[0]


def candidates(mentions: list[Mention], known: Resolution | None = None) -> tuple[list[Pair], list[Pair]]:
    """Close names to ask about, most similar first, and the false friends kept apart without asking."""

    decided = known.decided() if known else set()
    groups = _groups(mentions)
    by_type: dict[str, list[str]] = defaultdict(list)
    for key, items in groups.items():
        by_type[items[0].type].append(key)
    ask: list[tuple[float, Pair]] = []
    apart: list[Pair] = []
    for kind, keys in by_type.items():
        names = {key: _display(groups[key]) for key in keys}
        words = {key: set(tokens(names[key])) for key in keys}
        for left, right in combinations(sorted(keys), 2):
            a, b = words[left], words[right]
            if not a & b:
                continue
            score = similarity(names[left], names[right])
            short, long_ = sorted((a, b), key=len)
            contained = short < long_ and len(long_) - len(short) <= 2
            if score < CANDIDATE_SIMILARITY and not contained:
                continue
            pair = Pair(left=left, right=right, type=kind, left_name=names[left], right_name=names[right])
            difference = distinguishing_difference(names[left], names[right])
            if kind == "ErrorCode" and "|code:" in left and "|code:" in right:
                difference = difference or "different codes"
            if difference:
                apart.append(pair.model_copy(update={"reason": difference}))
            elif frozenset((left, right)) not in decided:
                ask.append((score, pair.model_copy(update={"note": contrast(names[left], names[right])})))
    ask.sort(key=lambda item: (-item[0], item[1].left, item[1].right))
    return [pair for _, pair in ask], apart


def _context(key: str, groups: dict[str, list[Mention]], facts: list[Fact], by_key: dict[str, Mention]) -> str:
    items = groups[key]
    description = max((item.description for item in items), key=len, default="")
    detail = max((item.attributes.get("instruction_text", "") for item in items), key=len, default="")
    places = sorted({(item.evidence.page, item.evidence.section) for item in items})[:3]
    where = "; ".join(f"p.{page}" + (f" {section}" if section else "") for page, section in places)
    keys = {item.key for item in items}
    used = [statement(fact, by_key) for fact in facts
            if (fact.source in keys or fact.target in keys) and fact.source in by_key and fact.target in by_key][:4]
    lines = [f"written at: {where}"]
    if description:
        lines.append(f"description: {description[:300]}")
    if detail:
        lines.append(f"steps: {detail[:300]}")
    lines.extend(f"fact: {text[:260]}" for text in used)
    return "\n   ".join(lines)


async def judge(llm, mentions: list[Mention], facts: list[Fact], known: Resolution | None = None, *,
                max_pairs: int = MAX_JUDGED_PAIRS) -> tuple[Resolution, list[Pair]]:
    """Ask the model about the close names not yet decided. Without a model nothing more is merged."""

    resolution = known.model_copy(deep=True) if known else Resolution()
    ask, apart = candidates(mentions, resolution)
    resolution.unjudged = ask[max_pairs:]
    ask = ask[:max_pairs]
    if llm is None or not ask:
        resolution.unjudged = [*ask, *resolution.unjudged] if llm is None else resolution.unjudged
        return resolution, apart
    groups = _groups(mentions)
    by_key = {mention.key: mention for mention in mentions}
    limit = asyncio.Semaphore(JUDGE_CONCURRENCY)

    async def one(batch: list[Pair]) -> None:
        ids = [f"M{index}" for index in range(1, len(batch) + 1)]
        sides = list(dict.fromkeys(key for pair in batch for key in (pair.left, pair.right)))
        labels = {key: f"N{index}" for index, key in enumerate(sides, start=1)}
        names = {**{pair.left: pair.left_name for pair in batch}, **{pair.right: pair.right_name for pair in batch}}
        text = ("Names:\n" + "\n".join(
            f"{labels[key]} [{key.split('|', 1)[0]}] '{names[key]}'\n   {_context(key, groups, facts, by_key)}"
            for key in sides) + "\n\nPairs:\n" + "\n".join(
            f"{pair_id}: {labels[pair.left]} '{pair.left_name}' vs {labels[pair.right]} '{pair.right_name}'"
            + (f" (contrast: {pair.note})" if pair.note else "") for pair_id, pair in zip(ids, batch)))
        schema = {"type": "object", "additionalProperties": False, "required": ["answers"], "properties": {
            "answers": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["id", "answer", "reason"],
                "properties": {"id": {"type": "string", "enum": ids},
                               "answer": {"type": "string", "enum": ["same", "different"]},
                               "reason": {"type": "string"}}}}}}
        try:
            async with limit:
                data = await llm.json(system=RESOLVE_PROMPT, user=text, schema=schema, name="kg_v4_resolve",
                                      max_output_tokens=4000)
            answers = {str(item.get("id")): item for item in data.get("answers") or []}
        except Exception as exc:
            logger.warning("Entity resolution batch failed: %s", exc)
            answers = {}
        for pair_id, pair in zip(ids, batch):
            answer = answers.get(pair_id)
            if answer is None:
                resolution.unjudged.append(pair)
                continue
            pair.reason = " ".join(str(answer.get("reason") or "").split())
            (resolution.same if answer.get("answer") == "same" else resolution.different).append(pair)

    await asyncio.gather(*(one(ask[index:index + JUDGE_BATCH]) for index in range(0, len(ask), JUDGE_BATCH)))
    return resolution, apart


def _close(left: str, right: str) -> bool:
    """Close enough to be the same thing under two wordings: similar, or one name within the other."""

    a, b = set(tokens(left)), set(tokens(right))
    short, long_ = sorted((a, b), key=len)
    return similarity(left, right) >= CANDIDATE_SIMILARITY or (bool(short) and short < long_ and len(long_) - len(short) <= 2)


class _Union:
    def __init__(self, names: dict[str, str], same: list[Pair], different: list[Pair]) -> None:
        self.parent = {key: key for key in names}
        self.members = {key: {key} for key in names}
        self.names = names
        self.same = {frozenset((pair.left, pair.right)) for pair in same}
        self.apart = {frozenset((pair.left, pair.right)) for pair in different}
        self.blocked: list[dict[str, str]] = []

    def find(self, key: str) -> str:
        while self.parent[key] != key:
            self.parent[key] = self.parent[self.parent[key]]
            key = self.parent[key]
        return key

    def union(self, left: str, right: str, why: str) -> bool:
        if left not in self.parent or right not in self.parent:
            return False
        a, b = self.find(left), self.find(right)
        if a == b:
            return True
        # A merge may not join, through a chain, two names known to differ, nor two names nobody
        # compared ("cable liner" and "gun liner" are not one thing because each was called "liner").
        for x in sorted(self.members[a]):
            for y in sorted(self.members[b]):
                reason = ("judged different" if frozenset((x, y)) in self.apart
                          else distinguishing_difference(self.names[x], self.names[y]))
                if not reason and frozenset((x, y)) not in self.same and not _close(self.names[x], self.names[y]):
                    reason = "never compared"
                if reason:
                    self.blocked.append({"left": self.names[left], "right": self.names[right], "reason": reason,
                                         "between": f"{self.names[x]} / {self.names[y]}", "proposed_by": why})
                    return False
        root, child = min(a, b), max(a, b)
        self.parent[child] = root
        self.members[root] |= self.members.pop(child)
        return True


def node_id(key: str) -> str:
    return "kg4n_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _merge_attributes(items: list[Mention]) -> dict[str, str]:
    values: dict[str, list[str]] = defaultdict(list)
    for item in items:
        for key, value in item.attributes.items():
            if value:
                values[key].append(value)
    merged = {}
    for key, found in values.items():
        if key == "instruction_text":
            merged[key] = max(found, key=len)
        elif key == "expected_result":
            merged[key] = "; ".join(dict.fromkeys(found))  # the manual may give two values: keep both
        else:
            merged[key] = Counter(found).most_common(1)[0][0]
    return merged


def _evidence(items: list[Mention]) -> list[Evidence]:
    unique: dict[tuple, Evidence] = {}
    rank = {"cited": 0, "matched": 1, "unit": 2}
    for item in sorted(items, key=lambda value: (rank[value.evidence.anchor], value.evidence.page)):
        unique.setdefault((item.evidence.page, tuple(item.evidence.segment_ids)), item.evidence)
    return list(unique.values())[:MAX_NODE_EVIDENCE]


def assemble(mentions: list[Mention], facts: list[Fact], resolution: Resolution | None = None, *,
             statuses: dict[str, dict[str, str]] | None = None) -> tuple[Graph, dict[str, str]]:
    """The graph and, for every mention, the node it became.

    ``statuses`` holds what the manual declares about a mention when nothing can be linked: a cause
    for which it gives no remedy, a problem it does not explain, a cause no symptom leads to.
    """

    resolution = resolution or Resolution()
    groups = _groups(mentions)
    names = {key: _display(items) for key, items in groups.items()}
    union = _Union(names, resolution.same, resolution.different)
    for pair in resolution.same:
        union.union(pair.left, pair.right, "resolver")
    # The names the survey gave to one part are one part.
    entries: dict[str, list[str]] = defaultdict(list)
    for item in mentions:
        if item.unit_id == "catalogue":
            entries[item.key.rsplit("/", 1)[0]].append(identity(item))
    for keys in entries.values():
        for other in keys[1:]:
            union.union(keys[0], other, "catalogue alias")
    members: dict[str, list[Mention]] = defaultdict(list)
    for key, items in groups.items():
        members[union.find(key)].extend(items)

    graph = Graph(kept_apart=union.blocked)
    of_mention: dict[str, str] = {}
    for root, items in members.items():
        catalogue = [item for item in items if item.unit_id == "catalogue"]
        read = [item for item in items if item.unit_id != "catalogue"] or items
        # A part keeps the name the survey chose for the whole manual; other things their commonest name.
        name = catalogue[0].name if catalogue and items[0].type == "Component" else _display(read)
        # Other wordings of the name; a change of case alone is not an alias.
        aliases = list({value.casefold(): value for value in sorted(
            {item.name for item in items}, key=lambda value: (value.casefold(), value), reverse=True)
            if value.casefold() != name.casefold()}.values())[::-1]
        codes = Counter(item.code for item in items if item.code)
        kinds = Counter(item.kind for item in items if item.kind)
        descriptions = sorted({item.description for item in items if item.description
                               and canonical(item.description) != canonical(name)}, key=len, reverse=True)
        node = Node(
            node_id=node_id(root), type=items[0].type, name=name, aliases=aliases,
            code=codes.most_common(1)[0][0] if codes else "", kind=kinds.most_common(1)[0][0] if kinds else "",
            stated=any(item.stated for item in items), description=descriptions[0] if descriptions else "",
            properties=_merge_attributes(items), evidence=_evidence(read), mention_keys=sorted(item.key for item in items))
        graph.nodes[node.node_id] = node
        for item in items:
            of_mention[item.key] = node.node_id
        if len({identity(item) for item in items}) > 1:
            graph.merges.append({"node_id": node.node_id, "type": node.type, "name": name, "aliases": aliases})

    by_key = {mention.key: mention for mention in mentions}
    edges: dict[tuple[str, str, str], Edge] = {}
    for fact in facts:
        source, target = of_mention.get(fact.source), of_mention.get(fact.target)
        if source is None or target is None or source == target:
            continue
        if fact.verdict == "contradicted":
            graph.rejected.append({
                "relation": fact.relation, "source": f"{graph.nodes[source].type}:{by_key[fact.source].name}",
                "target": f"{graph.nodes[target].type}:{by_key[fact.target].name}", "reason": fact.reason,
                "fact_id": fact.fact_id, "record": fact.record, "origin": fact.origin,
                "evidence": fact.evidence.model_dump(mode="json")})
            continue
        key = (fact.relation, source, target)
        if key not in edges:
            digest = hashlib.sha256("|".join(key).encode("utf-8")).hexdigest()[:20]
            edges[key] = Edge(edge_id=f"kg4e_{digest}", relation=fact.relation, source=source, target=target)
        edges[key].facts.append(fact)

    # The hierarchy is a forest: a link that would close a loop is dropped.
    parent: dict[str, str] = {}
    for key in sorted(edges):
        relation, child, above = key
        if relation != "PART_OF":
            continue
        cursor, loop = above, False
        while cursor in parent:
            cursor = parent[cursor]
            if cursor == child:
                loop = True
                break
        if loop or child in parent or above == child:
            del edges[key]
        else:
            parent[child] = above

    # A part enters the graph when diagnostic knowledge touches it, with the assemblies above it.
    # A symptom or a code always does: what the technician observes is knowledge even when the
    # manual explains nothing, and the graph then says so.
    touched = {node for (relation, source, target) in edges if relation not in STRUCTURE_RELATIONS
               for node in (source, target)}
    keep = set(touched) | {key for key, node in graph.nodes.items() if node.type in {"Symptom", "ErrorCode"}}
    for node in list(touched):
        cursor = node
        while cursor in parent:
            cursor = parent[cursor]
            keep.add(cursor)
    graph.edges = sorted((edge for key, edge in edges.items() if key[1] in keep and key[2] in keep),
                         key=lambda edge: edge.edge_id)
    for edge in graph.edges:
        edge.facts.sort(key=lambda fact: fact.fact_id)
    graph.nodes = {key: node for key, node in sorted(graph.nodes.items()) if key in keep}

    for key, values in sorted((statuses or {}).items()):
        node = graph.nodes.get(of_mention.get(key, ""))
        if node is not None:
            for name, value in values.items():
                node.properties.setdefault(name, value)
    # A status only describes an absence: a link found later replaces it.
    for node in graph.nodes.values():
        if node.type == "FailureMode":
            if graph.out_edges(node.node_id, "RESOLVED_BY"):
                node.properties["remedy_status"] = "stated"
            if graph.in_edges(node.node_id, "MAY_INDICATE", "INDICATES"):
                node.properties.pop("entry_status", None)
        elif node.type in {"Symptom", "ErrorCode"} and graph.out_edges(
                node.node_id, "MAY_INDICATE", "INDICATES", "ADDRESSED_BY", "CLEARED_BY"):
            node.properties.pop("diagnosis_status", None)
    return graph, of_mention


def summary(graph: Graph, resolution: Resolution, apart: list[Pair]) -> dict[str, Any]:
    return {"nodes": len(graph.nodes), "merged_nodes": len(graph.merges),
            "judged_same": len(resolution.same), "judged_different": len(resolution.different),
            "unjudged_pairs": len(resolution.unjudged), "false_friends_kept_apart": len(apart),
            "merges_blocked_by_a_difference": len(graph.kept_apart)}
