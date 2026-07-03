from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from backend.graph.store import seed_graph_state
from backend.routers.upload import pdf_store
from backend.services.run_metrics import ensure_run_metrics

_HEADING_RE = re.compile(r"^##\s+(?:(?:Page\s+)?(\d+)\b|(.+))", re.IGNORECASE)
_METADATA_RE = re.compile(r"^(Document type|Language|Asset):\s*(.+)$", re.IGNORECASE)


def build_store_from_markdown(path: str | Path, *, register: bool = False) -> dict[str, Any]:
    """Build a runtime-like store from a markdown manual fixture.

    Markdown golden fixtures are intentionally tiny and page-like. A level-2
    heading that starts with a number, e.g. ``## 2. Troubleshooting`` or
    ``## Page 2 - Fault Table``, starts that page. Content before the first
    level-2 heading is assigned to page 1.
    """
    manual_path = Path(path)
    text = manual_path.read_text(encoding="utf-8")
    metadata = _extract_metadata(text)
    pages = _split_markdown_pages(text)
    pdf_id = f"md_{uuid.uuid4().hex}"
    store: dict[str, Any] = {
        "pdf_id": pdf_id,
        "filename": manual_path.name,
        "pdf_path": str(manual_path),
        "pages": pages,
        "page_count": len(pages),
        "source_type": metadata.get("document_type", ""),
        "source_title": metadata.get("asset", manual_path.stem),
        "source_language": metadata.get("language", ""),
        "source_format": "markdown",
        "selected_models": {
            "scoping": None,
            "ontology_draft": None,
            "extraction": None,
        },
    }
    ensure_run_metrics(store)
    seed_graph_state(store, pdf_id)
    if register:
        pdf_store[pdf_id] = store
    return store


def _extract_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        match = _METADATA_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1).strip().lower().replace(" ", "_")
        metadata[key] = match.group(2).strip()
    return metadata


def _split_markdown_pages(text: str) -> list[dict[str, Any]]:
    pages_by_number: dict[int, list[str]] = {}
    current_page = 1
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading = _HEADING_RE.match(line)
        if heading:
            current_page = int(heading.group(1) or current_page)
        pages_by_number.setdefault(current_page, []).append(line)

    pages = [
        {
            "page_number": page_number,
            "text": "\n".join(lines).strip(),
        }
        for page_number, lines in sorted(pages_by_number.items())
        if "\n".join(lines).strip()
    ]
    if not pages:
        pages = [{"page_number": 1, "text": text.strip()}]
    return pages
