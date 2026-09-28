"""Pages whose layout carries meaning are shown to the model as images, with segment positions."""

from __future__ import annotations

import asyncio

import fitz

from backend.kg_v3.contracts import ReadingUnit
from backend.kg_v3.extractor import Extractor
from backend.kg_v3.ontology import load_ontology
from backend.kg_v3.reader import read_document
from backend.kg_v3.vision import PageImages, layout_pages
from scripts.kg_v3 import load_evidence
from tests.test_kg_v3_reader import ASSET


def flowchart_pdf(path) -> None:
    document = fitz.open()
    chart = document.new_page(width=595, height=842)
    chart.insert_text((72, 60), "Does the display operate?", fontsize=11)
    boxes = ["No", "1 Is the fuse open?", "Yes", "Replace the fuse.", "No", "2 Is the filter open?",
             "Yes", "Replace the filter.", "No", "3 Replace the PCB."]
    for index, text in enumerate(boxes):
        chart.insert_text((72 + 220 * (index % 2), 120 + 60 * index), text, fontsize=10)
        chart.draw_rect(fitz.Rect(66 + 220 * (index % 2), 108 + 60 * index, 260 + 220 * (index % 2),
                                  126 + 60 * index))
    prose = document.new_page(width=595, height=842)
    prose.insert_text((72, 60), "Maintenance", fontsize=11)
    prose.insert_textbox(fitz.Rect(72, 80, 520, 400), "Inspect the radiator fan intake screen for blockage "
                         "and clean it as required. Inspect the hoses and connections for leaks or damage, "
                         "and repair or replace them as required.", fontsize=10)
    document.save(path)


class Recorder:
    def __init__(self) -> None:
        self.calls = []

    async def json(self, *, user, images=None, **_kwargs):
        self.calls.append((user, images))
        return {"entities": [], "relations": [], "unclear": [], "section_context": []}


def test_a_flowchart_page_is_shown_as_an_image_with_positions_and_a_prose_page_is_not(tmp_path):
    pdf = tmp_path / "manual.pdf"
    flowchart_pdf(pdf)
    evidence, page_count, _ = load_evidence(pdf, ASSET)
    doc = read_document(list(evidence), page_count=page_count)
    assert layout_pages(doc) == {1}

    llm = Recorder()
    extractor = Extractor(llm, load_ontology(), asset_name="Test oven", reads=1, images=PageImages(pdf, doc))
    for page in (1, 2):
        ids = [segment.segment_id for segment in doc.pages[page]]
        asyncio.run(extractor._read_once(doc, ReadingUnit(unit_id=f"u{page}", pages=[page], segment_ids=ids), "A"))
    (chart_text, chart_images), (prose_text, prose_images) = llm.calls
    assert len(chart_images) == 1 and chart_images[0].startswith("data:image/png;base64,")
    assert "[p1.b1] @12," in chart_text
    assert prose_images is None and "@" not in prose_text
