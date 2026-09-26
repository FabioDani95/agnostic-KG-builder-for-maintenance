"""Station 6, ask: yellow facts of one source entry become one clear question.

Questions show the manual's words, numbered statements and the effect of each
option. Answers are applied by option ID, whoever gave them: accept confirms
all statements, reject removes them, correct keeps only the listed numbers.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict

from backend.kg_v3.checker import CheckedRelation, statement
from backend.kg_v3.contracts import (
    Answer,
    AnswerOption,
    Certificate,
    PageLabel,
    Question,
    QuestionKind,
    SourceExcerpt,
    Tier,
    Witness,
)
from backend.kg_v3.mapper import DocumentMap
from backend.kg_v3.merger import MergePair
from backend.kg_v3.ontology import OntologySpec
from backend.kg_v3.reader import DocumentText, render_segment

_PRIORITY = {"RESOLVED_BY": 3, "INDICATES": 3, "MAY_INDICATE": 2, "AFFECTS": 1}
MAX_EXCERPTS = 8


def _excerpts(doc: DocumentText, cites: list[str]) -> list[SourceExcerpt]:
    segments = doc.segments(cites)
    headers = [f"p{item.page}.t{item.table.table}.r1" for item in segments if item.table and item.table.row > 1]
    ordered = [*dict.fromkeys(item for item in headers if doc.segment(item) and item not in cites), *cites]
    excerpts = []
    for segment in doc.segments(ordered)[:MAX_EXCERPTS]:
        text = render_segment(segment).split("] ", 1)[-1]
        excerpts.append(SourceExcerpt(segment_id=segment.segment_id, page=segment.page, text=text))
    return excerpts


def relation_questions(doc: DocumentText, spec: OntologySpec, relations: list[CheckedRelation]) -> list[Question]:
    groups: dict[str, list[CheckedRelation]] = defaultdict(list)
    for relation in relations:
        if relation.assertion.tier is Tier.YELLOW:
            groups[relation.assertion.record_key].append(relation)
    # The same statements found in several entries become one question.
    merged: dict[tuple[str, ...], list[CheckedRelation]] = {}
    for record_key, items in sorted(groups.items()):
        signature = tuple(sorted(statement(spec, item.proposals[0]) for item in items))
        merged.setdefault(signature, []).extend(items)
    questions = []
    for items in merged.values():
        record_key = items[0].assertion.record_key
        cites = sorted({cite for item in items for cite in item.assertion.certificate.segment_ids},
                       key=lambda value: doc.position(value) or 0)
        statements = list(dict.fromkeys(statement(spec, item.proposals[0]) for item in items))
        proposal = [f"{index}. {text}" for index, text in enumerate(statements, start=1)]
        questions.append(Question(
            question_id=f"rel:{record_key}",
            kind=QuestionKind.RELATION_CHECK,
            title="Does the manual state these troubleshooting facts?",
            source=_excerpts(doc, cites) or _excerpts(doc, items[0].assertion.certificate.segment_ids),
            proposal=proposal,
            options=[
                AnswerOption(option_id="accept", label="Yes, all correct", effect="all statements enter the graph as verified"),
                AnswerOption(option_id="reject", label="No, none is stated", effect="the statements stay out of the graph"),
                AnswerOption(option_id="correct", label="Only some are correct",
                             effect="only the statement numbers you list enter the graph"),
            ],
            default_option_id="accept",
            priority=max(_PRIORITY.get(item.assertion.relation_type, 1) for item in items) * 10 + len(items),
            target={"assertion_ids": [item.assertion.assertion_id for item in items],
                    "statement_of": [statements.index(statement(spec, item.proposals[0])) + 1 for item in items]},
        ))
    return sorted(questions, key=lambda item: -item.priority)


def merge_questions(doc: DocumentText, pairs: list[MergePair]) -> list[Question]:
    questions = []
    for pair in pairs:
        cites = [*pair.left_cites[:1], *pair.right_cites[:1]]
        source = _excerpts(doc, cites)
        if not source:
            continue
        questions.append(Question(
            question_id=f"merge:{pair.left}|{pair.right}",
            kind=QuestionKind.MERGE_CHECK,
            title=f"Do '{pair.left_name}' and '{pair.right_name}' denote the same {pair.type}?",
            source=source,
            proposal=[f"Keep '{pair.left_name}' and '{pair.right_name}' as two separate {pair.type} nodes."],
            options=[
                AnswerOption(option_id="same", label="Same thing", effect="the two nodes become one, both names kept as aliases"),
                AnswerOption(option_id="different", label="Different things", effect="the two nodes stay separate"),
            ],
            default_option_id="different",
            priority=5,
            target={"left": pair.left, "right": pair.right},
        ))
    return questions


def unreadable_questions(page_map: DocumentMap) -> list[Question]:
    diagnostic = set(page_map.pages_with(PageLabel.DIAGNOSTIC))
    questions = []
    for page in page_map.pages_with(PageLabel.UNREADABLE):
        if not {page - 1, page + 1} & diagnostic:
            continue
        questions.append(Question(
            question_id=f"page:{page}",
            kind=QuestionKind.UNREADABLE_PAGE,
            title=f"Page {page} has no readable text next to diagnostic pages: should it be transcribed?",
            proposal=[f"Page {page} is probably a figure or a scan; the system could not read it."],
            options=[
                AnswerOption(option_id="skip", label="Skip it", effect="the page stays out of the graph"),
                AnswerOption(option_id="transcribe", label="Transcribe it",
                             effect="your transcription is kept in the run report for the next extraction"),
            ],
            default_option_id="skip",
            priority=4,
            target={"page": page},
        ))
    return questions


def approval_question(summary: list[str]) -> Question:
    # A changed graph needs a new approval: the ID follows the summary.
    digest = hashlib.sha256("\n".join(summary).encode("utf-8")).hexdigest()[:8]
    return Question(
        question_id=f"approval:{digest}",
        kind=QuestionKind.GRAPH_APPROVAL,
        title="May this graph be used by the maintenance agent?",
        proposal=summary,
        options=[
            AnswerOption(option_id="approve", label="Approve", effect="the graph is published for use"),
            AnswerOption(option_id="reject", label="Reject", effect="the graph stays a draft"),
        ],
        default_option_id="approve",
        priority=0,
    )


def _decided(certificate: Certificate, answer: Answer, keep: bool) -> Certificate:
    if keep:
        witnesses = [*certificate.witnesses, Witness.REVIEWER]
        return certificate.model_copy(update={"witnesses": list(dict.fromkeys(witnesses)),
                                              "confirmed_by": answer.answered_by, "rejected_by": None})
    witnesses = [item for item in certificate.witnesses if item is not Witness.REVIEWER]
    return certificate.model_copy(update={"witnesses": witnesses, "confirmed_by": None,
                                          "rejected_by": answer.answered_by})


def apply_relation_answers(relations: list[CheckedRelation], questions: list[Question],
                           answers: list[Answer]) -> list[CheckedRelation]:
    by_question = {item.question_id: item for item in questions}
    decisions: dict[str, tuple[Answer, bool]] = {}
    for answer in answers:
        question = by_question.get(answer.question_id)
        if question is None or question.kind is not QuestionKind.RELATION_CHECK:
            continue
        ids = list(question.target.get("assertion_ids") or [])
        numbers = list(question.target.get("statement_of") or range(1, len(ids) + 1))
        keep_numbers = {int(item) for item in answer.edits.get("keep") or [] if str(item).isdigit()}
        for number, assertion_id in zip(numbers, ids):
            keep = answer.option_id == "accept" or (answer.option_id == "correct" and number in keep_numbers)
            decisions[assertion_id] = (answer, keep)
    updated = []
    for relation in relations:
        decision = decisions.get(relation.assertion.assertion_id)
        if decision is None:
            updated.append(relation)
            continue
        answer, keep = decision
        certificate = _decided(relation.assertion.certificate, answer, keep)
        if answer.text:
            certificate = certificate.model_copy(update={"notes": [*certificate.notes, f"reviewer: {answer.text}"]})
        assertion = relation.assertion.model_copy(update={"certificate": certificate})
        updated.append(relation.model_copy(update={"assertion": assertion}))
    return updated


def merge_decisions(questions: list[Question], answers: list[Answer], pairs: list[MergePair]) -> list[MergePair]:
    """Pairs a reviewer declared the same thing."""

    same = {answer.question_id for answer in answers if answer.option_id == "same"}
    return [pair for pair in pairs if f"merge:{pair.left}|{pair.right}" in same]
