"""Blind annotation sheet: page ranges and branch lines are read as the annotator writes them."""

from __future__ import annotations

from scripts.kg_v3_annotate import _line, pages_from


def test_page_ranges():
    assert pages_from("45-47, 60") == [45, 46, 47, 60]


def test_branch_lines_keep_text_ids_and_kind():
    block = """- problema: Pump fails to operate | ID: p11.t1.r2
- azione: Clear the line | tipo: riparazione | ID: p11.t1.r2, p11.b6
- azione: Check the seal | tipo: controllo | ID: p11.t1.r9
- azione: Call the dealer | tipo: assistenza | ID:
"""
    assert _line(block, "problema") == [{"text": "Pump fails to operate", "ids": ["p11.t1.r2"], "kind": ""}]
    actions = _line(block, "azione")
    assert [item["kind"] for item in actions] == ["repair", "inspection", "escalation"]
    assert actions[0]["ids"] == ["p11.t1.r2", "p11.b6"] and actions[2]["ids"] == []
