import logging

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


def extract_text_by_page(pdf_path: str) -> list[dict]:
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
            if not text.strip():
                continue
            tables_markdown = _page_tables_markdown(page)
            if tables_markdown:
                pages_with_tables += 1
                text = text.rstrip() + "\n" + tables_markdown + "\n"
            pages.append({"page_number": page_num + 1, "text": text})
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
    return pages


def format_text_with_pages(pages: list[dict]) -> str:
    """Format extracted pages into a single string with page markers."""
    parts = []
    for page in pages:
        parts.append(f"--- PAGE {page['page_number']} ---")
        parts.append(page["text"])
    return "\n\n".join(parts)
