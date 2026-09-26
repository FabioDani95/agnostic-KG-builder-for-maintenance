"""Interchangeable reviewers for the V3 gates.

The same Question can be answered by a person, a briefed agent, a test script
or an automatic policy. A ReviewerChain asks them in order: an unanswered or
unsure question moves to the next reviewer, so a person sees only what the
agents could not settle. Changing the chain in configuration turns a manual run
into a fully automated one without touching the stations.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict

from backend.kg_v3.contracts import (
    Answer,
    PageLabel,
    Question,
    ReviewerIdentity,
    ReviewerKind,
    validate_answer,
)
from backend.kg_v3.prompts import REVIEWER_BRIEF

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class Reviewer(Protocol):
    identity: ReviewerIdentity

    async def review(self, questions: Sequence[Question]) -> list[Answer]:
        """Answer what can be settled now; omit the rest or mark it unsure."""
        ...


def render_question(question: Question) -> str:
    """Plain-text form shown identically to a person and to an agent."""

    lines = [f"Question {question.question_id} ({question.kind.value})", question.title, ""]
    if question.source:
        lines.append("What the manual says:")
        lines.extend(f"  [{item.segment_id}] page {item.page}: {item.text}" for item in question.source)
        lines.append("")
    lines.append("What the system proposes:")
    lines.extend(f"  - {statement}" for statement in question.proposal)
    lines.extend(["", "Answer with one option ID:"])
    for option in question.options:
        needs = " (write the correction)" if option.needs_input else ""
        lines.append(f"  {option.option_id}: {option.label}{needs} -> {option.effect}")
    return "\n".join(lines)


class AutoReviewer:
    """Accept every proposal. For smoke tests and dry runs, never for real approvals."""

    identity = ReviewerIdentity(kind=ReviewerKind.AUTO, name="accept-proposal")

    async def review(self, questions: Sequence[Question]) -> list[Answer]:
        return [
            Answer(
                question_id=question.question_id,
                option_id=question.default_option_id,
                rationale="default option",
                answered_by=self.identity,
            )
            for question in questions
        ]


class ScriptedReviewer:
    """Answer from a fixture that maps a question ID or kind to an option or answer fields."""

    def __init__(self, script: Mapping[str, str | Mapping[str, Any]], *, name: str = "script") -> None:
        self.identity = ReviewerIdentity(kind=ReviewerKind.SCRIPT, name=name)
        self._script = dict(script)

    async def review(self, questions: Sequence[Question]) -> list[Answer]:
        answers = []
        for question in questions:
            entry = self._script.get(question.question_id, self._script.get(question.kind.value))
            if entry is None:
                continue
            fields = {"option_id": entry} if isinstance(entry, str) else dict(entry)
            answers.append(Answer(question_id=question.question_id, answered_by=self.identity, **fields))
        return answers


class QuestionStore(Protocol):
    def publish(self, questions: Sequence[Question]) -> None: ...

    def answer_for(self, question_id: str) -> Answer | None: ...


class InMemoryQuestionStore:
    """Process-local store for tests; the application uses a persistent store."""

    def __init__(self) -> None:
        self.questions: dict[str, Question] = {}
        self.answers: dict[str, Answer] = {}

    def publish(self, questions: Sequence[Question]) -> None:
        for question in questions:
            self.questions.setdefault(question.question_id, question)

    def open_questions(self) -> list[Question]:
        return [question for key, question in self.questions.items() if key not in self.answers]

    def submit(self, answer: Answer) -> None:
        question = self.questions.get(answer.question_id)
        if question is None:
            raise KeyError(answer.question_id)
        validate_answer(question, answer)
        self.answers[answer.question_id] = answer

    def answer_for(self, question_id: str) -> Answer | None:
        return self.answers.get(question_id)


class HumanReviewer:
    """Publish questions for a person and return the answers already given."""

    def __init__(self, store: QuestionStore, *, name: str = "operator") -> None:
        self.identity = ReviewerIdentity(kind=ReviewerKind.HUMAN, name=name)
        self._store = store

    async def review(self, questions: Sequence[Question]) -> list[Answer]:
        self._store.publish(questions)
        answers = (self._store.answer_for(question.question_id) for question in questions)
        return [answer for answer in answers if answer is not None]


class StructuredLLM(Protocol):
    """Adapter over the budgeted, archived gateway: one strict structured call."""

    async def __call__(self, *, system: str, user: str, schema: type[SchemaT]) -> SchemaT: ...


class PageLabelChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    label: PageLabel


class AgentDecision(BaseModel):
    """Strict structured-output shape of one agent answer."""

    model_config = ConfigDict(extra="forbid")

    option_id: str
    correction: str
    keep_statements: list[int]
    page_label_changes: list[PageLabelChange]
    rationale: str
    cited_segment_ids: list[str]
    confident: bool


class AgentReviewer:
    """A briefed model that answers the same questions a person would see."""

    def __init__(
        self,
        llm: StructuredLLM,
        *,
        model: str,
        brief: str = REVIEWER_BRIEF,
        max_concurrency: int = 4,
    ) -> None:
        self.identity = ReviewerIdentity(
            kind=ReviewerKind.AGENT,
            name=model,
            prompt_hash=hashlib.sha256(brief.encode("utf-8")).hexdigest(),
        )
        self._llm = llm
        self._brief = brief
        self._limit = asyncio.Semaphore(max(1, max_concurrency))

    async def review(self, questions: Sequence[Question]) -> list[Answer]:
        answers = await asyncio.gather(*(self._answer(question) for question in questions))
        return [answer for answer in answers if answer is not None]

    async def _answer(self, question: Question) -> Answer | None:
        async with self._limit:
            try:
                decision = await self._llm(system=self._brief, user=render_question(question), schema=AgentDecision)
            except Exception as exc:  # the question stays open for the next reviewer
                logger.warning("Agent reviewer left %s open: %s", question.question_id, exc)
                return None
        rationale = decision.rationale.strip()
        pages = {str(change.page): change.label.value for change in decision.page_label_changes}
        edits: dict[str, Any] = {}
        if pages:
            edits["pages"] = pages
        if decision.keep_statements:
            edits["keep"] = sorted(set(decision.keep_statements))
        try:
            answer = Answer(
                question_id=question.question_id,
                option_id=decision.option_id.strip(),
                text=decision.correction.strip(),
                edits=edits,
                rationale=rationale or "no rationale given",
                cited_segment_ids=decision.cited_segment_ids,
                # An unexplained decision is passed on rather than trusted.
                confident=decision.confident and bool(rationale),
                answered_by=self.identity,
            )
            validate_answer(question, answer)
        except ValueError as exc:
            logger.warning("Agent reviewer gave an unusable answer to %s: %s", question.question_id, exc)
            return None
        return answer


@dataclass(frozen=True)
class ChainOutcome:
    answers: list[Answer]
    pending: list[Question]


class ReviewerChain:
    """Ask reviewers in order; unanswered or unsure questions move to the next one.

    Pending questions have been seen by every reviewer and wait for the last
    one, normally a person. A resumed run asks only that reviewer again.
    """

    def __init__(self, reviewers: Sequence[Reviewer]) -> None:
        if not reviewers:
            raise ValueError("a gate needs at least one reviewer")
        self.reviewers = list(reviewers)

    async def review(self, questions: Sequence[Question]) -> ChainOutcome:
        settled: dict[str, Answer] = {}
        open_questions = list(questions)
        for reviewer in self.reviewers:
            if not open_questions:
                break
            by_id = {question.question_id: question for question in open_questions}
            for answer in await reviewer.review(open_questions):
                question = by_id.get(answer.question_id)
                if question is None or answer.question_id in settled or not answer.confident:
                    continue
                try:
                    validate_answer(question, answer)
                except ValueError:
                    continue
                settled[answer.question_id] = answer
            open_questions = [question for question in open_questions if question.question_id not in settled]
        return ChainOutcome(
            answers=[settled[question.question_id] for question in questions if question.question_id in settled],
            pending=open_questions,
        )
