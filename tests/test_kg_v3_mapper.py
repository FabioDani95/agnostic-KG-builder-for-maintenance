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


def test_confirmed_section_sandwich_cannot_be_demoted():
    page_map = DocumentMap(entries=[
        PageMapEntry(page=1, label=PageLabel.DIAGNOSTIC, confirmed=True, section="4.2"),
        PageMapEntry(page=2, label=PageLabel.DIAGNOSTIC, unsure=True, section="4.2"),
        PageMapEntry(page=3, label=PageLabel.DIAGNOSTIC, confirmed=True, section="4.2"),
    ])
    assert protected_demotions(page_map, {"pages": {"2": "other"}}) == [2]
    assert apply_map_answer(page_map, {"pages": {"2": "other"}}).entries[1].label is PageLabel.DIAGNOSTIC


def test_confident_sections_are_not_reread_and_questions_are_small():
    from backend.kg_v3.mapper import map_questions, section_batches

    doc = _doc(45)
    doc.section_titles = {p: "A" if p < 25 else "B" for p in doc.pages}
    assert [len(b) for b in section_batches(doc, 20)] == [20, 4, 20, 1]
    llm = _TwoReadings([{p: "other" for p in batch} for batch in section_batches(doc, 20)])
    page_map = asyncio.run(map_pages(llm, doc))
    assert not llm.labellings
    assert all(len(q.proposal) <= 25 for q in map_questions(doc, page_map))


def test_the_map_gate_asks_a_few_questions_only_around_diagnostic_or_doubtful_pages():
    from backend.kg_v3.mapper import MAX_MAP_QUESTIONS, map_questions

    doc = _doc(400)
    entries = [PageMapEntry(page=page, label=PageLabel.OTHER, section=f"S{page}") for page in range(1, 401)]
    for page in (10, 11, 200, 399):
        entries[page - 1] = PageMapEntry(page=page, label=PageLabel.DIAGNOSTIC, section=f"S{page}")
    questions = map_questions(doc, DocumentMap(entries=entries))
    assert 1 <= len(questions) <= MAX_MAP_QUESTIONS
    shown = {int(line.split("|")[1].split(":")[0].strip()[1:]) for q in questions
             for line in q.proposal if "|" in line}
    assert {9, 10, 11, 12, 199, 200, 201, 398, 399, 400} == shown


def _pages(texts: dict[int, list[str]]) -> DocumentText:
    return DocumentText(page_count=max(texts), pages={
        page: [Segment(segment_id=f"p{page}.b{index}", page=page, kind=SegmentKind.TEXT, text=text,
                       evidence_id=f"ev{page}.{index}") for index, text in enumerate(lines, start=1)]
        for page, lines in texts.items()})


def test_a_flowchart_is_not_cut_at_every_page_the_map_names_differently():
    from backend.kg_v3.mapper import build_units

    doc = _pages({18: ["No Heat / No Cook", "RD", "WH"],
                  19: ["After power on, does the product operate?", "1 Repeat door open and close."],
                  20: ["Power Off", "5 Is there any beeping sound?", "No Adjust the latch board"],
                  21: ["8 Is the connector disconnected?", "Reconnect or repair the connector."]})
    page_map = DocumentMap(entries=[
        PageMapEntry(page=18, label=PageLabel.DIAGNOSTIC, section="No Heat / No Cook"),
        PageMapEntry(page=19, label=PageLabel.DIAGNOSTIC, section="No Heat Troubleshooting"),
        PageMapEntry(page=20, label=PageLabel.DIAGNOSTIC, section="No Heat Troubleshooting"),
        PageMapEntry(page=21, label=PageLabel.DIAGNOSTIC, section="High Voltage Troubleshooting"),
        *[PageMapEntry(page=page, label=PageLabel.OTHER) for page in range(1, 18)]])
    units = build_units(doc, page_map)
    assert [unit.pages for unit in units] == [[18, 19, 20, 21]]
    # Cut by size: the later unit still sees the chart title and the opening question.
    small = build_units(doc, page_map, max_chars=170)
    last = next(unit for unit in small if "p21.b1" in unit.segment_ids)
    assert len(small) > 1 and {"p18.b1", "p19.b1"} <= set(last.context_segment_ids)


def test_a_unit_cut_by_size_starts_at_a_page_rather_than_inside_it():
    from backend.kg_v3.mapper import build_units

    doc = _pages({1: ["Problem A: display dead " * 6, "1 Is the fuse open? " * 6],
                  2: ["2 Is the filter open?", "No Replace the filter.", "3 Replace the PCB."]})
    page_map = DocumentMap(entries=[PageMapEntry(page=page, label=PageLabel.DIAGNOSTIC, section="S")
                                    for page in (1, 2)])
    units = build_units(doc, page_map, max_chars=330)
    assert [unit.pages for unit in units] == [[1], [2]]
    assert "p1.b1" in units[1].context_segment_ids

