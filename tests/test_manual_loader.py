from __future__ import annotations

import json
from pathlib import Path

from backend.services.manual_loader import build_store_from_markdown

GOLDEN_DIR = Path("tests/golden")


def test_markdown_golden_manuals_load_as_runtime_stores():
    for expected_path in sorted((GOLDEN_DIR / "expected").glob("*.json")):
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        manual_path = GOLDEN_DIR / expected["manual"]

        store = build_store_from_markdown(manual_path)

        page_numbers = {page["page_number"] for page in store["pages"]}
        assert store["filename"] == manual_path.name
        assert store["source_format"] == "markdown"
        assert store["page_count"] == len(store["pages"])
        assert store["graph_state"]["current_phase"] == "loaded"
        assert store["graph_state"]["config_snapshot"]["pipeline"]["mode"] == "multi_agent"
        assert set(expected["expected_scoping"]["must_keep_pages"]).issubset(page_numbers)
        assert expected["asset"]["name"] in "\n".join(page["text"] for page in store["pages"])
