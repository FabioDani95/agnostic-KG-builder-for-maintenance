from backend.kg_v3.contracts import ReadingUnit, Segment, SegmentKind
from backend.kg_v3.extractor import Endpoint, Proposal
from backend.kg_v3.reader import DocumentText
from backend.kg_v3.references import resolve_references


def test_matrix_references_resolve_to_causes_and_report_missing_entry():
    segments = [Segment(segment_id=f"p1.b{i}", page=1, kind=SegmentKind.TEXT,
                        evidence_id=str(i), text=text) for i, text in enumerate([
                            "Vibration 1*2*41", "1. Alpha faulty", "2. Beta faulty"], 1)]
    heading = Segment(segment_id="p1.b0", page=1, kind=SegmentKind.TEXT, evidence_id="heading",
                      text="1. Section 1.1")
    doc = DocumentText(page_count=1, pages={1: [heading, *segments]})
    unit = ReadingUnit(unit_id="u1", pages=[1], segment_ids=[heading.segment_id, *[s.segment_id for s in segments]])
    proposals = [Proposal(unit_id="u1", read="A", relation_type="INDICATES", record="R1",
                          source=Endpoint(type="ErrorCode", code=str(n), name=f"Code {n}", cites=["p1.b1"]),
                          target=Endpoint(type="FailureMode", name="Alpha faulty", cites=["p1.b2"])) for n in (1, 41)]
    resolved, missing = resolve_references(doc, unit, proposals)
    assert len(resolved) == 1
    assert resolved[0].source.type == "Symptom"
    assert resolved[0].source.name == "Vibration"
    assert resolved[0].target.name == "Alpha faulty"
    assert resolved[0].cites == ["p1.b1", "p1.b2"]
    assert [ref["reference"] for ref in missing] == ["41"]
    # Numeric alarm elsewhere is not a reference merely because numbers coincide.
    unrelated = proposals[0].model_copy(update={"source": proposals[0].source.model_copy(update={"cites": ["p2.b1"]})})
    assert resolve_references(doc, unit, [unrelated])[0] == [unrelated]
