import fitz  # PyMuPDF


class PdfReadError(RuntimeError):
    """Raised when a PDF cannot be opened or text cannot be extracted."""


class PdfEncryptedError(PdfReadError):
    """Raised when a PDF is encrypted or otherwise password-protected."""


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
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages.append({"page_number": page_num + 1, "text": text})
    except Exception as exc:
        raise PdfReadError(
            f"Could not extract text from the selected PDF: {exc}"
        ) from exc
    finally:
        doc.close()

    return pages


def format_text_with_pages(pages: list[dict]) -> str:
    """Format extracted pages into a single string with page markers."""
    parts = []
    for page in pages:
        parts.append(f"--- PAGE {page['page_number']} ---")
        parts.append(page["text"])
    return "\n\n".join(parts)
