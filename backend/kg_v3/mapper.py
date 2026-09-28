"""Station 2, map: label every page, then cut diagnostic pages into reading units.

Two independent model readings label each batch of pages from a compact
outline. A page either reading calls diagnostic is read; a page both call
diagnostic is confirmed and a gate cannot drop it, because an extra page costs
little and a dropped one loses its branches. Pages without any text are
unreadable by construction. Units are consecutive diagnostic pages of one
section, cut only between segments, so that every segment is owned by exactly
one unit.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections import Counter
from typing import Any

from backend.kg_v3.contracts import (
    AnswerOption,
    DocumentMap,
    PageLabel,
    PageMapEntry,
    Question,
    QuestionKind,
    ReadingUnit,
    Segment,
    SegmentKind,
    assert_single_owner,
)
from backend.kg_v3.llm import ModelClient
from backend.kg_v3.prompts import MAP_PROMPT
from backend.kg_v3.reader import DocumentText, render_segment

logger = logging.getLogger(__name__)

OUTLINE_CHARS = 480
SHORT_LINE = 80
MAP_BATCH_PAGES = 20
MAP_READS = 2
UNIT_MAX_CHARS = 9000
UNIT_MAX_SEGMENTS = 160
CONTEXT_SEGMENTS = 2


def page_outline(doc: DocumentText, page: int, *, chars: int = OUTLINE_CHARS) -> str:
    """Start of the page plus its short lines (headings, labels) from anywhere on the page."""

    segments = doc.pages.get(page) or []
    tables = sorted({segment.table.table for segment in segments if segment.table})
    headers = next((" | ".join(segment.table.headers) for segment in segments if segment.table and segment.table.headers), "")
    table_note = f" [{len(tables)} table(s){': ' + headers if headers else ''}]" if tables else ""
    opening = " / ".join(segment.text for segment in segments)[: chars // 2]
    labels = [segment.text for segment in segments[1:] if segment.table is None and len(segment.text) <= SHORT_LINE]
    later = " / ".join(dict.fromkeys(labels))[: chars - len(opening)]
    section = f" [section: {doc.section_titles[page]}]" if page in doc.section_titles else ""
    return f"p{page}{section}{table_note}: {opening}" + (f" ... {later}" if later else "")


def fill_gaps(page_map: DocumentMap) -> DocumentMap:
    """Structural safety net: read continuations of diagnostic pages too.

    A page between two diagnostic pages, or a procedure page next to one, is
    read as diagnostic and marked unsure.
    """

    labels = {entry.page: entry.label for entry in page_map.entries}
    diagnostic = {page for page, label in labels.items() if label is PageLabel.DIAGNOSTIC}
    promote = {
        entry.page for entry in page_map.entries
        if entry.label in {PageLabel.OTHER, PageLabel.PROCEDURE}
        and ({entry.page - 1, entry.page + 1} <= diagnostic
             or (entry.label is PageLabel.PROCEDURE and {entry.page - 1, entry.page + 1} & diagnostic))
    }
    return DocumentMap(entries=[
        entry.model_copy(update={"label": PageLabel.DIAGNOSTIC, "unsure": True}) if entry.page in promote else entry
        for entry in page_map.entries
    ])


def _map_schema(pages: list[int]) -> dict[str, Any]:
    entry = {
        "type": "object", "additionalProperties": False, "required": ["page", "label", "section", "unsure"],
        "properties": {
            "page": {"type": "integer", "enum": pages},
            "label": {"type": "string", "enum": ["diagnostic", "procedure", "parts", "other"]},
            "section": {"type": "string"},
            "unsure": {"type": "boolean"},
        },
    }
    return {"type": "object", "additionalProperties": False, "required": ["pages"],
            "properties": {"pages": {"type": "array", "items": entry}}}


def combine_readings(page: int, readings: list[PageMapEntry], reads: int) -> PageMapEntry:
    """One entry from the independent readings of a page: any diagnostic vote is read."""

    diagnostic = [entry for entry in readings if entry.label is PageLabel.DIAGNOSTIC]
    if diagnostic:
        confirmed = len(diagnostic) == reads
        return PageMapEntry(page=page, label=PageLabel.DIAGNOSTIC,
                            section=next((entry.section for entry in diagnostic if entry.section), ""),
                            unsure=not confirmed or any(entry.unsure for entry in diagnostic),
                            confirmed=confirmed)
    labels = Counter(entry.label for entry in readings)
    label = labels.most_common(1)[0][0]
    return PageMapEntry(page=page, label=label,
                        section=next((entry.section for entry in readings if entry.section), ""),
                        unsure=len(labels) > 1 or any(entry.unsure for entry in readings))


def attach_pdf_sections(doc: DocumentText, pdf) -> None:
    """PDF bookmarks supply section boundaries without touching citable segments."""
    import fitz

    with fitz.open(pdf) as source:
        toc = source.get_toc()
    headings = {page: title for _level, title, page in toc if 1 <= page <= doc.page_count}
    current = ""
    for page in range(1, doc.page_count + 1):
        current = headings.get(page, current)
        if current:
            doc.section_titles[page] = current


def section_batches(doc: DocumentText, batch_pages: int) -> list[list[int]]:
    batches: list[list[int]] = []
    for page in sorted(doc.pages):
        if (not batches or len(batches[-1]) >= batch_pages
                or doc.section_titles.get(page, '') != doc.section_titles.get(batches[-1][-1], '')):
            batches.append([])
        batches[-1].append(page)
    return batches


async def map_pages(llm: ModelClient, doc: DocumentText, *, batch_pages: int = MAP_BATCH_PAGES,
                    reads: int = MAP_READS) -> DocumentMap:
    batches = section_batches(doc, batch_pages)
    reads = max(1, reads)

    async def label(batch: list[int]) -> dict[int, PageMapEntry] | None:
        text = "\n".join(page_outline(doc, page) for page in batch)
        try:
            data = await llm.json(system=MAP_PROMPT, user=text, schema=_map_schema(batch),
                                  name="kg_v3_map", max_output_tokens=4000)
        except Exception as exc:
            logger.warning("Page map batch %s-%s failed: %s", batch[0], batch[-1], exc)
            return None
        entries: dict[int, PageMapEntry] = {}
        for item in data.get("pages") or []:
            try:
                page = int(item["page"])
                entries[page] = PageMapEntry(page=page, label=PageLabel(item["label"]),
                                             section=doc.section_titles.get(page, str(item.get("section") or "")[:120]),
                                             unsure=bool(item.get("unsure")))
            except (KeyError, ValueError, TypeError):
                continue
        return entries

    first = await asyncio.gather(*(label(batch) for batch in batches))
    jobs = [(batch, result) for batch, result in zip(batches, first)]
    # A section is uncertain if incomplete, explicitly doubtful, mixed in label,
    # or lacking section evidence. Confident homogeneous sections need no second call.
    uncertain = [batch for batch, result in jobs if result is None or set(result) != set(batch)
                 or any(e.unsure or not e.section for e in result.values())
                 or len({e.label for e in result.values()}) > 1]
    for _ in range(1, reads):
        jobs.extend(zip(uncertain, await asyncio.gather(*(label(batch) for batch in uncertain))))
    readings: dict[int, list[PageMapEntry]] = {}
    failed: set[int] = set()
    for batch, result in jobs:
        if result is None:
            failed.update(batch)
            continue
        for page, entry in result.items():
            if page in batch:
                readings.setdefault(page, []).append(entry)
    entries = []
    for page in range(1, doc.page_count + 1):
        if page not in doc.pages:
            entries.append(PageMapEntry(page=page, label=PageLabel.UNREADABLE))
        elif page in readings:
            entry = combine_readings(page, readings[page], reads)
            # A reading that failed is not a vote: without it the page cannot be confirmed.
            entries.append(entry.model_copy(update={"confirmed": False}) if page in failed else entry)
        elif page in failed:  # every reading failed: kept for reading, never silently dropped
            entries.append(PageMapEntry(page=page, label=PageLabel.DIAGNOSTIC, unsure=True))
        else:
            entries.append(PageMapEntry(page=page, label=PageLabel.OTHER, unsure=True))
    return fill_gaps(DocumentMap(entries=entries))


def _ranges(pages: list[int]) -> str:
    if not pages:
        return "none"
    parts, start, previous = [], pages[0], pages[0]
    for page in pages[1:] + [None]:
        if page is not None and page == previous + 1:
            previous = page
            continue
        parts.append(f"{start}-{previous}" if previous != start else str(start))
        if page is not None:
            start = previous = page
    return ", ".join(parts)


def map_question(doc: DocumentText, page_map: DocumentMap) -> Question:
    """Gate 1: the whole map in one question, with the outline of every page."""

    diagnostic = page_map.pages_with(PageLabel.DIAGNOSTIC)
    confirmed = [entry.page for entry in page_map.entries if entry.confirmed]
    proposal = [
        f"Diagnostic pages to read in detail: {_ranges(diagnostic)}.",
        f"Pages both map readings label diagnostic (always read, a change cannot drop them): {_ranges(confirmed)}.",
        f"Pages labelled diagnostic with doubt: {_ranges([e.page for e in page_map.entries if e.unsure])}.",
        f"Unreadable pages (no text): {_ranges(page_map.pages_with(PageLabel.UNREADABLE))}.",
        "Label and outline of every page follow.",
    ]
    for entry in page_map.entries:
        outline = page_outline(doc, entry.page, chars=160) if entry.page in doc.pages else f"p{entry.page}: no text"
        doubt = ", unsure" if entry.unsure else ""
        proposal.append(f"{entry.label.value}{doubt} | {outline}")
    return Question(
        question_id="map",
        kind=QuestionKind.MAP_REVIEW,
        title="Is this page map right for extracting troubleshooting knowledge?",
        proposal=proposal,
        options=[
            AnswerOption(option_id="confirm", label="Yes, the map is right",
                         effect="the labelled diagnostic pages are read in detail"),
            AnswerOption(option_id="correct", label="Change some page labels",
                         effect="the listed pages get the new labels before reading; pages both map "
                                "readings label diagnostic stay diagnostic"),
        ],
        default_option_id="confirm",
        priority=100,
        target={"pages": diagnostic},
    )


MAX_MAP_QUESTIONS = 8


def map_questions(doc: DocumentText, page_map: DocumentMap) -> list[Question]:
    """Map review in a few questions: only around pages labelled diagnostic or doubtful.

    Confident non-diagnostic stretches need no reviewer. A page next to a diagnostic
    or doubtful one is shown too, so a reviewer can still add a missed continuation.
    """

    wanted = {entry.page for entry in page_map.entries
              if entry.label is PageLabel.DIAGNOSTIC or entry.unsure}
    shown = sorted({page + delta for page in wanted for delta in (-1, 0, 1)}
                   & {entry.page for entry in page_map.entries})
    if not shown:
        return []
    chunk = max(MAP_BATCH_PAGES, -(-len(shown) // MAX_MAP_QUESTIONS))
    by_page = {entry.page: entry for entry in page_map.entries}
    groups: list[list[PageMapEntry]] = []
    for page in shown:
        if not groups or len(groups[-1]) >= chunk:
            groups.append([])
        groups[-1].append(by_page[page])
    return [map_question(doc, DocumentMap(entries=entries)).model_copy(update={
        "question_id": f"map:{entries[0].page}-{entries[-1].page}"}) for entries in groups]


def _map_changes(page_map: DocumentMap, edits: dict[str, Any]) -> dict[int, PageLabel]:
    pages = {entry.page for entry in page_map.entries}
    changes: dict[int, PageLabel] = {}
    for page, label in dict(edits.get("pages") or {}).items():
        try:
            if int(page) in pages:
                changes[int(page)] = PageLabel(label)
        except ValueError:
            continue
    return changes


def protected_demotions(page_map: DocumentMap, edits: dict[str, Any]) -> list[int]:
    """Confirmed diagnostic pages a correction tried to drop; they stay diagnostic."""

    confirmed = {entry.page for entry in page_map.entries if entry.confirmed}
    sections: dict[str, list[int]] = {}
    for entry in page_map.entries:
        if entry.confirmed and entry.section:
            sections.setdefault(entry.section, []).append(entry.page)
    for entry in page_map.entries:
        anchors = sections.get(entry.section, [])
        if len(anchors) >= 2 and min(anchors) < entry.page < max(anchors):
            # Do not bridge a different intervening section.
            if all(e.section == entry.section for e in page_map.entries
                   if min(anchors) <= e.page <= max(anchors)):
                confirmed.add(entry.page)
    return sorted(page for page, label in _map_changes(page_map, edits).items()
                  if page in confirmed and label is not PageLabel.DIAGNOSTIC)


def apply_map_answer(page_map: DocumentMap, edits: dict[str, Any]) -> DocumentMap:
    protected = set(protected_demotions(page_map, edits))
    changes = {page: label for page, label in _map_changes(page_map, edits).items() if page not in protected}
    return page_map.relabel(changes) if changes else page_map


def _rendered_size(segment: Segment) -> int:
    return len(render_segment(segment)) + 1


TRAIL_PAGES = 3
TRAIL_SEGMENTS = 2


def trail_context(doc: DocumentText, run: list[int], first: Segment) -> list[str]:
    """Opening segments of the earlier pages of a diagnostic run, read-only.

    A flowchart, procedure or table often names its problem on the page where it
    starts and continues on the next pages; a unit cut later still sees that title.
    """

    pages = [page for page in run if page < first.page][-TRAIL_PAGES:]
    if doc.pages[first.page][0].segment_id != first.segment_id:
        pages.append(first.page)
    return [segment.segment_id for page in pages for segment in doc.pages[page][:TRAIL_SEGMENTS]
            if segment.segment_id != first.segment_id]


def build_units(
    doc: DocumentText,
    page_map: DocumentMap,
    *,
    max_chars: int = UNIT_MAX_CHARS,
    max_segments: int = UNIT_MAX_SEGMENTS,
) -> list[ReadingUnit]:
    """Consecutive diagnostic pages are read together, cut only by size.

    Section names from the map vary from page to page, so they only suggest where to
    cut: a section, like a table, starts a new unit when it fits whole in one.
    """

    sections = {entry.page: entry.section for entry in page_map.entries}
    diagnostic = [page for page in page_map.pages_with(PageLabel.DIAGNOSTIC) if page in doc.pages]
    runs: list[list[int]] = []
    for page in diagnostic:
        if runs and page == runs[-1][-1] + 1:
            runs[-1].append(page)
        else:
            runs.append([page])

    ordered = doc.segments()
    units: list[ReadingUnit] = []
    for run in runs:
        segments = [segment for page in run for segment in doc.pages[page]]
        chunks: list[list[Segment]] = [[]]
        size = 0
        for index, segment in enumerate(segments):
            table_start = (
                segment.kind is SegmentKind.TABLE_ROW
                and (index == 0 or segments[index - 1].table is None
                     or segments[index - 1].table.table != segment.table.table
                     or segments[index - 1].page != segment.page)
            )
            table_rows = 0
            if table_start:
                table_rows = sum(
                    _rendered_size(item) for item in segments[index:]
                    if item.page == segment.page and item.table and item.table.table == segment.table.table
                )
            section_start = index > 0 and segment.page != segments[index - 1].page and (
                sections.get(segment.page) != sections.get(segments[index - 1].page))
            section_size = 0
            if section_start:
                pages = [page for page in run if page >= segment.page]
                span = next((i for i, page in enumerate(pages) if sections.get(page) != sections.get(segment.page)),
                            len(pages))
                section_size = sum(_rendered_size(item) for page in pages[:span] for item in doc.pages[page])
            # Keep a table, or a section, whole when it fits in a unit of its own.
            wants_break = chunks[-1] and (
                (table_start and size + table_rows > max_chars and table_rows <= max_chars)
                or (section_start and size + section_size > max_chars and section_size <= max_chars))
            too_big = chunks[-1] and (size + _rendered_size(segment) > max_chars or len(chunks[-1]) >= max_segments)
            carried: list[Segment] = []
            if too_big and not wants_break and segment.table is None:
                # Cut at the start of the page rather than inside it (a flowchart is one page).
                head = [item for item in chunks[-1] if item.page == segment.page]
                if (head and len(head) < len(chunks[-1]) and not any(item.table for item in head)
                        and sum(map(_rendered_size, head)) <= max_chars // 2):
                    chunks[-1] = chunks[-1][:-len(head)]
                    carried = head
            if wants_break or too_big:
                chunks.append(carried)
                size = sum(map(_rendered_size, carried))
            chunks[-1].append(segment)
            size += _rendered_size(segment)
        for chunk in chunks:
            if not chunk:
                continue
            first = doc.position(chunk[0].segment_id) or 0
            context = trail_context(doc, run, chunk[0])
            context += [item.segment_id for item in ordered[max(0, first - CONTEXT_SEGMENTS):first]]
            # Keep the blocks introducing this table even when it is split over units.
            if chunk[0].table:
                table_first = next((i for i, s in enumerate(ordered) if s.page == chunk[0].page
                                    and s.table and s.table.table == chunk[0].table.table), first)
                i = table_first - 1
                while i >= 0 and ordered[i].page == chunk[0].page and ordered[i].table is None:
                    context.append(ordered[i].segment_id)
                    i -= 1
            context.extend(c for segment in chunk for c in doc.step_context(segment.segment_id))
            context = list(dict.fromkeys(context))
            if chunk[0].table and chunk[0].table.row > 1:
                header = f"p{chunk[0].page}.t{chunk[0].table.table}.r1"
                if doc.segment(header) and header not in context:
                    context.insert(0, header)
            owned = [item.segment_id for item in chunk]
            # The ID follows the content: a different map never reuses another unit's saved reads.
            digest = hashlib.sha256("|".join(owned).encode("utf-8")).hexdigest()[:6]
            units.append(ReadingUnit(
                unit_id=f"u{len(units) + 1:03d}-{digest}",
                section=sections.get(chunk[0].page, ""),
                pages=sorted({item.page for item in chunk}),
                segment_ids=owned,
                context_segment_ids=[item for item in context if item not in owned],
            ))
    assert_single_owner(units)
    return units
