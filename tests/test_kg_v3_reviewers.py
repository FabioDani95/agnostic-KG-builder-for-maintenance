"""V3 gates: a person, an agent or a script answer the same questions interchangeably."""

from __future__ import annotations

import asyncio
import hashlib

import pytest

from backend.kg_v3.contracts import (
    OPTION_IDS,
    Answer,
    AnswerOption,
    PageLabel,
    Question,
    QuestionKind,
    ReviewerIdentity,
    ReviewerKind,
    SourceExcerpt,
)
from backend.kg_v3.prompts import REVIEWER_BRIEF
from backend.kg_v3.reviewers import (
    AgentDecision,
    AgentReviewer,
    AutoReviewer,
    HumanReviewer,
    InMemoryQuestionStore,
    PageLabelChange,
    ReviewerChain,
    ScriptedReviewer,
    render_question,
)

PERSON = ReviewerIdentity(kind=ReviewerKind.HUMAN, name="operator")


def question(question_id: str, kind: QuestionKind = QuestionKind.RELATION_CHECK) -> Question:
    sourced = kind is QuestionKind.RELATION_CHECK
    return Question(
        question_id=question_id,
        kind=kind,
        title="Is this right?",
        source=[SourceExcerpt(segment_id="p11.t1.r2", page=11, text="Pump fails to operate. | Bleeder valve is open")]
        if sourced else [],
        proposal=["Symptom 'Pump fails to operate' may indicate 'Bleeder valve is open'"]
        if sourced else ["Pages 65-77 and 82-104 are diagnostic; page 85 is other"],
        options=[AnswerOption(option_id=item, label=item.title(), effect=f"apply {item}")
                 for item in sorted(OPTION_IDS[kind])],
        default_option_id="accept" if sourced else "confirm",
    )


def decision(option_id: str = "accept", **overrides) -> AgentDecision:
    fields = {
        "option_id": option_id, "correction": "", "keep_statements": [], "page_label_changes": [],
        "rationale": "Same table row states both.", "cited_segment_ids": ["p11.t1.r2"], "confident": True,
    }
    return AgentDecision(**{**fields, **overrides})


class FakeLLM:
    """Returns a prepared decision per question and records what the agent saw."""

    def __init__(self, decisions: dict[str, AgentDecision | Exception]) -> None:
        self.decisions = decisions
        self.seen: list[tuple[str, str]] = []

    async def __call__(self, *, system, user, schema):
        assert schema is AgentDecision
        self.seen.append((system, user))
        result = self.decisions[user.split()[1]]
        if isinstance(result, Exception):
            raise result
        return result


def test_person_and_agent_see_the_same_complete_question():
    text = render_question(question("q1"))
    for expected in ("Is this right?", "[p11.t1.r2] page 11:", "- Symptom 'Pump fails to operate'",
                     "accept: Accept -> apply accept", "correct: Correct (write the correction)"):
        assert expected in text


def test_auto_and_scripted_reviewers_run_gates_without_people():
    questions = [question("q1"), question("q2"), question("m1", QuestionKind.MAP_REVIEW)]
    auto = asyncio.run(AutoReviewer().review(questions))
    assert [(item.question_id, item.option_id) for item in auto] == [("q1", "accept"), ("q2", "accept"),
                                                                      ("m1", "confirm")]
    script = ScriptedReviewer({"q2": {"option_id": "reject", "rationale": "different rows"}, "map_review": "confirm"})
    scripted = asyncio.run(script.review(questions))
    assert [(item.question_id, item.option_id) for item in scripted] == [("q2", "reject"), ("m1", "confirm")]
    assert all(item.answered_by.kind is ReviewerKind.SCRIPT for item in scripted)


def test_person_answers_later_through_the_store():
    store = InMemoryQuestionStore()
    person = HumanReviewer(store)
    assert asyncio.run(person.review([question("q1")])) == []
    assert [item.question_id for item in store.open_questions()] == ["q1"]
    with pytest.raises(ValueError):
        store.submit(Answer(question_id="q1", option_id="correct", answered_by=PERSON))
    store.submit(Answer(question_id="q1", option_id="reject", answered_by=PERSON))
    assert [item.option_id for item in asyncio.run(person.review([question("q1")]))] == ["reject"]
    assert store.open_questions() == []


def test_agent_answers_are_traceable_to_model_and_brief():
    llm = FakeLLM({"q1": decision()})
    answers = asyncio.run(AgentReviewer(llm, model="gpt-6-luna").review([question("q1")]))
    assert answers[0].option_id == "accept"
    assert answers[0].answered_by.label == "agent:gpt-6-luna"
    assert answers[0].answered_by.prompt_hash == hashlib.sha256(REVIEWER_BRIEF.encode("utf-8")).hexdigest()
    system, user = llm.seen[0]
    assert system == REVIEWER_BRIEF
    assert user == render_question(question("q1"))


def test_agent_can_verify_and_correct_the_page_map():
    changes = [PageLabelChange(page=85, label=PageLabel.PROCEDURE)]
    llm = FakeLLM({"m1": decision("correct", page_label_changes=changes, rationale="Page 85 holds test values.")})
    answers = asyncio.run(AgentReviewer(llm, model="gpt-6-luna").review([question("m1", QuestionKind.MAP_REVIEW)]))
    assert answers[0].option_id == "correct"
    assert answers[0].edits == {"pages": {"85": "procedure"}}


def test_unusable_agent_answers_leave_the_question_open():
    llm = FakeLLM({
        "q1": decision("maybe"),
        "q2": RuntimeError("provider timeout"),
        "q3": decision("correct"),
        "q4": decision(rationale=""),
    })
    answers = asyncio.run(AgentReviewer(llm, model="gpt-6-luna").review(
        [question("q1"), question("q2"), question("q3"), question("q4")]
    ))
    assert [(item.question_id, item.confident) for item in answers] == [("q4", False)]


def test_chain_sends_a_person_only_what_the_agent_could_not_settle():
    store = InMemoryQuestionStore()
    agent = AgentReviewer(FakeLLM({"q1": decision(confident=False), "q2": decision("reject")}), model="gpt-6-luna")
    chain = ReviewerChain([agent, HumanReviewer(store)])
    outcome = asyncio.run(chain.review([question("q1"), question("q2")]))
    assert [(item.question_id, item.answered_by.kind) for item in outcome.answers] == [("q2", ReviewerKind.AGENT)]
    assert [item.question_id for item in outcome.pending] == ["q1"]
    assert [item.question_id for item in store.open_questions()] == ["q1"]

    store.submit(Answer(question_id="q1", option_id="accept", answered_by=PERSON))
    resumed = asyncio.run(ReviewerChain([HumanReviewer(store)]).review(outcome.pending))
    assert [(item.question_id, item.answered_by.kind) for item in resumed.answers] == [("q1", ReviewerKind.HUMAN)]
    assert resumed.pending == []
    with pytest.raises(ValueError):
        ReviewerChain([])
