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

from backend.kg_v3.contracts import Assertion, Certificate, VerifierVerdict, Witness
from backend.kg_v3.extractor import Proposal
from backend.kg_v3.llm import ModelClient
from backend.kg_v3.ontology import OntologySpec, verification_schema
from backend.kg_v3.prompts import VERIFY_PROMPT
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
    if left.type == right.type == "FailureMode" and not (left.stated and right.stated):
        return True
    return similarity(left.name, right.name) >= threshold


def _ends_match(left: Proposal, right: Proposal, threshold: float) -> bool:
    return (_end_matches(left.source, right.source, threshold)
            and _end_matches(left.target, right.target, threshold))


def same_relation(left: Proposal, right: Proposal) -> bool:
    """Same relation in two reads: equal names, or similar names cited at the same place.

    Similar names alone are not enough: 'low on up-stroke' and 'low on
    down-stroke' look alike but sit in different table rows.
    """

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


def structurally_supported(doc: DocumentText, proposal: Proposal) -> bool:
    """Both ends are written in the entry that states the relation."""

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
    condition = f" Conditions: {'; '.join(proposal.conditions)}." if proposal.conditions else ""
    return (f"{proposal.source.type} '{proposal.source.name}'{code} -> {proposal.relation_type} -> "
            f"{proposal.target.type} '{proposal.target.name}'{kind}. Meaning: {verb}{condition}")



class CheckedRelation(BaseModel):
    """An assertion together with the proposals it came from, for merging."""

    assertion: Assertion
    proposals: list[Proposal] = Field(default_factory=list)


class Checker:
    def __init__(self, llm: ModelClient, spec: OntologySpec, *, extractor_id: str, concurrency: int = 6) -> None:
        self.llm = llm
        self.spec = spec
        self.extractor_id = extractor_id
        self._limit = asyncio.Semaphore(max(1, concurrency))

    def _evidence_text(self, doc: DocumentText, cites: list[str]) -> str:
        segments = doc.segments(cites)
        headers = {f"p{item.page}.t{item.table.table}.r1" for item in segments if item.table and item.table.row > 1}
        # A numbered step is read with the problem it belongs to and its parent step.
        steps = {context for item in segments for context in doc.step_context(item.segment_id)}
        extra = [doc.segment(item) for item in sorted(headers | steps) if doc.segment(item) and item not in cites]
        ordered = sorted([*extra, *segments], key=lambda item: doc.position(item.segment_id) or 0)
        return render_segments(ordered, doc=doc)

    async def _verify(self, doc: DocumentText, batch: list[Candidate]) -> None:
        blocks = []
        for index, candidate in enumerate(batch, start=1):
            blocks.append(f"Statement S{index}: {statement(self.spec, candidate.lead)}\n"
                          f"Cited text:\n{self._evidence_text(doc, candidate.cites)}")
        ids = [f"S{index}" for index in range(1, len(batch) + 1)]
        try:
            async with self._limit:
                data = await self.llm.json(system=VERIFY_PROMPT, user="\n\n".join(blocks),
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
        candidates = [candidate for items in by_unit.values() for candidate in group_candidates(items)]
        for candidate in candidates:
            candidate.structure = (any(structurally_supported(doc, item) for item in candidate.proposals)
                                   and not restates(candidate.lead))
        pending = [item for item in candidates if not (item.structure and item.agreement) or restates(item.lead)]
        batches = [pending[index:index + VERIFY_BATCH] for index in range(0, len(pending), VERIFY_BATCH)]
        await asyncio.gather(*(self._verify(doc, batch) for batch in batches))
        return [CheckedRelation(assertion=self._assertion(candidate), proposals=candidate.proposals)
                for candidate in candidates]

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
