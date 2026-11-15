"""Stage 2, extract: each passage becomes records (problem, causes, actions) with the manual's words.

A record mirrors one source entry, so a cause never takes the remedy of the row beside it. The
model names parts from the catalogue, writes what the manual says about each item and cites
segment IDs. Nothing is discarded for a missing citation: such an item is anchored to the passage
that was read. A truncated answer splits the passage; table rows nobody used are read once more.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.kg_v3.contracts import ContextItem, ReadingUnit, SegmentKind
from backend.kg_v3.llm import TruncatedResponse
from backend.kg_v3.reader import DocumentText, render_segments
from backend.kg_v4.model import ACTION_KINDS, Evidence, Fact, Mention, Reference, UnitRecords
from backend.kg_v4.names import canonical
from backend.kg_v4.prompts import EXTRACT_PROMPT
from backend.kg_v4.sections import SectionIndex
from backend.kg_v4.survey import CATEGORIES, catalogue_brief, split_listed_parts, usable_component

logger = logging.getLogger(__name__)

EXTRACT_OUTPUT_TOKENS = 16000
MAX_SPLIT_DEPTH = 3
CONDITION_KINDS = ("if", "prerequisite", "warning", "expected", "order")
SEVERITIES = ("critical", "high", "medium", "low")
MATCH_THRESHOLD = 0.5
# Facts that link a problem, a cause and a remedy: a diagram page without any was not really read.
DIAGNOSTIC_LINKS = {"MAY_INDICATE", "INDICATES", "RESOLVED_BY", "ADDRESSED_BY", "CLEARED_BY"}


def _obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def item_schemas(segment_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Schemas of the items a model returns: citation list, action, cause and problem.

    Shared by extraction and by the gap search, so both return items of the same shape.
    Citations can only name segments that were shown.
    """

    text = {"type": "string"}
    cite = {"type": "array", "items": {"type": "string", "enum": sorted(set(segment_ids))} if segment_ids else text}
    conditions = {"type": "array", "items": _obj({"kind": {"type": "string", "enum": list(CONDITION_KINDS)},
                                                  "text": text})}
    action = _obj({"name": text, "kind": {"type": "string", "enum": list(ACTION_KINDS)}, "instruction": text,
                   "expected": text, "component": text, "conditions": conditions, "reference": text, "cite": cite})
    cause = _obj({"name": text, "description": text, "component": text, "conditions": conditions,
                  "no_remedy": {"type": "boolean"}, "cite": cite, "actions": {"type": "array", "items": action}})
    problem = _obj({"type": {"type": "string", "enum": ["Symptom", "ErrorCode", ""]}, "name": text, "code": text,
                    "description": text, "severity": {"type": "string", "enum": ["", *SEVERITIES]},
                    "component": text, "cite": cite})
    return {"cite": cite, "action": action, "cause": cause, "problem": problem}


def extraction_schema(segment_ids: list[str]) -> dict[str, Any]:
    """Strict schema of one extraction answer: records, described components, unclear passages."""

    text = {"type": "string"}
    items = item_schemas(segment_ids)
    record = _obj({"record": text, "problem": items["problem"], "see_also": text,
                   "actions": {"type": "array", "items": items["action"]},
                   "causes": {"type": "array", "items": items["cause"]}})
    component = _obj({"name": text, "part_of": text, "category": {"type": "string", "enum": ["", *CATEGORIES]},
                      "description": text, "cite": items["cite"]})
    return _obj({"records": {"type": "array", "items": record},
                 "components": {"type": "array", "items": component},
                 "unclear": {"type": "array", "items": _obj({"note": text, "cite": items["cite"]})}})


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())


class _Builder:
    """Turns one model answer into mentions and facts with evidence."""

    def __init__(self, doc: DocumentText, unit: ReadingUnit, sections: SectionIndex, read: str,
                 allowed: set[str]) -> None:
        self.doc, self.unit, self.sections, self.read, self.allowed = doc, unit, sections, read, allowed
        self.out = UnitRecords(unit_id=unit.unit_id, pages=list(unit.pages))
        self.components: dict[str, str] = {}
        self._owned = doc.segments(unit.segment_ids)

    def evidence(self, cites: list[str], text: str, fallback: Evidence | None = None) -> Evidence:
        valid = [cite for cite in dict.fromkeys(cites or []) if cite in self.allowed and self.doc.segment(cite)]
        if valid:
            first = self.doc.segment(valid[0])
            return Evidence(page=first.page, section=self.sections.section(valid[0], first.page),
                            segment_ids=valid, anchor="cited")
        # No citation: the fact stays, anchored where its words are found, or to its entry or passage.
        best, score = None, 0.0
        for segment in self._owned:
            value = _overlap(text, segment.text)
            if value > score:
                best, score = segment, value
        if best is not None and score >= MATCH_THRESHOLD:
            return Evidence(page=best.page, section=self.sections.section(best.segment_id, best.page),
                            segment_ids=[best.segment_id], anchor="matched")
        if fallback is not None:
            return fallback.model_copy(update={"anchor": "unit"})
        page = self.unit.pages[0]
        return Evidence(page=page, section=self.sections.section(page=page), anchor="unit")

    def mention(self, key: str, **fields: Any) -> Mention:
        mention = Mention(key=f"{self.unit.unit_id}/{self.read}/{key}", unit_id=self.unit.unit_id, **fields)
        self.out.mentions.append(mention)
        return mention

    def fact(self, relation: str, source: Mention, target: Mention, record: str,
             conditions: list[ContextItem] | None = None) -> None:
        cites = list(dict.fromkeys([*source.evidence.segment_ids, *target.evidence.segment_ids]))
        evidence = target.evidence.model_copy(update={"segment_ids": cites}) if cites else target.evidence
        self.out.facts.append(Fact(
            fact_id=f"{self.unit.unit_id}/{self.read}/f{len(self.out.facts) + 1}", relation=relation,
            source=source.key, target=target.key, record=f"{self.unit.unit_id}:{self.read}.{record}",
            conditions=conditions or [], evidence=evidence))

    def component(self, name: str, evidence: Evidence, **attributes: str) -> list[Mention]:
        """Mentions of the parts an item names; one mention per part and passage."""

        found = []
        for part in split_listed_parts(_clean(name)):
            if not usable_component(part):
                continue
            key = canonical(part)
            if key not in self.components:
                mention = self.mention(f"comp/{key}", type="Component", name=part, evidence=evidence,
                                       attributes={k: v for k, v in attributes.items() if v})
                self.components[key] = mention.key
            found.append(next(item for item in self.out.mentions if item.key == self.components[key]))
        return found

    def conditions(self, raw: Any, cites: list[str]) -> list[ContextItem]:
        items = []
        for value in raw or []:
            if isinstance(value, dict) and _clean(value.get("text")) and value.get("kind") in CONDITION_KINDS:
                items.append(ContextItem(kind=value["kind"], text=_clean(value["text"]),
                                         cite=tuple(cite for cite in cites if cite in self.allowed)))
        return sorted(set(items))

    def action(self, raw: dict[str, Any], key: str, record: str, parent: Mention | None, relation: str,
               fallback: Evidence | None) -> None:
        name = _clean(raw.get("name"))
        if not name:
            return
        kind = raw.get("kind") if raw.get("kind") in ACTION_KINDS else "repair"
        instruction, expected = _clean(raw.get("instruction")), _clean(raw.get("expected"))
        evidence = self.evidence(raw.get("cite") or [], f"{name} {instruction}", fallback)
        action = self.mention(key, type="CorrectiveAction", name=name, kind=kind, evidence=evidence, record=record,
                              attributes={k: v for k, v in (("instruction_text", instruction),
                                                            ("expected_result", expected)) if v})
        conditions = self.conditions(raw.get("conditions"), raw.get("cite") or [])
        if expected and not any(item.kind == "expected" for item in conditions):
            conditions = sorted({*conditions, ContextItem(kind="expected", text=expected,
                                                          cite=tuple(evidence.segment_ids))})
        if parent is not None:
            self.fact(relation, parent, action, record, conditions)
        for part in self.component(raw.get("component"), evidence):
            self.fact("ACTS_ON", action, part, record)
        reference = _clean(raw.get("reference"))
        if reference:
            self.out.references.append(Reference(text=reference, mention=action.key, unit_id=self.unit.unit_id,
                                                 page=evidence.page))

    def build(self, data: dict[str, Any]) -> UnitRecords:
        for number, raw in enumerate(data.get("records") or [], start=1):
            if not isinstance(raw, dict):
                continue
            record = _clean(raw.get("record")) or f"R{number}"
            record = f"{record}#{number}"  # two entries may get the same label from the model
            raw_problem = raw.get("problem") if isinstance(raw.get("problem"), dict) else {}
            problem = None
            kind, name, code = raw_problem.get("type"), _clean(raw_problem.get("name")), _clean(raw_problem.get("code"))
            if kind in {"Symptom", "ErrorCode"} and (name or code):
                if kind == "ErrorCode" and not code:
                    kind = "Symptom"  # an indication without a printed code is an observation
                attributes = {"severity": raw_problem["severity"]} if raw_problem.get("severity") in SEVERITIES else {}
                problem = self.mention(
                    f"{record}/p", type=kind, name=name or code, code=code if kind == "ErrorCode" else "",
                    description=_clean(raw_problem.get("description")), attributes=attributes, record=record,
                    evidence=self.evidence(raw_problem.get("cite") or [], f"{code} {name}"))
                if kind == "Symptom":
                    for part in self.component(raw_problem.get("component"), problem.evidence):
                        self.fact("OBSERVED_ON", problem, part, record)
            entry = problem.evidence if problem else None
            if problem is not None and _clean(raw.get("see_also")):
                self.out.references.append(Reference(text=_clean(raw["see_also"]), mention=problem.key,
                                                     unit_id=self.unit.unit_id, page=problem.evidence.page))
            direct = "ADDRESSED_BY" if problem and problem.type == "Symptom" else "CLEARED_BY"
            for index, item in enumerate(raw.get("actions") or [], start=1):
                if isinstance(item, dict):
                    self.action(item, f"{record}/a{index}", record, problem, direct, entry)
            for index, item in enumerate(raw.get("causes") or [], start=1):
                if not isinstance(item, dict) or not _clean(item.get("name")):
                    continue
                cause_name = _clean(item["name"])
                evidence = self.evidence(item.get("cite") or [], cause_name, entry)
                cause = self.mention(f"{record}/c{index}", type="FailureMode", name=cause_name, record=record,
                                     description=_clean(item.get("description")), evidence=evidence)
                if problem is not None:
                    self.fact("MAY_INDICATE" if problem.type == "Symptom" else "INDICATES", problem, cause, record,
                              self.conditions(item.get("conditions"), item.get("cite") or []))
                for part in self.component(item.get("component"), evidence):
                    self.fact("AFFECTS", cause, part, record)
                actions = [value for value in item.get("actions") or [] if isinstance(value, dict)]
                for position, value in enumerate(actions, start=1):
                    self.action(value, f"{record}/c{index}/a{position}", record, cause, "RESOLVED_BY", evidence)
                if item.get("no_remedy") and not actions:
                    self.out.no_remedy.append(cause.key)
        for raw in data.get("components") or []:
            if not isinstance(raw, dict) or not usable_component(_clean(raw.get("name"))):
                continue
            evidence = self.evidence(raw.get("cite") or [], _clean(raw.get("name")))
            parts = self.component(raw.get("name"), evidence, category=_clean(raw.get("category")))
            if parts and _clean(raw.get("description")) and not parts[0].description:
                position = self.out.mentions.index(parts[0])
                self.out.mentions[position] = parts[0].model_copy(update={"description": _clean(raw["description"])})
                parts[0] = self.out.mentions[position]
            for parent in self.component(raw.get("part_of"), evidence)[:1]:
                if parts and parent.key != parts[0].key:
                    self.fact("PART_OF", parts[0], parent, "structure")
        self.out.unclear = [{"note": _clean(item.get("note")), "cites": [c for c in item.get("cite") or []
                                                                         if c in self.allowed]}
                            for item in data.get("unclear") or [] if isinstance(item, dict)]
        return self.out


def _overlap(text: str, passage: str) -> float:
    """Share of a statement's words found in a segment (containment, order-free)."""

    words = set(canonical(text).split())
    if len(words) < 2:
        return 0.0
    return len(words & set(canonical(passage).split())) / len(words)


def merge_records(target: UnitRecords, part: UnitRecords) -> None:
    target.mentions.extend(part.mentions)
    target.facts.extend(part.facts)
    target.references.extend(part.references)
    target.no_remedy.extend(part.no_remedy)
    target.unclear.extend(part.unclear)
    target.notes.extend(part.notes)
    target.failed_reads += part.failed_reads
    target.reads += part.reads


def uncovered_rows(doc: DocumentText, unit: ReadingUnit, records: UnitRecords) -> list[str]:
    """Owned data rows of tables that no item cites: knowledge the first read may have skipped."""

    cited = {cite for mention in records.mentions for cite in mention.evidence.segment_ids}
    cited.update(cite for item in records.unclear for cite in item.get("cites") or [])
    rows = []
    for segment in doc.segments(unit.segment_ids):
        if segment.kind is not SegmentKind.TABLE_ROW or segment.segment_id in cited:
            continue
        headers = [item.casefold() for item in segment.table.headers]
        cells = [item.casefold() for item in segment.text.split(" | ")]
        if headers and cells == headers[:len(cells)]:
            continue
        rows.append(segment.segment_id)
    return rows


class Extractor:
    def __init__(self, llm, doc: DocumentText, sections: SectionIndex, *, asset_name: str, catalogue=(),
                 images: Any | None = None, concurrency: int = 6, output_tokens: int = EXTRACT_OUTPUT_TOKENS,
                 reread_rows: bool = True) -> None:
        self.llm, self.doc, self.sections = llm, doc, sections
        self.catalogue = list(catalogue)
        self.images = images
        self.system = EXTRACT_PROMPT.format(asset=asset_name)
        self.output_tokens = output_tokens
        self.reread_rows = reread_rows
        self._limit = asyncio.Semaphore(max(1, concurrency))

    def passage(self, unit: ReadingUnit) -> tuple[str, list[str], list[str]]:
        segment_ids = [*unit.context_segment_ids, *unit.segment_ids]
        ordered = sorted(self.doc.segments(segment_ids), key=lambda item: self.doc.position(item.segment_id) or 0)
        images, marks = self.images.for_segments(segment_ids) if self.images is not None else ([], {})
        text = render_segments(ordered, context=set(unit.context_segment_ids), doc=self.doc, marks=marks)
        head = catalogue_brief(self.catalogue, unit.pages)
        section = self.sections.section(page=unit.pages[0])
        title = f"Passage (section: {section}):" if section else "Passage:"
        return "\n".join(part for part in (head, title, text) if part), segment_ids, images

    async def _read(self, unit: ReadingUnit, read: str, depth: int = 0) -> UnitRecords:
        text, segment_ids, images = self.passage(unit)
        result = UnitRecords(unit_id=unit.unit_id, pages=list(unit.pages))
        try:
            async with self._limit:
                data = await self.llm.json(system=self.system, user=text, schema=extraction_schema(segment_ids),
                                           name="kg_v4_extract", max_output_tokens=self.output_tokens,
                                           images=images or None)
        except TruncatedResponse:
            if depth >= MAX_SPLIT_DEPTH or len(unit.segment_ids) < 2:
                result.failed_reads += 1
                result.notes.append(f"{read}: answer truncated and the passage cannot be split further")
                return result
            half = len(unit.segment_ids) // 2
            halves = [
                unit.model_copy(update={"segment_ids": unit.segment_ids[:half]}),
                unit.model_copy(update={"segment_ids": unit.segment_ids[half:], "context_segment_ids": list(
                    dict.fromkeys([*unit.context_segment_ids, *unit.segment_ids[:half][-2:]]))}),
            ]
            for label, part in zip("ab", await asyncio.gather(
                    *(self._read(item, f"{read}{label}", depth + 1) for item, label in zip(halves, "ab")))):
                merge_records(result, part)
            result.notes.append(f"{read}: passage split after a truncated answer")
            return result
        except Exception as exc:
            logger.warning("Read %s of %s failed: %s", read, unit.unit_id, exc)
            result.failed_reads += 1
            result.notes.append(f"{read}: read failed ({type(exc).__name__})")
            return result
        built = _Builder(self.doc, unit, self.sections, read, set(segment_ids)).build(data)
        built.reads = 1
        return built

    def unread_diagram_pages(self, unit: ReadingUnit, records: UnitRecords) -> list[int]:
        """Pages shown as images (flowcharts, diagrams) that yielded no problem-cause-remedy fact.

        A drawn page is the hardest to read and a read can come back empty for it without failing.
        """

        if self.images is None or records.failed_reads:
            return []
        read = {fact.evidence.page for fact in records.facts if fact.relation in DIAGNOSTIC_LINKS}
        read |= {segment.page for fact in records.facts if fact.relation in DIAGNOSTIC_LINKS
                 for segment in self.doc.segments(fact.evidence.segment_ids)}
        return sorted(page for page in set(unit.pages) & set(self.images.pages) - read
                      if any(segment.page == page for segment in self.doc.segments(unit.segment_ids)))

    async def extract(self, unit: ReadingUnit) -> UnitRecords:
        records = await self._read(unit, "A")
        missing = uncovered_rows(self.doc, unit, records) if self.reread_rows else []
        if missing and not records.failed_reads:
            headers = {f"p{row.page}.t{row.table.table}.r1" for row in self.doc.segments(missing)}
            focus = unit.model_copy(update={
                "segment_ids": missing,
                "context_segment_ids": list(dict.fromkeys(
                    [*unit.context_segment_ids, *(item for item in sorted(headers)
                                                  if item not in missing and self.doc.segment(item))])),
            })
            again = await self._read(focus, "C")
            for fact in again.facts:
                fact.origin = "reread"
            merge_records(records, again)
            records.notes.append(f"{len(missing)} unused table row(s) read again")
        for page in self.unread_diagram_pages(unit, records):
            owned = [segment.segment_id for segment in self.doc.segments(unit.segment_ids) if segment.page == page]
            # The titles of the earlier pages of the passage say which problem the diagram continues.
            titles = [segment.segment_id for earlier in unit.pages if earlier < page
                      for segment in self.doc.pages.get(earlier, [])[:2]]
            focus = unit.model_copy(update={"segment_ids": owned, "context_segment_ids": list(dict.fromkeys(
                [*unit.context_segment_ids, *titles]))})
            again = await self._read(focus, f"D{page}")
            for fact in again.facts:
                fact.origin = "reread"
            merge_records(records, again)
            records.notes.append(f"diagram page {page} read again: {len(again.facts)} fact(s)")
        return records

