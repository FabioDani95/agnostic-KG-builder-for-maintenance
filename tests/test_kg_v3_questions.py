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


def test_prompts_turn_flowchart_outcomes_and_expected_values_into_connected_branches():
    from backend.kg_v3.prompts import EXTRACTION_PROMPT, REVIEWER_BRIEF, VERIFY_PASSAGE_PROMPT

    # Each outcome of a decision step is a branch of the chart's problem, with the outcome as condition.
    assert "Each\n    outcome that prescribes an action is its own record" in EXTRACTION_PROMPT
    assert "Never give an action the outcome\n    of another question" in EXTRACTION_PROMPT
    # One problem per chart, and the outcome also on the problem link, so branches stay apart.
    assert "its first question describes\n    the same problem and is not a second one" in EXTRACTION_PROMPT
    assert "on the problem-to-failure link and on the actions" in EXTRACTION_PROMPT
    # A cause under a title that names its situation is linked to that problem.
    assert "16. Every failure mode needs its problem." in EXTRACTION_PROMPT
    # A test with a normal value is an inspection with expected context, tied to a problem.
    assert '"Suspected <component> fault"' in EXTRACTION_PROMPT
    assert "supports only the action that outcome leads to" in VERIFY_PASSAGE_PROMPT
    assert "A flowchart or numbered procedure\n   is one entry" in REVIEWER_BRIEF


def test_a_link_to_an_unnamed_cause_says_it_claims_the_path_of_the_problem_entry():
    from backend.kg_v3.checker import statement
    from backend.kg_v3.extractor import Endpoint, Proposal
    from backend.kg_v3.ontology import load_ontology
    from backend.kg_v3.prompts import VERIFY_PROMPT

    spec = load_ontology()
    link = Proposal(unit_id="u1", read="A", relation_type="MAY_INDICATE", record="R1", cites=["p18.b1", "p20.b8"],
                    source=Endpoint(type="Symptom", name="No heat / no cook"),
                    target=Endpoint(type="FailureMode", name="Faulty high voltage transformer", stated=False))
    remedy = link.model_copy(update={"relation_type": "RESOLVED_BY", "source": link.target, "target": Endpoint(
        type="CorrectiveAction", name="Measure transformer winding resistance", kind="inspection")})
    assert "flowchart or procedure that starts from this problem) leads to the check" in statement(spec, link)
    assert "the cited entry prescribes this check or remedy" in statement(spec, remedy)
    assert "the test whose outcome reveals such a cause is a check for it" in VERIFY_PROMPT
