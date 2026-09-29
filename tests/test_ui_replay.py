"""A replay of a finished run gives the interface the same events a live view received."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from backend.kg_v3.export import graph_json
from backend.ui.events import EventTranslator
from backend.ui.replay import replay_events, timeline
from tests.test_kg_v3_pipeline import ScriptedProvider, pipeline
from tests.test_kg_v3_reader import ASSET

ROOT = Path(__file__).resolve().parents[1]


def finished_run(doc, run_dir: Path):
    """A scripted run written like the command line writes it, with its live events."""

    raw: list[tuple[str, dict]] = [("step_started", {"step": "pdf_read"}), ("step_finished", {"step": "pdf_read"})]
    job, _ = pipeline(doc, ScriptedProvider(), run_dir)
    job.on_event = lambda kind, data: raw.append((kind, data))
    result = asyncio.run(job.run())
    graph = graph_json(result, doc, asset=ASSET, source_title="manual.pdf")
    (run_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
    (run_dir / "report.json").write_text(json.dumps(result.report), encoding="utf-8")
    translator = EventTranslator()
    live = translator.feed("run_started", {"mode": "live"}, 0.0)
    for kind, data in raw:
        live += translator.feed(kind, data, 0.0)
    live += translator.feed("run_finished", {"graph": graph, "status": result.status}, 0.0)
    return graph, live


def shape(events):
    return [(event.kind, event.data) for event in events if event.kind != "run_started"]


def test_replay_matches_the_live_events(manual_doc, tmp_path):
    graph, live = finished_run(manual_doc, tmp_path / "run")
    replayed = replay_events(tmp_path / "run", manual_id="m", version_id="v")
    assert shape(replayed) == shape(live)
    times = [event.t for event in replayed]
    assert times == sorted(times)
    final = next(event for event in replayed if event.kind == "graph_final").data
    assert {node["id"] for node in final["nodes"]} == {node["id"] for node in graph["nodes"]}
    assert replayed[0].data["cost_estimated"] is True  # no ledger: the total is spread over time


def test_untrusted_file_dates_fall_back_to_the_report(manual_doc, tmp_path):
    finished_run(manual_doc, tmp_path / "run")
    files = sorted((tmp_path / "run" / "state").glob("*.json"))
    for offset, path in enumerate(files):  # dates in reverse order: a copy or a restore
        os.utime(path, (2_000_000_000 - offset * 60, 2_000_000_000 - offset * 60))
    raw, start = timeline(tmp_path / "run")
    assert start is None
    times = [t for t, _, _ in raw]
    assert times == sorted(times) and times[-1] > 0


def test_saved_live_events_are_replayed_as_they_are(tmp_path):
    events = EventTranslator().feed("run_started", {"mode": "live", "manual_id": "m"}, 0.0)
    (tmp_path / "events.jsonl").write_text("\n".join(event.model_dump_json() for event in events) + "\n")
    assert replay_events(tmp_path, manual_id="m", version_id="v") == events


@pytest.mark.skipif(not (ROOT / "campaign/graco_gtx_2000ex/runs/v3_r1/state").exists(),
                    reason="local run state of Graco is not in this clone")
def test_graco_replay_ends_with_its_graph(tmp_path):
    run_dir = ROOT / "campaign/graco_gtx_2000ex/runs/v3_r1"
    events = replay_events(run_dir, manual_id="graco_gtx_2000ex", version_id="runs~v3_r1",
                           ledger=ROOT / "campaign/real_call_budget.jsonl", cache_dir=tmp_path)
    graph = json.loads((run_dir / "graph.json").read_text(encoding="utf-8"))
    final = next(event for event in events if event.kind == "graph_final").data
    assert [node["id"] for node in final["nodes"]] == [node["id"] for node in graph["nodes"]]
    assert [edge["id"] for edge in final["edges"]] == [edge["id"] for edge in graph["edges"]]
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert events[-1].data["verified"] == report["graph"]["edges_by_tier"]["green"]
    if not events[0].data["cost_estimated"]:
        spent = report["usage"]["estimated_cost_usd"] + report["agent_usage"]["estimated_cost_usd"]
        assert events[-1].cost_usd == pytest.approx(spent, abs=0.002)
