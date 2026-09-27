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
MAP_BATCH_PAGES = 60
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
    return f"p{page}{table_note}: {opening}" + (f" ... {later}" if later else "")


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


async def map_pages(llm: ModelClient, doc: DocumentText, *, batch_pages: int = MAP_BATCH_PAGES,
                    reads: int = MAP_READS) -> DocumentMap:
    readable = sorted(doc.pages)
    batches = [readable[index:index + batch_pages] for index in range(0, len(readable), batch_pages)]
    reads = max(1, reads)

    async def label(batch: list[int]) -> dict[int, PageMapEntry] | None:
        text = "\n".join(page_outline(doc, page) for page in batch)
        try:
            data = await llm.json(system=MAP_PROMPT, user=text, schema=_map_schema(batch),
                                  name="kg_v3_map", max_output_tokens=12000)
        except Exception as exc:
            logger.warning("Page map batch %s-%s failed: %s", batch[0], batch[-1], exc)
            return None
        entries: dict[int, PageMapEntry] = {}
        for item in data.get("pages") or []:
            try:
                page = int(item["page"])
                entries[page] = PageMapEntry(page=page, label=PageLabel(item["label"]),
                                             section=str(item.get("section") or "")[:120],
                                             unsure=bool(item.get("unsure")))
            except (KeyError, ValueError, TypeError):
                continue
        return entries

    jobs = [(batch, read) for batch in batches for read in range(reads)]
    results = await asyncio.gather(*(label(batch) for batch, _ in jobs))
    readings: dict[int, list[PageMapEntry]] = {}
    failed: set[int] = set()
    for (batch, _), result in zip(jobs, results):
        if result is None:
            failed.update(batch)
            continue
        for page, entry in result.items():
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
    return sorted(page for page, label in _map_changes(page_map, edits).items()
                  if page in confirmed and label is not PageLabel.DIAGNOSTIC)


def apply_map_answer(page_map: DocumentMap, edits: dict[str, Any]) -> DocumentMap:
    protected = set(protected_demotions(page_map, edits))
    changes = {page: label for page, label in _map_changes(page_map, edits).items() if page not in protected}
    return page_map.relabel(changes) if changes else page_map


def _rendered_size(segment: Segment) -> int:
    return len(render_segment(segment)) + 1


def build_units(
    doc: DocumentText,
    page_map: DocumentMap,
    *,
    max_chars: int = UNIT_MAX_CHARS,
    max_segments: int = UNIT_MAX_SEGMENTS,
) -> list[ReadingUnit]:
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
            # Keep a table whole when it fits in a unit of its own.
            wants_break = table_start and chunks[-1] and size + table_rows > max_chars and table_rows <= max_chars
            too_big = chunks[-1] and (size + _rendered_size(segment) > max_chars or len(chunks[-1]) >= max_segments)
            if wants_break or too_big:
                chunks.append([])
                size = 0
            chunks[-1].append(segment)
            size += _rendered_size(segment)
        for chunk in chunks:
            if not chunk:
                continue
            first = doc.position(chunk[0].segment_id) or 0
            context = [item.segment_id for item in ordered[max(0, first - CONTEXT_SEGMENTS):first]]
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
