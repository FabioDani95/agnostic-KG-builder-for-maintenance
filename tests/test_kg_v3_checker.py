"""V3 checking and merging rules: tolerant to wording, strict on place, numbers and direction."""

from __future__ import annotations

from backend.kg_v3.checker import group_candidates, normalize_name, same_relation, similarity, structurally_supported
from backend.kg_v3.contracts import DocumentMap, PageLabel, PageMapEntry, Segment, SegmentKind, TableCoordinates
from backend.kg_v3.extractor import Endpoint, Proposal
from backend.kg_v3.mapper import fill_gaps
from backend.kg_v3.merger import _contained
from backend.kg_v3.reader import DocumentText


def proposal(read, source, target, cite, *, type_="MAY_INDICATE", stated=True, code=""):
    return Proposal(
        unit_id="u1", read=read, relation_type=type_,
        source=Endpoint(type="Symptom" if not code else "ErrorCode", name=source, code=code, cites=[cite]),
        target=Endpoint(type="FailureMode", name=target, stated=stated, cites=[cite]),
        record="R1", cites=[cite],
    )


def test_names_compare_by_meaning_preserving_normalisation():
    assert normalize_name("Output is low on down- stroke.") == "output is low on down-stroke"
    assert similarity("Air supply restricted", "Restricted air supply") == 1.0
    assert similarity("Error E-12 active", "Error E-13 active") == 0.0


def test_reads_agree_on_paraphrases_at_the_same_place_only():
    a = proposal("A", "Pump fails to operate", "Air supply restricted", "p11.t1.r2")
    assert same_relation(a, proposal("B", "Pump does not operate", "Restricted air supply", "p11.t1.r2"))
    up = proposal("A", "Output low on up-stroke", "Worn piston valve", "p11.t1.r14")
    down = proposal("B", "Output low on down-stroke", "Worn piston valve", "p11.t1.r13")
    assert not same_relation(up, down)
    unnamed = proposal("B", "Pump fails to operate", "Unspecified cause of pump failure", "p11.t1.r2", stated=False)
    assert same_relation(a, unnamed)
    [candidate] = group_candidates([unnamed, proposal("A", "Pump fails to operate", "Air supply restricted",
                                                      "p11.t1.r2")])
    assert candidate.lead.target.stated and candidate.agreement
    assert not same_relation(proposal("A", "Overheat", "Fan", "p5.b1", code="E1"),
                             proposal("B", "Overheat", "Fan", "p5.b1", code="E2"))


def test_structure_witness_needs_one_row_or_neighbouring_blocks():
    segments = [
        Segment(segment_id="p2.b1", page=2, kind=SegmentKind.TEXT, text="Problem: no power", evidence_id="e1"),
        Segment(segment_id="p2.b2", page=2, kind=SegmentKind.TEXT, text="Cause: blown fuse", evidence_id="e2"),
        Segment(segment_id="p2.b3", page=2, kind=SegmentKind.TEXT, text="Other text", evidence_id="e3"),
        Segment(segment_id="p2.t1.r2", page=2, kind=SegmentKind.TABLE_ROW, text="a | b", evidence_id="e4",
                table=TableCoordinates(table=1, row=2)),
        Segment(segment_id="p2.t1.r3", page=2, kind=SegmentKind.TABLE_ROW, text="c | d", evidence_id="e5",
                table=TableCoordinates(table=1, row=3)),
    ]
    doc = DocumentText(page_count=2, pages={2: segments})

    def cited(*ids):
        item = proposal("A", "x", "y", ids[0])
        return item.model_copy(update={"cites": list(ids)})

    assert structurally_supported(doc, cited("p2.t1.r2"))
    assert structurally_supported(doc, cited("p2.b1", "p2.b2"))
    assert not structurally_supported(doc, cited("p2.b1", "p2.b3"))
    assert not structurally_supported(doc, cited("p2.t1.r2", "p2.t1.r3"))


def test_map_safety_net_reads_continuations_of_diagnostic_pages():
    labels = {36: PageLabel.OTHER, 37: PageLabel.DIAGNOSTIC, 38: PageLabel.PROCEDURE, 39: PageLabel.DIAGNOSTIC,
              40: PageLabel.OTHER, 41: PageLabel.PROCEDURE, 42: PageLabel.OTHER}
    page_map = fill_gaps(DocumentMap(entries=[PageMapEntry(page=page, label=label) for page, label in labels.items()]))
    assert page_map.pages_with(PageLabel.DIAGNOSTIC) == [37, 38, 39]
    assert [entry.unsure for entry in page_map.entries if entry.page == 38] == [True]


def test_names_that_only_add_words_go_to_the_merge_judge():
    assert _contained("Clean displacement rod", "Clean displacement rod; see Service on pages 12-19")
    assert not _contained("Close", "Close bleeder valve")


def test_a_compound_name_never_bridges_two_actions_into_one_node():
    from backend.kg_v3.checker import CheckedRelation
    from backend.kg_v3.contracts import Assertion, Certificate
    from backend.kg_v3.merger import assemble

    def relation(action_a, action_b, cite):
        a = Proposal(unit_id="u1", read="A", relation_type="RESOLVED_BY",
                     source=Endpoint(type="FailureMode", name="Worn piston valve", cites=[cite]),
                     target=Endpoint(type="CorrectiveAction", name=action_a, cites=[cite]), record="R1", cites=[cite])
        b = a.model_copy(update={"read": "B", "target": Endpoint(type="CorrectiveAction", name=action_b, cites=[cite])})
        assertion = Assertion(assertion_id=action_a, relation_type="RESOLVED_BY", source_key="s", target_key="t",
                              record_key="u1:A.R1", certificate=Certificate(segment_ids=[cite]))
        return CheckedRelation(assertion=assertion, proposals=[a, b])

    compound = "Clear the piston valve and replace the piston valve seals"
    graph = assemble([relation("Clear the piston valve", compound, "p11.t1.r14"),
                      relation("Replace the piston valve seals", compound, "p11.t1.r14")], [])
    assert {graph.nodes_by_id[edge.target].name for edge in graph.edges} == {
        "Clear the piston valve", "Replace the piston valve seals"}


def _eastman_like_doc() -> DocumentText:
    texts = [
        ("p38.b1", "Problem: The tool does not move down"),
        ("p38.b2", "5.Check tool connections."),
        ("p38.b3", "a) Hit the Cut Down button to verify the"),
        ("p38.b4", "corresponding green LED light is on."),
        ("p38.b5", "6.The tool delays coming down."),
        ("p38.b6", "a) Check the 24 VDC power supply."),
    ]
    segments = [Segment(segment_id=key, page=38, kind=SegmentKind.TEXT, text=text, evidence_id=f"e{index}")
                for index, (key, text) in enumerate(texts)]
    return DocumentText(page_count=38, pages={38: segments})


def test_numbered_steps_and_broken_sentences_are_explicit():
    from backend.kg_v3.reader import render_segments

    doc = _eastman_like_doc()
    assert doc.step["p38.b3"] == doc.step["p38.b4"] and doc.step["p38.b3"][1] == "5a"
    assert "p38.b4" in doc.continuation and doc.step_group("p38.b6") != doc.step_group("p38.b3")
    text = render_segments(doc.segments(), doc=doc)
    assert "[p38.b3] (step 5a) a) Hit the Cut Down button to verify the [p38.b4] corresponding" in text
    assert "[p38.b6] (step 6a)" in text


def test_structure_joins_one_numbered_step_but_not_two():
    doc = _eastman_like_doc()

    def cited(*ids):
        item = proposal("A", "x", "y", ids[0])
        return item.model_copy(update={"cites": list(ids)})

    assert structurally_supported(doc, cited("p38.b5", "p38.b6"))
    assert not structurally_supported(doc, cited("p38.b3", "p38.b6"))


def test_a_cause_that_repeats_the_problem_is_never_green_alone():
    from backend.kg_v3.checker import restates

    assert restates(proposal("A", "Fan failure", "Fan failure", "p64.t1.r5"))
    assert not restates(proposal("A", "Fan failure", "Fan blocked by dust", "p64.t1.r5"))


def test_unnamed_causes_with_the_same_remedies_become_one():
    from backend.kg_v3.checker import CheckedRelation
    from backend.kg_v3.contracts import Assertion, Certificate
    from backend.kg_v3.merger import assemble

    def remedy(cause, action):
        item = Proposal(unit_id="u1", read="A", relation_type="RESOLVED_BY",
                        source=Endpoint(type="FailureMode", name=cause, stated=False, cites=["p38.b25"]),
                        target=Endpoint(type="CorrectiveAction", name=action, cites=["p38.b29"]),
                        record="R1", cites=["p38.b29"])
        return CheckedRelation(assertion=Assertion(assertion_id=cause + action, relation_type="RESOLVED_BY",
                                                   source_key="s", target_key="t", record_key="u1:A.R1",
                                                   certificate=Certificate(segment_ids=["p38.b29"])),
                               proposals=[item])

    relations = [remedy(cause, action) for cause in ("Unspecified cause of reduced vacuum",
                                                     "Unspecified cause of odor while cutting")
                 for action in ("Replace the vacuum filters", "Clean the vacuum hose")]
    graph = assemble(relations, [])
    assert len({edge.source for edge in graph.edges}) == 1 and len(graph.edges) == 2


def test_structure_needs_both_ends_in_the_entry_that_states_the_link():
    doc = _eastman_like_doc()
    cause_in_step_5 = Proposal(
        unit_id="u1", read="A", relation_type="RESOLVED_BY",
        source=Endpoint(type="FailureMode", name="Tool connection fault", cites=["p38.b2"]),
        target=Endpoint(type="CorrectiveAction", name="Check the power supply", cites=["p38.b6"]),
        record="R1", cites=["p38.b6"])
    assert not structurally_supported(doc, cause_in_step_5)
    same_step = cause_in_step_5.model_copy(update={
        "target": Endpoint(type="CorrectiveAction", name="Hit Cut Down", cites=["p38.b3"]), "cites": ["p38.b3"]})
    assert structurally_supported(doc, same_step)


def test_rows_under_a_merged_cell_belong_to_its_entry():
    from backend.kg_v3.checker import same_record

    def row(number, inherited):
        return Segment(segment_id=f"p11.t1.r{number}", page=11, kind=SegmentKind.TABLE_ROW, text=f"r{number}",
                       evidence_id=f"e{number}", table=TableCoordinates(table=1, row=number, inherited_columns=inherited))

    doc = DocumentText(page_count=11, pages={11: [row(2, []), row(3, [0]), row(4, [0]), row(5, [])]})
    assert same_record(doc, "p11.t1.r2", "p11.t1.r4")
    assert not same_record(doc, "p11.t1.r4", "p11.t1.r5")


def test_a_cause_repeating_its_problem_becomes_unnamed():
    from backend.kg_v3.contracts import ReadingUnit
    from backend.kg_v3.extractor import parse_read
    from backend.kg_v3.ontology import load_ontology

    unit = ReadingUnit(unit_id="u1", pages=[64], segment_ids=["p64.t1.r5"])
    data = {"entities": [
        {"key": "E1", "type": "ErrorCode", "name": "Fan failure", "code": "3", "kind": "", "stated": True, "cite": ["p64.t1.r5"]},
        {"key": "E2", "type": "FailureMode", "name": "Fan failure", "code": "", "kind": "", "stated": True, "cite": ["p64.t1.r5"]},
        {"key": "E3", "type": "CorrectiveAction", "name": "Contact service", "code": "", "kind": "escalation", "stated": True, "cite": ["p64.t1.r5"]}],
        "relations": [{"type": "INDICATES", "source": "E1", "target": "E2", "record": "R1", "conditions": [], "cite": ["p64.t1.r5"]},
                      {"type": "RESOLVED_BY", "source": "E2", "target": "E3", "record": "R1", "conditions": [], "cite": ["p64.t1.r5"]}],
        "unclear": []}
    proposals, _, notes = parse_read(data, unit=unit, read="A", spec=load_ontology(), allowed={"p64.t1.r5"})
    causes = {item.target.name for item in proposals if item.relation_type == "INDICATES"}
    assert causes == {"Unspecified cause of fan failure"}
    assert all(not item.source.stated for item in proposals if item.relation_type == "RESOLVED_BY")


def test_an_unnamed_cause_never_bridges_two_named_causes():
    from backend.kg_v3.checker import CheckedRelation
    from backend.kg_v3.contracts import Assertion, Certificate
    from backend.kg_v3.merger import assemble

    unnamed = Endpoint(type="FailureMode", name="Unspecified cause of tool not moving", stated=False, cites=["p38.b4"])
    symptom = Endpoint(type="Symptom", name="Tool does not move down", cites=["p38.b4"])

    def agreed(named_cause, cite):
        a = Proposal(unit_id="u1", read="A", relation_type="MAY_INDICATE", source=symptom,
                     target=Endpoint(type="FailureMode", name=named_cause, cites=[cite]), record="R1", cites=[cite])
        b = a.model_copy(update={"read": "B", "target": unnamed})
        return CheckedRelation(assertion=Assertion(assertion_id=named_cause, relation_type="MAY_INDICATE",
                                                   source_key="s", target_key="t", record_key="u1:A.R1",
                                                   certificate=Certificate(segment_ids=[cite])), proposals=[a, b])

    graph = assemble([agreed("Tool mapping is incorrect", "p38.b6"), agreed("24 VDC power supply fault", "p38.b21")], [])
    assert {graph.nodes_by_id[edge.target].name for edge in graph.edges} == {
        "Tool mapping is incorrect", "24 VDC power supply fault"}
    single = assemble([agreed("Tool mapping is incorrect", "p38.b6")], [])
    assert len(single.nodes) == 2  # the unnamed cause joins its only named partner


def test_a_step_is_verified_with_its_problem_and_parent_step():
    doc = _eastman_like_doc()
    assert doc.step_context("p38.b6") == ["p38.b1", "p38.b5"]
    assert doc.step_context("p38.b2") == ["p38.b1"]
    assert doc.step_context("p38.b1") == []
