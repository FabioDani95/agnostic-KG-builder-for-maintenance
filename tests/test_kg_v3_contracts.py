"""V3 contracts: citable segments, single ownership, witness tiers, answerable questions."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.kg_v3.contracts import (
    OPTION_IDS,
    Answer,
    AnswerOption,
    Assertion,
    Certificate,
    DocumentMap,
    Gate,
    PageLabel,
    PageMapEntry,
    Question,
    QuestionKind,
    ReadingUnit,
    ReviewerIdentity,
    ReviewerKind,
    Segment,
    SegmentKind,
    SourceExcerpt,
    TableCoordinates,
    Tier,
    VerifierVerdict,
    Witness,
    assert_single_owner,
    assign_tier,
    validate_answer,
)

PERSON = ReviewerIdentity(kind=ReviewerKind.HUMAN, name="operator")
AGENT = ReviewerIdentity(kind=ReviewerKind.AGENT, name="gpt-6-luna", prompt_hash="abc")


def options(kind: QuestionKind) -> list[AnswerOption]:
    return [AnswerOption(option_id=item, label=item, effect=f"apply {item}") for item in sorted(OPTION_IDS[kind])]


def relation_question(**overrides) -> Question:
    fields = {
        "question_id": "q1",
        "kind": QuestionKind.RELATION_CHECK,
        "title": "Does the manual state this branch?",
        "source": [SourceExcerpt(segment_id="p11.t1.r2", page=11, text="Pump fails to operate. | Restricted line")],
        "proposal": ["Symptom 'Pump fails to operate' may indicate 'Restricted line'"],
        "options": options(QuestionKind.RELATION_CHECK),
        "default_option_id": "accept",
    }
    return Question(**{**fields, **overrides})


def test_segments_are_short_page_scoped_locators():
    row = Segment(
        segment_id="p11.t1.r3", page=11, kind=SegmentKind.TABLE_ROW, text="| Obstructed hose | Clear",
        evidence_id="ev_1", table=TableCoordinates(table=1, row=3, headers=["PROBLEM", "CAUSE", "SOLUTION"],
                                                  inherited_columns=[0]),
    )
    assert row.table.inherited_columns == [0]
    for segment_id in ("p38.b4", "p38.b4.2", "p7.o1"):
        Segment(segment_id=segment_id, page=int(segment_id[1:].split(".")[0]), kind=SegmentKind.TEXT,
                text="text", evidence_id="ev_2")
    with pytest.raises(ValidationError):
        Segment(segment_id="ev_abc", page=1, kind=SegmentKind.TEXT, text="text", evidence_id="ev_3")
    with pytest.raises(ValidationError):
        Segment(segment_id="p12.b1", page=11, kind=SegmentKind.TEXT, text="text", evidence_id="ev_4")
    with pytest.raises(ValidationError):
        Segment(segment_id="p11.b1", page=11, kind=SegmentKind.TEXT, text="text", evidence_id="ev_5",
                table=TableCoordinates(table=1, row=1))


def test_each_segment_is_read_by_one_unit_only():
    first = ReadingUnit(unit_id="u1", pages=[11], segment_ids=["p11.t1.r2", "p11.t1.r3"])
    second = ReadingUnit(unit_id="u2", pages=[11, 12], segment_ids=["p12.b1"], context_segment_ids=["p11.t1.r3"])
    assert_single_owner([first, second])
    with pytest.raises(ValueError, match="p11.t1.r3"):
        assert_single_owner([first, ReadingUnit(unit_id="u3", pages=[11], segment_ids=["p11.t1.r3"])])
    with pytest.raises(ValidationError):
        ReadingUnit(unit_id="u4", pages=[11], segment_ids=["p11.b1"], context_segment_ids=["p11.b1"])


def test_map_corrections_relabel_pages_and_clear_doubt():
    page_map = DocumentMap(entries=[
        PageMapEntry(page=84, label=PageLabel.DIAGNOSTIC),
        PageMapEntry(page=85, label=PageLabel.OTHER, unsure=True),
    ])
    corrected = page_map.relabel({85: PageLabel.PROCEDURE})
    assert corrected.pages_with(PageLabel.DIAGNOSTIC, PageLabel.PROCEDURE) == [84, 85]
    assert not corrected.entries[1].unsure
    with pytest.raises(ValueError):
        page_map.relabel({999: PageLabel.DIAGNOSTIC})
    with pytest.raises(ValidationError):
        DocumentMap(entries=[PageMapEntry(page=1, label=PageLabel.OTHER)] * 2)


S, A, V = Witness.STRUCTURE, Witness.AGREEMENT, Witness.VERIFIER


@pytest.mark.parametrize(
    ("witnesses", "verdict", "expected"),
    [
        ([S, A], None, Tier.GREEN),
        ([S, V], VerifierVerdict.SUPPORTED, Tier.GREEN),
        ([S], None, Tier.YELLOW),
        ([A], VerifierVerdict.UNCLEAR, Tier.YELLOW),
        ([V], VerifierVerdict.SUPPORTED, Tier.YELLOW),
        ([S, A], VerifierVerdict.NOT_SUPPORTED, Tier.YELLOW),
        ([], VerifierVerdict.NOT_SUPPORTED, Tier.RED),
        ([], VerifierVerdict.UNCLEAR, Tier.RED),
    ],
)
def test_two_witnesses_make_green_one_yellow_none_red(witnesses, verdict, expected):
    certificate = Certificate(segment_ids=["p11.t1.r2"], witnesses=witnesses, verifier_verdict=verdict)
    assert assign_tier(certificate) is expected


def test_reviewer_decisions_override_automatic_witnesses():
    confirmed = Certificate(segment_ids=["p11.b1"], witnesses=[Witness.REVIEWER], confirmed_by=AGENT)
    rejected = Certificate(segment_ids=["p11.b1"], witnesses=[S, A], rejected_by=PERSON)
    assert assign_tier(confirmed) is Tier.GREEN
    assert assign_tier(rejected) is Tier.RED
    for inconsistent in (
        {"witnesses": [V]},
        {"witnesses": [Witness.REVIEWER]},
        {"witnesses": [Witness.REVIEWER], "confirmed_by": AGENT, "rejected_by": PERSON},
        {"witnesses": [S, S]},
    ):
        with pytest.raises(ValidationError):
            Certificate(segment_ids=["p11.b1"], **inconsistent)


def test_assertions_round_trip_with_their_certificate():
    assertion = Assertion(
        assertion_id="a1", relation_type="MAY_INDICATE", source_key="E1", target_key="E2", record_key="u1:R1",
        conditions=["on the down-stroke"], certificate=Certificate(segment_ids=["p11.t1.r5"], witnesses=[S, A]),
    )
    restored = Assertion.model_validate(assertion.model_dump(mode="json"))
    assert restored == assertion
    assert restored.tier is Tier.GREEN


def test_questions_are_single_step_decisions():
    question = relation_question()
    assert question.gate is Gate.DOUBTS
    assert Question.model_validate(question.model_dump(mode="json")) == question
    for broken in (
        {"title": "Relation to check"},
        {"options": options(QuestionKind.MERGE_CHECK)},
        {"default_option_id": "correct"},
        {"source": []},
        {"proposal": []},
    ):
        with pytest.raises(ValidationError):
            relation_question(**broken)
    approval = Question(
        question_id="q2", kind=QuestionKind.GRAPH_APPROVAL, title="May this graph be used?",
        proposal=["120 green relations, 3 unanswered questions"], options=options(QuestionKind.GRAPH_APPROVAL),
        default_option_id="approve",
    )
    assert approval.gate is Gate.APPROVAL


def test_answers_must_be_applicable():
    question = relation_question()
    validate_answer(question, Answer(question_id="q1", option_id="accept", answered_by=PERSON))
    validate_answer(question, Answer(question_id="q1", option_id="correct", text="Cause is a worn seal",
                                     answered_by=PERSON))
    for answer in (
        Answer(question_id="q1", option_id="maybe", answered_by=PERSON),
        Answer(question_id="q1", option_id="correct", answered_by=PERSON),
        Answer(question_id="other", option_id="accept", answered_by=PERSON),
    ):
        with pytest.raises(ValueError):
            validate_answer(question, answer)
    with pytest.raises(ValidationError):
        Answer(question_id="q1", option_id="accept", answered_by=AGENT)
    with pytest.raises(ValidationError):
        ReviewerIdentity(kind=ReviewerKind.AGENT, name="gpt-6-luna")
