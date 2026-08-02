"""PDF compatibility adapter over the characterized extraction service."""

from __future__ import annotations

import hashlib
import json
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

ADAPTER_VERSION = "pdf-v2"


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
                page_raw_id = _stable_id("raw", source.source_id, "page", str(page_number), page_raw_hash)
                flags = []
                ocr_confidence = page_record.get("ocr_confidence")
                if page_record.get("ocr_status") in {"failed", "empty", "unavailable"}:
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
                for block_index, block in enumerate(blocks):
                    block_text = str(block[4] or "").strip()
                    if not block_text:
                        continue
                    locator = PdfLocator(
                        page=page_number,
                        quote=block_text[:2000],
                        extraction_method=method,
                        block_index=block_index,
                    )
                    raw_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
                    raw_unit_id = _stable_id(
                        "raw",
                        source.source_id,
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
                    in {"applied", "failed", "empty", "unavailable"}
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
        evidence_id = _stable_id("ev", source.source_id, raw_unit_id, locator_hash)
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


def evidence_units_to_legacy_pages(evidence_units: list[EvidenceUnit]) -> list[dict]:
    """Temporary PDF-only projection for the characterized semantic core."""
    by_page: dict[int, list[str]] = {}
    methods: dict[int, str] = {}
    for evidence in evidence_units:
        if not isinstance(evidence.locator, PdfLocator):
            raise ValueError("The PDF compatibility projection accepts only PDF evidence")
        if not evidence.eligible_for_semantic_processing:
            continue
        by_page.setdefault(evidence.locator.page, []).append(evidence.locator.quote)
        methods[evidence.locator.page] = evidence.locator.extraction_method
    return [
        {
            "page_number": page,
            "text": "\n\n".join(dict.fromkeys(by_page[page])),
            "text_source": "ocr" if methods[page] == "ocr" else "native",
        }
        for page in sorted(by_page)
    ]
