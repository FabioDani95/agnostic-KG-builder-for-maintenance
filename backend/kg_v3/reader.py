"""Station 1, read: canonical PDF evidence becomes short, citable segments.

No model is involved. Tables stay where they are on the page, every cell is
shown with its column name and merged cells are repeated on the rows they
span, so the extractor sees each table row as a complete entry.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from backend.adapters.pdf import _semantic_page_units
from backend.domain.evidence import EvidenceUnit, QualityFlag
from backend.domain.locators import PdfLocator
from backend.kg_v3.contracts import Segment, SegmentKind, TableCoordinates

MAX_SEGMENT_CHARS = 700
MAX_HEADER_CHARS = 40
_SENTENCE_END = re.compile(r"(?<=[.!?;:])\s+")
_GENERIC_HEADER = re.compile(r"^col\d+$", re.IGNORECASE)
CELL_SEPARATOR = " | "


@dataclass
class DocumentText:
    """All segments of a document in reading order, page by page."""

    page_count: int
    pages: dict[int, list[Segment]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._by_id: dict[str, Segment] = {}
        self._position: dict[str, int] = {}
        for page in sorted(self.pages):
            for segment in self.pages[page]:
                self._position[segment.segment_id] = len(self._by_id)
                self._by_id[segment.segment_id] = segment

    def segment(self, segment_id: str) -> Segment | None:
        return self._by_id.get(segment_id)

    def position(self, segment_id: str) -> int | None:
        """Global reading-order index, used to tell neighbouring segments apart."""
        return self._position.get(segment_id)

    def segments(self, segment_ids: list[str] | None = None) -> list[Segment]:
        if segment_ids is None:
            return list(self._by_id.values())
        return [self._by_id[item] for item in segment_ids if item in self._by_id]

    @property
    def unreadable_pages(self) -> list[int]:
        return [page for page in range(1, self.page_count + 1) if not self.pages.get(page)]


def _cells(evidence: EvidenceUnit) -> tuple[list[str], list[object], list[str]]:
    layout = dict(evidence.attributes.get("table_layout") or {})
    cells = [str(cell or "").strip() for cell in layout.get("cells") or []]
    boxes = list(layout.get("cell_bboxes") or [None] * len(cells))
    headers = [str(item or "").strip() for item in layout.get("column_headers") or []]
    # Header names are short labels; long "headers" are a first data row.
    if (not headers or all(_GENERIC_HEADER.match(item) or not item for item in headers)
            or any(len(item) > MAX_HEADER_CHARS for item in headers)):
        headers = []
    return cells, boxes, headers


def _row_top(evidence: EvidenceUnit) -> float:
    layout = dict(evidence.attributes.get("table_layout") or {})
    box = layout.get("row_bbox") or layout.get("table_bbox")
    if box:
        return float(box[1])
    tops = [float(item[1]) for item in layout.get("cell_bboxes") or [] if item]
    return min(tops) if tops else 0.0


def _split_block(text: str) -> list[str]:
    compact = " ".join(text.split())
    if len(compact) <= MAX_SEGMENT_CHARS:
        return [compact]
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(compact):
        if current and len(current) + len(sentence) + 1 > MAX_SEGMENT_CHARS:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def _low_quality(evidence: EvidenceUnit) -> bool:
    return QualityFlag.OCR_LOW_CONFIDENCE in evidence.quality_flags


def _table_segments(page: int, ordinal: int, rows: list[EvidenceUnit]) -> list[Segment]:
    segments: list[Segment] = []
    previous: list[str] = []
    headers: list[str] = []
    for evidence in sorted(rows, key=lambda item: item.locator.row_index or 0):
        cells, boxes, row_headers = _cells(evidence)
        headers = headers or row_headers
        inherited: list[int] = []
        filled = list(cells)
        for column, value in enumerate(cells):
            merged = column < len(boxes) and boxes[column] is None
            if not value and merged and column < len(previous) and previous[column]:
                filled[column] = previous[column]
                inherited.append(column)
        previous = filled
        text = CELL_SEPARATOR.join(filled).strip(" |")
        if not text:
            continue
        segments.append(Segment(
            segment_id=f"p{page}.t{ordinal}.r{evidence.locator.row_index}",
            page=page,
            kind=SegmentKind.TABLE_ROW,
            text=text,
            evidence_id=evidence.evidence_id,
            table=TableCoordinates(table=ordinal, row=evidence.locator.row_index or 1,
                                   headers=headers, inherited_columns=inherited),
            low_quality=_low_quality(evidence),
        ))
    return segments


def _page_segments(page: int, units: list[EvidenceUnit]) -> list[Segment]:
    chosen, _ = _semantic_page_units(units)
    blocks = [item for item in chosen if item.locator.block_index is not None]
    ocr = [item for item in chosen if item.locator.ocr_region_index is not None]
    tables: dict[int, list[EvidenceUnit]] = defaultdict(list)
    for item in chosen:
        if item.locator.table_index is not None and item.locator.row_index is not None:
            tables[item.locator.table_index].append(item)
    # Keep the adapter's reading order for text and put each table before the
    # first block that starts below the table's top edge.
    placed: list[tuple[str, object]] = [("block", item) for item in blocks]
    for table_index in sorted(tables, key=lambda key: min(_row_top(row) for row in tables[key])):
        top = min(_row_top(row) for row in tables[table_index])
        position = next(
            (index for index, (kind, item) in enumerate(placed)
             if kind == "block" and item.locator.bbox and item.locator.bbox[1] >= top - 1),
            len(placed),
        )
        placed.insert(position, ("table", table_index))
    placed.extend(("ocr", item) for item in ocr)

    segments: list[Segment] = []
    block_number = table_number = ocr_number = 0
    for kind, item in placed:
        if kind == "table":
            table_number += 1
            segments.extend(_table_segments(page, table_number, tables[item]))
        elif kind == "block":
            block_number += 1
            pieces = _split_block(item.locator.quote)
            for piece_number, piece in enumerate(pieces, start=1):
                if not piece:
                    continue
                suffix = f".{piece_number}" if len(pieces) > 1 else ""
                segments.append(Segment(
                    segment_id=f"p{page}.b{block_number}{suffix}", page=page, kind=SegmentKind.TEXT,
                    text=piece, evidence_id=item.evidence_id, bbox=item.locator.bbox, low_quality=_low_quality(item),
                ))
        else:
            ocr_number += 1
            text = " ".join(item.locator.quote.split())
            if text:
                segments.append(Segment(
                    segment_id=f"p{page}.o{ocr_number}", page=page, kind=SegmentKind.OCR_TEXT,
                    text=text, evidence_id=item.evidence_id, low_quality=True,
                ))
    return segments


def read_document(evidence_units: list[EvidenceUnit], *, page_count: int | None = None) -> DocumentText:
    by_page: dict[int, list[EvidenceUnit]] = defaultdict(list)
    for evidence in evidence_units:
        if isinstance(evidence.locator, PdfLocator) and evidence.eligible_for_semantic_processing:
            by_page[evidence.locator.page].append(evidence)
    pages = {page: _page_segments(page, units) for page, units in sorted(by_page.items())}
    total = max([page_count or 0, *pages]) if pages else (page_count or 0)
    return DocumentText(page_count=total, pages={page: items for page, items in pages.items() if items})


def render_segment(segment: Segment, *, marker: str = "") -> str:
    """One line per segment, with column names and inherited cells made explicit."""

    prefix = f"[{segment.segment_id}]{marker} "
    if segment.table is None:
        return prefix + segment.text
    cells = segment.text.split(CELL_SEPARATOR)
    headers = segment.table.headers
    if headers and [cell.casefold() for cell in cells] == [item.casefold() for item in headers[:len(cells)]]:
        return prefix + "TABLE COLUMNS: " + CELL_SEPARATOR.join(cells)
    parts = []
    for column, value in enumerate(cells):
        name = headers[column] if column < len(headers) and headers[column] else f"column {column + 1}"
        same = " (same as row above)" if column in segment.table.inherited_columns else ""
        parts.append(f"{name}{same}: {value}")
    return prefix + CELL_SEPARATOR.join(parts)


def render_segments(segments: list[Segment], *, context: set[str] | None = None) -> str:
    """Page-separated text; context segments are marked read-only."""

    context = context or set()
    lines: list[str] = []
    current_page = None
    for segment in segments:
        if segment.page != current_page:
            current_page = segment.page
            lines.append(f"=== page {segment.page} ===")
        lines.append(render_segment(segment, marker=" (context)" if segment.segment_id in context else ""))
    return "\n".join(lines)
