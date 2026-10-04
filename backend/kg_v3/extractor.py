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
from backend.kg_v3.llm import ModelClient, TruncatedResponse, call_metadata
from backend.kg_v3.ontology import ACTION_KINDS, OntologySpec, extraction_schema, ontology_brief
from backend.kg_v3.prompts import EXTRACTION_PROMPT, QUALITY_EXTRACTION_RULES
from backend.kg_v3.quality_contracts import Denotation, Epistemic, EvidenceBinding, Method, ScopeStatus
from backend.kg_v3.reader import DocumentText, render_segments
from backend.kg_v3.source_index import bind_proposal, inventory_mentions

logger = logging.getLogger(__name__)

EXTRACTION_OUTPUT_TOKENS = 16000
# Name of a cause the source does not name and no check points to.
UNSPECIFIED_CAUSE = "Unspecified cause of"
MAX_SPLIT_DEPTH = 3


class Endpoint(BaseModel):
    model_config = {'extra': 'forbid'}
    mention_id: str = ''
    concept_id: str = ''
    instance_id: str = ''
    entry_id: str = ''
    branch_id: str = ''
    document_id: str = ''
    asset_scope_id: str = ''
    denotation_status: Denotation = 'LEGACY_UNCLASSIFIED'
    evidence_ref_ids: list[str] = Field(default_factory=list)
    type: str
    name: str
    code: str = ""
    kind: str = ""
    stated: bool = True
    cites: list[str] = Field(default_factory=list)

    @property
    def placeholder(self) -> bool:
        return self.denotation_status == 'PLACEHOLDER' or (self.denotation_status == 'LEGACY_UNCLASSIFIED'
                 and self.type == 'FailureMode' and self.name.startswith(UNSPECIFIED_CAUSE))


class Proposal(BaseModel):
    """One relation proposed by one read, with both ends resolved."""

    model_config = {'extra': 'forbid'}
    proposal_id: str = ''
    fact_fingerprint: str = ''
    entry_id: str = ''
    branch_id: str = ''
    scope_status: ScopeStatus = 'LEGACY_UNKNOWN'
    evidence_bindings: list[EvidenceBinding] = Field(default_factory=list)
    epistemic_status: Epistemic = 'LEGACY_UNCLASSIFIED'
    evidence_modalities: list[str] = Field(default_factory=list)
    premise_refs: list[str] = Field(default_factory=list)
    support_rationale: str = ''
    extraction_method: Method = 'PRIMARY'
    origin_call_id: str = ''
    origin_metadata: dict = Field(default_factory=dict)
    origin_request_id: str = ''
    review_trigger: str = ''
    parent_proposal_ids: list[str] = Field(default_factory=list)
    validation_issues: list[str] = Field(default_factory=list)
    search_hint: list[str] = Field(default_factory=list)
    schema_repaired: bool = False
    unit_id: str
    read: str
    relation_type: str
    source: Endpoint
    target: Endpoint
    record: str
    conditions: list[ContextItem] = Field(default_factory=list)
    context_bindings: list[dict] = Field(default_factory=list)
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
    raw_reads: list[dict[str, Any]] = Field(default_factory=list)
    entity_inventory: list[dict[str, Any]] = Field(default_factory=list)
    dispositions: list[dict[str, Any]] = Field(default_factory=list)
    unclear: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    failed_reads: int = 0
    failed_segments: list[str] = Field(default_factory=list)
    unresolved_references: list[dict[str, Any]] = Field(default_factory=list)


def extraction_prompt(spec: OntologySpec, asset_name: str) -> str:
    return EXTRACTION_PROMPT.format(asset=asset_name, ontology=ontology_brief(spec))


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


REPEAT_SIMILARITY = 0.9
# A cause the manual does not write, named almost like its problem, adds nothing but a restatement.
DERIVED_REPEAT_SIMILARITY = 0.8


def _repeats(problem: str, cause: str, threshold: float = REPEAT_SIMILARITY) -> bool:
    from backend.kg_v3.checker import similarity  # checker imports this module

    return similarity(problem, cause) >= threshold


def consistent_denotation(end: Endpoint) -> Endpoint:
    """The denotation status and the 'stated' flag of one entity tell the same story."""

    status = end.denotation_status
    if status == "LEGACY_UNCLASSIFIED":
        return end
    if end.type == "FailureMode" and end.name.startswith(UNSPECIFIED_CAUSE):
        status = "PLACEHOLDER"
    elif status == "STATED" and not end.stated:
        status = "INFERRED"
    return end.model_copy(update={"denotation_status": status, "stated": status == "STATED"})


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
        entities[key] = consistent_denotation(Endpoint(
            type=kind, name=name, code=" ".join(str(item.get("code") or "").split()),
            kind=action_kind if action_kind in ACTION_KINDS else "",
            stated=bool(item.get("stated", True)),
            denotation_status=item.get('denotation_status', 'LEGACY_UNCLASSIFIED'),
            cites=[cite for cite in item.get("cite") or [] if cite in allowed],
        ))
    # A cause that only repeats its problem is no cause: keep the chain with an unnamed one.
    for item in data.get("relations") or []:
        if not isinstance(item, dict):
            continue
        source, target = entities.get(str(item.get("source") or "")), entities.get(str(item.get("target") or ""))
        if (source and target and target.type == "FailureMode" and source.type != "FailureMode"
                and not target.placeholder and _repeats(source.name, target.name, REPEAT_SIMILARITY
                                                        if target.stated else DERIVED_REPEAT_SIMILARITY)):
            entities[str(item["target"])] = consistent_denotation(target.model_copy(update={
                "name": f"{UNSPECIFIED_CAUSE} {source.name[:1].lower()}{source.name[1:]}", "stated": False}))
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
        issues = []
        repaired_schema = False
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
            repaired_schema = True
            item_notes.append("relation type repaired from the types of its ends")
        cites = [cite for cite in item.get("cite") or [] if cite in allowed]
        if not cites and not (source.cites or target.cites):
            issues.append('MISSING_EVIDENCE')
            item_notes.append('MISSING_EVIDENCE: unit start is only a search hint')
        record = str(item.get("record") or f"R{index + 1}")
        context = list(item.get('conditions') or [])
        if relation.name == 'RESOLVED_BY':
            for shared in data.get('section_context') or []:
                if (isinstance(shared, dict) and record in shared.get('records', [])
                        and shared.get('kind') in {'warning', 'prerequisite'}):
                    context.append({**{k: shared[k] for k in ('kind', 'text', 'cite') if k in shared},
                                    'scope': 'section'})
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
            cites=cites, notes=item_notes, validation_issues=issues,
            search_hint=unit.segment_ids[:1] if 'MISSING_EVIDENCE' in issues else [], schema_repaired=repaired_schema,
            branch_id=str(item.get('branch_id') or ''), entry_id=str(item.get('entry_id') or ''),
            premise_refs=[c for c in item.get('premise_refs', []) if c in allowed],
            evidence_bindings=[EvidenceBinding(role='branch_path', evidence_ref_ids=item['branch_path_refs'])]
                              if item.get('branch_path_refs') else [],
            support_rationale=str(item.get('support_rationale') or ''),
        ))
    unclear = [
        {"unit_id": unit.unit_id, "read": read, "note": str(item.get("note") or ""),
         "cites": [cite for cite in item.get("cite") or [] if cite in allowed]}
        for item in data.get("unclear") or [] if isinstance(item, dict)
    ]
    return proposals, unclear, notes


class Extractor:
    def __init__(self, llm: ModelClient, spec: OntologySpec, *, asset_name: str, reads: int = 2,
                 output_tokens: int = EXTRACTION_OUTPUT_TOKENS, concurrency: int = 6,
                 images: Any | None = None, source_index=None, regions: Any | None = None) -> None:
        self.llm = llm
        self.source_index = source_index
        # Crops of catalogued image regions (vision.QualityImages), for pages without text.
        self.regions = regions
        # Page images (backend.kg_v3.vision.PageImages) for pages whose layout carries meaning.
        self.images = images
        self.spec = spec
        self.reads = max(1, reads)
        self.output_tokens = output_tokens
        self.system = extraction_prompt(spec, asset_name)
        if source_index is not None:
            self.system += QUALITY_EXTRACTION_RULES
        self.prompt_id = prompt_hash(self.system)
        self._limit = asyncio.Semaphore(max(1, concurrency))

    async def _read(self, doc: DocumentText, unit: ReadingUnit, read: str, depth: int = 0) -> UnitExtraction:
        result = await self._read_once(doc, unit, read, depth)
        structured = [s.segment_id for s in doc.segments(unit.segment_ids)
                      if s.table or doc.step_group(s.segment_id) is not None]
        if result.proposals or not structured:
            return result
        retry = await self._read_once(doc, unit, read, depth)
        retry.notes = result.notes + [f"{read}: empty structured reading retried"] + retry.notes
        if retry.proposals:
            return retry
        if depth == 0 and len(unit.segment_ids) >= 2:
            half = len(unit.segment_ids) // 2
            retry = UnitExtraction(unit_id=unit.unit_id, notes=retry.notes + [f"{read}: empty unit split in halves"])
            for ids in (unit.segment_ids[:half], unit.segment_ids[half:]):
                # Preserve the source window, including headers and merged-cell origins.
                context = list(dict.fromkeys(unit.context_segment_ids + [s for s in unit.segment_ids if s not in ids]))
                part = await self._read_once(doc, unit.model_copy(update={
                    "segment_ids": ids, "context_segment_ids": context}), read, depth + 1)
                retry.raw_reads.extend(part.raw_reads)
                retry.entity_inventory.extend(part.entity_inventory)
                retry.dispositions.extend(part.dispositions)
                retry.proposals.extend(part.proposals)
                retry.unclear.extend(part.unclear)
                retry.notes.extend(part.notes)
                retry.unresolved_references.extend(part.unresolved_references)
                retry.failed_reads += part.failed_reads
                if not part.proposals:
                    retry.failed_segments.extend(s for s in ids if s in structured)
        else:
            retry.failed_segments = structured
        return retry

    async def _read_once(self, doc: DocumentText, unit: ReadingUnit, read: str, depth: int = 0) -> UnitExtraction:
        # Both profiles read the same rendered passage in reading order and cite segment IDs;
        # the quality profile adds IDs for numbered cell items and image regions.
        segment_ids = [*unit.context_segment_ids, *unit.segment_ids]
        ordered = sorted(doc.segments(segment_ids), key=lambda item: doc.position(item.segment_id) or 0)
        images, marks = self.images.for_segments(segment_ids) if self.images is not None else ([], {})
        text = render_segments(ordered, context=set(unit.context_segment_ids), doc=doc, marks=marks)
        aliases: dict[str, str] = {}
        if self.source_index is not None:
            extra, aliases = quality_part_ids(self.source_index, ordered, unit)
            text = (text + "\n" + extra).strip()
            region_ids = [] if unit.segment_ids else unit.owned_region_ids
            if region_ids and self.regions is not None:
                images = [*images, *self.regions.crops(region_ids)]
        allowed = [*segment_ids, *aliases]
        result = UnitExtraction(unit_id=unit.unit_id)
        try:
            async with self._limit:
                data = await self.llm.json(system=self.system, user=text,
                                           schema=extraction_schema(self.spec, allowed, branches=[] if self.source_index is not None else None),
                                           name="kg_v3_extract", max_output_tokens=self.output_tokens,
                                           images=images or None)
        except TruncatedResponse:
            if depth >= MAX_SPLIT_DEPTH or len(unit.segment_ids) < 2:
                result.failed_reads += 1
                result.failed_segments.extend(unit.segment_ids or unit.owned_evidence_ref_ids)
                result.notes.append(f"{read}: answer truncated and the unit cannot be split further")
                return result
            half = len(unit.segment_ids) // 2
            parts = [
                unit.model_copy(update={"segment_ids": unit.segment_ids[:half]}),
                unit.model_copy(update={"segment_ids": unit.segment_ids[half:],
                                        "context_segment_ids": unit.context_segment_ids + unit.segment_ids[half - 1:half]}),
            ]
            for part in await asyncio.gather(*(self._read(doc, item, read, depth + 1) for item in parts)):
                result.raw_reads.extend(part.raw_reads)
                result.entity_inventory.extend(part.entity_inventory)
                result.dispositions.extend(part.dispositions)
                result.proposals.extend(part.proposals)
                result.unclear.extend(part.unclear)
                result.notes.extend(part.notes)
                result.unresolved_references.extend(part.unresolved_references)
                result.failed_reads += part.failed_reads
                result.failed_segments.extend(part.failed_segments)
            result.notes.append(f"{read}: unit split after a truncated answer")
            return result
        except Exception as exc:
            logger.warning("Read %s of %s failed: %s", read, unit.unit_id, exc)
            result.failed_reads += 1
            result.failed_segments.extend(unit.segment_ids or unit.owned_evidence_ref_ids)
            result.notes.append(f"{read}: read failed ({type(exc).__name__})")
            return result
        if aliases:
            data = translate_cites(data, aliases)
        proposals, unclear, notes = parse_read(data, unit=unit, read=read, spec=self.spec,
                                               allowed={*segment_ids, *aliases.values()})
        result.raw_reads.append({'read': read, 'data': data})
        result.entity_inventory.extend(data.get('entities') or [])
        from backend.kg_v3.references import resolve_references  # references imports this module
        proposals, result.unresolved_references = resolve_references(doc, unit, proposals)
        if self.source_index is not None:
            proposals = [bind_proposal(self.source_index, doc, p, unit) for p in proposals]
            inventory_mentions(self.source_index, data.get('entities') or [], unit, read)
            metadata = call_metadata(self.llm)
            proposals = [p.model_copy(update={'origin_call_id': metadata.get('call_id', ''), 'origin_metadata': metadata}) for p in proposals]
            result.raw_reads[-1]['call'] = metadata
        result.dispositions.extend({'proposal_id': p.proposal_id or p.record_key, 'issues': p.validation_issues}
                                   for p in proposals if p.validation_issues)
        if data.get("entities") and not proposals:
            notes.append(f"{read}: entities returned without usable relations; not counted as extraction coverage")
        result.proposals, result.unclear, result.notes = proposals, unclear, notes
        return result

    async def extract(self, doc: DocumentText, unit: ReadingUnit) -> UnitExtraction:
        labels = "ABCDEFG"[: self.reads]
        reads = await asyncio.gather(*(self._read(doc, unit, label) for label in labels))
        merged = UnitExtraction(unit_id=unit.unit_id)
        for item in reads:
            merged.raw_reads.extend(item.raw_reads)
            merged.entity_inventory.extend(item.entity_inventory)
            merged.dispositions.extend(item.dispositions)
            merged.proposals.extend(item.proposals)
            merged.unclear.extend(item.unclear)
            merged.notes.extend(item.notes)
            merged.unresolved_references.extend(item.unresolved_references)
            merged.failed_reads += item.failed_reads
            merged.failed_segments.extend(item.failed_segments)
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
            merged.failed_segments.extend(coverage.failed_segments)
            merged.notes.append(f"coverage: {len(missing)} unused table row(s) read again")
        cited = {c for p in merged.proposals for c in p.all_cites}
        merged.failed_segments = sorted(set(merged.failed_segments) - cited)
        return merged


def uncovered_rows(doc: DocumentText, unit: ReadingUnit, extraction: UnitExtraction) -> list[str]:
    """Owned data rows of tables that no proposal cites."""

    cited = {cite for proposal in extraction.proposals for cite in proposal.all_cites}
    index = getattr(doc, "source_index", None)
    if index is not None:  # a cited cell item cites its row
        cited |= {index.evidence[cite].segment_id for cite in cited if cite in index.evidence}
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


def quality_part_ids(index, segments, unit) -> tuple[str, dict[str, str]]:
    """IDs for the numbered items inside table cells and for image regions.

    A row ID cites the whole row; an item ID ("p51.t1.r2/2.3": column 2, item 3) cites one
    numbered cause or remedy exactly. Image regions are cited where a fact is only drawn.
    """
    aliases: dict[str, str] = {}
    lines: list[str] = []
    for segment in segments:
        for ref_id in index.atomic_refs.get(segment.segment_id, []):
            ref = index.evidence[ref_id]
            if ref.kind != "TABLE_ITEM":
                continue
            alias = f"{segment.segment_id}/{(ref.column or 0) + 1}.{ref.item_index}"
            aliases[alias] = ref_id
            lines.append(f"[{alias}] {ref.exact_text}")
    if lines:
        lines.insert(0, "Numbered items inside table cells (cite one when a relation uses only that item):")
    regions = [r for r in [*unit.owned_evidence_ref_ids, *unit.context_evidence_ref_ids]
               if r in index.evidence and index.evidence[r].kind == "VISUAL_REGION"]
    if regions:
        if not unit.segment_ids:
            lines.append(f"Page {', '.join(str(p) for p in unit.pages)} has no machine-readable text: "
                         "read the attached image(s).")
        lines.append("Image regions (cite them for facts read only from the image):")
        for number, ref_id in enumerate(sorted(regions, key=lambda r: (index.evidence[r].page,
                                                                       index.evidence[r].bbox or ())), 1):
            ref = index.evidence[ref_id]
            region = index.regions.get(ref.region_id)
            alias = f"p{ref.page}.img{number}"
            aliases[alias] = ref_id
            label = (region.kind if region else "PAGE").lower()
            transcription = f": {ref.transcription}" if ref.transcription else ""
            lines.append(f"[{alias}] {label} region{transcription}")
    return "\n".join(lines), aliases


def translate_cites(data: dict[str, Any], aliases: dict[str, str]) -> dict[str, Any]:
    """Replace part IDs by their evidence IDs everywhere the model cites."""

    def swap(values):
        return [aliases.get(value, value) for value in values or []] if isinstance(values, list) else values

    out = dict(data)
    for key in ("entities", "relations", "unclear"):
        items = []
        for item in data.get(key) or []:
            if isinstance(item, dict):
                item = dict(item)
                for field_name in ("cite", "cites", "premise_refs", "branch_path_refs"):
                    if field_name in item:
                        item[field_name] = swap(item[field_name])
                if isinstance(item.get("conditions"), list):
                    item["conditions"] = [{**c, "cite": swap(c.get("cite"))} if isinstance(c, dict) else c
                                          for c in item["conditions"]]
            items.append(item)
        out[key] = items
    return out
