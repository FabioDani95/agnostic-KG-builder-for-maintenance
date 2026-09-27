"""Station 3, extract: two independent reads per unit, tolerant to small mistakes.

The model names things in its own words and cites segment IDs. A malformed item
is repaired when its meaning is clear (for example a reversed relation) and
otherwise noted; it never invalidates the rest of the answer. A truncated
answer splits the unit. Table rows that neither read used are read once more.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

from pydantic import BaseModel, Field

from backend.kg_v3.contracts import ContextItem, ReadingUnit, SegmentKind
from backend.kg_v3.llm import ModelClient, TruncatedResponse
from backend.kg_v3.ontology import ACTION_KINDS, OntologySpec, extraction_schema, ontology_brief
from backend.kg_v3.prompts import EXTRACTION_PROMPT
from backend.kg_v3.reader import DocumentText, render_segments

logger = logging.getLogger(__name__)

EXTRACTION_OUTPUT_TOKENS = 16000
# Name of a cause the source does not name and no check points to.
UNSPECIFIED_CAUSE = "Unspecified cause of"
MAX_SPLIT_DEPTH = 3


class Endpoint(BaseModel):
    type: str
    name: str
    code: str = ""
    kind: str = ""
    stated: bool = True
    cites: list[str] = Field(default_factory=list)

    @property
    def placeholder(self) -> bool:
        return self.type == "FailureMode" and self.name.startswith(UNSPECIFIED_CAUSE)


class Proposal(BaseModel):
    """One relation proposed by one read, with both ends resolved."""

    unit_id: str
    read: str
    relation_type: str
    source: Endpoint
    target: Endpoint
    record: str
    conditions: list[ContextItem] = Field(default_factory=list)
    cites: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def record_key(self) -> str:
        return f"{self.unit_id}:{self.read}:{self.record}"

    @property
    def all_cites(self) -> list[str]:
        return sorted({*self.cites, *self.source.cites, *self.target.cites,
                       *(cite for condition in self.conditions for cite in condition.cite)})


class UnitExtraction(BaseModel):
    unit_id: str
    proposals: list[Proposal] = Field(default_factory=list)
    unclear: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    failed_reads: int = 0
    unresolved_references: list[dict[str, Any]] = Field(default_factory=list)


def extraction_prompt(spec: OntologySpec, asset_name: str) -> str:
    return EXTRACTION_PROMPT.format(asset=asset_name, ontology=ontology_brief(spec))


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _repeats(problem: str, cause: str) -> bool:
    from backend.kg_v3.checker import similarity

    return similarity(problem, cause) >= 0.9


def parse_read(data: dict[str, Any], *, unit: ReadingUnit, read: str, spec: OntologySpec,
               allowed: set[str]) -> tuple[list[Proposal], list[dict[str, Any]], list[str]]:
    """Turn one raw answer into proposals, repairing what is clear and noting the rest."""

    notes: list[str] = []
    entities: dict[str, Endpoint] = {}
    for item in data.get("entities") or []:
        if not isinstance(item, dict):
            continue
        key, kind, name = str(item.get("key") or "").strip(), str(item.get("type") or ""), " ".join(str(item.get("name") or "").split())
        if not key or not name or kind not in spec.extractable_types:
            notes.append(f"{read}: entity {key or '?'} skipped (missing name or unknown type)")
            continue
        action_kind = str(item.get("kind") or "")
        entities[key] = Endpoint(
            type=kind, name=name, code=" ".join(str(item.get("code") or "").split()),
            kind=action_kind if action_kind in ACTION_KINDS else "",
            stated=bool(item.get("stated", True)),
            cites=[cite for cite in item.get("cite") or [] if cite in allowed],
        )
    # A cause that only repeats its problem is no cause: keep the chain with an unnamed one.
    for item in data.get("relations") or []:
        if not isinstance(item, dict):
            continue
        source, target = entities.get(str(item.get("source") or "")), entities.get(str(item.get("target") or ""))
        if (source and target and target.type == "FailureMode" and source.type != "FailureMode"
                and target.stated and _repeats(source.name, target.name)):
            entities[str(item["target"])] = target.model_copy(update={
                "name": f"{UNSPECIFIED_CAUSE} {source.name[:1].lower()}{source.name[1:]}", "stated": False})
            notes.append(f"{read}: cause '{target.name}' repeats its problem, marked unnamed")
    proposals: list[Proposal] = []
    for index, item in enumerate(data.get("relations") or []):
        if not isinstance(item, dict):
            continue
        source, target = entities.get(str(item.get("source") or "")), entities.get(str(item.get("target") or ""))
        if source is None or target is None:
            notes.append(f"{read}: relation {index} skipped (unknown entity)")
            continue
        relation = spec.relation(str(item.get("type") or ""))
        item_notes: list[str] = []
        if relation is None or (relation.domain, relation.range) != (source.type, target.type):
            repaired = spec.relation_between(source.type, target.type)
            reversed_ = spec.relation_between(target.type, source.type)
            if repaired is not None:
                relation = repaired
            elif reversed_ is not None:
                source, target, relation = target, source, reversed_
            else:
                notes.append(f"{read}: relation {index} skipped ({source.type} to {target.type} is not in the ontology)")
                continue
            item_notes.append("relation type repaired from the types of its ends")
        cites = [cite for cite in item.get("cite") or [] if cite in allowed]
        if not cites and not (source.cites or target.cites):
            cites = unit.segment_ids[:1]
            item_notes.append("approximate evidence: no citation given, unit start used")
        record = str(item.get("record") or f"R{index + 1}")
        context = list(item.get('conditions') or [])
        if relation.name == 'RESOLVED_BY':
            for shared in data.get('section_context') or []:
                if (isinstance(shared, dict) and record in shared.get('records', [])
                        and shared.get('kind') in {'warning', 'prerequisite'}):
                    context.append({k: shared[k] for k in ('kind', 'text', 'cite') if k in shared})
        conditions = []
        for value in context:
            try:
                condition = ContextItem.model_validate(value)
                conditions.append(condition.model_copy(update={'cite': tuple(c for c in condition.cite if c in allowed)}))
            except (ValueError, TypeError):
                item_notes.append('malformed context item; other facts retained')
        proposals.append(Proposal(
            unit_id=unit.unit_id, read=read, relation_type=relation.name, source=source, target=target,
            record=record,
            conditions=sorted(set(conditions)),
            cites=cites, notes=item_notes,
        ))
    unclear = [
        {"unit_id": unit.unit_id, "read": read, "note": str(item.get("note") or ""),
         "cites": [cite for cite in item.get("cite") or [] if cite in allowed]}
        for item in data.get("unclear") or [] if isinstance(item, dict)
    ]
    return proposals, unclear, notes


class Extractor:
    def __init__(self, llm: ModelClient, spec: OntologySpec, *, asset_name: str, reads: int = 2,
                 output_tokens: int = EXTRACTION_OUTPUT_TOKENS, concurrency: int = 6) -> None:
        self.llm = llm
        self.spec = spec
        self.reads = max(1, reads)
        self.output_tokens = output_tokens
        self.system = extraction_prompt(spec, asset_name)
        self.prompt_id = prompt_hash(self.system)
        self._limit = asyncio.Semaphore(max(1, concurrency))

    async def _read(self, doc: DocumentText, unit: ReadingUnit, read: str, depth: int = 0) -> UnitExtraction:
        allowed = [*unit.context_segment_ids, *unit.segment_ids]
        ordered = sorted(doc.segments(allowed), key=lambda item: doc.position(item.segment_id) or 0)
        text = render_segments(ordered, context=set(unit.context_segment_ids), doc=doc)
        result = UnitExtraction(unit_id=unit.unit_id)
        try:
            async with self._limit:
                data = await self.llm.json(system=self.system, user=text,
                                           schema=extraction_schema(self.spec, allowed),
                                           name="kg_v3_extract", max_output_tokens=self.output_tokens)
        except TruncatedResponse:
            if depth >= MAX_SPLIT_DEPTH or len(unit.segment_ids) < 2:
                result.failed_reads += 1
                result.notes.append(f"{read}: answer truncated and the unit cannot be split further")
                return result
            half = len(unit.segment_ids) // 2
            parts = [
                unit.model_copy(update={"segment_ids": unit.segment_ids[:half]}),
                unit.model_copy(update={"segment_ids": unit.segment_ids[half:],
                                        "context_segment_ids": unit.context_segment_ids + unit.segment_ids[half - 1:half]}),
            ]
            for part in await asyncio.gather(*(self._read(doc, item, read, depth + 1) for item in parts)):
                result.proposals.extend(part.proposals)
                result.unclear.extend(part.unclear)
                result.notes.extend(part.notes)
                result.unresolved_references.extend(part.unresolved_references)
                result.failed_reads += part.failed_reads
            result.notes.append(f"{read}: unit split after a truncated answer")
            return result
        except Exception as exc:
            logger.warning("Read %s of %s failed: %s", read, unit.unit_id, exc)
            result.failed_reads += 1
            result.notes.append(f"{read}: read failed ({type(exc).__name__})")
            return result
        proposals, unclear, notes = parse_read(data, unit=unit, read=read, spec=self.spec, allowed=set(allowed))
        from backend.kg_v3.references import resolve_references

        proposals, result.unresolved_references = resolve_references(doc, unit, proposals)
        if data.get("entities") and not proposals:
            notes.append(f"{read}: entities returned without usable relations; not counted as extraction coverage")
        result.proposals, result.unclear, result.notes = proposals, unclear, notes
        return result

    async def extract(self, doc: DocumentText, unit: ReadingUnit) -> UnitExtraction:
        labels = "ABCDEFG"[: self.reads]
        reads = await asyncio.gather(*(self._read(doc, unit, label) for label in labels))
        merged = UnitExtraction(unit_id=unit.unit_id)
        for item in reads:
            merged.proposals.extend(item.proposals)
            merged.unclear.extend(item.unclear)
            merged.notes.extend(item.notes)
            merged.unresolved_references.extend(item.unresolved_references)
            merged.failed_reads += item.failed_reads
        missing = uncovered_rows(doc, unit, merged)
        if missing:
            header_rows = {f"p{row.page}.t{row.table.table}.r1" for row in doc.segments(missing)}
            focus = unit.model_copy(update={
                "segment_ids": missing,
                "context_segment_ids": [item for item in sorted(header_rows) if item not in missing and doc.segment(item)],
            })
            coverage = await self._read(doc, focus, "C")
            merged.proposals.extend(proposal.model_copy(update={"unit_id": unit.unit_id}) for proposal in coverage.proposals)
            merged.unclear.extend(coverage.unclear)
            merged.unresolved_references.extend(coverage.unresolved_references)
            merged.notes.extend(coverage.notes)
            merged.failed_reads += coverage.failed_reads
            merged.notes.append(f"coverage: {len(missing)} unused table row(s) read again")
        return merged


def uncovered_rows(doc: DocumentText, unit: ReadingUnit, extraction: UnitExtraction) -> list[str]:
    """Owned data rows of tables that no proposal cites."""

    cited = {cite for proposal in extraction.proposals for cite in proposal.all_cites}
    # An all-unclear response must not suppress the single bounded coverage read.
    # After some facts are extracted, explicitly ambiguous rows remain abstentions.
    if extraction.proposals:
        cited.update(cite for item in extraction.unclear for cite in item.get("cites") or [])
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
