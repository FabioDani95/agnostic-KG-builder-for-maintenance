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
    ReviewerKind,
    SourceExcerpt,
    Tier,
    Witness,
    validate_answer,
)
from backend.kg_v3.mapper import DocumentMap
from backend.kg_v3.merger import MergePair
from backend.kg_v3.ontology import OntologySpec
from backend.kg_v3.reader import DocumentText, render_segment
from backend.kg_v3.run_state import digest
from backend.kg_v3.source_index import HUMAN_ISSUES, RESOLVABLE_ISSUES

_PRIORITY = {"RESOLVED_BY": 3, "INDICATES": 3, "MAY_INDICATE": 2, "AFFECTS": 1}
MAX_HEADERS = 4


def _excerpts(doc: DocumentText, cites: list[str]) -> list[SourceExcerpt]:
    # Every cited segment is shown: a reviewer cannot confirm a statement it does not see.
    segments = doc.segments(cites)
    headers = [f"p{item.page}.t{item.table.table}.r1" for item in segments if item.table and item.table.row > 1]
    headers = list(dict.fromkeys(item for item in headers if doc.segment(item) and item not in cites))
    ordered = [*headers[:MAX_HEADERS], *cites]
    excerpts = []
    for segment in doc.segments(ordered):
        text = render_segment(segment).split("] ", 1)[-1]
        excerpts.append(SourceExcerpt(segment_id=segment.segment_id, page=segment.page, text=text))
    return excerpts


def relation_questions(doc: DocumentText, spec: OntologySpec, relations: list[CheckedRelation]) -> list[Question]:
    groups: dict[str, list[CheckedRelation]] = defaultdict(list)
    for relation in relations:
        if relation.assertion.tier is Tier.YELLOW:
            groups[(relation.assertion.branch_id, relation.assertion.record_key)].append(relation)
    # The same statements found in several entries become one question.
    merged: dict[tuple[str, ...], list[CheckedRelation]] = {}
    for record_key, items in sorted(groups.items()):
        signature = (tuple(sorted(statement(spec, item.proposals[0]) for item in items)),
                     tuple(sorted((item.assertion.branch_id, assertion_fingerprint(item.assertion)) for item in items)))
        merged.setdefault(signature, []).extend(items)
    questions = []
    for items in merged.values():
        record_key = items[0].assertion.record_key
        cites = sorted({cite for item in items for cite in item.assertion.certificate.segment_ids},
                       key=lambda value: doc.position(value) or 0)
        statements = list(dict.fromkeys(statement(spec, item.proposals[0]) for item in items))
        proposal = [f"{index}. {text}" for index, text in enumerate(statements, start=1)]
        fingerprints = {i.assertion.assertion_id: assertion_fingerprint(i.assertion) for i in items}
        fingerprint = digest(fingerprints)
        regions = []
        if doc.source_index:
            regions = [doc.source_index.regions[doc.source_index.evidence[r].region_id].model_dump(mode='json')
                       for i in items for r in i.assertion.certificate.evidence_ref_ids
                       if doc.source_index.evidence[r].kind == 'VISUAL_REGION']
        questions.append(Question(
            question_id=f"rel:{record_key}:{fingerprint[:20]}", content_fingerprint=fingerprint, source_regions=regions,
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
            target={"quality": any(i.assertion.branch_id for i in items), "assertion_fingerprints": fingerprints, "assertion_ids": [item.assertion.assertion_id for item in items],
                    "statement_of": [statements.index(statement(spec, item.proposals[0])) + 1 for item in items]},
        ))
    return sorted(questions, key=lambda item: -item.priority)


def merge_questions(doc: DocumentText, pairs: list[MergePair]) -> list[Question]:
    questions = []
    for pair in pairs:
        cites = [*pair.left_cites[:1], *pair.right_cites[:1]]
        regions = []
        if doc.source_index:
            refs = [doc.source_index.evidence[r] for r in cites if r in doc.source_index.evidence]
            regions = [doc.source_index.regions[r.region_id].model_dump(mode='json') for r in refs if r.region_id]
            # Segment citations stay; a cited cell item shows its row.
            cites = list(dict.fromkeys([*(c for c in cites if doc.segment(c)), *(r.segment_id for r in refs if r.segment_id)]))
        source = _excerpts(doc, cites)
        if not source and not regions:
            continue
        questions.append(Question(
            question_id=f"merge:{pair.left}|{pair.right}",
            kind=QuestionKind.MERGE_CHECK,
            title=f"Do '{pair.left_name}' and '{pair.right_name}' denote the same {pair.type}?",
            source=source, source_regions=regions,
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


def approval_question(summary: list[str], approval_payload=None) -> Question:
    # A changed graph needs a new approval: the ID follows the summary.
    fingerprint = digest(approval_payload) if approval_payload is not None else hashlib.sha256("\n".join(summary).encode("utf-8")).hexdigest()
    short = fingerprint[:24]
    return Question(
        question_id=f"approval:{short}", content_fingerprint=fingerprint, target={"approval_fingerprint": fingerprint},
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
        kind = answer.answered_by.kind
        reviewed = kind in {ReviewerKind.HUMAN, ReviewerKind.AGENT}
        if certificate.contract_version == 'kg-ingestion-quality-1' and reviewed:
            # The reviewer read the shown source: it settles what a verifier settles;
            # only a person settles a source conflict or a required human review.
            cleared = RESOLVABLE_ISSUES | (HUMAN_ISSUES if kind is ReviewerKind.HUMAN else frozenset())
            certificate = certificate.model_copy(update={
                'validation_issues': [i for i in certificate.validation_issues if i not in cleared]})
            if not certificate.validation_issues:
                certificate = certificate.model_copy(update={
                    'scope_status': 'VERIFIED_REVIEW',
                    'verified_bindings': [b.model_copy(update={'support_status': 'SUPPORTED',
                        'verification_call_id': f'{kind.value}:' + answer.question_id}) for b in certificate.verified_bindings],
                    'verifier_metadata': [*certificate.verifier_metadata, {'kind': f'{kind.value.upper()}_SOURCE_REVIEW',
                        'question_id': answer.question_id, 'reviewer': answer.answered_by.model_dump(mode='json')}]})
        elif kind is ReviewerKind.HUMAN:
            certificate = certificate.model_copy(update={'validation_issues': [i for i in certificate.validation_issues if i != 'HUMAN_REVIEW_REQUIRED']})
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
        validate_answer(question, answer)
        if answer.content_fingerprint and answer.content_fingerprint != question.content_fingerprint:
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
        question = by_question[answer.question_id]
        expected = question.target.get('assertion_fingerprints', {}).get(relation.assertion.assertion_id)
        if expected and expected != assertion_fingerprint(relation.assertion):
            updated.append(relation)
            continue
        old_decider = relation.assertion.certificate.confirmed_by or relation.assertion.certificate.rejected_by
        if old_decider and old_decider.kind is ReviewerKind.HUMAN and answer.answered_by.kind is not ReviewerKind.HUMAN:
            updated.append(relation)
            continue
        if keep and answer.answered_by.kind is ReviewerKind.AGENT and relation.assertion.branch_id:
            # An agent's acceptance counts when it cites the shown text; an image-only
            # question was answered from the attached crops.
            shown = {e.segment_id for e in question.source}
            if shown and not set(answer.cited_segment_ids) & shown:
                updated.append(relation)
                continue
        certificate = _decided(relation.assertion.certificate, answer, keep)
        if answer.text:
            certificate = certificate.model_copy(update={"notes": [*certificate.notes, f"reviewer: {answer.text}"]})
        assertion = relation.assertion.model_copy(update={"certificate": certificate, "scope_status": certificate.scope_status})
        updated.append(relation.model_copy(update={"assertion": assertion}))
    return updated


def merge_decisions(questions: list[Question], answers: list[Answer], pairs: list[MergePair]) -> list[MergePair]:
    """Pairs a reviewer declared the same thing."""

    same = {answer.question_id for answer in answers if answer.option_id == "same"}
    return [pair for pair in pairs if f"merge:{pair.left}|{pair.right}" in same]


def assertion_fingerprint(assertion):
    return digest({'fact': assertion.original_fact or {'source': assertion.source_key, 'target': assertion.target_key,
                   'relation': assertion.relation_type}, 'scope': [assertion.entry_id, assertion.branch_id],
                   'evidence': sorted(assertion.certificate.evidence_ref_ids or assertion.certificate.segment_ids),
                   'conditions': [c.model_dump(mode='json') for c in assertion.conditions]})


def approval_payload(graph, validation=None):
    # No workflow, timestamps, cost or approval answer: applying approval leaves
    # this payload invariant. Per-occurrence semantic decisions are included.
    return {'nodes': sorted([n.model_dump(mode='json') for n in graph.nodes.values()], key=lambda n: n['node_id']),
            'occurrences': sorted([{'edge': [e.relation_type, e.source, e.target],
                                  'assertion': a.model_dump(mode='json'), 'tier': a.tier.value}
                                 for e in graph.edges for a in e.assertions], key=lambda v: v['assertion']['assertion_id']),
            'validation': validation or {}}
