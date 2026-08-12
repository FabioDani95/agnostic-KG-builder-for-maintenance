import logging
import re
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Hard caps so table rendering can never blow up the prompt budget.
_MAX_TABLE_CHARS_PER_PAGE = 6000
_MAX_TABLES_PER_PAGE = 4
_MAX_TABLE_ROWS = 60


class PdfReadError(RuntimeError):
    """Raised when a PDF cannot be opened or text cannot be extracted."""


class PdfEncryptedError(PdfReadError):
    """Raised when a PDF is encrypted or otherwise password-protected."""


def _ocr_page_text(page, *, language: str, dpi: int) -> str:
    """Run PyMuPDF's Tesseract-backed OCR for one page.

    PyMuPDF keeps OCR optional at runtime. If the Tesseract binary or language
    data are unavailable, the caller records that state and preserves the
    native page instead of failing the whole manual.
    """
    text_page = page.get_textpage_ocr(language=language, dpi=dpi, full=True)
    return str(page.get_text("text", textpage=text_page) or "")


def _ocr_quality_score(text: str) -> float:
    """Return a conservative, format-agnostic OCR quality proxy.

    PyMuPDF's page-level OCR API does not expose Tesseract word confidences.
    Treating every successful call as trustworthy was therefore a fail-open
    signal.  This proxy does not pretend to be an engine confidence: it only
    detects obviously sparse or corrupted output and routes it to review.
    """
    value = str(text or "").strip()
    if not value:
        return 0.0
    printable = sum(character.isprintable() for character in value) / len(value)
    alphanumeric = sum(character.isalnum() for character in value) / len(value)
    tokens = re.findall(r"[^\W_]{2,}", value, flags=re.UNICODE)
    replacement_ratio = value.count("\ufffd") / len(value)
    control_ratio = sum(
        not character.isprintable() and character not in "\n\r\t"
        for character in value
    ) / len(value)
    length_signal = min(1.0, len(value) / 160.0)
    token_signal = min(1.0, len(tokens) / 18.0)
    score = (
        0.30 * printable
        + 0.25 * alphanumeric
        + 0.20 * length_signal
        + 0.25 * token_signal
        - 0.60 * replacement_ratio
        - 0.60 * control_ratio
    )
    return round(max(0.0, min(1.0, score)), 4)


def _ocr_settings(config: dict[str, Any] | None = None) -> dict[str, Any]:
    if config is not None:
        return dict(config)
    from backend.app_config import get_pdf_ingestion_config

    return dict((get_pdf_ingestion_config().get("ocr") or {}))


def apply_selective_ocr(
    pdf_path: str,
    pages: list[dict],
    page_numbers: list[int] | set[int],
    *,
    config: dict[str, Any] | None = None,
    max_pages: int | None = None,
) -> dict[str, Any]:
    """OCR only low-text candidate pages and update them in place."""
    cfg = _ocr_settings(config)
    report: dict[str, Any] = {
        "enabled": bool(cfg.get("enabled", True)),
        "candidate_pages": [],
        "attempted": 0,
        "succeeded": 0,
        "kept_native": 0,
        "empty": 0,
        "failed": 0,
        "low_quality": 0,
        "unavailable": False,
        "unavailable_pages": [],
        "skipped_budget": 0,
        "skipped_pages": [],
    }
    if not report["enabled"] or not pdf_path:
        return report

    minimum_chars = max(0, int(cfg.get("min_native_chars", 80) or 0))
    allowed = {int(number) for number in page_numbers if int(number) > 0}
    candidates = [
        page for page in pages
        if int(page.get("page_number", 0) or 0) in allowed
        and int(page.get("native_text_chars", len(str(page.get("text", "") or ""))) or 0) < minimum_chars
    ]
    candidates.sort(key=lambda page: int(page.get("page_number", 0) or 0))
    limit = len(candidates) if max_pages is None else max(0, int(max_pages))
    skipped = candidates[limit:]
    report["skipped_budget"] = len(skipped)
    report["skipped_pages"] = [int(page["page_number"]) for page in skipped]
    for record in skipped:
        record["ocr_status"] = "skipped_budget"
    candidates = candidates[:limit]
    report["candidate_pages"] = [int(page["page_number"]) for page in candidates]
    if not candidates:
        return report

    language = str(cfg.get("language") or "eng")
    dpi = max(72, int(cfg.get("dpi", 200) or 200))
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        report["failed"] = len(candidates)
        report["error"] = f"Could not open PDF for OCR: {exc}"
        return report

    try:
        for candidate_index, record in enumerate(candidates):
            page_number = int(record["page_number"])
            report["attempted"] += 1
            try:
                ocr_text = _ocr_page_text(doc[page_number - 1], language=language, dpi=dpi)
            except Exception as exc:
                message = str(exc)
                lowered = message.lower()
                if "tesseract" in lowered or "tessdata" in lowered or "ocr initialisation" in lowered:
                    report["unavailable"] = True
                    report["error"] = message
                    unavailable = candidates[candidate_index:]
                    report["unavailable_pages"] = [
                        int(item["page_number"]) for item in unavailable
                    ]
                    for item in unavailable:
                        item["ocr_status"] = "unavailable"
                        item["ocr_error"] = message
                    break
                report["failed"] += 1
                record["ocr_status"] = "failed"
                record["ocr_error"] = message
                continue

            cleaned = ocr_text.strip()
            native = str(record.get("text", "") or "").strip()
            record["ocr_text_chars"] = len(cleaned)
            quality_score = _ocr_quality_score(cleaned)
            record["ocr_quality_score"] = quality_score
            # Backwards-compatible field consumed by PdfAdapter.  The source
            # marker makes clear this is a deterministic quality proxy rather
            # than a probability reported by Tesseract.
            record["ocr_confidence"] = quality_score
            record["ocr_confidence_source"] = "quality_proxy"
            if cleaned and quality_score < float(cfg.get("min_confidence", 0.80) or 0.80):
                report["low_quality"] += 1
            if not cleaned:
                report["empty"] += 1
                record["ocr_status"] = "empty"
            elif len(cleaned) > len(native):
                record["text"] = ocr_text
                record["text_source"] = "ocr"
                record["ocr_status"] = "applied"
                report["succeeded"] += 1
            else:
                record["ocr_status"] = "native_better"
                report["kept_native"] += 1
    finally:
        doc.close()
    return report


def summarize_page_ingestion(pages: list[dict]) -> dict[str, Any]:
    by_source: dict[str, int] = {}
    by_ocr_status: dict[str, int] = {}
    for page in pages:
        source = str(page.get("text_source") or "native")
        status = str(page.get("ocr_status") or "not_attempted")
        by_source[source] = by_source.get(source, 0) + 1
        by_ocr_status[status] = by_ocr_status.get(status, 0) + 1
    return {
        "physical_pages": len(pages),
        "pages_by_text_source": by_source,
        "pages_by_ocr_status": by_ocr_status,
        "unreadable_pages": [
            int(page.get("page_number", 0) or 0)
            for page in pages
            if not str(page.get("text", "") or "").strip()
        ],
    }


def _clean_table_cell(value: object) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").replace("|", "/")
    return " ".join(text.split()).strip()


def _render_table_markdown(rows: list[list[str]]) -> str:
    header, *body = rows
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in [header, *body]]
    lines = ["| " + " | ".join(padded[0]) + " |", "|" + "---|" * width]
    lines.extend("| " + " | ".join(row) + " |" for row in padded[1:])
    return "\n".join(lines)


def _page_tables_markdown(page) -> str:
    """Render detected layout tables as Markdown so row structure survives.

    Plain text extraction flattens troubleshooting tables (symptom | cause |
    remedy) into unordered fragments; the structured rendering is appended to
    the page text so downstream extraction sees both.
    """
    try:
        finder = page.find_tables()
        tables = list(getattr(finder, "tables", None) or [])
    except Exception:
        return ""

    blocks: list[str] = []
    total_chars = 0
    for table in tables[:_MAX_TABLES_PER_PAGE]:
        try:
            raw_rows = table.extract()
        except Exception:
            continue
        rows = [
            [_clean_table_cell(cell) for cell in row]
            for row in (raw_rows or [])[:_MAX_TABLE_ROWS]
        ]
        rows = [row for row in rows if any(row)]
        if len(rows) < 2 or max(len(row) for row in rows) < 2:
            continue
        markdown = _render_table_markdown(rows)
        if total_chars + len(markdown) > _MAX_TABLE_CHARS_PER_PAGE:
            break
        total_chars += len(markdown)
        blocks.append(markdown)

    if not blocks:
        return ""
    return "\n\n[STRUCTURED TABLES DETECTED ON THIS PAGE]\n" + "\n\n".join(blocks)


def extract_text_by_page(
    pdf_path: str,
    *,
    ocr_config: dict[str, Any] | None = None,
) -> list[dict]:
    """Extract text from each page of a PDF file."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        cause_msg = str(getattr(exc, "__cause__", "")).lower()
        msg = f"{str(exc).lower()} {cause_msg}"
        if "encrypt" in msg or "password" in msg:
            raise PdfEncryptedError(
                "The selected PDF is encrypted or password-protected and cannot be processed."
            ) from exc
        raise PdfReadError(
            f"Could not open the selected PDF for text extraction: {exc}"
        ) from exc

    pages = []
    pages_with_tables = 0
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            tables_markdown = _page_tables_markdown(page)
            if tables_markdown:
                pages_with_tables += 1
                text = text.rstrip() + "\n" + tables_markdown + "\n"
            pages.append({
                "page_number": page_num + 1,
                "text": text,
                "native_text_chars": len(text.strip()),
                "text_source": "native" if text.strip() else "empty",
                "ocr_status": "not_attempted",
            })
    except Exception as exc:
        raise PdfReadError(
            f"Could not extract text from the selected PDF: {exc}"
        ) from exc
    finally:
        doc.close()

    if pages_with_tables:
        logger.info(
            "[pdf] Structured tables appended on %d/%d page(s)",
            pages_with_tables,
            len(pages),
        )
    cfg = _ocr_settings(ocr_config)
    # OCR must run before PdfAdapter freezes RawUnits/EvidenceUnits.  A later
    # scoping-time mutation cannot update that canonical inventory.  Inspect
    # every physical page here, within an explicit bounded budget; skipped
    # low-text pages retain a disposition that downstream review can surface.
    inventory_max_pages = max(
        0,
        int(
            cfg.get(
                "inventory_max_pages",
                cfg.get("selected_max_pages", cfg.get("bootstrap_max_pages", 24)),
            )
            or 0
        ),
    )
    apply_selective_ocr(
        pdf_path,
        pages,
        set(range(1, len(pages) + 1)),
        config=cfg,
        max_pages=inventory_max_pages,
    )
    return pages


def format_text_with_pages(pages: list[dict]) -> str:
    """Format extracted pages into a single string with page markers."""
    parts = []
    for page in pages:
        parts.append(f"--- PAGE {page['page_number']} ---")
        parts.append(page["text"])
    return "\n\n".join(parts)
