"""V3 station 1 and unit building on a generated PDF with a merged table cell."""

from __future__ import annotations

import fitz

from backend.kg_v3.contracts import DocumentMap, PageLabel, PageMapEntry, SegmentKind
from backend.kg_v3.mapper import build_units, page_outline
from backend.kg_v3.reader import read_document, render_segment, render_segments
from scripts.kg_v3 import load_evidence

ASSET = {"name": "Test pump", "description": "Test pump", "brand": "Acme", "model": "P1", "asset_type": "pump"}


def troubleshooting_pdf(path) -> None:
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 60), "Troubleshooting", fontsize=16)
    xs, ys = [72, 222, 372, 522], [100, 120, 150, 180, 210]
    rows = [["PROBLEM", "CAUSE", "SOLUTION"], ["Pump fails to operate.", "Air supply restricted", "Clear the line"],
            [None, "Fluid dried on rod", "Clean the rod"], ["Output is low", "Worn packings", "Replace packings"]]
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for index, y in enumerate(ys):
        # No line under the first cell of row 2: the PROBLEM cell spans two rows.
        page.draw_line((xs[1] if index == 2 else xs[0], y), (xs[3], y))
    for row_index, row in enumerate(rows):
        for column, text in enumerate(row):
            if text:
                page.insert_text((xs[column] + 4, ys[row_index] + 14), text, fontsize=9)
    page.insert_text((72, 240), "NOTE: contact your distributor if the motor ices.", fontsize=9)
    document.save(path)


def test_tables_read_in_place_with_column_names_and_merged_cells(tmp_path):
    pdf = tmp_path / "manual.pdf"
    troubleshooting_pdf(pdf)
    evidence, page_count, _ = load_evidence(pdf, ASSET)
    doc = read_document(list(evidence), page_count=page_count)

    ids = [segment.segment_id for segment in doc.pages[1]]
    assert ids[0] == "p1.b1" and ids[-1].startswith("p1.b")
    assert ids[1:5] == ["p1.t1.r1", "p1.t1.r2", "p1.t1.r3", "p1.t1.r4"]
    merged = doc.segment("p1.t1.r3")
    assert merged.kind is SegmentKind.TABLE_ROW and merged.table.inherited_columns == [0]
    assert render_segment(doc.segment("p1.t1.r1")) == "[p1.t1.r1] TABLE COLUMNS: PROBLEM | CAUSE | SOLUTION"
    assert render_segment(merged) == (
        "[p1.t1.r3] PROBLEM (same as row above): Pump fails to operate. | CAUSE: Fluid dried on rod"
        " | SOLUTION: Clean the rod"
    )
    assert "=== page 1 ===" in render_segments(doc.pages[1])
    assert "[1 table(s): PROBLEM | CAUSE | SOLUTION]" in page_outline(doc, 1)
    assert doc.segment(ids[-1]).evidence_id and doc.unreadable_pages == []


def test_units_own_every_diagnostic_segment_once(tmp_path):
    pdf = tmp_path / "manual.pdf"
    troubleshooting_pdf(pdf)
    evidence, page_count, _ = load_evidence(pdf, ASSET)
    doc = read_document(list(evidence), page_count=page_count)
    page_map = DocumentMap(entries=[PageMapEntry(page=1, label=PageLabel.DIAGNOSTIC, section="Troubleshooting")])

    units = build_units(doc, page_map)
    assert [unit.segment_ids for unit in units] == [[segment.segment_id for segment in doc.pages[1]]]
    small = build_units(doc, page_map, max_chars=200)
    owned = [segment for unit in small for segment in unit.segment_ids]
    assert sorted(owned) == sorted(segment.segment_id for segment in doc.pages[1])
    continued = next(unit for unit in small if unit.segment_ids[0] == "p1.t1.r3")
    assert "p1.t1.r1" in continued.context_segment_ids
    assert build_units(doc, DocumentMap(entries=[PageMapEntry(page=1, label=PageLabel.OTHER)])) == []
