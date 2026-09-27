"""Questions show the reviewer every segment their statements cite."""

from __future__ import annotations

from backend.kg_v3.contracts import Segment, SegmentKind
from backend.kg_v3.questions import _excerpts
from backend.kg_v3.reader import DocumentText


def test_every_cited_segment_reaches_the_reviewer():
    # One problem with twelve listed causes, as in a symptom/cause matrix.
    segments = [Segment(segment_id=f"p3.b{index}", page=3, kind=SegmentKind.TEXT,
                        text=f"{index}. Cause number {index}", evidence_id=f"ev{index}")
                for index in range(1, 14)]
    doc = DocumentText(page_count=3, pages={3: segments})
    cites = [segment.segment_id for segment in segments]
    shown = [excerpt.segment_id for excerpt in _excerpts(doc, cites)]
    assert shown == cites


def test_prompts_keep_causes_derived_from_remedies_apart_from_stated_ones():
    # A cause derived from a check may be named but never marked as written in the manual.
    from backend.kg_v3.prompts import EXTRACTION_PROMPT, REVIEWER_BRIEF, VERIFY_PROMPT

    assert "A cause derived\n   from a check or remedy is never stated" in EXTRACTION_PROMPT
    assert "check or remedy turned around into a fault" in VERIFY_PROMPT
    assert "(not written in the manual) only claims" in VERIFY_PROMPT
    assert "(not written in the manual) is correct" in REVIEWER_BRIEF


def test_a_derived_cause_is_shown_as_not_written_and_a_named_read_does_not_override_it():
    from backend.kg_v3.checker import CheckedRelation, statement
    from backend.kg_v3.contracts import Assertion, Certificate
    from backend.kg_v3.extractor import Endpoint, Proposal
    from backend.kg_v3.merger import assemble
    from backend.kg_v3.ontology import load_ontology

    def proposal(read, stated):
        return Proposal(unit_id="u1", read=read, relation_type="RESOLVED_BY", record="R1", cites=["p1.b1"],
                        source=Endpoint(type="FailureMode", name="Incorrect input voltage", stated=stated),
                        target=Endpoint(type="CorrectiveAction", name="Make sure the correct voltage is applied",
                                        kind="inspection"))

    derived, written = proposal("A", False), proposal("B", True)
    assert "'Incorrect input voltage' (not written in the manual)" in statement(load_ontology(), derived)
    relation = CheckedRelation(assertion=Assertion(
        assertion_id="u1.c1", relation_type="RESOLVED_BY", source_key="FailureMode:Incorrect input voltage",
        target_key="CorrectiveAction:Make sure the correct voltage is applied", record_key="u1:A.R1",
        certificate=Certificate(segment_ids=["p1.b1"])), proposals=[derived, written])
    cause = next(node for node in assemble([relation], []).nodes.values() if node.type == "FailureMode")
    assert not cause.stated


def test_the_kpi_judge_sees_a_derived_cause_unnamed_only_where_the_manual_names_none():
    from scripts.kg_v3_evaluate import pair_line

    edge = {"source_name": "No wire feed", "target_name": "Incorrect input voltage", "target_stated": False}
    unstated_gold = {"kind": "indicator", "left": "No wire feed", "right": ""}
    stated_gold = {"kind": "indicator", "left": "No wire feed", "right": "Wrong voltage"}
    assert pair_line("P1", unstated_gold, [edge]).split(". Extracted context:")[0].endswith("may indicate a cause the manual does not name")
    assert pair_line("P1", stated_gold, [edge]).split(". Extracted context:")[0].endswith("may indicate 'Incorrect input voltage'")
    # A cause presented as written in the manual keeps its name and is judged as such.
    claimed = {**edge, "target_stated": True}
    assert pair_line("P1", unstated_gold, [claimed]).split(". Extracted context:")[0].endswith("may indicate 'Incorrect input voltage'")
