"""Pages the model must see as an image: flowcharts, labelled diagrams and transcribed pages.

The V3 rule finds pages whose text is broken into many short pieces. A flowchart drawn as
vector graphics with two lines of text escapes it, and its branches were never read. Such a
page has many drawing operations, no table and little text; it is shown as an image too, and
it is read when it stands inside or next to pages that hold troubleshooting knowledge.
"""

from __future__ import annotations

from pathlib import Path

from backend.kg_v3.vision import PageImages

MIN_DRAWINGS = 40
MAX_TEXT_SEGMENTS = 15


def drawn_pages(doc, geometry: dict[int, dict]) -> set[int]:
    """Pages that are mostly a drawing: many strokes, no table, few text segments."""

    pages = set()
    for page, segments in doc.pages.items():
        drawings = int((geometry.get(page) or {}).get("drawing_count") or 0)
        if (drawings >= MIN_DRAWINGS and not any(segment.table for segment in segments)
                and len(segments) <= MAX_TEXT_SEGMENTS):
            pages.add(page)
    return pages


class DiagramImages(PageImages):
    """Page images for layout pages (V3 rule) and for drawn pages."""

    def __init__(self, pdf: Path, doc, geometry: dict[int, dict] | None = None, transcribed=()) -> None:
        super().__init__(pdf, doc)
        if geometry is None:
            from backend.adapters.pdf import page_layout_inventory

            geometry = page_layout_inventory(Path(pdf))
        self.drawn = drawn_pages(doc, geometry)
        # A transcribed page is shown too: the image is its source, the segments a reading of it.
        self.pages = set(self.pages) | self.drawn | set(transcribed)


def pages_to_read_with(diagnostic: set[int], drawn: set[int]) -> set[int]:
    """Drawn pages that continue troubleshooting pages: next to one, or between two of them."""

    extra: set[int] = set()
    changed = True
    while changed:
        changed = False
        for page in sorted(drawn - diagnostic - extra):
            if {page - 1, page + 1} & (diagnostic | extra):
                extra.add(page)
                changed = True
    return extra
