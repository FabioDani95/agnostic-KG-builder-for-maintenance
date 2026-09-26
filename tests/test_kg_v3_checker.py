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
