from __future__ import annotations

import fitz

from backend.services import pdf_service


def _write_pdf(path) -> None:
    doc = fitz.open()
    first = doc.new_page()
    first.insert_text((72, 72), "Cover and manual title")
    doc.new_page()  # Deliberately image/blank-like: no native text.
    third = doc.new_page()
    third.insert_text((72, 72), "Troubleshooting: motor does not start")
    doc.save(path)
    doc.close()


def test_pdf_loader_preserves_every_physical_page(tmp_path):
    path = tmp_path / "manual.pdf"
    _write_pdf(path)

    pages = pdf_service.extract_text_by_page(
        str(path),
        ocr_config={"enabled": False},
    )

    assert [page["page_number"] for page in pages] == [1, 2, 3]
    assert pages[1]["text"] == ""
    assert pages[1]["text_source"] == "empty"
    assert pdf_service.summarize_page_ingestion(pages)["unreadable_pages"] == [2]


def test_selective_ocr_only_updates_low_text_candidate_pages(tmp_path, monkeypatch):
    path = tmp_path / "manual.pdf"
    _write_pdf(path)
    pages = pdf_service.extract_text_by_page(
        str(path),
        ocr_config={"enabled": False},
    )
    calls: list[int] = []

    def fake_ocr(page, *, language, dpi):
        calls.append(page.number + 1)
        return "ATC troubleshooting flowchart: check the carousel sensor."

    monkeypatch.setattr(pdf_service, "_ocr_page_text", fake_ocr)
    report = pdf_service.apply_selective_ocr(
        str(path),
        pages,
        {2, 3},
        config={
            "enabled": True,
            "language": "eng",
            "dpi": 200,
            "min_native_chars": 20,
        },
        max_pages=5,
    )

    assert calls == [2]
    assert report["candidate_pages"] == [2]
    assert report["attempted"] == 1
    assert report["succeeded"] == 1
    assert pages[1]["text_source"] == "ocr"
    assert "carousel sensor" in pages[1]["text"]


def test_missing_ocr_runtime_is_reported_without_losing_native_pages(tmp_path, monkeypatch):
    path = tmp_path / "manual.pdf"
    _write_pdf(path)
    pages = pdf_service.extract_text_by_page(
        str(path),
        ocr_config={"enabled": False},
    )

    def unavailable(*args, **kwargs):
        raise RuntimeError("Tesseract language data not found")

    monkeypatch.setattr(pdf_service, "_ocr_page_text", unavailable)
    report = pdf_service.apply_selective_ocr(
        str(path),
        pages,
        {2},
        config={"enabled": True, "min_native_chars": 20},
        max_pages=1,
    )

    assert report["unavailable"] is True
    assert report["attempted"] == 1
    assert pages[1]["text"] == ""
    assert pages[1]["ocr_status"] == "unavailable"
