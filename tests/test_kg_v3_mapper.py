"""Two independent map readings: any diagnostic vote is read, agreement protects a page."""

from __future__ import annotations

import asyncio

from backend.kg_v3.contracts import DocumentMap, PageLabel, PageMapEntry, Segment, SegmentKind
from backend.kg_v3.mapper import apply_map_answer, combine_readings, map_pages, protected_demotions
from backend.kg_v3.reader import DocumentText


def _doc(pages: int) -> DocumentText:
    return DocumentText(page_count=pages, pages={
        page: [Segment(segment_id=f"p{page}.b1", page=page, kind=SegmentKind.TEXT,
                       text=f"Page {page} text", evidence_id=f"ev{page}")]
        for page in range(1, pages + 1)})


class _TwoReadings:
    """Each call answers with the next scripted labelling, or fails when it is None."""

    def __init__(self, labellings: list[dict[int, str] | None]) -> None:
        self.labellings = list(labellings)

    async def json(self, **_kwargs):
        labels = self.labellings.pop(0)
        if labels is None:
            raise RuntimeError("provider error")
        return {"pages": [{"page": page, "label": label, "section": "", "unsure": False}
                          for page, label in labels.items()]}


def test_either_reading_suffices_and_agreement_confirms():
    doc = _doc(4)
    llm = _TwoReadings([{1: "other", 2: "diagnostic", 3: "diagnostic", 4: "parts"},
                        {1: "other", 2: "diagnostic", 3: "other", 4: "parts"}])
    page_map = asyncio.run(map_pages(llm, doc))
    entries = {entry.page: entry for entry in page_map.entries}
    assert entries[2].label is PageLabel.DIAGNOSTIC and entries[2].confirmed and not entries[2].unsure
    assert entries[3].label is PageLabel.DIAGNOSTIC and not entries[3].confirmed and entries[3].unsure
    assert entries[1].label is PageLabel.OTHER and entries[4].label is PageLabel.PARTS


def test_a_failed_reading_is_not_a_vote():
    doc = _doc(2)
    llm = _TwoReadings([{1: "diagnostic", 2: "other"}, None])
    entries = {entry.page: entry for entry in asyncio.run(map_pages(llm, doc)).entries}
    assert entries[1].label is PageLabel.DIAGNOSTIC and not entries[1].confirmed


def test_a_gate_cannot_drop_a_confirmed_page_but_can_drop_a_doubtful_one():
    page_map = DocumentMap(entries=[
        PageMapEntry(page=1, label=PageLabel.DIAGNOSTIC, confirmed=True),
        PageMapEntry(page=2, label=PageLabel.DIAGNOSTIC, unsure=True),
        PageMapEntry(page=3, label=PageLabel.OTHER),
    ])
    edits = {"pages": {"1": "other", "2": "procedure", "3": "diagnostic"}}
    assert protected_demotions(page_map, edits) == [1]
    labels = {entry.page: entry.label for entry in apply_map_answer(page_map, edits).entries}
    assert labels == {1: PageLabel.DIAGNOSTIC, 2: PageLabel.PROCEDURE, 3: PageLabel.DIAGNOSTIC}


def test_combined_label_without_diagnostic_votes_follows_the_majority():
    entry = combine_readings(5, [PageMapEntry(page=5, label=PageLabel.PROCEDURE),
                                 PageMapEntry(page=5, label=PageLabel.PROCEDURE)], 2)
    assert entry.label is PageLabel.PROCEDURE and not entry.unsure and not entry.confirmed
