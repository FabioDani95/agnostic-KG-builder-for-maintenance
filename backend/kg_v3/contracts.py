"""Typed contracts exchanged by the V3 stations and gates.

Design rules encoded here (docs/PIANO_V3.md):

* The model cites system-owned segment IDs. Evidence text is taken from the
  segment, so different wording is never a reason to discard knowledge.
* Each segment belongs to exactly one reading unit; context is read-only.
* Every assertion carries a certificate: the independent witnesses that support
  it, the verifier verdict and the reviewer decision. Two witnesses make it
  green, one makes it yellow, none makes it red.
* A reviewer receives only questions that expect an answer. Option IDs are
  fixed per question kind, so an answer is applied the same way whether it came
  from a person, an agent or a test script.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SEGMENT_ID_PATTERN = r"^p[1-9]\d*\.(?:b\d+(?:\.\d+)?|t\d+\.r\d+|o\d+)$"


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ContextItem(_Contract):
    kind: Literal['if', 'prerequisite', 'warning', 'expected', 'order'] = 'if'
    text: str = Field(min_length=1)
    cite: tuple[str, ...] = ()

    @model_validator(mode='before')
    @classmethod
    def legacy_string(cls, value):
        return {'kind': 'if', 'text': value} if isinstance(value, str) else value

    def __lt__(self, other):
        return (self.kind, self.text, self.cite) < (other.kind, other.text, other.cite)


def context_text(items) -> str:
    return '; '.join(f'[{item.kind}] {item.text}' for value in items
                     for item in [ContextItem.model_validate(value)])


# Reading ------------------------------------------------------------------


class SegmentKind(StrEnum):
    TEXT = "text"
    TABLE_ROW = "table_row"
    OCR_TEXT = "ocr_text"


class TableCoordinates(_Contract):
    table: int = Field(ge=1)
    row: int = Field(ge=1)
    headers: list[str] = Field(default_factory=list)
    # Columns whose value was repeated from the row above (merged cells).
    inherited_columns: list[int] = Field(default_factory=list)
    confirmed_inherited_columns: list[int] = Field(default_factory=list)


class Segment(_Contract):
    """Smallest citable piece of a page: a text block, a sentence or a table row."""

    segment_id: str = Field(pattern=SEGMENT_ID_PATTERN)
    page: int = Field(ge=1)
    kind: SegmentKind
    text: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    bbox: tuple[float, float, float, float] | None = None
    table: TableCoordinates | None = None
    low_quality: bool = False

    @model_validator(mode="after")
    def _consistent(self) -> Segment:
        if not self.segment_id.startswith(f"p{self.page}."):
            raise ValueError("a segment ID starts with its own page")
        if (self.kind is SegmentKind.TABLE_ROW) != (self.table is not None):
            raise ValueError("table coordinates belong to table rows only")
        return self


# Mapping ------------------------------------------------------------------


class PageLabel(StrEnum):
    DIAGNOSTIC = "diagnostic"
    PROCEDURE = "procedure"
    PARTS = "parts"
    OTHER = "other"
    UNREADABLE = "unreadable"


class PageMapEntry(_Contract):
    page: int = Field(ge=1)
    label: PageLabel
    section: str = ""
    unsure: bool = False
    # Every independent map reading labelled the page diagnostic: a gate may not drop it.
    confirmed: bool = False


class DocumentMap(_Contract):
    """One label per physical page. The map gate may correct it."""

    entries: list[PageMapEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _one_entry_per_page(self) -> DocumentMap:
        pages = [entry.page for entry in self.entries]
        if len(pages) != len(set(pages)):
            raise ValueError("each page has exactly one map entry")
        return self

    def pages_with(self, *labels: PageLabel) -> list[int]:
        return sorted(entry.page for entry in self.entries if entry.label in labels)

    def relabel(self, changes: dict[int, PageLabel]) -> DocumentMap:
        """Apply a reviewer's corrections; corrected pages are no longer unsure."""

        unknown = set(changes) - {entry.page for entry in self.entries}
        if unknown:
            raise ValueError(f"unknown pages: {sorted(unknown)}")
        return DocumentMap(entries=[
            entry.model_copy(update={"label": changes[entry.page], "unsure": False})
            if entry.page in changes else entry
            for entry in self.entries
        ])


class ReadingUnit(_Contract):
    """Pages read together. Owned segments are extracted; context is read-only."""

    unit_id: str = Field(min_length=1)
    section: str = ""
    pages: list[int] = Field(min_length=1)
    segment_ids: list[str] = Field(min_length=1)
    context_segment_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _context_is_not_owned(self) -> ReadingUnit:
        if set(self.segment_ids) & set(self.context_segment_ids):
            raise ValueError("a segment is either owned or context, never both")
        return self


def assert_single_owner(units: Iterable[ReadingUnit]) -> None:
    """Every segment is extracted by exactly one unit, so nothing is read twice by accident."""

    owner: dict[str, str] = {}
    for unit in units:
        for segment_id in unit.segment_ids:
            if segment_id in owner:
                raise ValueError(f"segment {segment_id} is owned by {owner[segment_id]} and {unit.unit_id}")
            owner[segment_id] = unit.unit_id


# Checking -----------------------------------------------------------------


class Witness(StrEnum):
    STRUCTURE = "structure"  # both ends cited in the same row, block or entry
    AGREEMENT = "agreement"  # found by both independent reads
    VERIFIER = "verifier"  # a check restricted to the cited text found it
    REVIEWER = "reviewer"  # a person, agent or script confirmed it


class VerifierVerdict(StrEnum):
    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"
    UNCLEAR = "unclear"


class Tier(StrEnum):
    GREEN = "green"  # enters the graph
    YELLOW = "yellow"  # becomes a question
    RED = "red"  # stays out of the graph, listed in the run report


class ReviewerKind(StrEnum):
    HUMAN = "human"
    AGENT = "agent"
    SCRIPT = "script"
    AUTO = "auto"


class ReviewerIdentity(_Contract):
    kind: ReviewerKind
    name: str = Field(min_length=1)
    # An agent decision is reproducible only with the exact brief it received.
    prompt_hash: str = ""

    @model_validator(mode="after")
    def _agent_is_traceable(self) -> ReviewerIdentity:
        if self.kind is ReviewerKind.AGENT and not self.prompt_hash:
            raise ValueError("an agent reviewer needs the hash of its brief")
        return self

    @property
    def label(self) -> str:
        return f"{self.kind.value}:{self.name}"


class Certificate(_Contract):
    """Why an assertion is in the graph, and who decided about it."""

    segment_ids: list[str] = Field(min_length=1)
    witnesses: list[Witness] = Field(default_factory=list)
    verifier_verdict: VerifierVerdict | None = None
    confirmed_by: ReviewerIdentity | None = None
    rejected_by: ReviewerIdentity | None = None
    extractor: str = ""
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _consistent(self) -> Certificate:
        if len(self.witnesses) != len(set(self.witnesses)):
            raise ValueError("each witness is listed once")
        if (Witness.VERIFIER in self.witnesses) != (self.verifier_verdict is VerifierVerdict.SUPPORTED):
            raise ValueError("the verifier witness means a supported verdict")
        if (Witness.REVIEWER in self.witnesses) != (self.confirmed_by is not None):
            raise ValueError("the reviewer witness names who confirmed")
        if self.confirmed_by is not None and self.rejected_by is not None:
            raise ValueError("an assertion is either confirmed or rejected")
        return self


def assign_tier(certificate: Certificate) -> Tier:
    """Two witnesses: green. One, or witnesses in conflict: yellow. None: red.

    A reviewer decision overrides the automatic witnesses.
    """

    if certificate.rejected_by is not None:
        return Tier.RED
    witnesses = set(certificate.witnesses)
    if Witness.REVIEWER in witnesses:
        return Tier.GREEN
    support = len(witnesses & {Witness.STRUCTURE, Witness.AGREEMENT, Witness.VERIFIER})
    if certificate.verifier_verdict is VerifierVerdict.NOT_SUPPORTED:
        return Tier.YELLOW if support else Tier.RED
    if support >= 2:
        return Tier.GREEN
    return Tier.YELLOW if support == 1 else Tier.RED


class Assertion(_Contract):
    """One ontology relation proposed for the graph, with its certificate."""

    assertion_id: str = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    source_key: str = Field(min_length=1)
    target_key: str = Field(min_length=1)
    # Source occurrence (table row, list entry, paragraph) the relation comes from.
    record_key: str = Field(min_length=1)
    conditions: list[ContextItem] = Field(default_factory=list)
    certificate: Certificate

    @property
    def tier(self) -> Tier:
        return assign_tier(self.certificate)


# Asking -------------------------------------------------------------------


class Gate(StrEnum):
    MAP = "map"  # is the page map right?
    DOUBTS = "doubts"  # is this uncertain knowledge right?
    APPROVAL = "approval"  # may the graph be used?


class QuestionKind(StrEnum):
    MAP_REVIEW = "map_review"
    RELATION_CHECK = "relation_check"
    MERGE_CHECK = "merge_check"
    UNREADABLE_PAGE = "unreadable_page"
    GRAPH_APPROVAL = "graph_approval"


GATE_OF_KIND: dict[QuestionKind, Gate] = {
    QuestionKind.MAP_REVIEW: Gate.MAP,
    QuestionKind.RELATION_CHECK: Gate.DOUBTS,
    QuestionKind.MERGE_CHECK: Gate.DOUBTS,
    QuestionKind.UNREADABLE_PAGE: Gate.DOUBTS,
    QuestionKind.GRAPH_APPROVAL: Gate.APPROVAL,
}

# Fixed option IDs per kind: stations apply an answer by its ID.
OPTION_IDS: dict[QuestionKind, frozenset[str]] = {
    QuestionKind.MAP_REVIEW: frozenset({"confirm", "correct"}),
    QuestionKind.RELATION_CHECK: frozenset({"accept", "reject", "correct"}),
    QuestionKind.MERGE_CHECK: frozenset({"same", "different"}),
    QuestionKind.UNREADABLE_PAGE: frozenset({"skip", "transcribe"}),
    QuestionKind.GRAPH_APPROVAL: frozenset({"approve", "reject"}),
}

# Choosing one of these requires a correction in the answer text or edits.
INPUT_OPTION_IDS = frozenset({"correct", "transcribe"})

# Kinds that must show the manual's own words next to the proposal.
SOURCED_KINDS = frozenset({QuestionKind.RELATION_CHECK, QuestionKind.MERGE_CHECK})


class SourceExcerpt(_Contract):
    segment_id: str = Field(pattern=SEGMENT_ID_PATTERN)
    page: int = Field(ge=1)
    text: str = Field(min_length=1)


class AnswerOption(_Contract):
    option_id: str = Field(min_length=1)
    label: str = Field(min_length=1)  # what a person reads on the button
    effect: str = Field(min_length=1)  # what happens to the graph if chosen

    @property
    def needs_input(self) -> bool:
        return self.option_id in INPUT_OPTION_IDS


class Question(_Contract):
    """One decision a reviewer can take in one step, without looking elsewhere."""

    question_id: str = Field(min_length=1)
    kind: QuestionKind
    title: str = Field(min_length=1)
    source: list[SourceExcerpt] = Field(default_factory=list)
    proposal: list[str] = Field(min_length=1)  # what the system believes, in plain statements
    options: list[AnswerOption] = Field(min_length=2)
    default_option_id: str = Field(min_length=1)
    priority: int = 0
    # Machine reference to what the answer changes: assertion IDs, pages, node keys.
    target: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _answerable(self) -> Question:
        if not self.title.rstrip().endswith("?"):
            raise ValueError("a question title must be a question")
        ids = [option.option_id for option in self.options]
        if len(ids) != len(set(ids)) or set(ids) != OPTION_IDS[self.kind]:
            raise ValueError(f"{self.kind.value} questions offer exactly {sorted(OPTION_IDS[self.kind])}")
        if self.default_option_id not in ids or self.default_option_id in INPUT_OPTION_IDS:
            raise ValueError("the default option is a listed option that needs no input")
        if self.kind in SOURCED_KINDS and not self.source:
            raise ValueError(f"{self.kind.value} questions show what the manual says")
        return self

    @property
    def gate(self) -> Gate:
        return GATE_OF_KIND[self.kind]


class Answer(_Contract):
    question_id: str = Field(min_length=1)
    option_id: str = Field(min_length=1)
    text: str = ""
    edits: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    cited_segment_ids: list[str] = Field(default_factory=list)
    # False hands the question to the next reviewer instead of deciding.
    confident: bool = True
    answered_by: ReviewerIdentity
    answered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _agents_explain(self) -> Answer:
        if self.answered_by.kind is ReviewerKind.AGENT and not self.rationale.strip():
            raise ValueError("an agent answer states its reason")
        return self


def validate_answer(question: Question, answer: Answer) -> None:
    """Raise ValueError unless the answer can be applied to this question."""

    if answer.question_id != question.question_id:
        raise ValueError("the answer refers to another question")
    option = next((item for item in question.options if item.option_id == answer.option_id), None)
    if option is None:
        raise ValueError(f"unknown option {answer.option_id!r}")
    if option.needs_input and not (answer.text.strip() or answer.edits):
        raise ValueError(f"option {answer.option_id!r} needs a correction")
