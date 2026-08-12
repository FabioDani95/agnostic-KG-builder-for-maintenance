"""PDF compatibility adapter over the characterized extraction service."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import fitz

from backend.app_config import get_pdf_ingestion_config
from backend.domain.evidence import (
    EvidenceContent,
    EvidenceUnit,
    IngestionInfo,
    LanguageInfo,
    LanguageQualification,
    ProvenanceRef,
    QualityFlag,
    RawReference,
    RawUnitDraft,
    RecordRole,
)
from backend.domain.locators import PdfLocator
from backend.domain.sources import Source
from backend.domain.workspace import Workspace
from backend.services.pdf_service import extract_text_by_page

ADAPTER_VERSION = "pdf-v3"
EVIDENCE_ANCHOR_PREFIX = "EVIDENCE_ID"


def _top_left_order(
    indexed_blocks: list[tuple[int, tuple]],
) -> list[tuple[int, tuple]]:
    return sorted(
        indexed_blocks,
        key=lambda item: (
            round(float(item[1][1] or 0), 1),
            round(float(item[1][0] or 0), 1),
            round(float(item[1][3] or 0), 1),
            round(float(item[1][2] or 0), 1),
            item[0],
        ),
    )


def _layout_reading_order(
    blocks: list[tuple],
    *,
    page_width: float,
    page_height: float | None = None,
) -> list[tuple[int, tuple]]:
    """Return deterministic block order, using column-major order when supported.

    PyMuPDF's native block order and a simple y/x sort both interleave two-column
    troubleshooting records.  This conservative detector switches to column-major
    order only when each side has multiple narrow blocks, a real gutter, and
    vertically overlapping content.  Full-width headings and footers split the
    page into bands and retain their physical position.
    """
    all_indexed = [
        (index, block)
        for index, block in enumerate(blocks)
        if len(block) >= 5 and str(block[4] or "").strip()
    ]
    header: list[tuple[int, tuple]] = []
    footer: list[tuple[int, tuple]] = []
    indexed = list(all_indexed)
    if page_height and page_height > 0:
        header = [item for item in indexed if float(item[1][3]) <= page_height * 0.06]
        footer = [item for item in indexed if float(item[1][1]) >= page_height * 0.92]
        marginal_ids = {item[0] for item in header + footer}
        indexed = [item for item in indexed if item[0] not in marginal_ids]
    fallback = _top_left_order(header) + _top_left_order(indexed) + _top_left_order(footer)
    if len(indexed) < 4 or page_width <= 0:
        return fallback

    midpoint = page_width / 2.0
    edge_tolerance = page_width * 0.02
    narrow_limit = page_width * 0.55
    narrow = [
        item
        for item in indexed
        if float(item[1][2]) - float(item[1][0]) <= narrow_limit
    ]
    left_seed = [
        item for item in narrow if float(item[1][2]) <= midpoint + edge_tolerance
    ]
    right_seed = [
        item for item in narrow if float(item[1][0]) >= midpoint - edge_tolerance
    ]
    if len(left_seed) < 2 or len(right_seed) < 2:
        return fallback

    left_edge = max(float(item[1][2]) for item in left_seed)
    right_edge = min(float(item[1][0]) for item in right_seed)
    if right_edge - left_edge < max(8.0, page_width * 0.015):
        return fallback

    left_top = min(float(item[1][1]) for item in left_seed)
    left_bottom = max(float(item[1][3]) for item in left_seed)
    right_top = min(float(item[1][1]) for item in right_seed)
    right_bottom = max(float(item[1][3]) for item in right_seed)
    vertical_overlap = max(0.0, min(left_bottom, right_bottom) - max(left_top, right_top))
    shorter_column = max(1.0, min(left_bottom - left_top, right_bottom - right_top))
    if vertical_overlap / shorter_column < 0.25:
        return fallback

    split = (left_edge + right_edge) / 2.0
    assignment_tolerance = max(2.0, page_width * 0.004)
    left: list[tuple[int, tuple]] = []
    right: list[tuple[int, tuple]] = []
    spanning: list[tuple[int, tuple]] = []
    for item in indexed:
        block = item[1]
        if float(block[2]) <= split + assignment_tolerance:
            left.append(item)
        elif float(block[0]) >= split - assignment_tolerance:
            right.append(item)
        else:
            spanning.append(item)
    if len(left) < 2 or len(right) < 2:
        return fallback

    left = _top_left_order(left)
    right = _top_left_order(right)
    spanning = _top_left_order(spanning)
    ordered: list[tuple[int, tuple]] = []
    for span in spanning:
        span_y = float(span[1][1])
        before_left = [item for item in left if float(item[1][1]) < span_y]
        before_right = [item for item in right if float(item[1][1]) < span_y]
        ordered.extend(before_left)
        ordered.extend(before_right)
        left = [item for item in left if item not in before_left]
        right = [item for item in right if item not in before_right]
        ordered.append(span)
    ordered.extend(left)
    ordered.extend(right)
    return _top_left_order(header) + ordered + _top_left_order(footer)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:28]
    return f"{prefix}_{digest}"


def _canonical_hash(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PdfAdapterResult:
    raw_units: list[RawUnitDraft]
    evidence_units: list[EvidenceUnit]
    page_previews: list[dict]


class PdfAdapter:
    def inspect(
        self,
        *,
        path: Path,
        workspace: Workspace,
        source: Source,
        included_pages: set[int] | None = None,
        scope_version: int | None = None,
    ) -> PdfAdapterResult:
        if source.source_kind.value != "pdf":
            raise ValueError("PdfAdapter accepts only PDF sources")
        pages = extract_text_by_page(str(path))
        allowed = included_pages if included_pages is not None else {page["page_number"] for page in pages}
        minimum_ocr_confidence = float(
            (get_pdf_ingestion_config().get("ocr") or {}).get("min_confidence", 0.80)
        )
        document = fitz.open(path)
        raw_units: list[RawUnitDraft] = []
        evidence_units: list[EvidenceUnit] = []
        previews: list[dict] = []
        document_table_index = 0
        try:
            for page_record in pages:
                page_number = int(page_record["page_number"])
                page = document[page_number - 1]
                page_text = str(page_record.get("text") or "")
                page_quote = next(
                    (line.strip() for line in page_text.splitlines() if line.strip()),
                    f"[Physical page {page_number}: no readable text]",
                )
                method = "ocr" if page_record.get("text_source") == "ocr" else "native_text"
                page_locator = PdfLocator(
                    page=page_number,
                    quote=page_quote[:1000],
                    extraction_method=method,
                )
                page_raw_hash = hashlib.sha256(page_text.encode("utf-8")).hexdigest()
                page_raw_id = _stable_id(
                    "raw",
                    source.source_id,
                    ADAPTER_VERSION,
                    "page",
                    str(page_number),
                    page_raw_hash,
                )
                flags = []
                ocr_confidence = page_record.get("ocr_confidence")
                if page_record.get("ocr_status") in {
                    "failed", "empty", "unavailable", "skipped_budget",
                }:
                    flags.append(QualityFlag.OCR_LOW_CONFIDENCE)
                if not page_text.strip() and QualityFlag.OCR_LOW_CONFIDENCE not in flags:
                    flags.append(QualityFlag.OCR_LOW_CONFIDENCE)
                if ocr_confidence is not None and float(ocr_confidence) < minimum_ocr_confidence:
                    flags.append(QualityFlag.OCR_LOW_CONFIDENCE)
                raw_units.append(
                    RawUnitDraft(
                        raw_unit_id=page_raw_id,
                        parent_raw_unit_id=None,
                        unit_kind="pdf_page",
                        source_id=source.source_id,
                        structure_id=f"page:{page_number}",
                        locator=page_locator,
                        raw_hash=page_raw_hash,
                        adapter_version=ADAPTER_VERSION,
                        quality_flags=flags,
                    )
                )
                previews.append(
                    {
                        "page": page_number,
                        "text": page_text,
                        "extraction_method": method,
                        "quality_flags": [flag.value for flag in flags],
                        "included": page_number in allowed,
                    }
                )
                blocks = list(page.get_text("blocks") or [])
                ordered_blocks = _layout_reading_order(
                    blocks,
                    page_width=float(page.rect.width),
                    page_height=float(page.rect.height),
                )
                for block_index, (source_block_index, block) in enumerate(ordered_blocks):
                    block_text = str(block[4] or "").strip()
                    if not block_text:
                        continue
                    bbox = tuple(round(float(value), 3) for value in block[:4])
                    locator = PdfLocator(
                        page=page_number,
                        quote=block_text,
                        extraction_method=method,
                        block_index=block_index,
                        source_block_index=source_block_index,
                        bbox=bbox,
                    )
                    raw_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
                    raw_unit_id = _stable_id(
                        "raw",
                        source.source_id,
                        ADAPTER_VERSION,
                        "block",
                        str(page_number),
                        str(block_index),
                        raw_hash,
                    )
                    raw_units.append(
                        RawUnitDraft(
                            raw_unit_id=raw_unit_id,
                            parent_raw_unit_id=page_raw_id,
                            unit_kind="block",
                            source_id=source.source_id,
                            structure_id=f"page:{page_number}",
                            locator=locator,
                            raw_hash=raw_hash,
                            adapter_version=ADAPTER_VERSION,
                            quality_flags=flags,
                        )
                    )
                    if page_number not in allowed:
                        continue
                    evidence_units.append(
                        self._evidence(
                            workspace=workspace,
                            source=source,
                            raw_unit_id=raw_unit_id,
                            raw_hash=raw_hash,
                            locator=locator,
                            text=block_text,
                            structure_id=f"page:{page_number}",
                            flags=flags,
                        )
                    )

                # This direct layout inventory deliberately bypasses the legacy
                # prompt-rendering caps in pdf_service. Caps may shape a later
                # payload; they can never truncate RawUnit inventory.
                try:
                    tables = list(getattr(page.find_tables(), "tables", None) or [])
                except Exception:
                    tables = []
                for table in tables:
                    document_table_index += 1
                    table_index = document_table_index
                    try:
                        rows = list(table.extract() or [])
                    except Exception:
                        rows = []
                    normalized_rows = [
                        [str(cell or "").replace("\r", " ").replace("\n", " ").strip() for cell in row]
                        for row in rows
                    ]
                    table_text = "\n".join(" | ".join(row) for row in normalized_rows).strip()
                    table_quote = table_text or f"[Empty table {table_index} on page {page_number}]"
                    table_locator = PdfLocator(
                        page=page_number,
                        quote=table_quote[:4000],
                        extraction_method="table",
                        table_index=table_index,
                    )
                    table_hash = hashlib.sha256(table_text.encode("utf-8")).hexdigest()
                    table_raw_id = _stable_id(
                        "raw",
                        source.source_id,
                        ADAPTER_VERSION,
                        "table",
                        str(page_number),
                        str(table_index),
                        table_hash,
                    )
                    raw_units.append(
                        RawUnitDraft(
                            raw_unit_id=table_raw_id,
                            parent_raw_unit_id=page_raw_id,
                            unit_kind="table",
                            source_id=source.source_id,
                            structure_id=f"page:{page_number}:table:{table_index}",
                            locator=table_locator,
                            raw_hash=table_hash,
                            adapter_version=ADAPTER_VERSION,
                            quality_flags=flags,
                        )
                    )
                    for row_index, row in enumerate(normalized_rows, start=1):
                        row_text = " | ".join(row).strip()
                        row_quote = row_text or (
                            f"[Empty table row {row_index}, table {table_index}, page {page_number}]"
                        )
                        row_locator = PdfLocator(
                            page=page_number,
                            quote=row_quote[:4000],
                            extraction_method="table",
                            table_index=table_index,
                            row_index=row_index,
                        )
                        row_hash = hashlib.sha256(row_text.encode("utf-8")).hexdigest()
                        row_raw_id = _stable_id(
                            "raw",
                            source.source_id,
                            ADAPTER_VERSION,
                            "table_row",
                            str(page_number),
                            str(table_index),
                            str(row_index),
                            row_hash,
                        )
                        raw_units.append(
                            RawUnitDraft(
                                raw_unit_id=row_raw_id,
                                parent_raw_unit_id=page_raw_id,
                                unit_kind="table_row",
                                source_id=source.source_id,
                                structure_id=f"page:{page_number}:table:{table_index}",
                                locator=row_locator,
                                raw_hash=row_hash,
                                adapter_version=ADAPTER_VERSION,
                                quality_flags=flags,
                            )
                        )
                        if page_number in allowed and row_text:
                            evidence_units.append(
                                self._evidence(
                                    workspace=workspace,
                                    source=source,
                                    raw_unit_id=row_raw_id,
                                    raw_hash=row_hash,
                                    locator=row_locator,
                                    text=row_text,
                                    structure_id=(
                                        f"page:{page_number}:table:{table_index}"
                                    ),
                                    flags=flags,
                                )
                            )

                ocr_regions = list(page_record.get("ocr_regions") or [])
                if not ocr_regions and (
                    page_record.get("text_source") == "ocr"
                    or page_record.get("ocr_status")
                    in {"applied", "failed", "empty", "unavailable", "skipped_budget"}
                ):
                    ocr_regions = [
                        {
                            "text": page_text,
                            "confidence": ocr_confidence,
                        }
                    ]
                for region_index, region in enumerate(ocr_regions, start=1):
                    region_text = str(region.get("text") or "")
                    region_quote = (
                        region_text.strip()
                        or f"[Unreadable OCR region {region_index} on page {page_number}]"
                    )
                    region_flags = list(flags)
                    region_confidence = region.get("confidence")
                    if (
                        region_confidence is not None
                        and float(region_confidence) < minimum_ocr_confidence
                        and QualityFlag.OCR_LOW_CONFIDENCE not in region_flags
                    ):
                        region_flags.append(QualityFlag.OCR_LOW_CONFIDENCE)
                    region_locator = PdfLocator(
                        page=page_number,
                        quote=region_quote[:4000],
                        extraction_method="ocr",
                        ocr_region_index=region_index,
                    )
                    region_hash = hashlib.sha256(region_text.encode("utf-8")).hexdigest()
                    region_raw_id = _stable_id(
                        "raw",
                        source.source_id,
                        ADAPTER_VERSION,
                        "ocr_region",
                        str(page_number),
                        str(region_index),
                        region_hash,
                    )
                    raw_units.append(
                        RawUnitDraft(
                            raw_unit_id=region_raw_id,
                            parent_raw_unit_id=page_raw_id,
                            unit_kind="ocr_region",
                            source_id=source.source_id,
                            structure_id=f"page:{page_number}:ocr",
                            locator=region_locator,
                            raw_hash=region_hash,
                            adapter_version=ADAPTER_VERSION,
                            quality_flags=region_flags,
                        )
                    )
                    if page_number in allowed and region_text.strip():
                        evidence_units.append(
                            self._evidence(
                                workspace=workspace,
                                source=source,
                                raw_unit_id=region_raw_id,
                                raw_hash=region_hash,
                                locator=region_locator,
                                text=region_text.strip(),
                                structure_id=f"page:{page_number}:ocr",
                                flags=region_flags,
                            )
                        )
        finally:
            document.close()
        return PdfAdapterResult(
            raw_units=raw_units,
            evidence_units=evidence_units,
            page_previews=previews,
        )

    @staticmethod
    def _evidence(
        *,
        workspace: Workspace,
        source: Source,
        raw_unit_id: str,
        raw_hash: str,
        locator: PdfLocator,
        text: str,
        structure_id: str,
        flags: list[QualityFlag],
    ) -> EvidenceUnit:
        locator_hash = _canonical_hash(locator.model_dump(mode="json"))
        evidence_id = _stable_id(
            "ev",
            source.source_id,
            ADAPTER_VERSION,
            raw_unit_id,
            locator_hash,
        )
        return EvidenceUnit(
            evidence_id=evidence_id,
            workspace_id=workspace.workspace_id,
            asset_id=workspace.asset.asset_id,
            source_id=source.source_id,
            source_kind=source.source_kind,
            authority=source.authority,
            locator=locator,
            provenance_refs=[
                ProvenanceRef(
                    role="primary",
                    raw_unit_id=raw_unit_id,
                    source_id=source.source_id,
                    locator=locator,
                    raw_hash=raw_hash,
                    structure_id=structure_id,
                )
            ],
            language=LanguageInfo(
                detected="unknown",
                qualification=LanguageQualification.UNKNOWN,
            ),
            record_role=RecordRole.GENERIC_EVIDENCE,
            content=EvidenceContent(
                observation=text,
                semantic_texts={"observation": text},
            ),
            quality_flags=flags,
            raw_ref=RawReference(
                source_id=source.source_id,
                raw_unit_id=raw_unit_id,
                locator_hash=locator_hash,
            ),
            ingestion=IngestionInfo(
                adapter_version=ADAPTER_VERSION,
                # Scope association is stored separately so the immutable
                # EvidenceUnit remains stable across identical revisions.
                scope_version=None,
            ),
        )


def _semantic_text_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    return re.sub(r"\s+", " ", normalized).strip()


def pdf_evidence_sort_key(evidence: EvidenceUnit) -> tuple[int, int, int, int, str]:
    """Return physical reading order without depending on hash-based evidence IDs."""
    locator = evidence.locator
    if not isinstance(locator, PdfLocator):
        return (0, 9, 0, 0, evidence.evidence_id)
    if locator.block_index is not None:
        kind_rank, primary, secondary = 0, locator.block_index, 0
    elif locator.table_index is not None:
        kind_rank, primary, secondary = 1, locator.table_index, locator.row_index or 0
    elif locator.ocr_region_index is not None:
        kind_rank, primary, secondary = 2, locator.ocr_region_index, 0
    else:
        kind_rank, primary, secondary = 3, 0, 0
    return (locator.page, kind_rank, primary, secondary, evidence.evidence_id)


def evidence_anchor(evidence: EvidenceUnit) -> str:
    """Stable anchor exposed to the semantic core and returned in provenance."""
    return evidence.evidence_id


def _render_evidence(evidence: EvidenceUnit) -> str:
    return (
        f"[[{EVIDENCE_ANCHOR_PREFIX}: {evidence_anchor(evidence)}]]\n"
        f"{evidence.locator.quote.strip()}"
    )


def _semantic_page_units(items: list[EvidenceUnit]) -> tuple[list[EvidenceUnit], str]:
    """Choose one coherent reading plus non-duplicated structured table rows."""
    ordered = sorted(items, key=pdf_evidence_sort_key)
    blocks = [item for item in ordered if item.locator.block_index is not None]
    ocr_regions = [item for item in ordered if item.locator.ocr_region_index is not None]
    table_rows = [
        item for item in ordered
        if item.locator.table_index is not None and item.locator.row_index is not None
    ]

    block_text = _semantic_text_key(" ".join(item.locator.quote for item in blocks))
    ocr_text = _semantic_text_key(" ".join(item.locator.quote for item in ocr_regions))
    if ocr_regions and len(ocr_text) > len(block_text):
        selected = list(ocr_regions)
        text_source = "ocr"
    else:
        selected = list(blocks or ocr_regions)
        text_source = "native" if blocks else "ocr"

    covered = _semantic_text_key(" ".join(item.locator.quote for item in selected))
    for row in table_rows:
        row_text = _semantic_text_key(row.locator.quote)
        if not row_text or row_text in covered:
            continue
        selected.append(row)
        covered = f"{covered} {row_text}".strip()

    # Defensive fallback for legacy/custom evidence that has no positional subtype.
    if not selected:
        selected = ordered
        text_source = "ocr" if any(
            item.locator.extraction_method == "ocr" for item in ordered
        ) else "native"

    unique: list[EvidenceUnit] = []
    seen_quotes: set[str] = set()
    for item in selected:
        quote_key = _semantic_text_key(item.locator.quote)
        if quote_key and quote_key not in seen_quotes:
            seen_quotes.add(quote_key)
            unique.append(item)
    return unique, text_source


def evidence_units_to_legacy_pages(evidence_units: list[EvidenceUnit]) -> list[dict]:
    """Project canonical PDF evidence into ordered, anchored semantic pages.

    The evidence repository deliberately uses opaque hash IDs.  Those IDs are
    stable identities, not reading-order keys, so this bridge reconstructs the
    physical locator order before text reaches scoping or ontology extraction.
    """
    by_page: dict[int, list[EvidenceUnit]] = {}
    for evidence in evidence_units:
        if not isinstance(evidence.locator, PdfLocator):
            raise ValueError("The PDF compatibility projection accepts only PDF evidence")
        if evidence.eligible_for_semantic_processing:
            by_page.setdefault(evidence.locator.page, []).append(evidence)

    pages: list[dict] = []
    for page_number in sorted(by_page):
        units, text_source = _semantic_page_units(by_page[page_number])
        pages.append({
            "page_number": page_number,
            "text": "\n\n".join(_render_evidence(item) for item in units),
            "text_source": text_source,
            "evidence_anchors": [evidence_anchor(item) for item in units],
        })
    return pages
