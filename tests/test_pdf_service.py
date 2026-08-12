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


def test_missing_ocr_runtime_disposes_all_remaining_low_text_pages(tmp_path, monkeypatch):
    path = tmp_path / "image-pages.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    doc.new_page()
    doc.save(path)
    doc.close()
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
        {1, 2, 3},
        config={"enabled": True, "min_native_chars": 20},
        max_pages=3,
    )

    assert report["attempted"] == 1
    assert report["unavailable_pages"] == [1, 2, 3]
    assert [page["ocr_status"] for page in pages] == [
        "unavailable",
        "unavailable",
        "unavailable",
    ]


def test_inventory_ocr_scans_low_text_pages_beyond_front_matter(tmp_path, monkeypatch):
    path = tmp_path / "long-manual.pdf"
    doc = fitz.open()
    for page_number in range(1, 21):
        page = doc.new_page()
        if page_number != 20:
            page.insert_text((72, 72), f"Technical manual content page {page_number} " * 5)
    doc.save(path)
    doc.close()
    calls: list[int] = []

    def fake_ocr(page, *, language, dpi):
        calls.append(page.number + 1)
        return "Fault condition: axis will not move. Remedy: reconnect the axis cable."

    monkeypatch.setattr(pdf_service, "_ocr_page_text", fake_ocr)
    pages = pdf_service.extract_text_by_page(
        str(path),
        ocr_config={
            "enabled": True,
            "min_native_chars": 80,
            "inventory_max_pages": 4,
            "min_confidence": 0.50,
        },
    )

    assert calls == [20]
    assert pages[19]["ocr_status"] == "applied"
    assert pages[19]["text_source"] == "ocr"
    assert pages[19]["ocr_confidence_source"] == "quality_proxy"


def test_ocr_budget_skip_is_an_explicit_page_disposition(tmp_path, monkeypatch):
    path = tmp_path / "image-pages.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    doc.save(path)
    doc.close()
    pages = pdf_service.extract_text_by_page(
        str(path),
        ocr_config={"enabled": False},
    )
    monkeypatch.setattr(
        pdf_service,
        "_ocr_page_text",
        lambda page, **kwargs: "Readable OCR diagnostic record with cause and remedy.",
    )

    report = pdf_service.apply_selective_ocr(
        str(path),
        pages,
        {1, 2},
        config={"enabled": True, "min_native_chars": 80},
        max_pages=1,
    )

    assert report["candidate_pages"] == [1]
    assert report["skipped_pages"] == [2]
    assert pages[1]["ocr_status"] == "skipped_budget"
