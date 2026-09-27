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


def test_campaign_precision_discovers_manual_from_nested_run_path(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from scripts import campaign

    monkeypatch.setattr(campaign, 'CAMPAIGN', tmp_path)
    monkeypatch.setattr(campaign, 'ROOT', tmp_path.parent)
    monkeypatch.setattr(campaign, 'asset', lambda manual: {'name': manual})
    graph = {'nodes': [{'id': 'f', 'name': 'fault'}, {'id': 'a', 'name': 'repair'}],
             'edges': [{'id': 'e', 'from': 'f', 'to': 'a', 'type': 'RESOLVED_BY', 'trusted': True,
                        'conditions': [], 'occurrences': [{'evidence': [{'page': 2, 'text': 'fault: repair'}]}]}]}
    run = tmp_path / 'manual' / 'runs' / 'v3_r1'
    run.mkdir(parents=True)
    (run / 'graph.json').write_text(json.dumps(graph))
    gold = tmp_path / 'manual' / 'gold'
    gold.mkdir()
    (gold / 'gold.json').write_text(json.dumps({'pages': [1]}))
    args = SimpleNamespace(ids=[], new=True, score=False, force=False, per_system=1)
    campaign.cmd_precision(args)
    entries = json.loads((tmp_path / 'results/precision/chiave_non_aprire_2.json').read_text())['items']
    assert len(entries) == 1
    assert next(iter(entries.values()))['manual'] == 'manual'
    assert next(iter(entries.values()))['outside_gold_pages']
