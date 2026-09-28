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


def test_new_links_sheet_marks_relations_the_earlier_run_did_not_trust(tmp_path):
    from scripts.kg_v3_precision_sheet import write_new_links_sheet

    def graph(links):
        nodes = {name for link in links for name in link[1:]}
        return {"nodes": [{"id": name, "name": name} for name in nodes], "edges": [
            {"id": f"e{index}", "from": source, "to": target, "type": kind, "trusted": True, "conditions": [],
             "occurrences": [{"evidence": [{"page": 3, "text": "No heat: replace the fuse"}]}]}
            for index, (kind, source, target) in enumerate(links)]}

    before, after = tmp_path / "before.json", tmp_path / "after.json"
    before.write_text(json.dumps(graph([("RESOLVED_BY", "Fuse open", "Replace the fuse")])))
    after.write_text(json.dumps(graph([("RESOLVED_BY", "Open fuse", "Replace the fuse"),
                                       ("MAY_INDICATE", "No heat", "Open fuse")])))
    counts = write_new_links_sheet([("m", after, before)], 3, tmp_path / "s.md", tmp_path / "k.json", {}, "t")
    assert counts == {"m": {"new": 1, "kept": 1}}
    systems = {item["relation"]: item["system"] for item in json.loads((tmp_path / "k.json").read_text())["items"].values()}
    assert systems == {"MAY_INDICATE": "v3_new", "RESOLVED_BY": "v3_kept"}
