#!/usr/bin/env python3
"""Build the deterministic five-table/riga-61 PDF fixture for AC-PDF-004."""

from __future__ import annotations

import hashlib
from pathlib import Path

import fitz

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "tests" / "fixtures" / "manuals" / "g1_pdf_inventory.pdf"
MARKER = "G1_TABLE_5_ROW_61_MARKER"


def _draw_table(page, *, table_number: int, row_count: int) -> None:
    left, right = 56.0, 539.0
    top, bottom = 120.0, 760.0
    columns = [left, 150.0, 350.0, right]
    row_height = (bottom - top) / row_count
    for x in columns:
        page.draw_line((x, top), (x, bottom), color=(0, 0, 0), width=0.5)
    for row_index in range(row_count + 1):
        y = top + row_index * row_height
        page.draw_line((left, y), (right, y), color=(0, 0, 0), width=0.5)
    font_size = min(7.0, max(4.0, row_height * 0.48))
    for row_index in range(1, row_count + 1):
        if row_index == 1:
            values = ["row", "observation", "action"]
        else:
            marker = MARKER if table_number == 5 and row_index == 61 else ""
            values = [
                str(row_index),
                marker or f"table {table_number} inspection {row_index}",
                f"maintenance action {row_index}",
            ]
        y = top + (row_index - 1) * row_height + row_height * 0.68
        for column_index, value in enumerate(values):
            page.insert_text(
                (columns[column_index] + 2, y),
                value,
                fontsize=font_size,
                fontname="helv",
            )


def build() -> bytes:
    document = fitz.open()
    try:
        document.set_metadata(
            {
                "title": "G1 deterministic hierarchical PDF inventory fixture",
                "author": "log-kg-builder acceptance suite",
                "subject": "AC-PDF-004",
                "keywords": "G1,AC-PDF-004,RawUnit",
                "creator": "scripts/build_g1_pdf_fixture.py",
                "producer": "PyMuPDF",
                "creationDate": "D:20260729000000Z",
                "modDate": "D:20260729000000Z",
            }
        )
        for table_number in range(1, 6):
            page = document.new_page(width=595, height=842)
            page.insert_text(
                (56, 54),
                "SERIAL: HP7-000042",
                fontsize=10,
                fontname="helv",
            )
            page.insert_text(
                (56, 78),
                f"Maintenance inventory table {table_number}",
                fontsize=12,
                fontname="helv",
            )
            _draw_table(
                page,
                table_number=table_number,
                row_count=61 if table_number == 5 else 4,
            )
        return document.tobytes(
            garbage=4,
            deflate=True,
            clean=True,
            no_new_id=True,
        )
    finally:
        document.close()


def main() -> int:
    payload = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)
    print(f"{OUTPUT.relative_to(REPO_ROOT)} sha256={hashlib.sha256(payload).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
