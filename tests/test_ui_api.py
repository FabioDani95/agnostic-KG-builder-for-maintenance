"""The local API over a small campaign tree: library, graph, questions, evidence, events, spending."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.ui.api import UiSettings, create_app
from backend.ui.budget import Limits
from backend.ui.events import EventTranslator
from tests.ui_support import campaign_tree


@pytest.fixture()
def settings(tmp_path, manual_doc):
    root = campaign_tree(tmp_path, manual_doc)
    ledger = root / "ledger.jsonl"
    ledger.write_text("\n".join(json.dumps(line) for line in [
        {"event": "ledger_initialized", "absolute_budget_usd": 20.0},
        {"event": "call_reserved", "call_id": "campaign_x:1", "worst_case_cost_usd": 0.01},
        {"event": "call_finalized", "call_id": "campaign_x:1", "charged_cost_usd": 0.25},
        {"event": "call_reserved", "call_id": "ui_test_pump_v3_r1:2", "worst_case_cost_usd": 0.01},
        {"event": "call_finalized", "call_id": "ui_test_pump_v3_r1:2", "charged_cost_usd": 0.02},
    ]) + "\n", encoding="utf-8")
    return UiSettings(root=root, campaign=root / "campaign", workspace=root / "workspace", ledger=ledger,
                      frontend=root / "dist", limits=Limits())


@pytest.fixture()
def client(settings):
    return TestClient(create_app(settings))


def test_the_library_lists_each_manual_once_with_its_latest_version(client):
    rows = client.get("/api/manuals").json()
    assert [row["id"] for row in rows] == ["test_pump"]
    assert rows[0]["machine"]["name"] == "Test pump" and rows[0]["versions"] == 3
    detail = client.get("/api/manuals/test_pump").json()
    assert {version["version_id"] for version in detail["versions"]} >= {"runs~v3_r1", "runs_E~v3_r1"}
    assert client.get("/api/manuals/missing").status_code == 404


def test_graph_report_and_questions_of_a_version(client):
    graph = client.get("/api/manuals/test_pump/versions/runs~v3_r1/graph").json()
    assert graph["nodes"] and graph["edges"]
    assert client.get("/api/manuals/test_pump/versions/runs~v3_r1/report").json()["status"] == "approved"
    questions = client.get("/api/manuals/test_pump/versions/runs~v3_r1/questions").json()
    assert questions["copy_needed"] is True and questions["editable"] is False
    assert questions["open"] and questions["open"][0]["claims_it"]
    assert client.get("/api/manuals/test_pump/versions/runs~v9/graph").status_code == 404


def test_evidence_text_and_page_image(client):
    graph = client.get("/api/manuals/test_pump/versions/runs~v3_r1/graph").json()
    cited = graph["edges"][0]["occurrences"][0]["evidence"][0]
    segment = client.get(f"/api/manuals/test_pump/segments/{cited['segment_id']}").json()
    assert segment["text"] == cited["text"] and segment["page"] == cited["page"]
    image = client.get("/api/manuals/test_pump/pages/1.png?scale=1")
    assert image.status_code == 200 and image.content.startswith(b"\x89PNG")
    assert client.get("/api/manuals/test_pump/pages/9.png").status_code == 404


def events_of(text: str) -> list[dict]:
    return [json.loads(line[len("data: "):]) for line in text.splitlines() if line.startswith("data: ")]


def test_a_replay_streams_every_event_and_resumes_after_the_last_seen(client):
    stream = client.get("/api/manuals/test_pump/versions/runs~v3_r1/events?speed=0")
    assert stream.headers["content-type"].startswith("text/event-stream")
    events = events_of(stream.text)
    assert events[0]["kind"] == "run_started" and events[-1]["kind"] == "run_finished"
    later = events_of(client.get("/api/manuals/test_pump/versions/runs~v3_r1/events?speed=0",
                                 headers={"Last-Event-ID": "5"}).text)
    assert [event["seq"] for event in later] == [event["seq"] for event in events[5:]]


def test_a_running_run_is_followed_until_it_ends(client, settings):
    run = settings.workspace / "test_pump" / "runs" / "v3_r1"
    run.mkdir(parents=True)
    translator = EventTranslator()
    lines = [*translator.feed("run_started", {"mode": "live"}, 0.0),
             *translator.feed("run_failed", {"message": "BudgetExceededError"}, 1.0)]
    (run / "events.jsonl").write_text(lines[0].model_dump_json() + "\n", encoding="utf-8")
    version = client.get("/api/manuals/test_pump").json()["versions"]
    assert next(v for v in version if v["origin"] == "workspace")["status"] == "running"
    (run / "events.jsonl").write_text("".join(line.model_dump_json() + "\n" for line in lines), encoding="utf-8")
    events = events_of(client.get("/api/manuals/test_pump/versions/workspace~v3_r1/events").text)
    assert [event["kind"] for event in events] == ["run_started", "run_failed"]


def test_spending_is_read_from_the_ledger(client):
    budget = client.get("/api/budget").json()
    assert budget["committed_usd"] == 0.27 and budget["ui_spent_usd"] == 0.02
    assert budget["ceiling_usd"] == 15.0 and budget["ui_limit_usd"] == 0.5
    estimate = client.get("/api/estimate?pages=20").json()
    assert estimate["based_on"] == ["test_pump"]
