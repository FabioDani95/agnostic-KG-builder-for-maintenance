"""Station 5, merge: one node per thing, one edge per fact, aliases kept.

Names equal after normalisation merge directly; error codes merge by code.
Similar names go to a model judge; different numbers never merge. Only the
pairs the judge cannot settle become questions. Graph IDs are made by the code.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from collections import Counter, defaultdict
from itertools import combinations

from pydantic import BaseModel, Field

from backend.kg_v3.checker import (
    CheckedRelation,
    normalize_name,
    restates,
    similarity,
    statement,
    structurally_supported,
)
from backend.kg_v3.contracts import Assertion, Certificate, ContextItem, Tier, Witness
from backend.kg_v3.extractor import UNSPECIFIED_CAUSE, Endpoint, Proposal
from backend.kg_v3.llm import ModelClient
from backend.kg_v3.ontology import load_ontology
from backend.kg_v3.prompts import MERGE_PROMPT
from backend.kg_v3.reader import DocumentText, render_segments

logger = logging.getLogger(__name__)

JUDGE_THRESHOLD = 0.8
ALIAS_SIMILARITY = 0.75
JUDGE_BATCH = 12
MAX_JUDGED_PAIRS = 400
_TIER_RANK = {Tier.GREEN: 0, Tier.YELLOW: 1, Tier.RED: 2}


def identity(endpoint: Endpoint) -> str:
    if endpoint.code and endpoint.type == "ErrorCode":
        numbers = ",".join(sorted(set(re.findall(r"\d+", endpoint.name))))
        return f"{endpoint.type}|code:{normalize_name(endpoint.code)}|name_numbers:{numbers}"
    return f"{endpoint.type}|{normalize_name(endpoint.name)}"


def node_id(identity_key: str) -> str:
    return "v3n_" + hashlib.sha256(identity_key.encode("utf-8")).hexdigest()[:20]


class MergePair(BaseModel):
    left: str
    right: str
    left_name: str
    right_name: str
    type: str
    left_cites: list[str] = Field(default_factory=list)
    right_cites: list[str] = Field(default_factory=list)
    verdict: str = ""
    rationale: str = ""
    cited_segments: list[str] = Field(default_factory=list)


class MergePlan(BaseModel):
    same: list[MergePair] = Field(default_factory=list)
    unsure: list[MergePair] = Field(default_factory=list)
    different: list[MergePair] = Field(default_factory=list)


class GraphNode(BaseModel):
    node_id: str
    type: str
    name: str
    code: str = ""
    kind: str = ""
    stated: bool = True
    aliases: list[str] = Field(default_factory=list)
    cites: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    edge_id: str
    relation_type: str
    source: str
    target: str
    assertions: list[Assertion]

    @property
    def tier(self) -> Tier:
        return min((item.tier for item in self.assertions), key=_TIER_RANK.__getitem__)

    @property
    def conditions(self) -> list[ContextItem]:
        # Edge-level context contains only constraints common to every occurrence.
        # Alternatives (including immediate vs conditional) live on each assertion.
        contexts = [set(item.conditions) for item in self.assertions if item.tier is not Tier.RED]
        return sorted(set.intersection(*contexts)) if contexts else []


class MergedGraph(BaseModel):
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    edges: list[GraphEdge] = Field(default_factory=list)
    merged_aliases: int = 0
    blocked_merges: list[dict[str, str]] = Field(default_factory=list)

    @property
    def nodes_by_id(self) -> dict[str, GraphNode]:
        return {node.node_id: node for node in self.nodes.values()}


def _endpoints(relations: list[CheckedRelation]) -> dict[str, list[Endpoint]]:
    found: dict[str, list[Endpoint]] = {}
    for relation in relations:
        for proposal in relation.proposals:
            for endpoint in (proposal.source, proposal.target):
                found.setdefault(identity(endpoint), []).append(endpoint)
    return found


def _contained(left: str, right: str) -> bool:
    """One name is the other plus extra words, such as a cross-reference."""

    a, b = set(normalize_name(left).split()), set(normalize_name(right).split())
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 2 and short < long_


def merge_candidates(relations: list[CheckedRelation]) -> list[MergePair]:
    endpoints = _endpoints(relations)
    by_type: dict[str, list[str]] = {}
    for key, items in endpoints.items():
        by_type.setdefault(items[0].type, []).append(key)
    pairs: list[MergePair] = []
    for kind, keys in by_type.items():
        for left, right in combinations(sorted(keys), 2):
            if "|code:" in left or "|code:" in right:
                continue
            a, b = endpoints[left][0], endpoints[right][0]
            if similarity(a.name, b.name) >= JUDGE_THRESHOLD or _contained(a.name, b.name):
                pairs.append(MergePair(
                    left=left, right=right, left_name=a.name, right_name=b.name, type=kind,
                    left_cites=sorted({c for item in endpoints[left] for c in item.cites})[:3],
                    right_cites=sorted({c for item in endpoints[right] for c in item.cites})[:3],
                ))
    # Two reads that name one end of the same relation differently are always judged:
    # their names would otherwise be joined without asking whether they mean the same.
    seen = {(pair.left, pair.right) for pair in pairs}
    for relation in relations:
        lead = relation.proposals[0]
        for other in relation.proposals[1:]:
            for mine, theirs in ((lead.source, other.source), (lead.target, other.target)):
                left, right = sorted((identity(mine), identity(theirs)))
                if (left == right or (left, right) in seen or not (mine.stated and theirs.stated)
                        or "|code:" in left or similarity(mine.name, theirs.name) < ALIAS_SIMILARITY):
                    continue
                seen.add((left, right))
                a, b = (mine, theirs) if identity(mine) == left else (theirs, mine)
                pairs.append(MergePair(left=left, right=right, left_name=a.name, right_name=b.name, type=a.type,
                                       left_cites=sorted(a.cites)[:3], right_cites=sorted(b.cites)[:3]))
    return pairs[:MAX_JUDGED_PAIRS]


def _regroup(doc: DocumentText, relation: CheckedRelation, proposals: list[Proposal], suffix: str) -> CheckedRelation:
    """Part of a relation whose reads disagree: its own witnesses, never agreement across the split."""

    original = relation.assertion.certificate
    lead = proposals[0]
    witnesses = []
    if (Witness.STRUCTURE in original.witnesses
            and any(structurally_supported(doc, item) for item in proposals) and not restates(lead)):
        witnesses.append(Witness.STRUCTURE)
    if len({item.read for item in proposals} & {"A", "B"}) >= 2 and Witness.AGREEMENT in original.witnesses:
        witnesses.append(Witness.AGREEMENT)
    # The verifier judged the lead statement only.
    verdict = original.verifier_verdict if not suffix else None
    if verdict is not None and Witness.VERIFIER in original.witnesses:
        witnesses.append(Witness.VERIFIER)
    certificate = Certificate(
        segment_ids=sorted({cite for item in proposals for cite in item.all_cites}) or original.segment_ids,
        witnesses=witnesses, verifier_verdict=verdict, extractor=original.extractor,
        notes=[*original.notes, "the reads name an end of this relation differently and the names differ in meaning"],
    )
    assertion = Assertion(
        assertion_id=f"{relation.assertion.assertion_id}{'.' + suffix if suffix else ''}",
        relation_type=lead.relation_type,
        source_key=f"{lead.source.type}:{lead.source.name}", target_key=f"{lead.target.type}:{lead.target.name}",
        record_key=f"{lead.unit_id}:{lead.read}.{lead.record}",
        conditions=sorted({condition for item in proposals for condition in item.conditions}),
        certificate=certificate,
    )
    return CheckedRelation(assertion=assertion, proposals=proposals)


def split_disagreements(doc: DocumentText, relations: list[CheckedRelation],
                        different: list[MergePair]) -> list[CheckedRelation]:
    """A relation whose reads name an end with names judged different becomes one relation per name.

    Each part keeps only its own witnesses, so the disagreement is asked about
    instead of one name silently replacing the other.
    """

    apart_keys = {frozenset((pair.left, pair.right)) for pair in different}
    result: list[CheckedRelation] = []
    for relation in relations:
        lead, others = relation.proposals[0], relation.proposals[1:]
        apart = [other for other in others
                 if any(frozenset((identity(mine), identity(theirs))) in apart_keys
                        for mine, theirs in ((lead.source, other.source), (lead.target, other.target)))]
        if not apart:
            result.append(relation)
            continue
        together = [lead, *(other for other in others if other not in apart)]
        result.append(_regroup(doc, relation, together, ""))
        result.extend(_regroup(doc, relation, [other], f"s{index}") for index, other in enumerate(apart, start=1))
    return result


MERGE_CONTEXT_STATEMENTS = 10
MERGE_CONTEXT_SEGMENTS = 3


def merge_context(key: str, cites: list[str], doc: DocumentText | None,
                  relations: list[CheckedRelation]) -> str:
    spec = load_ontology()
    direct = [p for r in relations for p in r.proposals if key in {identity(p.source), identity(p.target)}]
    causes = {identity(e) for p in direct for e in (p.source, p.target) if e.type == "FailureMode"}
    connected = direct + [p for r in relations for p in r.proposals
                          if identity(p.source) in causes or identity(p.target) in causes]
    lines = list(dict.fromkeys(statement(spec, p) for p in connected))[:MERGE_CONTEXT_STATEMENTS]
    # Where the name itself is written; its branches above carry the rest of the entry.
    own = cites or sorted({c for p in direct for c in p.all_cites})
    evidence = sorted(own[:MERGE_CONTEXT_SEGMENTS], key=lambda c: doc.position(c) or 0 if doc else 0)
    source = render_segments(doc.segments(evidence), doc=doc) if doc else "(source unavailable)"
    return "Connected problem/remedy branches:\n" + "\n".join(lines) + "\nCited source:\n" + source


async def judge_pairs(llm: ModelClient | None, pairs: list[MergePair],
                      doc: DocumentText | None = None, relations: list[CheckedRelation] = ()) -> MergePlan:
    plan = MergePlan()
    if not pairs:
        return plan
    if llm is None:
        plan.unsure = pairs
        return plan

    async def judge(batch: list[MergePair]) -> None:
        ids = [f"M{index}" for index in range(1, len(batch) + 1)]
        # Each name's context is written once per call, however many pairs it is in.
        sides: dict[str, tuple[str, list[str]]] = {}
        for pair in batch:
            sides.setdefault(pair.left, (pair.left_name, pair.left_cites))
            sides.setdefault(pair.right, (pair.right_name, pair.right_cites))
        labels = {key: f"N{index}" for index, key in enumerate(sides, start=1)}
        contexts = "\n\n".join(f"{labels[key]} '{name}': {merge_context(key, cites, doc, relations)}"
                                for key, (name, cites) in sides.items())
        text = ("Names and their context:\n\n" + contexts + "\n\nPairs:\n"
                + "\n".join(f"{pair_id}: {pair.type} {labels[pair.left]} '{pair.left_name}' vs "
                            f"{labels[pair.right]} '{pair.right_name}'" for pair_id, pair in zip(ids, batch)))
        schema = {"type": "object", "additionalProperties": False, "required": ["answers"], "properties": {
            "answers": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["id", "answer", "rationale", "cited_segments"],
                "properties": {"id": {"type": "string", "enum": ids},
                               "answer": {"type": "string", "enum": ["same", "different", "unsure"]},
                               "rationale": {"type": "string"},
                               "cited_segments": {"type": "array", "items": {"type": "string"}}},
            }}}}
        try:
            data = await llm.json(system=MERGE_PROMPT, user=text, schema=schema, name="kg_v3_merge",
                                  max_output_tokens=3000)
            answers = {str(item.get("id")): item for item in data.get("answers") or []}
        except Exception as exc:
            logger.warning("Merge judge failed: %s", exc)
            answers = {}
        for pair_id, pair in zip(ids, batch):
            answer = answers.get(pair_id, {})
            pair.rationale = str(answer.get("rationale") or "").strip()
            pair.cited_segments = [c for c in answer.get("cited_segments", []) if doc and doc.segment(c)]
            verdict = answer.get("answer", "unsure")
            pair.verdict = ("unsure" if verdict == "same" and not (pair.rationale and pair.cited_segments)
                            else verdict if verdict in {"same", "different", "unsure"} else "unsure")

    await asyncio.gather(*(judge(pairs[index:index + JUDGE_BATCH]) for index in range(0, len(pairs), JUDGE_BATCH)))
    for pair in pairs:
        {"same": plan.same, "different": plan.different}.get(pair.verdict, plan.unsure).append(pair)
    return plan


class _UnionFind:
    def __init__(self, endpoints: dict[str, list[Endpoint]], different: list[MergePair]) -> None:
        self.parent: dict[str, str] = {}
        self.members: dict[str, set[str]] = {}
        self.endpoints = endpoints
        self.apart = {frozenset((p.left, p.right)) for p in different}
        self.blocked: list[dict[str, str]] = []

    def find(self, key: str) -> str:
        self.parent.setdefault(key, key)
        self.members.setdefault(key, {key})
        while self.parent[key] != key:
            self.parent[key] = self.parent[self.parent[key]]
            key = self.parent[key]
        return key

    def union(self, left: str, right: str) -> None:
        if left not in self.endpoints or right not in self.endpoints:
            return
        a, b = self.find(left), self.find(right)
        if a != b:
            for x in sorted(self.members[a]):
                for y in sorted(self.members[b]):
                    ex, ey = self.endpoints[x][0], self.endpoints[y][0]
                    reason = ('different' if frozenset((x, y)) in self.apart else
                              'different_codes' if ex.code and ey.code and normalize_name(ex.code) != normalize_name(ey.code) else
                              'different_numbers' if set(re.findall(r'\d+', ex.name)) !=
                              set(re.findall(r'\d+', ey.name)) else
                              'different_types' if ex.type != ey.type else '')
                    if reason:
                        self.blocked.append({'left': left, 'right': right, 'reason': reason,
                                             'constraint_left': x, 'constraint_right': y})
                        return
            root, child = min(a, b), max(a, b)
            self.parent[child] = root
            self.members[root].update(self.members[child])


def _stated(items: list[Endpoint]) -> bool:
    """A node is written in the source only if no read names it as derived from a check or remedy.

    A placeholder ("Unspecified cause of ...") names nothing and does not vote.
    """

    if items[0].type != "FailureMode":
        return any(item.stated for item in items)
    named = [item for item in items if not item.name.startswith(UNSPECIFIED_CAUSE)]
    return bool(named) and all(item.stated for item in named)


def assemble(relations: list[CheckedRelation], same_pairs: list[MergePair],
             different_pairs: list[MergePair] = ()) -> MergedGraph:
    endpoints = _endpoints(relations)
    groups = _UnionFind(endpoints, different_pairs)
    for key in endpoints:
        groups.find(key)
    for pair in same_pairs:
        groups.union(pair.left, pair.right)
    # Reads that agree on a relation may name its ends in their own words. Their
    # names become one node only when they are close, or one end is unnamed: a
    # compound name ("clear the valve and replace the seals") must not bridge
    # two separate actions into one node.
    # An unnamed cause joins a named one only when it matches exactly one named
    # cause in the whole document; otherwise it would bridge different causes.
    partners: dict[str, set[str]] = defaultdict(set)
    for relation in relations:
        lead = relation.proposals[0]
        for other in relation.proposals[1:]:
            for mine, theirs in ((lead.source, other.source), (lead.target, other.target)):
                if mine.placeholder != theirs.placeholder and mine.type == theirs.type == "FailureMode":
                    named, unnamed = (theirs, mine) if mine.placeholder else (mine, theirs)
                    partners[identity(unnamed)].add(identity(named))
    for unnamed, named in partners.items():
        if len(named) == 1:
            groups.union(unnamed, next(iter(named)))

    # Only actual placeholders from the same source entry may use shared remedies.
    # A named, inferred cause has exactly the same identity rules as a stated cause.
    remedies: dict[str, set[str]] = defaultdict(set)
    origins: dict[str, set[tuple]] = defaultdict(set)
    for relation in relations:
        for proposal in relation.proposals:
            if proposal.relation_type == "RESOLVED_BY" and proposal.source.placeholder:
                remedies[identity(proposal.source)].add(identity(proposal.target))
                anchors = proposal.source.cites or proposal.cites
                origins[identity(proposal.source)].update((proposal.unit_id, cite) for cite in anchors)
    for left, right in combinations(sorted(remedies), 2):
        shared = remedies[left] & remedies[right]
        if (origins[left] & origins[right] and len(shared) >= 2
                and len(shared) / len(remedies[left] | remedies[right]) >= 0.6):
            groups.union(left, right)

    members: dict[str, list[Endpoint]] = {}
    for key, items in endpoints.items():
        members.setdefault(groups.find(key), []).extend(items)
    graph = MergedGraph(blocked_merges=groups.blocked)
    for root, items in members.items():
        named = [item for item in items if item.stated] or items
        names = Counter(item.name for item in named)
        first_seen = {value: index for index, value in reversed(list(enumerate(item.name for item in named)))}
        name = sorted(names, key=lambda value: (-names[value], first_seen[value]))[0]
        codes = Counter(item.code for item in items if item.code)
        kinds = Counter(item.kind for item in items if item.kind)
        graph.nodes[root] = GraphNode(
            node_id=node_id(root), type=items[0].type, name=name,
            code=codes.most_common(1)[0][0] if codes else "",
            kind=kinds.most_common(1)[0][0] if kinds else "",
            stated=_stated(items),
            aliases=sorted({item.name for item in items} - {name}),
            cites=sorted({cite for item in items for cite in item.cites}),
        )
        graph.merged_aliases += len(names) - 1

    edges: dict[tuple[str, str, str], GraphEdge] = {}
    for relation in relations:
        lead = relation.proposals[0]
        source = graph.nodes[groups.find(identity(lead.source))].node_id
        target = graph.nodes[groups.find(identity(lead.target))].node_id
        key = (lead.relation_type, source, target)
        if key not in edges:
            digest = hashlib.sha256("|".join(key).encode("utf-8")).hexdigest()[:20]
            edges[key] = GraphEdge(edge_id=f"v3e_{digest}", relation_type=lead.relation_type,
                                   source=source, target=target, assertions=[])
        edges[key].assertions.append(relation.assertion)
    graph.edges = list(edges.values())
    return graph
