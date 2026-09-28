"""Station 4, check: independent witnesses give each proposed relation a tier.

Witnesses: the page structure (both ends written in one table row or block, or
in two neighbouring blocks), agreement between the two reads, and a verifier
that sees only the cited text. Names are compared by meaning-preserving
normalisation and similarity, never by exact characters.
"""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from backend.kg_v3.contracts import (
    Assertion,
    Certificate,
    ReadingUnit,
    Tier,
    VerifierVerdict,
    Witness,
    context_text,
)
from backend.kg_v3.extractor import Proposal
from backend.kg_v3.llm import ModelClient
from backend.kg_v3.ontology import OntologySpec, verification_schema
from backend.kg_v3.prompts import VERIFY_PASSAGE_PROMPT, VERIFY_PROMPT
from backend.kg_v3.reader import DocumentText, render_segments

logger = logging.getLogger(__name__)

LOOSE_NAME_MATCH = 0.5
VERIFY_BATCH = 25
_DIGITS = re.compile(r"\d+")


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"(\w)-\s+(\w)", r"\1-\2", text)  # hyphenation across a line break
    text = re.sub(r"[^\w\s-]", " ", text)
    return " ".join(text.split()).strip(" -")


def similarity(left: str, right: str) -> float:
    a, b = normalize_name(left), normalize_name(right)
    if a == b:
        return 1.0
    if set(_DIGITS.findall(a)) != set(_DIGITS.findall(b)):
        return 0.0
    in_order = SequenceMatcher(None, a, b).ratio()
    any_order = SequenceMatcher(None, " ".join(sorted(a.split())), " ".join(sorted(b.split()))).ratio()
    return max(in_order, any_order)


def _end_matches(left, right, threshold: float) -> bool:
    # An end the source does not name ("Unspecified cause of ...") matches the named one.
    if left.type == right.type == "FailureMode" and (left.placeholder or right.placeholder):
        return True
    if left.type == right.type == "FailureMode" and not (left.stated and right.stated):
        return normalize_name(left.name) == normalize_name(right.name)
    return similarity(left.name, right.name) >= threshold


def _ends_match(left: Proposal, right: Proposal, threshold: float) -> bool:
    return (_end_matches(left.source, right.source, threshold)
            and _end_matches(left.target, right.target, threshold))


def context_key(proposal: Proposal) -> tuple:
    """Context identity excludes citation spelling, but never drops typed constraints."""
    return tuple(sorted((c.kind, normalize_name(c.text)) for c in proposal.conditions))


def same_relation(left: Proposal, right: Proposal) -> bool:
    """Same relation in two reads: equal names, or similar names cited at the same place.

    Similar names alone are not enough: 'low on up-stroke' and 'low on
    down-stroke' look alike but sit in different table rows.
    """

    if context_key(left) != context_key(right):
        return False
    if left.relation_type != right.relation_type:
        return False
    if left.source.code and right.source.code and normalize_name(left.source.code) != normalize_name(right.source.code):
        return False
    if (normalize_name(left.source.name), normalize_name(left.target.name)) == (
            normalize_name(right.source.name), normalize_name(right.target.name)):
        return True
    overlap = set(left.all_cites) & set(right.all_cites)
    return bool(overlap) and _ends_match(left, right, LOOSE_NAME_MATCH)


class Candidate(BaseModel):
    """Proposals of different reads that state the same relation."""

    candidate_id: str
    proposals: list[Proposal]
    structure: bool = False
    verdict: VerifierVerdict | None = None

    @property
    def lead(self) -> Proposal:
        return self.proposals[0]

    @property
    def reads(self) -> set[str]:
        return {proposal.read for proposal in self.proposals}

    @property
    def agreement(self) -> bool:
        return len(self.reads & {"A", "B"}) >= 2

    @property
    def cites(self) -> list[str]:
        return sorted({cite for proposal in self.proposals for cite in proposal.all_cites})


def group_candidates(proposals: list[Proposal]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for proposal in proposals:
        match = next(
            (item for item in candidates
             if item.lead.unit_id == proposal.unit_id and proposal.read not in item.reads
             and same_relation(item.lead, proposal)),
            None,
        )
        if match is None:
            candidates.append(Candidate(candidate_id=f"{proposal.unit_id}.c{len(candidates) + 1}", proposals=[proposal]))
        else:
            match.proposals.append(proposal)
    for candidate in candidates:  # the read that names both ends leads
        candidate.proposals.sort(key=lambda item: -(item.source.stated + item.target.stated))
    return candidates


def same_record(doc: DocumentText, left: str, right: str) -> bool:
    """Two segments of one source entry: one row (merged cells included), one step, or neighbours."""

    if left == right:
        return True
    a, b = doc.segment(left), doc.segment(right)
    if a is None or b is None or a.page != b.page:
        return False
    if a.table and b.table:
        if a.table.table != b.table.table:
            return False
        low, high = sorted((a, b), key=lambda item: item.table.row)
        # Rows below a merged cell repeat it: they stay in the entry the cell starts.
        rows = range(low.table.row + 1, high.table.row + 1)
        return all((segment := doc.segment(f"p{a.page}.t{a.table.table}.r{row}")) is not None
                   and segment.table.inherited_columns for row in rows)
    if a.table or b.table:
        return False
    group_a, group_b = doc.step_group(left), doc.step_group(right)
    if group_a is not None or group_b is not None:
        return group_a == group_b
    first, second = doc.position(left), doc.position(right)
    return first is not None and second is not None and abs(first - second) == 1


def _aligned_list_support(segment, proposal: Proposal) -> bool:
    """Multiple lists require a unique literal position match; wrapping is ambiguous.

    This grants a structural witness, not a semantic judgement. Paraphrases or
    uncertain line breaks must obtain another witness from the verifier.
    """
    if not segment.table or proposal.relation_type != "RESOLVED_BY":
        return True
    cells = segment.table.cell_items or [[cell] for cell in segment.text.split(" | ")]
    lists = [[piece.strip() for line in cell for piece in
              re.split(r"\n|[•●▪]|(?:^|\s)\d+[.)]\s+", line) if piece.strip()] for cell in cells]
    multiple = {column: values for column, values in enumerate(lists) if len(values) > 1}
    if len(multiple) < 2:
        return True

    def positions(name):
        key = normalize_name(name)
        return [(col, index) for col, values in multiple.items() for index, text in enumerate(values)
                if key and (key == normalize_name(text) or key in normalize_name(text))]

    left, right = positions(proposal.source.name), positions(proposal.target.name)
    return (len(left) == len(right) == 1 and left[0][0] != right[0][0]
            and left[0][1] == right[0][1]
            and len(multiple[left[0][0]]) == len(multiple[right[0][0]]))


def structurally_supported(doc: DocumentText, proposal: Proposal) -> bool:
    """Both ends are written in the entry that states the relation."""

    if any(not _aligned_list_support(segment, proposal) for segment in doc.segments(proposal.all_cites)):
        return False
    anchors = proposal.cites or sorted({*proposal.source.cites, *proposal.target.cites})
    for anchor in anchors:
        if not all(same_record(doc, anchor, other) for other in proposal.cites):
            continue
        if all(any(same_record(doc, anchor, cite) for cite in end.cites) or not end.cites
               for end in (proposal.source, proposal.target)):
            return True
    return False


def restates(proposal: Proposal) -> bool:
    """A problem-to-cause relation whose cause only repeats the problem."""

    return proposal.target.type == "FailureMode" and similarity(proposal.source.name, proposal.target.name) >= 0.9


def statement(spec: OntologySpec, proposal: Proposal) -> str:
    relation = spec.relation(proposal.relation_type)
    verb = relation.description if relation else proposal.relation_type
    if proposal.target.kind == "inspection":
        verb = "For this problem or cause the manual prescribes this check or test (it need not repair anything)."
    elif proposal.target.kind == "escalation":
        verb = "For this problem or cause the manual says to contact service or the dealer."
    code = f" (code {proposal.source.code})" if proposal.source.code else ""
    kind = f" [{proposal.target.kind}]" if proposal.target.kind else ""
    condition = f" Context: {context_text(proposal.conditions)}." if proposal.conditions else ""

    def unwritten(end) -> str:
        return " (not written in the manual)" if end.type == "FailureMode" and not end.stated else ""

    return (f"{proposal.source.type} '{proposal.source.name}'{unwritten(proposal.source)}{code} -> "
            f"{proposal.relation_type} -> {proposal.target.type} '{proposal.target.name}'"
            f"{unwritten(proposal.target)}{kind}. Meaning: {verb}{condition}")



STRUCTURE_READ = "S"
MAX_INHERITED_PROPOSALS = 300


def _origin_row(doc: DocumentText, segment, column: int):
    """The row whose cell a merged cell repeats: the nearest row above that does not inherit it."""

    row = segment.table.row - 1
    while row >= 1:
        above = doc.segment(f"p{segment.page}.t{segment.table.table}.r{row}")
        if above is None or above.table is None:
            return None
        if column not in above.table.inherited_columns:
            return above
        row -= 1
    return None


def inherited_cell_proposals(doc: DocumentText, proposals: list[Proposal]) -> list[Proposal]:
    """Hypotheses from merged cells: a remedy of the row a merged cell starts in, for each row repeating it.

    A merged cell holds one text for several rows; the reads often link its remedy to the
    first row only. The code proposes the remedy for the causes of every row that
    repeats the cell, and the checker keeps a proposal only when the verifier, reading
    that row, confirms it. The remedies of the first row's own cells are rejected there.
    """

    by_segment: dict[str, list[Proposal]] = {}
    for proposal in proposals:
        for cite in proposal.all_cites:
            by_segment.setdefault(cite, []).append(proposal)
    existing = {(item.unit_id, normalize_name(item.source.name), normalize_name(item.target.name), context_key(item))
                for item in proposals if item.relation_type == "RESOLVED_BY"}
    added: list[Proposal] = []
    for segment in doc.segments(sorted(by_segment)):
        if segment.table is None or not segment.table.confirmed_inherited_columns:
            continue
        unit_id = by_segment[segment.segment_id][0].unit_id
        causes: dict[str, object] = {}
        for item in by_segment[segment.segment_id]:
            if item.unit_id != unit_id:
                continue
            for end in (item.source, item.target):
                if end.type == "FailureMode":
                    causes.setdefault(normalize_name(end.name), end)
        for column in segment.table.confirmed_inherited_columns:
            origin = _origin_row(doc, segment, column)
            if origin is None:
                continue
            actions: list = []
            for item in by_segment.get(origin.segment_id, []):
                if (item.unit_id == unit_id and item.relation_type == "RESOLVED_BY"
                        and not any(similarity(item.target.name, other.target.name) >= 0.75
                                    and context_key(item) == context_key(other) for other in actions)):
                    actions.append(item)
            for cause_key, cause in causes.items():
                for original in actions:
                    action = original.target
                    key = (unit_id, cause_key, normalize_name(action.name), context_key(original))
                    if key in existing or len(added) >= MAX_INHERITED_PROPOSALS:
                        continue
                    existing.add(key)
                    added.append(Proposal(
                        unit_id=unit_id, read=STRUCTURE_READ, relation_type="RESOLVED_BY",
                        source=cause.model_copy(update={"cites": sorted({*cause.cites, segment.segment_id})}),
                        target=action.model_copy(update={"cites": [segment.segment_id]}),
                        record=f"inherited:{segment.segment_id}", cites=[segment.segment_id],
                        conditions=list(original.conditions),
                        notes=["remedy of a merged cell this row repeats; kept only when the verifier confirms it"],
                    ))
    return added


class CheckedRelation(BaseModel):
    """An assertion together with the proposals it came from, for merging."""

    assertion: Assertion
    proposals: list[Proposal] = Field(default_factory=list)


def unit_batches(candidates: list[Candidate], size: int = VERIFY_BATCH) -> list[list[Candidate]]:
    """Candidates of one unit together, so each verification reads one passage."""

    by_unit: dict[str, list[Candidate]] = {}
    for candidate in candidates:
        by_unit.setdefault(candidate.lead.unit_id, []).append(candidate)
    return [items[start:start + size] for items in by_unit.values() for start in range(0, len(items), size)]


class Checker:
    def __init__(self, llm: ModelClient, spec: OntologySpec, *, extractor_id: str, concurrency: int = 6,
                 units: list[ReadingUnit] | None = None) -> None:
        self.llm = llm
        self.spec = spec
        self.extractor_id = extractor_id
        self._limit = asyncio.Semaphore(max(1, concurrency))
        # With the reading units, the verifier reads the passage the extraction read.
        self.units = {unit.unit_id: unit for unit in units or []}

    def _evidence_text(self, doc: DocumentText, cites: list[str], passage: list[str] = ()) -> str:
        segments = doc.segments(sorted({*cites, *passage}))
        headers = {f"p{item.page}.t{item.table.table}.r1" for item in segments if item.table and item.table.row > 1}
        # A numbered step is read with the problem it belongs to and its parent step.
        steps = {context for item in doc.segments(cites) for context in doc.step_context(item.segment_id)}
        known = {item.segment_id for item in segments}
        extra = [doc.segment(item) for item in sorted(headers | steps) if doc.segment(item) and item not in known]
        ordered = sorted([*extra, *segments], key=lambda item: doc.position(item.segment_id) or 0)
        return render_segments(ordered, doc=doc)

    def _request(self, doc: DocumentText, batch: list[Candidate]) -> tuple[str, str]:
        unit = self.units.get(batch[0].lead.unit_id)
        if unit is not None and all(candidate.lead.unit_id == unit.unit_id for candidate in batch):
            passage = [*unit.context_segment_ids, *unit.segment_ids]
            cites = sorted({cite for candidate in batch for cite in candidate.cites})
            lines = [f"Statement S{index}: {statement(self.spec, candidate.lead)} Cited: {', '.join(candidate.cites)}"
                     for index, candidate in enumerate(batch, start=1)]
            return VERIFY_PASSAGE_PROMPT, ("Passage:\n" + self._evidence_text(doc, cites, passage)
                                           + "\n\nStatements:\n" + "\n".join(lines))
        blocks = [f"Statement S{index}: {statement(self.spec, candidate.lead)}\n"
                  f"Cited text:\n{self._evidence_text(doc, candidate.cites)}"
                  for index, candidate in enumerate(batch, start=1)]
        return VERIFY_PROMPT, "\n\n".join(blocks)

    async def _verify(self, doc: DocumentText, batch: list[Candidate]) -> None:
        system, user = self._request(doc, batch)
        ids = [f"S{index}" for index in range(1, len(batch) + 1)]
        try:
            async with self._limit:
                data = await self.llm.json(system=system, user=user,
                                           schema=verification_schema(ids), name="kg_v3_verify",
                                           max_output_tokens=4000)
        except Exception as exc:
            logger.warning("Verification batch failed: %s", exc)
            return
        verdicts = {str(item.get("id")): str(item.get("verdict")) for item in data.get("verdicts") or []}
        for statement_id, candidate in zip(ids, batch):
            try:
                candidate.verdict = VerifierVerdict(verdicts[statement_id])
            except (KeyError, ValueError):
                candidate.verdict = None

    async def check(self, doc: DocumentText, proposals: list[Proposal]) -> list[CheckedRelation]:
        by_unit: dict[str, list[Proposal]] = {}
        for proposal in proposals:
            by_unit.setdefault(proposal.unit_id, []).append(proposal)
        for proposal in inherited_cell_proposals(doc, proposals):
            by_unit.setdefault(proposal.unit_id, []).append(proposal)
        candidates = [candidate for items in by_unit.values() for candidate in group_candidates(items)]
        for candidate in candidates:
            candidate.structure = (any(structurally_supported(doc, item) for item in candidate.proposals)
                                   and not restates(candidate.lead))
        pending = [item for item in candidates if not (item.structure and item.agreement) or restates(item.lead)]
        await asyncio.gather(*(self._verify(doc, batch) for batch in unit_batches(pending)))
        # A structural hypothesis no read made survives only with the verifier's support.
        candidates = [candidate for candidate in candidates
                      if candidate.reads != {STRUCTURE_READ} or candidate.verdict is VerifierVerdict.SUPPORTED]
        return [CheckedRelation(assertion=self._assertion(candidate), proposals=candidate.proposals)
                for candidate in candidates]

    async def recheck_split(self, doc: DocumentText, before: list[CheckedRelation],
                            after: list[CheckedRelation]) -> list[CheckedRelation]:
        old = {r.assertion.assertion_id: r for r in before}
        changed = [r for r in after if r.assertion.assertion_id not in old
                   or r.assertion.certificate != old[r.assertion.assertion_id].assertion.certificate]
        candidates = [Candidate(candidate_id=r.assertion.assertion_id, proposals=r.proposals,
                                structure=Witness.STRUCTURE in r.assertion.certificate.witnesses) for r in changed]
        await asyncio.gather(*(self._verify(doc, batch) for batch in unit_batches(candidates)))
        updates = {c.candidate_id: CheckedRelation(assertion=self._assertion(c), proposals=c.proposals)
                   for c in candidates}
        return [updates.get(r.assertion.assertion_id, r) for r in after]

    async def repair_actions(self, doc: DocumentText, relations: list[CheckedRelation],
                             *, limit: int = 12) -> list[CheckedRelation]:
        """One bounded attempt to salvage only a supported portion of a rejected action.

        Originals remain auditable. A reduction is a new, independently verified
        assertion with the original typed context, never a reviewer override.
        """
        selected = [r for r in relations if r.assertion.relation_type == "RESOLVED_BY"
                    and (r.assertion.certificate.verifier_verdict is VerifierVerdict.NOT_SUPPORTED
                         or r.assertion.certificate.rejected_by is not None)][:max(0, limit)]
        if not selected:
            return []
        ids = [r.assertion.assertion_id for r in selected]
        schema = {"type": "object", "additionalProperties": False, "required": ["repairs"], "properties": {
            "repairs": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                "required": ["id", "action", "cites"], "properties": {
                    "id": {"type": "string", "enum": ids}, "action": {"type": "string"},
                    "cites": {"type": "array", "items": {"type": "string"}}}}}}}
        blocks = [f"{r.assertion.assertion_id}: {statement(self.spec, r.proposals[0])}\n"
                  f"{self._evidence_text(doc, r.assertion.certificate.segment_ids)}" for r in selected]
        try:
            data = await self.llm.json(name="kg_v3_reduce_action", schema=schema, max_output_tokens=3000,
                system="""For each rejected compound action retain only a strictly smaller portion supported
by its own source entry. Do not add any new instruction. Never borrow a neighbour's remedy.
Keep its cause and all typed conditions, warnings and prerequisites unchanged; if those are
wrong, return no repair. Return at most one reduction per id, with source segment citations.
If the entire action is unsupported or cannot be reduced, omit it.""", user="\n\n".join(blocks))
        except Exception as exc:
            logger.warning("Action reduction failed: %s", exc)
            return []
        by_id = {r.assertion.assertion_id: r for r in selected}
        proposals = []
        seen = set()
        for item in data.get("repairs", []):
            original = by_id.get(item.get("id"))
            if original is None or item["id"] in seen:
                continue
            lead = original.proposals[0]
            name = str(item.get("action") or "").strip()
            cites = sorted(set(item.get("cites", [])) & set(original.assertion.certificate.segment_ids))
            if not name or not cites or normalize_name(name) == normalize_name(lead.target.name):
                continue
            seen.add(item["id"])
            proposals.append((item["id"], lead.model_copy(update={
                "read": "repair", "target": lead.target.model_copy(update={"name": name, "cites": cites}),
                "cites": cites, "conditions": list(original.assertion.conditions),
                "notes": lead.notes + ["supported portion proposed from " + item["id"]]})))
        candidates = [Candidate(candidate_id=key + ".reduced", proposals=[p],
                                structure=structurally_supported(doc, p)) for key, p in proposals]
        await asyncio.gather(*(self._verify(doc, batch) for batch in unit_batches(candidates)))
        return [CheckedRelation(assertion=self._assertion(c), proposals=c.proposals) for c in candidates
                if c.verdict is VerifierVerdict.SUPPORTED and self._assertion(c).tier is not Tier.RED]

    def _assertion(self, candidate: Candidate) -> Assertion:
        witnesses = []
        if candidate.structure:
            witnesses.append(Witness.STRUCTURE)
        # A cause that repeats its problem adds no knowledge: never green on its own.
        if candidate.agreement and not restates(candidate.lead):
            witnesses.append(Witness.AGREEMENT)
        if candidate.verdict is VerifierVerdict.SUPPORTED:
            witnesses.append(Witness.VERIFIER)
        notes = sorted({note for proposal in candidate.proposals for note in proposal.notes})
        if not candidate.lead.source.stated or not candidate.lead.target.stated:
            notes.append("one end is not named in the source")
        if restates(candidate.lead):
            notes.append("the cause repeats the problem")
        lead = candidate.lead
        return Assertion(
            assertion_id=candidate.candidate_id,
            relation_type=lead.relation_type,
            source_key=f"{lead.source.type}:{lead.source.name}",
            target_key=f"{lead.target.type}:{lead.target.name}",
            record_key=f"{lead.unit_id}:{lead.read}.{lead.record}",
            conditions=sorted({condition for proposal in candidate.proposals for condition in proposal.conditions}),
            certificate=Certificate(
                segment_ids=candidate.cites,
                witnesses=witnesses,
                verifier_verdict=candidate.verdict,
                extractor=self.extractor_id,
                notes=notes,
            ),
        )
