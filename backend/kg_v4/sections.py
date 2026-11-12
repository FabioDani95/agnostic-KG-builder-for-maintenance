"""Sections, printed page numbers and cross-references of a manual, read from the PDF itself.

No model is involved. Every segment gets the trail of headings above it, so each fact can carry
page and section. Headings come from the PDF bookmarks when they are usable and from lines set
larger or bolder than the body text. Printed page numbers let "see page 63" point to the right
PDF page; section numbers ("6.3", "9-1") and titles point to the page where the heading stands.
"""

from __future__ import annotations

import re
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from backend.kg_v4.names import canonical, tokens

MAX_HEADING_CHARS = 90
MAX_SECTION_CHARS = 140
BOOKMARK_LEVELS = 9  # font headings rank below every bookmark level
_LETTERS = re.compile(r"[^\W\d_]{2,}")
_PRINTED = re.compile(r"^(?:page\s*)?-?\s*(\d{1,4})\s*-?$", re.I)
_SECTION_NUMBER = re.compile(r"^\s*((?:\d+[.-])*\d+)[.)]?\s+\S")
_PAGE_REF = re.compile(r"\b(?:pages?|pg\.?|p\.)\s*(\d{1,4})\b", re.I)
_SECTION_REF = re.compile(r"(?:\b(?:sections?|sect\.|chapter|paragraph|par\.)|§)\s*((?:\d+[.-])*\d+)"
                          r"(?:\s*(?:,|and|&)\s*((?:\d+[.-])*\d+))?", re.I)


@dataclass(frozen=True)
class Heading:
    page: int
    top: float
    text: str
    level: int


@dataclass
class SectionIndex:
    page_count: int = 0
    headings: list[Heading] = field(default_factory=list)
    by_segment: dict[str, str] = field(default_factory=dict)
    by_page: dict[int, str] = field(default_factory=dict)
    # Printed number = PDF page - offset, when the manual numbers its pages consistently.
    page_offset: int = 0

    def section(self, segment_id: str = "", page: int = 0) -> str:
        return self.by_segment.get(segment_id) or self.by_page.get(page, "")

    def pdf_page(self, printed: int) -> int | None:
        page = printed + self.page_offset
        return page if 1 <= page <= self.page_count else None

    def heading_pages(self, number: str = "", title: str = "") -> list[int]:
        """Pages whose heading starts with a section number or carries a title."""

        if number:
            wanted = re.sub(r"[.-]", ".", number).strip(".")
            found = []
            for heading in self.headings:
                match = _SECTION_NUMBER.match(heading.text)
                if match and re.sub(r"[.-]", ".", match.group(1)).strip(".") == wanted:
                    found.append(heading.page)
            return sorted(set(found))
        want = set(tokens(title))
        if len(want) < 2:
            return []
        return sorted({heading.page for heading in self.headings
                       if len(set(tokens(heading.text))) >= 2 and set(tokens(heading.text)) <= want})

    def resolve(self, text: str) -> tuple[list[int], str]:
        """PDF pages a printed pointer leads to, and the section named there."""

        pages: list[int] = []
        for match in _PAGE_REF.finditer(text):
            page = self.pdf_page(int(match.group(1)))
            if page:
                pages.append(page)
        for match in _SECTION_REF.finditer(text):
            for number in filter(None, match.groups()):
                pages.extend(self.heading_pages(number=number))
        if not pages:
            pages.extend(self.heading_pages(title=text))
        pages = sorted(set(pages))
        return pages, (self.by_page.get(pages[0], "") if pages else "")


def has_reference(text: str) -> bool:
    return bool(_PAGE_REF.search(text) or _SECTION_REF.search(text))


def _usable_bookmarks(toc: list) -> list[tuple[int, int, float, str]]:
    """(level, page, top, title) for bookmarks that name something; junk outlines give nothing."""

    items = []
    for entry in toc:
        level, title, page = int(entry[0]), " ".join(str(entry[1]).split()), int(entry[2])
        top = 0.0
        if len(entry) > 3 and isinstance(entry[3], dict):
            point = entry[3].get("to")
            top = float(getattr(point, "y", 0.0) or 0.0)
        if _LETTERS.search(title) and page >= 1:
            items.append((min(level, BOOKMARK_LEVELS), page, top, title[:MAX_HEADING_CHARS]))
    titles = Counter(title for _, _, _, title in items)
    # One title repeated for every bookmark ("#EV#", "Untitled") is no outline.
    if not items or (len(items) >= 3 and titles.most_common(1)[0][1] > 0.6 * len(items)):
        return []
    return items


def _page_lines(page) -> list[dict]:
    lines = []
    for block in page.get_text("dict").get("blocks", []):
        block_lines = [line for line in block.get("lines", [])
                       if any(str(span.get("text", "")).strip() for span in line.get("spans", []))]
        for line in block_lines:
            spans = [span for span in line.get("spans", []) if str(span.get("text", "")).strip()]
            text = " ".join(" ".join(str(span["text"]).split()) for span in spans).strip()
            lines.append({
                "text": text, "size": max(float(span["size"]) for span in spans),
                "bold": all(int(span.get("flags", 0)) & 16 or "bold" in str(span.get("font", "")).lower()
                            for span in spans),
                "top": float(line["bbox"][1]), "bottom": float(line["bbox"][3]),
                "chars": sum(len(str(span["text"])) for span in spans), "block_lines": len(block_lines),
            })
    return lines


def _printed_number(lines: list[dict], height: float) -> int | None:
    for line in lines:
        if line["top"] < 0.08 * height or line["bottom"] > 0.92 * height:
            match = _PRINTED.match(line["text"])
            if match:
                return int(match.group(1))
    return None


def build_sections(pdf: Path | str, doc=None) -> SectionIndex:
    """Read headings and page numbers from the PDF; with the read document, map them to segments."""

    import fitz

    with fitz.open(pdf) as source:
        page_count = source.page_count
        bookmarks = _usable_bookmarks(source.get_toc(simple=False))
        pages = {number: (_page_lines(page), float(page.rect.height)) for number, page in enumerate(source, 1)}
    sizes: Counter = Counter()
    for lines, _ in pages.values():
        for line in lines:
            sizes[round(line["size"], 1)] += line["chars"]
    body = sizes.most_common(1)[0][0] if sizes else 10.0

    tables: dict[int, list[tuple[float, float]]] = {}
    if doc is not None:
        for page, segments in doc.pages.items():
            tables[page] = [(segment.bbox[1], segment.bbox[3]) for segment in segments
                            if segment.table is not None and segment.bbox]

    # (page, top, text, size, kind): a running header at the top of the page, a line set larger
    # than the body, or a short bold line standing alone.
    candidates: list[tuple[int, float, str, float, str]] = []
    offsets: Counter = Counter()
    for number, (lines, height) in pages.items():
        printed = _printed_number(lines, height)
        if printed is not None:
            offsets[number - printed] += 1
        if number == 1 and page_count > 4:
            continue  # a cover names the document, not a section
        for line in lines:
            text = line["text"]
            if not (4 <= len(text) <= MAX_HEADING_CHARS) or not _LETTERS.search(text) or text.endswith((".", ",", ";")):
                continue
            if any(top - 1 <= line["top"] <= bottom + 1 for top, bottom in tables.get(number, [])):
                continue
            if line["top"] < 0.10 * height and len(text) <= 60 and line["block_lines"] <= 2:
                kind = "running"
            elif line["size"] >= body + 1.5 and line["block_lines"] <= 3:
                kind = "larger"
            elif (line["bold"] and line["size"] >= body and line["block_lines"] == 1 and text[:1].isupper()
                  and len(text) <= 70 and (len(text.split()) >= 2 or len(text) >= 8)):
                kind = "bold"
            else:
                continue
            candidates.append((number, line["top"], text, round(line["size"], 1), kind))
    # A line printed on most pages (product name, footer) is neither a heading nor a chapter header.
    repeated = Counter()
    for page_texts in ({(page, canonical(text)) for page, _, text, _, _ in candidates},):
        repeated.update(text for _, text in page_texts)
    limit = max(4, page_count // 3)
    ranks = sorted({size for _, _, _, size, kind in candidates if kind == "larger"}, reverse=True)

    headings = [Heading(page, top, title, level) for level, page, top, title in bookmarks]
    known = {(heading.page, canonical(heading.text)) for heading in headings}
    running = ""
    for page, top, text, size, kind in sorted(candidates):
        name = canonical(text)
        if repeated[name] > limit or (page, name) in known:
            continue
        weakest = BOOKMARK_LEVELS + 2 + len(ranks)
        if kind == "running":
            if name == running:
                # The same chapter header on its next page: a weak (bold) heading does not carry over.
                headings.append(Heading(page, top, "", weakest))
                continue
            running, level = name, BOOKMARK_LEVELS + 1
        else:
            level = BOOKMARK_LEVELS + 2 + ranks.index(size) if kind == "larger" else weakest
        headings.append(Heading(page, top, text, level))
    headings.sort(key=lambda item: (item.page, item.top, item.level))

    index = SectionIndex(page_count=page_count, headings=[heading for heading in headings if heading.text])
    if offsets:
        offset, votes = offsets.most_common(1)[0]
        if votes >= 3 and votes >= 0.5 * sum(offsets.values()):
            index.page_offset = offset

    # The trail of open headings after each heading, in document order.
    trail: list[Heading] = []
    states: list[tuple[tuple[int, float], str]] = []
    for heading in headings:
        while trail and trail[-1].level >= heading.level:
            trail.pop()
        if heading.text:
            trail.append(heading)
        states.append(((heading.page, heading.top), " > ".join(item.text for item in trail[-3:])[:MAX_SECTION_CHARS]))
    keys = [key for key, _ in states]

    def at(page: int, top: float) -> str:
        position = bisect_right(keys, (page, top + 2.0))
        return states[position - 1][1] if position else ""

    for page in range(1, page_count + 1):
        # A page is named by its first heading when it opens with one, else by what continues onto it.
        first = next((heading for heading in headings if heading.page == page and heading.text), None)
        index.by_page[page] = at(page, first.top if first and first.top < 0.25 * pages[page][1] else -1.0)
    if doc is not None:
        for page, segments in doc.pages.items():
            for segment in segments:
                index.by_segment[segment.segment_id] = (at(page, segment.bbox[1]) if segment.bbox
                                                        else index.by_page.get(page, ""))
    return index
