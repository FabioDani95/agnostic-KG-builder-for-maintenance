"""Regressions of the defects found in the first real quality_v1 runs (pilot 2026-10-01).

Each test names the defect it guards: shuffled evidence, truncated verification, page-wide
conflict quarantine, image questions an agent could not answer, unscoped prose relations and
per-proposal records that hid compound remedies from the scorer.
"""

from __future__ import annotations

import asyncio
import json
import re

from backend.kg_v3.checker import Checker
from backend.kg_v3.contracts import (
    Answer,
    AnswerOption,
    Question,
    QuestionKind,
    ReviewerIdentity,
    ReviewerKind,
    Segment,
    SegmentKind,
    Tier,
)
from backend.kg_v3.extractor import Endpoint, Extractor, Proposal
from backend.kg_v3.llm import TruncatedResponse
from backend.kg_v3.mapper import build_quality_units
from backend.kg_v3.questions import apply_relation_answers, relation_questions
from backend.kg_v3.reader import DocumentText
from backend.kg_v3.reviewers import AgentDecision, AgentReviewer
from backend.kg_v3.source_index import bind_proposal
from scripts.kg_v3_evaluate import v3_edges
from tests.test_kg_v3_quality_pipeline import SPEC, Fake, check, index_for, page_map, proposal, setup_table

AGENT = ReviewerIdentity(kind=ReviewerKind.AGENT, name="gpt-6-luna", prompt_hash="0" * 64)


def prose_doc(count=5):
    texts = ["No heat", "Is the fuse open?", "Yes", "Replace the fuse.", "Check the door switch."][:count]
    segments = [Segment(segment_id=f"p1.b{n}", page=1, kind=SegmentKind.TEXT, text=text,
                        evidence_id=f"block {n}", bbox=(10, 20 * n, 200, 20 * n + 12))
                for n, text in enumerate(texts, 1)]
    return DocumentText(page_count=1, pages={1: segments})


class Recorder(Fake):
    """Answers extraction with nothing and records what the model was shown."""

    async def json(self, **kw):
        if kw["name"] == "kg_v3_extract":
            self.calls.append(kw)
            return {"entities": [], "relations": [], "unclear": [], "section_context": []}
        return await super().json(**kw)


def test_extraction_reads_the_passage_in_reading_order_like_the_base_profile():
    doc = prose_doc()
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index)
    llm = Recorder()
    asyncio.run(Extractor(llm, SPEC, asset_name="Oven", reads=1, source_index=index).extract(doc, units[0]))
    user = llm.calls[0]["user"]
    assert user.startswith("=== page 1 ===")
    order = [int(n) for n in re.findall(r"\[p1\.b(\d+)\]", user)]
    assert order == sorted(order) == [1, 2, 3, 4, 5]
    assert "evidence_" not in user  # opaque hash IDs are never shown to the model
    cites = llm.calls[0]["schema"]["properties"]["entities"]["items"]["properties"]["cite"]["items"]["enum"]
    assert set(cites) == {f"p1.b{n}" for n in range(1, 6)}


def test_numbered_cell_items_get_part_ids_that_resolve_to_one_item():
    doc, index, units = setup_table()

    class ItemCiter(Fake):
        async def json(self, **kw):
            if kw["name"] != "kg_v3_extract":
                return await super().json(**kw)
            assert "[p1.t1.r2/3.2] 2. Replace fuse" in kw["user"]
            entities = [
                {"key": "c", "type": "FailureMode", "name": "Blown fuse", "kind": "", "code": "", "stated": True,
                 "cite": ["p1.t1.r2"], "denotation_status": "STATED"},
                {"key": "a", "type": "CorrectiveAction", "name": "Replace fuse", "kind": "repair", "code": "",
                 "stated": True, "cite": ["p1.t1.r2/3.2"], "denotation_status": "STATED"},
            ]
            relations = [{"type": "RESOLVED_BY", "source": "c", "target": "a", "record": "R1", "conditions": [],
                          "cite": ["p1.t1.r2", "p1.t1.r2/3.2"], "premise_refs": []}]
            return {"entities": entities, "relations": relations, "unclear": [], "section_context": []}

    doc, index, units = setup_table("1. Inspect fuse 2. Replace fuse 3. Contact service")
    out = asyncio.run(Extractor(ItemCiter(), SPEC, asset_name="Pump", reads=1, source_index=index).extract(doc, units[0]))
    [p] = out.proposals
    item = next(r for r in index.atomic_refs["p1.t1.r2"] if index.evidence[r].item_index == 2)
    assert p.target.evidence_ref_ids == [item]
    assert not {"UNRESOLVED_SCOPE", "CROSS_BRANCH_CONTAMINATION"} & set(p.validation_issues)


def test_a_truncated_verification_is_asked_again_in_halves():
    doc = prose_doc()
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index)
    ps = [bind_proposal(index, doc, Proposal(
        unit_id=units[0].unit_id, read="A", record=f"R{n}", relation_type="RESOLVED_BY",
        source=Endpoint(type="FailureMode", name=f"Fault {n}", cites=["p1.b2"], stated=True, denotation_status="STATED"),
        target=Endpoint(type="CorrectiveAction", name=f"Action {n}", kind="repair", cites=["p1.b4"],
                        denotation_status="STATED"),
        cites=["p1.b2", "p1.b4"]), units[0]) for n in range(8)]

    class Truncating(Fake):
        async def json(self, **kw):
            if kw["name"] == "kg_v3_verify" and len(kw["schema"]["properties"]["verdicts"]["items"]["properties"]["id"]["enum"]) > 2:
                self.calls.append(kw)
                raise TruncatedResponse("kg_v3_verify: output limit reached")
            return await super().json(**kw)

    llm = Truncating()
    relations = check(doc, index, units, ps, llm)
    assert all(r.assertion.certificate.verifier_verdict is not None for r in relations)
    assert all(c["max_output_tokens"] >= 16000 for c in llm.calls if c["name"] == "kg_v3_verify")


def test_verifier_uses_the_base_rules_and_keeps_placeholder_semantics():
    doc = prose_doc()
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index)
    p = bind_proposal(index, doc, Proposal(
        unit_id=units[0].unit_id, read="A", record="R1", relation_type="RESOLVED_BY",
        source=Endpoint(type="FailureMode", name="Unspecified cause of no heat", cites=["p1.b1"], stated=False,
                        denotation_status="PLACEHOLDER"),
        target=Endpoint(type="CorrectiveAction", name="Replace the fuse", kind="repair", cites=["p1.b4"],
                        denotation_status="STATED"),
        cites=["p1.b1", "p1.b4"]), units[0])
    llm = Fake()
    check(doc, index, units, [p], llm)
    [call] = [c for c in llm.calls if c["name"] == "kg_v3_verify"]
    assert "judge the problem and the check or remedy, not\nthe cause name" in call["system"]
    assert "(not written in the manual)" in call["user"]
    assert "evidence_" not in call["user"]


def test_prose_relations_get_a_unit_scope_not_an_unresolved_one():
    doc = prose_doc()
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index)
    make = lambda read: bind_proposal(index, doc, Proposal(  # noqa: E731
        unit_id=units[0].unit_id, read=read, record="R1", relation_type="MAY_INDICATE",
        source=Endpoint(type="Symptom", name="No heat", cites=["p1.b1"], denotation_status="STATED"),
        target=Endpoint(type="FailureMode", name="Open fuse", cites=["p1.b2", "p1.b3"], stated=False,
                        denotation_status="INFERRED"),
        cites=["p1.b1", "p1.b2", "p1.b3"], premise_refs=["p1.b2"]), units[0])
    a, b = make("A"), make("B")
    assert a.branch_id and a.branch_id == b.branch_id
    assert index.entries[index.branches[a.branch_id].entry_id].kind == "UNRESOLVED"
    assert "UNRESOLVED_SCOPE" not in a.validation_issues and "CROSS_BRANCH_CONTAMINATION" not in a.validation_issues
    [relation] = check(doc, index, units, [a, b])
    assert relation.assertion.tier is Tier.GREEN and not relation.assertion.certificate.validation_issues


def test_an_agent_confirmation_promotes_a_quality_relation_it_read():
    doc, index, units = setup_table()

    class Unclear(Fake):
        async def json(self, **kw):
            data = await super().json(**kw)
            if kw["name"] == "kg_v3_verify":
                for verdict in data["verdicts"]:
                    verdict["verdict"] = "unclear"
            return data

    relations = check(doc, index, units, [proposal(doc, index, units)], Unclear())
    assert relations[0].assertion.tier is Tier.YELLOW
    questions = relation_questions(doc, SPEC, relations)
    answers = [Answer(question_id=q.question_id, option_id="accept", answered_by=AGENT, rationale="row 2 states it",
                      cited_segment_ids=[q.source[0].segment_id]) for q in questions]
    [promoted] = apply_relation_answers(relations, questions, answers)
    assert promoted.assertion.tier is Tier.GREEN
    blind = [a.model_copy(update={"cited_segment_ids": []}) for a in answers]
    assert apply_relation_answers(relations, questions, blind)[0].assertion.tier is Tier.YELLOW


def test_an_agent_answers_an_image_question_from_its_crops():
    question = Question(
        question_id="rel:image", kind=QuestionKind.RELATION_CHECK, title="Does the manual state this?",
        source_regions=[{"region_id": "region_1", "page": 3, "bbox": [0, 0, 10, 10], "render_fingerprint": "f"}],
        proposal=["1. 'No heat' may indicate an open fuse"],
        options=[AnswerOption(option_id="accept", label="Yes", effect="kept"),
                 AnswerOption(option_id="reject", label="No", effect="dropped"),
                 AnswerOption(option_id="correct", label="Partly", effect="Keep selected statements")],
        default_option_id="accept")
    seen = []

    async def llm(*, system, user, schema, images=None):
        seen.append(images)
        return AgentDecision(option_id="accept", correction="", keep_statements=[], page_label_changes=[],
                             rationale="the arrow from Yes leads to the fuse box", cited_segment_ids=[], confident=True)

    answers = asyncio.run(AgentReviewer(llm, model="gpt-6-luna", images=lambda q: ["data:image/png;base64,AA=="])
                         .review([question]))
    assert answers and answers[0].option_id == "accept" and seen == [["data:image/png;base64,AA=="]]
    assert asyncio.run(AgentReviewer(llm, model="gpt-6-luna").review([question])) == []


def test_scorer_groups_the_remedies_of_one_branch(tmp_path):
    occurrence = {"evidence": [], "conditions": [], "tier": "green"}
    graph = {"nodes": [{"id": n, "name": n} for n in ["cause", "inspect", "replace"]], "edges": [
        {"type": "RESOLVED_BY", "from": "cause", "to": target, "occurrences": [
            {**occurrence, "branch_id": "branch_1", "record": f"u1:A.R{n}"}]}
        for n, target in enumerate(["inspect", "replace"])]}
    (tmp_path / "graph.json").write_text(json.dumps(graph))
    assert {e["record"] for e in v3_edges(tmp_path)} == {"branch_1"}


def test_verification_runs_in_small_batches():
    doc = prose_doc()
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index)
    ps = [bind_proposal(index, doc, Proposal(
        unit_id=units[0].unit_id, read="A", record=f"R{n}", relation_type="RESOLVED_BY",
        source=Endpoint(type="FailureMode", name=f"Fault {n}", cites=["p1.b2"], denotation_status="STATED"),
        target=Endpoint(type="CorrectiveAction", name=f"Action {n}", kind="repair", cites=["p1.b4"],
                        denotation_status="STATED"),
        cites=["p1.b2", "p1.b4"]), units[0]) for n in range(25)]
    llm = Fake()
    asyncio.run(Checker(llm, SPEC, extractor_id="fixture", units=units, source_index=index).check(doc, ps))
    sizes = [len(c["schema"]["properties"]["verdicts"]["items"]["properties"]["id"]["enum"])
             for c in llm.calls if c["name"] == "kg_v3_verify"]
    assert sum(sizes) == 25 and max(sizes) <= 10


def test_alias_candidates_need_real_part_numbers():
    from backend.kg_v3.merger import PART_NUMBER

    assert PART_NUMBER.findall("1. Replace the PCB (EBR75341201). Fuse 250V 10A") == ["EBR75341201"]
    assert PART_NUMBER.findall("2. Check item 3 and 4") == []
