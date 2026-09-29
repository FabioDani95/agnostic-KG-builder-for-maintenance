"""The optional event hook of the pipeline changes nothing: same result, same state, same graph."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from backend.kg_v3.export import graph_json
from tests.test_kg_v3_pipeline import ScriptedProvider, pipeline
from tests.test_kg_v3_reader import ASSET

# Wall-clock values differ between two runs by nature.
VOLATILE = {"answered_at", "seconds"}


def stable(value):
    if isinstance(value, dict):
        return {key: stable(item) for key, item in value.items() if key not in VOLATILE}
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def run(doc, workdir: Path, on_event=None):
    job, _ = pipeline(doc, ScriptedProvider(), workdir)
    job.on_event = on_event
    result = asyncio.run(job.run())
    state = {path.name: stable(json.loads(path.read_text(encoding="utf-8")))
             for path in sorted((workdir / "state").glob("*.json"))}
    graph = stable(graph_json(result, doc, asset=ASSET, source_title="manual.pdf"))
    return stable(result.model_dump(mode="json")), state, graph


def test_results_are_identical_with_and_without_the_hook(manual_doc, tmp_path):
    events: list[tuple[str, dict]] = []
    plain = run(manual_doc, tmp_path / "plain")
    observed = run(manual_doc, tmp_path / "observed", on_event=lambda kind, data: events.append((kind, data)))
    assert observed == plain

    kinds = [kind for kind, _ in events]
    assert kinds.count("step_started") == kinds.count("step_finished") > 0
    saved = [data["name"] for kind, data in events if kind == "state_saved"]
    units = [name for name in saved if name.startswith("extract_")]
    assert len(units) == len(plain[0]["units"])  # one event per unit, as it finishes
    assert saved.index("map") < saved.index("units") < saved.index(units[0])
    assert all("cost_usd" in data for _, data in events)


def test_a_failing_listener_never_stops_or_changes_the_run(manual_doc, tmp_path):
    def broken(kind, data):
        raise RuntimeError("the view is gone")

    assert run(manual_doc, tmp_path / "broken", on_event=broken) == run(manual_doc, tmp_path / "plain")


def test_a_resumed_run_reports_what_it_loaded(manual_doc, tmp_path):
    run(manual_doc, tmp_path / "run")
    events: list[tuple[str, dict]] = []
    run(manual_doc, tmp_path / "run", on_event=lambda kind, data: events.append((kind, data)))
    loaded = {data["name"] for kind, data in events if kind == "state_loaded"}
    assert "map" in loaded and any(name.startswith("extract_") for name in loaded)
