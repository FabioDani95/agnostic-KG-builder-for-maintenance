"""Runs started from the interface: upload, new manual, spending checks, command line, stop.

No test starts the real command line: the process is replaced by a stand-in.
"""

from __future__ import annotations

import json
import sys

import pytest
from fastapi.testclient import TestClient

from backend.ui import jobs as jobs_module
from backend.ui.api import UiSettings, create_app
from backend.ui.budget import Limits
from tests.test_kg_v3_reader import troubleshooting_pdf
from tests.ui_support import campaign_tree


class FakeProcess:
    started: list[list[str]] = []
    environments: list[dict] = []

    def __init__(self, command, **kwargs):
        FakeProcess.started.append(command)
        FakeProcess.environments.append(kwargs.get("env") or {})
        self.pid = 999_999_999  # no such process

    def poll(self):
        return 0


def make_client(tmp_path, manual_doc, *, committed=12.8, ui_spent=0.0, ceiling=15.0):
    root = campaign_tree(tmp_path, manual_doc)
    ledger = root / "ledger.jsonl"
    ledger.write_text("\n".join(json.dumps(line) for line in [
        {"event": "call_finalized", "call_id": "campaign:1", "charged_cost_usd": committed},
        {"event": "call_finalized", "call_id": "ui_x_v3_r1:1", "charged_cost_usd": ui_spent},
    ]) + "\n", encoding="utf-8")
    settings = UiSettings(root=root, campaign=root / "campaign", workspace=root / "workspace", ledger=ledger,
                          frontend=root / "dist", limits=Limits(ceiling_usd=ceiling))
    return TestClient(create_app(settings)), settings


@pytest.fixture(autouse=True)
def no_real_process(monkeypatch):
    FakeProcess.started = []
    monkeypatch.setattr(jobs_module.subprocess, "Popen", FakeProcess)


def upload(client, tmp_path, name="pump.pdf"):
    pdf = tmp_path / name
    troubleshooting_pdf(pdf)
    return client.post("/api/uploads", files={"file": (name, pdf.read_bytes(), "application/pdf")})


def test_a_file_that_is_not_a_pdf_is_refused(tmp_path, manual_doc):
    client, _ = make_client(tmp_path, manual_doc)
    response = client.post("/api/uploads", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 422 and "non è un PDF" in response.json()["detail"]


def test_an_uploaded_pdf_becomes_a_workspace_manual(tmp_path, manual_doc):
    client, settings = make_client(tmp_path, manual_doc)
    uploaded = upload(client, tmp_path / "..", "other.pdf").json()
    assert uploaded["pages"] == 1 and uploaded["size_bytes"] > 0
    # The campaign manual has no sha256 in this tree, so the PDF is new here.
    created = client.post("/api/manuals", json={"upload_id": uploaded["upload_id"], "name": "Test pump",
                                                "brand": "Acme", "model": "P-2", "type": "pump"}).json()
    assert created["id"] == "acme_p_2"
    folder = settings.workspace / "acme_p_2"
    assert (folder / "manual.pdf").exists() and "Acme" in (folder / "info.yaml").read_text()
    again = client.post("/api/manuals", json={"upload_id": uploaded["upload_id"], "name": "Test pump"}).json()
    assert again["id"] == "acme_p_2"  # the same PDF is a new version of the same manual
    assert client.get("/api/manuals/acme_p_2").json()["origin"] == "workspace"


def test_a_run_starts_the_campaign_command_line_under_workspace(tmp_path, manual_doc):
    client, settings = make_client(tmp_path, manual_doc)
    started = client.post("/api/manuals/test_pump/runs", json={"reviewers": "human"})
    assert started.status_code == 200 and started.json()["version_id"] == "workspace~v3_r1"
    command = FakeProcess.started[0]
    assert command[1].endswith("scripts/kg_v3.py") and command[2:4] == ["--manual", "test_pump"]
    assert command[command.index("--gates") + 1] == "ui-human" and "--events" in command
    assert command[command.index("--out") + 1].startswith(str(settings.workspace))
    # The ceiling handed to the run keeps the interface within its own limit.
    assert float(command[command.index("--spend-ceiling") + 1]) == pytest.approx(12.8 + 0.5, abs=1e-3)
    assert command[command.index("--run-id") + 1] == "ui_test_pump_v3_r1"
    job = json.loads((settings.workspace / "test_pump" / "runs" / "v3_r1" / "job.json").read_text())
    assert job["reviewers"] == "human"


def test_runs_that_would_not_fit_the_spending_are_refused(tmp_path, manual_doc):
    client, _ = make_client(tmp_path, manual_doc, committed=15.0)
    refused = client.post("/api/manuals/test_pump/runs", json={"reviewers": "agent"})
    assert refused.status_code == 409 and "tetto" in refused.json()["detail"]
    client, _ = make_client(tmp_path / "second", manual_doc, ui_spent=0.5)
    refused = client.post("/api/manuals/test_pump/runs", json={"reviewers": "agent"})
    assert refused.status_code == 409 and "interfaccia" in refused.json()["detail"]
    assert FakeProcess.started == []


def test_stopping_a_run_that_is_not_running_is_refused(tmp_path, manual_doc):
    client, _ = make_client(tmp_path, manual_doc)
    client.post("/api/manuals/test_pump/runs", json={"reviewers": "agent"})
    stopped = client.post("/api/manuals/test_pump/versions/workspace~v3_r1/stop")
    assert stopped.status_code == 409


REAL_POPEN = jobs_module.subprocess.Popen  # the stand-in above would starve the reading of its pipes


def fake_identify(monkeypatch, script: str, seen: list):
    monkeypatch.setattr(jobs_module.subprocess, "Popen", REAL_POPEN)

    def command(self, pdf, ceiling):
        seen.append(ceiling)
        return [sys.executable, "-c", script]
    monkeypatch.setattr(jobs_module.Jobs, "identify_command", command)


ANSWER = ('import json; print(json.dumps({"machine": {"name": "Acme P1 pump", "brand": "Acme", "model": "P1", '
          '"type": "pump"}, "model": "gpt-6-luna", "seconds": 0.8, "cost_usd": 0.0003, "read": "text"}))')


def test_the_machine_is_read_from_the_first_pages_once_and_kept(tmp_path, manual_doc, monkeypatch):
    client, _ = make_client(tmp_path, manual_doc)
    seen: list = []
    fake_identify(monkeypatch, ANSWER, seen)
    upload_id = upload(client, tmp_path).json()["upload_id"]
    first = client.post(f"/api/uploads/{upload_id}/machine").json()
    assert first["machine"] == {"name": "Acme P1 pump", "brand": "Acme", "model": "P1", "type": "pump"}
    assert first["cached"] is False and first["cost_usd"] == 0.0003
    assert client.post(f"/api/uploads/{upload_id}/machine").json()["cached"] is True
    assert len(seen) == 1 and 12.8 < seen[0] <= 12.81  # one small call under a tight ceiling


def test_reading_the_machine_is_refused_without_money_or_upload(tmp_path, manual_doc, monkeypatch):
    client, _ = make_client(tmp_path, manual_doc, ui_spent=0.5)
    seen: list = []
    fake_identify(monkeypatch, ANSWER, seen)
    upload_id = upload(client, tmp_path).json()["upload_id"]
    refused = client.post(f"/api/uploads/{upload_id}/machine")
    assert refused.status_code == 422 and "scrivili tu" in refused.json()["detail"] and not seen
    assert client.post(f"/api/uploads/{'0' * 64}/machine").status_code == 422


def test_a_failed_reading_says_so_and_keeps_nothing(tmp_path, manual_doc, monkeypatch):
    client, settings = make_client(tmp_path, manual_doc)
    fake_identify(monkeypatch, "import sys; sys.exit('quota exceeded')", [])
    upload_id = upload(client, tmp_path).json()["upload_id"]
    failed = client.post(f"/api/uploads/{upload_id}/machine")
    assert failed.status_code == 422 and "quota exceeded" in failed.json()["detail"]
    assert not (settings.workspace / "uploads" / f"{upload_id}.machine.json").exists()


def test_the_first_pages_are_read_as_text(tmp_path):
    from backend.ui.identify import clean, first_pages

    pdf = tmp_path / "pump.pdf"
    troubleshooting_pdf(pdf)
    text, cover = first_pages(pdf)
    assert text and cover is None
    assert clean({"brand": " Acme ", "model": "P1", "type": "pump", "name": ""})["name"] == "Acme P1 pump"


def test_settings_start_from_the_command_line_defaults_and_never_return_the_key(tmp_path, manual_doc):
    client, settings = make_client(tmp_path, manual_doc)
    shown = client.get("/api/settings").json()
    assert (shown["reasoning"], shown["reads"], shown["agent_model"], shown["human_questions"]) == ("low", 2, "gpt-6-luna", 10)
    assert "api_key" not in shown and shown["key"]["source"] in {"env", "none"}
    saved = client.put("/api/settings", json={"reads": 1, "agent_reasoning": "high", "human_questions": 5,
                                              "node_labels": True, "api_key": "sk-test-0123456789abcdefWXYZ"}).json()
    assert saved["reads"] == 1 and saved["node_labels"] is True
    assert saved["key"] == {"source": "custom", "hint": "…WXYZ"} and "sk-test" not in json.dumps(saved)
    stored = settings.workspace / "settings.json"
    assert stored.stat().st_mode & 0o777 == 0o600
    assert client.put("/api/settings", json={"api_key": "not a key"}).status_code == 422
    assert client.put("/api/settings", json={"reads": 7}).status_code == 422
    assert client.put("/api/settings", json={"clear_api_key": True}).json()["key"]["source"] != "custom"


def test_a_new_run_takes_the_settings_and_the_key_written_here(tmp_path, manual_doc):
    client, settings = make_client(tmp_path, manual_doc)
    client.put("/api/settings", json={"reasoning": "medium", "reads": 3, "agent_model": "gpt-5.6-luna",
                                      "human_questions": 5, "api_key": "sk-test-0123456789abcdefWXYZ"})
    started = client.post("/api/manuals/test_pump/runs", json={"reviewers": "human"})
    assert started.status_code == 200
    command = " ".join(FakeProcess.started[-1])
    for flag in ("--reasoning medium", "--reads 3", "--agent-model gpt-5.6-luna", "--human-questions 5"):
        assert flag in command
    assert FakeProcess.environments[-1]["OPENAI_API_KEY"] == "sk-test-0123456789abcdefWXYZ"
    run_dir = settings.workspace / "test_pump" / "runs" / "v3_r1"
    assert jobs_module.question_budget(run_dir) == 5
