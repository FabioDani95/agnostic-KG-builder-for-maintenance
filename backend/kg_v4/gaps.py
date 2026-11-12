"""Stage 5, gaps: the graph says what it lacks, and the manual is searched for exactly that.

After the first construction the controller lists the gaps a maintenance agent would hit: a cause
without a remedy, a symptom or code without a cause or remedy, a cause no symptom leads to. For
each gap it retrieves the passages most likely to hold the answer (the entry itself, the targets
of its printed pointers, the best lexical matches in the whole manual) and asks one targeted
question. An answer found there becomes facts, checked like any other; when the manual states
nothing, the node says so instead of staying an orphan. The number of calls is bounded.

Two repairs need no model: a pointer from one entry to another ("like 'Pump gets too hot'") is
followed, and an item whose own name names a catalogued part is linked to that part.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
from collections import Counter, defaultdict
from typing import Any

from pydantic import BaseModel, Field

from backend.kg_v3.contracts import ContextItem
from backend.kg_v3.reader import DocumentText, render_segments
from backend.kg_v4.extract import CONDITION_KINDS, extraction_schema
from backend.kg_v4.model import ACTION_KINDS, Evidence, Fact, Graph, Mention, Reference
from backend.kg_v4.names import canonical, similarity, tokens
from backend.kg_v4.prompts import GAP_PROMPT
from backend.kg_v4.sections import SectionIndex
from backend.kg_v4.survey import is_the_machine, split_listed_parts, usable_component

logger = logging.getLogger(__name__)

GAP_KINDS = ("cause_without_remedy", "problem_without_diagnosis", "cause_without_problem")
GAPS_PER_CALL = 8
PASSAGE_CHARS = 12000
WINDOW = 5
GAP_OUTPUT_TOKENS = 8000
ENTRY_RELATIONS = ("MAY_INDICATE", "INDICATES")
DIRECT_RELATIONS = ("ADDRESSED_BY", "CLEARED_BY")
NAME_LINK = {"FailureMode": "AFFECTS", "CorrectiveAction": "ACTS_ON", "Symptom": "OBSERVED_ON"}
_QUOTED = re.compile(r"[\"'“‘«]([^\"'”’»]{4,})[\"'”’»]")
_POINTER = re.compile(r"^\s*(?:like|same as|as for|see(?: also)?|refer to|as in)\b[\s:]*", re.I)


class Gap(BaseModel):
    gap_id: str
    kind: str
    node_id: str
    type: str
    name: str
    mention: str  # a mention of the node, the end new facts attach to
    pages: list[int] = Field(default_factory=list)
    segments: list[str] = Field(default_factory=list)
    hint: str = ""


def find_gaps(graph: Graph) -> list[Gap]:
    """What a diagnosis would miss; nodes whose absence the manual already declares are not gaps."""

    gaps = []
    for node in sorted(graph.nodes.values(), key=lambda item: item.node_id):
        kind = ""
        if node.type == "FailureMode":
            if not graph.out_edges(node.node_id, "RESOLVED_BY") and not node.properties.get("remedy_status"):
                kind = "cause_without_remedy"
            elif not graph.in_edges(node.node_id, *ENTRY_RELATIONS) and not node.properties.get("entry_status"):
                kind = "cause_without_problem"
        elif node.type in {"Symptom", "ErrorCode"}:
            if (not graph.out_edges(node.node_id, *ENTRY_RELATIONS, *DIRECT_RELATIONS)
                    and not node.properties.get("diagnosis_status")):
                kind = "problem_without_diagnosis"
        if not kind or not node.mention_keys:
            continue
        own = [key for key in node.mention_keys if not key.startswith("catalogue/")] or node.mention_keys
        around = [graph.nodes[edge.source].name for edge in graph.in_edges(node.node_id)][:2]
        around += [graph.nodes[edge.target].name for edge in graph.out_edges(node.node_id)][:2]
        gaps.append(Gap(
            gap_id=f"{kind}:{node.node_id}", kind=kind, node_id=node.node_id, type=node.type, mention=own[0],
            name=f"{node.code}: {node.name}" if node.code and node.code != node.name else node.name,
            pages=sorted({item.page for item in node.evidence}),
            segments=[cite for item in node.evidence for cite in item.segment_ids],
            hint="; ".join(around)))
    return gaps


class Retriever:
    """Lexical search over the segments of the manual (BM25), enough to find where a name is written."""

    def __init__(self, doc: DocumentText) -> None:
        self.doc = doc
        self.segments = doc.segments()
        self.words = [Counter(tokens(segment.text)) for segment in self.segments]
        self.frequency: Counter = Counter(word for words in self.words for word in words)
        self.average = sum(sum(words.values()) for words in self.words) / max(1, len(self.words))

    def search(self, query: str, *, limit: int = 3, exclude_pages: set[int] | frozenset[int] = frozenset()) -> list[str]:
        terms = set(tokens(query))
        scored = []
        for index, words in enumerate(self.words):
            if self.segments[index].page in exclude_pages:
                continue
            length = sum(words.values())
            score = 0.0
            for term in terms & words.keys():
                idf = math.log(1 + (len(self.words) - self.frequency[term] + 0.5) / (self.frequency[term] + 0.5))
                score += idf * words[term] * 2.2 / (words[term] + 1.2 * (0.25 + 0.75 * length / self.average))
            if score > 0:
                scored.append((score, index))
        scored.sort(reverse=True)
        return [self.segments[index].segment_id for _, index in scored[:limit]]

    def window(self, segment_ids: list[str], *, radius: int = WINDOW) -> list[str]:
        positions = {self.doc.position(cite) for cite in segment_ids} - {None}
        keep = sorted({index for position in positions
                       for index in range(max(0, position - radius), min(len(self.segments), position + radius + 1))})
        return [self.segments[index].segment_id for index in keep]


def _gap_schema(ids: list[str], segment_ids: list[str]) -> dict[str, Any]:
    records = extraction_schema(segment_ids)["properties"]["records"]["items"]["properties"]
    action, cause = records["actions"]["items"], records["causes"]["items"]
    cite = action["properties"]["cite"]
    text = {"type": "string"}
    bare_cause = {"type": "object", "additionalProperties": False,
                  "required": ["name", "description", "component", "cite"],
                  "properties": {key: cause["properties"][key] for key in ("name", "description", "component", "cite")}}
    problem = {"type": "object", "additionalProperties": False, "required": ["type", "name", "code", "cite"],
               "properties": {"type": {"type": "string", "enum": ["Symptom", "ErrorCode"]}, "name": text,
                              "code": text, "cite": cite}}
    answer = {"type": "object", "additionalProperties": False,
              "required": ["id", "status", "actions", "causes", "problems"],
              "properties": {"id": {"type": "string", "enum": ids},
                             "status": {"type": "string", "enum": ["found", "not_stated"]},
                             "actions": {"type": "array", "items": action},
                             "causes": {"type": "array", "items": bare_cause},
                             "problems": {"type": "array", "items": problem}}}
    return {"type": "object", "additionalProperties": False, "required": ["answers"],
            "properties": {"answers": {"type": "array", "items": answer}}}


_QUESTION = {
    "cause_without_remedy": "cause without remedy: what check or remedy does the manual prescribe for it?",
    "problem_without_diagnosis": "problem without cause or remedy: which causes does the manual name for it, "
                                 "or which checks and remedies does it give directly?",
    "cause_without_problem": "cause without problem: which symptom or code does the manual associate with it?",
}


class GapRepair:
    """Bounded, targeted reading of the manual for the gaps of a graph."""

    def __init__(self, llm, doc: DocumentText, sections: SectionIndex, *, asset_name: str, verifier=None,
                 references: list[Reference] = (), max_calls: int = 24, concurrency: int = 6) -> None:
        self.llm, self.doc, self.sections, self.verifier = llm, doc, sections, verifier
        self.system = GAP_PROMPT.format(asset=asset_name)
        self.retriever = Retriever(doc)
        self.references = defaultdict(list)
        for reference in references:
            self.references[reference.mention].append(reference)
        self.max_calls = max_calls
        self.calls = 0
        self.asked: set[str] = set()
        self._limit = asyncio.Semaphore(max(1, concurrency))
        self._serial = 0

    def passage_ids(self, gap: Gap, node_mentions: list[str]) -> list[str]:
        """Segments to show for one gap: its own entry first, then pointer targets, then lexical matches."""

        ids = self.retriever.window(gap.segments) if gap.segments else [
            segment.segment_id for page in gap.pages[:1] for segment in self.doc.pages.get(page, [])][:40]
        for key in node_mentions:
            for reference in self.references.get(key, []):
                for page in reference.target_pages[:2]:
                    ids.extend(segment.segment_id for segment in self.doc.pages.get(page, [])[:40])
        # Elsewhere in the manual: the entry's own page is already shown.
        found = self.retriever.search(f"{gap.name} {gap.hint}", limit=3, exclude_pages=frozenset(gap.pages))
        ids.extend(self.retriever.window(found, radius=2))
        return list(dict.fromkeys(ids))

    def plan(self, graph: Graph) -> list[tuple[list[Gap], list[str]]]:
        """Gaps not asked yet, grouped by the page they were read on so that passages are shared."""

        gaps = [gap for gap in find_gaps(graph) if gap.gap_id not in self.asked]
        by_page: dict[int, list[Gap]] = defaultdict(list)
        for gap in gaps:
            by_page[gap.pages[0] if gap.pages else 0].append(gap)
        calls = []
        for page in sorted(by_page):
            group = by_page[page]
            for start in range(0, len(group), GAPS_PER_CALL):
                batch = group[start:start + GAPS_PER_CALL]
                ids: list[str] = []
                for gap in batch:
                    ids.extend(self.passage_ids(gap, graph.nodes[gap.node_id].mention_keys))
                ids = list(dict.fromkeys(ids))
                # The entries themselves come first; the passage is cut where the budget ends.
                kept, size = [], 0
                for segment in self.doc.segments(ids):
                    size += len(segment.text) + 20
                    if size > PASSAGE_CHARS:
                        break
                    kept.append(segment.segment_id)
                calls.append((batch, kept))
        return calls

    def _mention(self, node_type: str, name: str, evidence: Evidence, **fields: Any) -> Mention:
        self._serial += 1
        return Mention(key=f"gap/{self._serial}/{canonical(name)[:60]}", type=node_type, name=name,
                       evidence=evidence, unit_id="gap", **fields)

    def _evidence(self, cites: list[str], allowed: set[str], fallback: Gap) -> Evidence:
        valid = [cite for cite in dict.fromkeys(cites or []) if cite in allowed and self.doc.segment(cite)]
        if valid:
            first = self.doc.segment(valid[0])
            return Evidence(page=first.page, section=self.sections.section(valid[0], first.page),
                            segment_ids=valid, anchor="cited")
        page = fallback.pages[0] if fallback.pages else 1
        return Evidence(page=page, section=self.sections.section(page=page), segment_ids=fallback.segments[:3],
                        anchor="unit")

    def _apply(self, gap: Gap, answer: dict[str, Any], allowed: set[str], anchor: Mention,
               statuses: dict[str, dict[str, str]]) -> tuple[list[Mention], list[Fact]]:
        mentions: list[Mention] = []
        facts: list[Fact] = []
        record = f"gap:{gap.node_id}"

        def fact(relation: str, source: Mention, target: Mention, conditions=()) -> None:
            facts.append(Fact(fact_id=f"gap/{gap.node_id}/{len(facts) + 1}/{self._serial}", relation=relation,
                              source=source.key, target=target.key, record=record, conditions=list(conditions),
                              evidence=target.evidence if target.key != anchor.key else source.evidence,
                              origin="gap_repair"))

        def parts(name: Any, evidence: Evidence) -> list[Mention]:
            found = []
            for part in split_listed_parts(" ".join(str(name or "").split())):
                if usable_component(part):
                    found.append(self._mention("Component", part, evidence))
            mentions.extend(found)
            return found

        def actions(raw: list, parent: Mention, relation: str) -> None:
            for item in raw or []:
                name = " ".join(str(item.get("name") or "").split())
                if not name:
                    continue
                evidence = self._evidence(item.get("cite"), allowed, gap)
                attributes = {key: " ".join(str(item.get(field) or "").split())
                              for key, field in (("instruction_text", "instruction"), ("expected_result", "expected"))}
                action = self._mention("CorrectiveAction", name, evidence,
                                       kind=item.get("kind") if item.get("kind") in ACTION_KINDS else "repair",
                                       attributes={key: value for key, value in attributes.items() if value})
                mentions.append(action)
                conditions = [ContextItem(kind=value["kind"], text=" ".join(str(value["text"]).split()),
                                          cite=tuple(evidence.segment_ids))
                              for value in item.get("conditions") or []
                              if isinstance(value, dict) and value.get("kind") in CONDITION_KINDS and value.get("text")]
                fact(relation, parent, action, conditions)
                for part in parts(item.get("component"), evidence):
                    fact("ACTS_ON", action, part)

        found = answer.get("status") == "found"
        if gap.kind == "cause_without_remedy":
            actions(answer.get("actions") if found else [], anchor, "RESOLVED_BY")
        elif gap.kind == "problem_without_diagnosis":
            actions(answer.get("actions") if found else [], anchor,
                    "ADDRESSED_BY" if gap.type == "Symptom" else "CLEARED_BY")
            for item in (answer.get("causes") if found else []) or []:
                name = " ".join(str(item.get("name") or "").split())
                if not name:
                    continue
                evidence = self._evidence(item.get("cite"), allowed, gap)
                cause = self._mention("FailureMode", name, evidence,
                                      description=" ".join(str(item.get("description") or "").split()))
                mentions.append(cause)
                fact("MAY_INDICATE" if gap.type == "Symptom" else "INDICATES", anchor, cause)
                for part in parts(item.get("component"), evidence):
                    fact("AFFECTS", cause, part)
        else:
            for item in (answer.get("problems") if found else []) or []:
                name, code = (" ".join(str(item.get(key) or "").split()) for key in ("name", "code"))
                kind = item.get("type") if item.get("type") in {"Symptom", "ErrorCode"} else "Symptom"
                if not (name or code) or (kind == "ErrorCode" and not code):
                    continue
                problem = self._mention(kind, name or code, self._evidence(item.get("cite"), allowed, gap),
                                        code=code if kind == "ErrorCode" else "")
                mentions.append(problem)
                fact("MAY_INDICATE" if kind == "Symptom" else "INDICATES", problem, anchor)
        if not any(item.source == anchor.key or item.target == anchor.key for item in facts):
            # Nothing to link: the graph states the absence instead of leaving an orphan.
            status = {"cause_without_remedy": ("remedy_status", "not_stated"),
                      "problem_without_diagnosis": ("diagnosis_status", "not_stated"),
                      "cause_without_problem": ("entry_status", "none_in_manual")}[gap.kind]
            statuses.setdefault(anchor.key, {})[status[0]] = status[1]
            return [], []
        return mentions, facts

    async def _ask(self, batch: list[Gap], segment_ids: list[str], by_key: dict[str, Mention],
                   statuses: dict[str, dict[str, str]]) -> tuple[list[Mention], list[Fact]]:
        ids = [f"G{index}" for index in range(1, len(batch) + 1)]
        ordered = sorted(self.doc.segments(segment_ids), key=lambda item: self.doc.position(item.segment_id) or 0)
        lines = []
        for label, gap in zip(ids, batch):
            where = ", ".join(f"p.{page}" for page in gap.pages[:3])
            near = f" Connected to: {gap.hint}." if gap.hint else ""
            lines.append(f"{label}: {gap.type} '{gap.name}' ({where}). {_QUESTION[gap.kind]}{near}")
        try:
            async with self._limit:
                data = await self.llm.json(
                    system=self.system, name="kg_v4_gap", max_output_tokens=GAP_OUTPUT_TOKENS,
                    schema=_gap_schema(ids, [segment.segment_id for segment in ordered]),
                    user="Gaps:\n" + "\n".join(lines) + "\n\nPassages:\n" + render_segments(ordered, doc=self.doc))
        except Exception as exc:
            logger.warning("Gap repair call failed: %s", exc)
            return [], []
        answers = {str(item.get("id")): item for item in data.get("answers") or [] if isinstance(item, dict)}
        mentions: list[Mention] = []
        facts: list[Fact] = []
        allowed = set(segment_ids)
        for label, gap in zip(ids, batch):
            self.asked.add(gap.gap_id)
            answer = answers.get(label)
            if answer is None:
                continue
            new_mentions, new_facts = self._apply(gap, answer, allowed, by_key[gap.mention], statuses)
            mentions.extend(new_mentions)
            facts.extend(new_facts)
        if facts and self.verifier is not None:
            # A found answer is checked against the same passages, like any extracted fact.
            lookup = {**by_key, **{mention.key: mention for mention in mentions}}
            facts = await self.verifier.check(facts, lookup, segment_ids)
        return mentions, facts

    async def repair(self, graph: Graph, by_key: dict[str, Mention],
                     statuses: dict[str, dict[str, str]]) -> tuple[list[Mention], list[Fact], dict[str, int]]:
        """One round: ask about the open gaps within the remaining budget."""

        calls = self.plan(graph)
        allowed = calls[:max(0, self.max_calls - self.calls)]
        self.calls += len(allowed)
        results = await asyncio.gather(*(self._ask(batch, ids, by_key, statuses) for batch, ids in allowed))
        mentions = [mention for found, _ in results for mention in found]
        facts = [fact for _, found in results for fact in found]
        asked = sum(len(batch) for batch, _ in allowed)
        return mentions, facts, {"gaps": sum(len(batch) for batch, _ in calls), "asked": asked, "calls": len(allowed),
                                 "deferred": sum(len(batch) for batch, _ in calls[len(allowed):]),
                                 "new_facts": len(facts)}


def resolve_references(references: list[Reference], sections: SectionIndex) -> list[Reference]:
    """Printed pointers with the PDF pages and section they lead to."""

    resolved = []
    for reference in references:
        pages, section = sections.resolve(reference.text)
        resolved.append(reference.model_copy(update={"target_pages": pages, "target_section": section,
                                                     "resolved": bool(pages)}))
    return resolved


def follow_entry_pointers(graph: Graph, references: list[Reference], of_mention: dict[str, str],
                          by_key: dict[str, Mention]) -> list[Fact]:
    """"Like 'Pump gets too hot'": the entry takes the causes and direct remedies of the entry it names."""

    problems = {node.node_id: node for node in graph.nodes.values() if node.type in {"Symptom", "ErrorCode"}}
    facts: list[Fact] = []
    for reference in references:
        source_id = of_mention.get(reference.mention)
        source = problems.get(source_id)
        if source is None:
            continue
        quoted = _QUOTED.findall(reference.text) or [_POINTER.sub("", reference.text)]
        target = None
        for text in quoted:
            scored = sorted(((max(similarity(text, name) for name in [node.name, *node.aliases]), node.node_id)
                             for node in problems.values() if node.node_id != source_id), reverse=True)
            if scored and scored[0][0] >= 0.85:
                target = problems[scored[0][1]]
                break
        if target is None:
            continue
        for edge in graph.out_edges(target.node_id, *ENTRY_RELATIONS, *DIRECT_RELATIONS):
            end = graph.nodes[edge.target]
            relation = edge.relation
            if end.type == "FailureMode":
                relation = "MAY_INDICATE" if source.type == "Symptom" else "INDICATES"
            elif end.type == "CorrectiveAction":
                relation = "ADDRESSED_BY" if source.type == "Symptom" else "CLEARED_BY"
            if not end.mention_keys or graph.out_edges(source.node_id, relation) and any(
                    item.target == end.node_id for item in graph.out_edges(source.node_id, relation)):
                continue
            facts.append(Fact(
                fact_id=f"reference/{source.node_id}/{end.node_id}/{relation}", relation=relation,
                source=reference.mention, target=end.mention_keys[0], record=f"reference:{source.node_id}",
                conditions=[ContextItem(kind="if", text=f"as for '{target.name}' ({reference.text})")],
                evidence=by_key[reference.mention].evidence, origin="reference"))
    return facts


def link_named_parts(graph: Graph, mentions: list[Mention],
                     machine: set[str] | frozenset[str] = frozenset()) -> list[Fact]:
    """An item whose own name names a part of the machine is linked to that part.

    "Replace the V-belt" acts on the V-belt; "Worn drive roll" affects the drive roll. The link
    rests on the item's own words, read from the manual; it is marked ``name_mention`` so that a
    consumer, or a metric, can leave it out. Only the longest part name found counts, so a "fan
    motor" is not also linked to every "motor". A word that names the machine itself ("pump" in
    the manual of a pump) is no part: linking every item to it would only build an artificial hub.
    """

    # Every part the manual names counts, also one no fact has touched yet: the link brings it in.
    parts: dict[tuple[str, ...], Mention] = {}
    in_graph = {key: node.node_id for node in graph.nodes.values() if node.type == "Component"
                for key in node.mention_keys}
    for item in sorted(mentions, key=lambda value: (value.key not in in_graph, value.key)):
        if (item.type == "Component" and usable_component(item.name) and tokens(item.name)
                and not is_the_machine(item.name, machine)):
            parts.setdefault(tuple(tokens(item.name)), item)
    facts: list[Fact] = []
    for node in sorted(graph.nodes.values(), key=lambda item: item.node_id):
        relation = NAME_LINK.get(node.type)
        if relation is None or not node.mention_keys:
            continue
        linked = {edge.target for edge in graph.out_edges(node.node_id, relation)}
        words = tokens(node.name)
        spans: list[tuple[int, int, str]] = []
        for part, item in parts.items():
            size = len(part)
            for start in range(len(words) - size + 1):
                if tuple(words[start:start + size]) == part:
                    spans.append((start, start + size, item.key))
        # Keep maximal spans only.
        maximal = [span for span in spans if not any(other != span and other[0] <= span[0] and span[1] <= other[1]
                                                     and (other[1] - other[0]) > (span[1] - span[0]) for other in spans)]
        for key in sorted({key for _, _, key in maximal}):
            if in_graph.get(key) in linked or not node.evidence:
                continue
            facts.append(Fact(fact_id=f"name/{node.node_id}/{canonical(parts_name(parts, key))}", relation=relation,
                              source=node.mention_keys[0], target=key, record="name_mention",
                              evidence=node.evidence[0], origin="name_mention"))
    return facts


def parts_name(parts: dict[tuple[str, ...], Mention], key: str) -> str:
    return next(item.name for item in parts.values() if item.key == key)
