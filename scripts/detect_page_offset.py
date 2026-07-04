#!/usr/bin/env python3
"""Test printed-page-offset autodetection against real PDF manuals.

Usage:
    python3 scripts/detect_page_offset.py [pdf ...]

Without arguments, every PDF in manuals/ is analysed. For each manual the
script prints the offset detected from printed page labels, from ToC anchoring
(using a regex ToC parse, no LLM), and the combined verdict, plus the vote
distributions so a wrong detection can be diagnosed at a glance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _analyse(pdf_path: Path) -> dict:
    from backend.services.cutplan_service import find_toc_pages
    from backend.services.page_offset_service import (
        detect_page_offset,
        parse_toc_entries_from_text,
    )
    from backend.services.pdf_service import extract_text_by_page

    pages = extract_text_by_page(str(pdf_path))
    toc_found, toc_text, toc_start, toc_end = find_toc_pages(pages)
    toc_entries = parse_toc_entries_from_text(toc_text) if toc_found else []
    detection = detect_page_offset(
        pages,
        toc_entries or None,
        toc_page_range=(toc_start, toc_end) if toc_found else None,
    )
    return {
        "file": pdf_path.name,
        "physical_pages": len(pages),
        "toc_found": toc_found,
        "toc_entries_parsed": len(toc_entries),
        "detection": detection,
    }


def main(argv: list[str]) -> int:
    if argv:
        targets = [Path(arg) for arg in argv]
    else:
        targets = sorted((REPO_ROOT / "manuals").glob("*.pdf"))
    if not targets:
        print("No PDF manuals found.", file=sys.stderr)
        return 1

    for pdf_path in targets:
        result = _analyse(pdf_path)
        detection = result["detection"]
        print(f"=== {result['file']}")
        print(f"    physical pages: {result['physical_pages']} | "
              f"ToC: {'found' if result['toc_found'] else 'not found'} "
              f"({result['toc_entries_parsed']} entries parsed)")
        for key in ("label_detection", "toc_detection"):
            sub = detection[key]
            print(f"    {sub['source']}: offset={sub['offset']} "
                  f"confidence={sub['confidence']} votes={json.dumps(sub['votes'])}")
        print(f"    --> OFFSET {detection['offset']} "
              f"(source={detection['source']}, confidence={detection['confidence']}, "
              f"agreement={detection['agreement']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
