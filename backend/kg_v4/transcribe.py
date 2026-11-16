"""Pages without usable text, read from their image by a vision model.

A scanned page, a drawing whose lettering is made of strokes, or a page whose text layer is a
broken character map gives the reader nothing to cite. Rules that cost nothing find such pages;
only they are sent to the model, as an image, and the model returns what is printed, block by
block. The blocks become segments of the page, citable like any other and marked as transcribed.
A page with good text is never sent: its text layer is exact and free.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from backend.kg_v3.contracts import Segment, SegmentKind
from backend.kg_v3.reader import DocumentText
from backend.kg_v4.prompts import TRANSCRIBE_PROMPT
from backend.kg_v4.sections import BOOKMARK_LEVELS, MAX_SECTION_CHARS, Heading, SectionIndex

logger = logging.getLogger(__name__)

MIN_TEXT_CHARS = 80  # less than a title and a page number
MIN_IMAGE_SHARE = 0.25  # a picture over a quarter of the page: a scan
MIN_STROKES = 200  # a drawing with its lettering made of strokes
GARBLED_WORD_SHARE = 0.3  # words holding characters no language uses
GARBLED_MIN_WORDS = 30
# Transcribed segments are p<page>.o101, .o102, ...: never an ID the reader gives.
FIRST_BLOCK = 101
IMAGE_ZOOM = 2.0
OUTPUT_TOKENS = 8000
BLOCK_KINDS = ("heading", "text", "list_item", "table_row", "flow_step", "figure")
_SPACES = re.compile(r"[ \t\r\f\v]+")

TRANSCRIPT_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "required": ["legible", "language", "printed_page", "blocks"],
    "properties": {
        "legible": {"type": "boolean"},
        "language": {"type": "string"},
        "printed_page": {"type": "string"},
        "blocks": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["kind", "text"],
            "properties": {"kind": {"type": "string", "enum": list(BLOCK_KINDS)}, "text": {"type": "string"}}}},
    },
}


def _unusable(char: str) -> bool:
    return char == "�" or unicodedata.category(char) in {"Co", "Cn", "Cs", "Cc"}


def garbled(text: str) -> bool:
    """Text whose words are mostly made of characters no language uses (a broken character map).

    Rows of leader dots printed with a broken font do not count: they are a few long "words".
    """

    words = text.split()
    if len(words) < GARBLED_MIN_WORDS:
        return False
    return sum(any(_unusable(char) for char in word) for word in words) >= GARBLED_WORD_SHARE * len(words)


def page_kind(text: str, image_share: float, strokes: int) -> str:
    """text, scanned (a picture or drawing with no text layer), garbled or blank."""

    if len(text.strip()) < MIN_TEXT_CHARS:
        return "scanned" if image_share >= MIN_IMAGE_SHARE or strokes >= MIN_STROKES else "blank"
    return "garbled" if garbled(text) else "text"


def pages_without_text(doc: DocumentText, geometry: dict[int, dict] | None = None) -> dict[int, str]:
    """Pages to transcribe with their reason; pages with usable text and blank pages are left out."""

    geometry = geometry if geometry is not None else doc.page_geometry
    found = {}
    for page in range(1, doc.page_count + 1):
        layout = geometry.get(page) or {}
        text = "\n".join(segment.text for segment in doc.pages.get(page, []))
        kind = page_kind(text, float(layout.get("image_area_share") or 0), int(layout.get("drawing_count") or 0))
        if kind in {"scanned", "garbled"}:
            found[page] = kind
    return found


def page_image(pdf: Path, page: int, zoom: float = IMAGE_ZOOM) -> str:
    import fitz

    with fitz.open(pdf) as source:
        pixmap = source[page - 1].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return "data:image/png;base64," + base64.b64encode(pixmap.tobytes("png")).decode()


def clean_blocks(raw: Any) -> list[dict[str, str]]:
    blocks = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        text = "\n".join(line for line in (_SPACES.sub(" ", part).strip() for part in str(item.get("text") or "").split("\n"))
                         if line)
        if text and re.search(r"\w", text):
            blocks.append({"kind": item.get("kind") if item.get("kind") in BLOCK_KINDS else "text", "text": text})
    return blocks


class Transcriber:
    """One call per page: the image in, the printed text out."""

    def __init__(self, llm, pdf: Path, *, asset_name: str, concurrency: int = 6) -> None:
        self.llm, self.pdf = llm, Path(pdf)
        self.system = TRANSCRIBE_PROMPT.format(asset=asset_name)
        self._limit = asyncio.Semaphore(max(1, concurrency))

    async def page(self, page: int, reason: str) -> dict[str, Any]:
        """The transcript of a page; ``failed`` when the call did not return one."""

        try:
            image = await asyncio.to_thread(page_image, self.pdf, page)
            async with self._limit:
                data = await self.llm.json(system=self.system, user=f"Page {page} of the manual.",
                                           schema=TRANSCRIPT_SCHEMA, name="kg_v4_transcribe",
                                           max_output_tokens=OUTPUT_TOKENS, images=[image])
        except Exception as exc:
            logger.warning("Transcription of page %s failed: %s", page, exc)
            return {"page": page, "reason": reason, "failed": True, "error": type(exc).__name__, "blocks": []}
        return {"page": page, "reason": reason, "failed": False, "legible": bool(data.get("legible", True)),
                "language": str(data.get("language") or ""), "printed_page": str(data.get("printed_page") or ""),
                "blocks": clean_blocks(data.get("blocks"))}


def segments_of(transcript: dict[str, Any]) -> list[Segment]:
    page = int(transcript["page"])
    return [Segment(segment_id=f"p{page}.o{number}", page=page, kind=SegmentKind.OCR_TEXT,
                    text=block["text"].replace("\n", " "), evidence_id=f"transcript:p{page}.o{number}",
                    low_quality=not transcript.get("legible", True))
            for number, block in enumerate(transcript["blocks"], start=FIRST_BLOCK)]


def is_transcribed(segment: Segment) -> bool:
    return segment.evidence_id.startswith("transcript:")


def with_transcripts(doc: DocumentText, transcripts: list[dict[str, Any]]) -> DocumentText:
    """The document with the transcribed pages in place of what the reader had for them."""

    pages = dict(doc.pages)
    for transcript in transcripts:
        segments = segments_of(transcript)
        if segments:
            pages[int(transcript["page"])] = segments
    return DocumentText(page_count=doc.page_count, pages=pages, section_titles=doc.section_titles,
                        page_geometry=doc.page_geometry, source_index=doc.source_index,
                        candidate_dispositions=doc.candidate_dispositions)


def add_sections(sections: SectionIndex, transcripts: list[dict[str, Any]]) -> None:
    """Name the transcribed pages and their segments by the headings read on them.

    A heading opens a section, under the chapter of the PDF outline when the PDF has one; a page
    without a heading continues the section of the page before it. Printed page numbers read on
    the images give the page offset when the text layer gave none.
    """

    outlined = any(heading.level <= BOOKMARK_LEVELS for heading in sections.headings)
    offsets: Counter = Counter()
    carried, chapter_before = "", None
    for transcript in sorted(transcripts, key=lambda item: int(item["page"])):
        page = int(transcript["page"])
        chapter = sections.by_page.get(page, "")
        if chapter != chapter_before or not carried:
            carried = chapter or sections.by_page.get(page - 1, "")
        chapter_before = chapter
        printed = re.fullmatch(r"\D{0,6}(\d{1,4})\D{0,3}", transcript.get("printed_page", "").strip())
        if printed:
            offsets[page - int(printed.group(1))] += 1
        opening = ""
        for position, (segment, block) in enumerate(zip(segments_of(transcript), transcript["blocks"])):
            if block["kind"] == "heading":
                title = block["text"].replace("\n", " ")
                root = chapter.split(" > ")[0] if outlined and chapter else ""
                carried = (f"{root} > {title}" if root and title not in chapter else title)[:MAX_SECTION_CHARS]
                sections.headings.append(Heading(page, float(position), title, BOOKMARK_LEVELS + 2))
            if position < 2:
                opening = carried
            sections.by_segment[segment.segment_id] = carried
        if transcript["blocks"]:
            sections.by_page[page] = opening or carried
    sections.headings.sort(key=lambda item: (item.page, item.top, item.level))
    if offsets and not sections.page_offset:
        offset, votes = offsets.most_common(1)[0]
        if votes >= 3 and votes >= 0.5 * sum(offsets.values()):
            sections.page_offset = offset


def summary(wanted: dict[int, str], transcripts: list[dict[str, Any]], skipped: list[int]) -> dict[str, Any]:
    """What the report says about the pages read from their image."""

    done = [item for item in transcripts if not item.get("failed")]
    return {
        "pages_without_text": dict(Counter(wanted.values())),
        "transcribed_pages": sorted(int(item["page"]) for item in done if item["blocks"]),
        "empty_pages": sorted(int(item["page"]) for item in done if not item["blocks"]),
        "hard_to_read_pages": sorted(int(item["page"]) for item in done if item["blocks"] and not item.get("legible", True)),
        "failed_pages": sorted(int(item["page"]) for item in transcripts if item.get("failed")),
        "pages_over_the_limit": sorted(skipped),
        "blocks": sum(len(item["blocks"]) for item in done),
        "languages": dict(Counter(item.get("language") or "?" for item in done if item["blocks"])),
    }
