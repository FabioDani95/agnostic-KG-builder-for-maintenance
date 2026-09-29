"""Evidence for the interface: the text of a segment and the image of a page.

The text comes from the same reader the pipeline uses; a manual is read once per
process. Page images are rendered with PyMuPDF and cached on disk.
"""

from __future__ import annotations

import threading
from pathlib import Path

from backend.kg_v3.reader import DocumentText, render_segment

MAX_SCALE = 3.0


class Evidence:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self._docs: dict[Path, DocumentText] = {}
        self._lock = threading.Lock()

    def document(self, manual_dir: Path) -> DocumentText:
        pdf = manual_dir / "manual.pdf"
        with self._lock:
            if pdf not in self._docs:
                from backend.kg_v3.mapper import attach_pdf_sections
                from backend.kg_v3.reader import read_document
                from scripts.kg_v3 import info_asset, load_evidence

                evidence, page_count, _ = load_evidence(pdf, info_asset(manual_dir / "info.yaml"))
                doc = read_document(list(evidence), page_count=page_count)
                attach_pdf_sections(doc, pdf)
                self._docs[pdf] = doc
            return self._docs[pdf]

    def segment(self, manual_dir: Path, segment_id: str) -> dict:
        found = self.document(manual_dir).segments([segment_id])
        if not found:
            raise KeyError(segment_id)
        segment = found[0]
        return {"segment_id": segment.segment_id, "page": segment.page,
                "bbox": list(segment.bbox) if segment.bbox else None,
                "text": render_segment(segment).split("] ", 1)[-1]}

    def page_png(self, manual_id: str, manual_dir: Path, page: int, scale: float) -> Path:
        import fitz

        scale = max(0.5, min(MAX_SCALE, round(scale * 2) / 2))
        target = self.cache_dir / "pages" / manual_id / f"{page}@{scale:g}.png"
        if target.exists():
            return target
        with fitz.open(manual_dir / "manual.pdf") as document:
            if not 1 <= page <= document.page_count:
                raise KeyError(page)
            pixmap = document[page - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            target.parent.mkdir(parents=True, exist_ok=True)
            pixmap.save(str(target))
        return target
