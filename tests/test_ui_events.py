"""Interface events translated from a scripted run: stations, units, checks and the final graph."""

from __future__ import annotations

import asyncio

from backend.kg_v3.export import graph_json
from backend.ui.events import EventTranslator, edge_id, endpoint_id, page_of
from tests.test_kg_v3_pipeline import ScriptedProvider, pipeline
from tests.test_kg_v3_reader import ASSET


def translated(doc, workdir):
    raw: list[tuple[str, dict]] = []
    job, _ = pipeline(doc, ScriptedProvider(), workdir)
    job.on_event = lambda kind, data: raw.append((kind, data))
    result = asyncio.run(job.run())
    graph = graph_json(result, doc, asset=ASSET, source_title="manual.pdf")
    translator = EventTranslator()
    events = translator.feed("run_started", {"manual_id": "m", "version_id": "v", "mode": "live"}, 0.0)
    for index, (kind, data) in enumerate(raw, start=1):
        events += translator.feed(kind, data, float(index))
    events += translator.feed("run_finished", {"graph": graph, "status": result.status, "open_questions": 0},
                              float(len(raw) + 1))
    return result, graph, events


def test_a_run_becomes_ordered_interface_events(manual_doc, tmp_path):
    result, graph, events = translated(manual_doc, tmp_path / "run")
    assert [event.seq for event in events] == list(range(1, len(events) + 1))
    assert events[0].kind == "run_started" and events[-1].kind == "run_finished"

    running = [event.data["station"] for event in events if event.kind == "station" and event.data["state"] == "running"]
    assert running[:3] == ["map", "extract", "check"] and "merge" in running and running[-1] == "ask"
    done = [event for event in events if event.kind == "station" and event.data["state"] == "done"]
    assert len(done) == len(running)  # every station that ran is closed

    extracted = [event for event in events if event.kind == "unit_extracted"]
    assert [event.data["index"] for event in extracted] == list(range(1, len(result.units) + 1))
    assert all(event.data["total"] == len(result.units) for event in extracted)
    assert any(event.kind == "relations_checked" for event in events)

    finished = events[-1].data
    assert finished["status"] == result.status
    assert finished["verified"] == sum(edge.tier.value == "green" for edge in result.graph.edges)


def test_provisional_ids_meet_the_final_graph(manual_doc, tmp_path):
    result, graph, events = translated(manual_doc, tmp_path / "run")
    final = next(event for event in events if event.kind == "graph_final").data
    seen_nodes = {node["id"] for event in events for node in event.data.get("nodes", [])
                  if event.kind in ("unit_extracted", "relations_checked")}
    final_ids = {node["id"] for node in final["nodes"]}
    # Every node of the manual is either seen with its final ID or merged into one.
    for node in graph["nodes"][1:]:
        assert node["id"] in seen_nodes or node["id"] in final["merged_into"].values()
    for provisional, target in final["merged_into"].items():
        assert target in final_ids
    symptom = next(node for node in graph["nodes"] if node["name"] == "Pump fails to operate")
    # The two reads named the symptom differently; both provisional nodes land on the final one.
    for name in ("Pump fails to operate", "Pump does not operate"):
        provisional = endpoint_id({"type": "Symptom", "name": name})
        assert final["merged_into"].get(provisional, provisional) == symptom["id"]

    # Final edges are the checked ones once their ends follow the merges.
    moved = final["merged_into"]
    checked = {edge_id(edge["type"], moved.get(edge["from"], edge["from"]), moved.get(edge["to"], edge["to"]))
               for event in events if event.kind == "relations_checked" for edge in event.data["edges"]}
    for edge in graph["edges"]:
        if not edge.get("derived"):
            assert edge["id"] in checked


def test_small_helpers():
    assert page_of("p12.t1.r3") == 12 and page_of("x") is None
    assert edge_id("AFFECTS", "a", "b") != edge_id("AFFECTS", "b", "a")


def test_the_event_log_appends_and_a_resume_continues_the_numbering(tmp_path):
    from backend.ui.events import EventLog, UiEvent

    path = tmp_path / "events.jsonl"
    first = EventLog(path)
    first("run_started", {"mode": "live"})
    first("step_started", {"step": "map"})
    first("run_failed", {"message": "BudgetExceededError: ceiling"})
    resumed = EventLog(path)
    resumed("run_started", {"mode": "resume"})
    events = [UiEvent.model_validate_json(line) for line in path.read_text().splitlines()]
    assert [event.seq for event in events] == [1, 2, 3, 4, 5]
    assert [event.kind for event in events] == ["run_started", "station", "station", "run_failed", "run_started"]


def test_interface_presets_leave_the_approval_to_the_person():
    from scripts.kg_v3 import GATE_PRESETS

    for name in ("ui-agent", "ui-interactive", "ui-human"):
        assert GATE_PRESETS[name]["approval"] == [] and GATE_PRESETS[name]["map"] == ["agent"]
    assert GATE_PRESETS["ui-human"]["doubts"] == ["human"]


def test_a_resumed_run_shows_every_station_it_loaded(manual_doc, tmp_path):
    translated(manual_doc, tmp_path / "run")
    raw: list[tuple[str, dict]] = []
    job, _ = pipeline(manual_doc, ScriptedProvider(), tmp_path / "run")
    job.on_event = lambda kind, data: raw.append((kind, data))
    asyncio.run(job.run())
    translator = EventTranslator()
    events = [event for kind, data in raw for event in translator.feed(kind, data, 0.0)]
    running = {event.data["station"] for event in events if event.kind == "station" and event.data["state"] == "running"}
    assert running == {"map", "extract", "check", "merge", "ask"}
