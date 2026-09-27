import json

import pytest

from scripts.kg_v3_precision_sheet import write_sheet


def test_blind_sheet_samples_outside_gold_using_all_occurrences(tmp_path):
    graph = {"nodes": [{"id": "f", "name": "fault"}, {"id": "a", "name": "repair"}], "edges": []}
    for i, pages in enumerate(([5], [5, 1], [1], [6])):
        graph["edges"].append({"id": str(i), "from": "f", "to": "a", "type": "RESOLVED_BY", "trusted": True,
                               "conditions": [], "occurrences": [{"evidence": [{"page": p, "text": f"source {p}"}]}
                                                                    for p in pages]})
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph))
    sheet, key = tmp_path / "sheet.md", tmp_path / "key.json"
    write_sheet([("m", path, None)], 4, sheet, key, {"m": "Manual"}, "test", {"m": [1]})
    entries = {item["edge"]: item for item in json.loads(key.read_text())["items"].values()}
    assert entries["0"]["outside_gold_pages"] and entries["3"]["outside_gold_pages"]
    assert not entries["1"]["outside_gold_pages"] and not entries["2"]["outside_gold_pages"]
    assert "outside_gold_pages" not in sheet.read_text()
    assert sheet.read_text().count("- Giudizio: `?`") == 4
    with pytest.raises(FileExistsError):
        write_sheet([], 4, sheet, key, {}, "test")
