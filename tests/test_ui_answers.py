"""A person answers, the run resumes with no call, and the graph is approved only after the answers."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.kg_v3.contracts import Tier
from backend.kg_v3.llm import ModelClient
from backend.kg_v3.run import Pipeline, RunConfig
from backend.ui import jobs as jobs_module
from backend.ui.api import UiSettings, create_app
from backend.ui.budget import Limits
from backend.ui.store import FileQuestionStore
from scripts.kg_v3 import GATE_PRESETS
from tests.test_kg_v3_pipeline import FailingProvider
from tests.ui_support import campaign_tree, scripted_run


class FakeProcess:
    started: list[list[str]] = []

    def __init__(self, command, **kwargs):
        FakeProcess.started.append(command)
        self.pid = 999_999_999

    def poll(self):
        return 0


@pytest.fixture(autouse=True)
def no_real_process(monkeypatch):
    FakeProcess.started = []
    monkeypatch.setattr(jobs_module.subprocess, "Popen", FakeProcess)


@pytest.fixture()
def setup(tmp_path, manual_doc):
    root = campaign_tree(tmp_path, manual_doc)
    ledger = root / "ledger.jsonl"
    ledger.write_text(json.dumps({"event": "call_finalized", "call_id": "campaign:1", "charged_cost_usd": 12.8}) + "\n")
    settings = UiSettings(root=root, campaign=root / "campaign", workspace=root / "workspace", ledger=ledger,
                          frontend=root / "dist", limits=Limits(), resume_wait_seconds=0)
    # A run started from the interface with doubts for the person, as scripts/kg_v3.py --gates ui-human writes it.
    run = settings.workspace / "test_pump" / "runs" / "v3_r1"
    run.mkdir(parents=True)
    scripted_run(manual_doc, run, gates=GATE_PRESETS["ui-human"])
    (run / "job.json").write_text(json.dumps({"reviewers": "human"}))
    return TestClient(create_app(settings)), settings, run


def resume(doc, run: Path):
    """What the command line does on «Applica»: the same run folder, the person's store, no model call."""

    llm = ModelClient(model="gpt-6-luna", client_factory=FailingProvider)
    job = Pipeline(doc=doc, asset_name="Test pump", llm=llm, agent_llm=llm, workdir=run,
                   human_store=FileQuestionStore(run / "people.json"),
                   config=RunConfig(gates=GATE_PRESETS["ui-human"]))
    return asyncio.run(job.run())


PATH = "/api/manuals/test_pump/versions/workspace~v3_r1"


def test_answers_apply_with_no_call_and_approval_comes_after(setup, manual_doc):
    client, settings, run = setup
    questions = client.get(f"{PATH}/questions").json()
    assert questions["awaiting_approval"] and not questions["can_approve"] and questions["editable"]
    open_ = questions["open"]
    assert open_ and all(question["kind"] == "relation_check" for question in open_)

    refused = client.post(f"{PATH}/approve", json={"decision": "approve"})
    assert refused.status_code == 409 and "Rispondi prima" in refused.json()["detail"]
    bad = client.post(f"{PATH}/questions/{open_[0]['question_id']}/answer", json={"option_id": "correct"})
    assert bad.status_code == 409  # "Solo in parte" needs the statements to keep

    for question in open_:
        assert client.post(f"{PATH}/questions/{question['question_id']}/answer",
                           json={"option_id": "reject"}).status_code == 200
    state = client.get(f"{PATH}/questions").json()
    assert not state["open"] and state["unapplied"] == len(open_) and not state["can_approve"]

    assert client.post(f"{PATH}/apply").status_code == 200
    command = FakeProcess.started[-1]
    assert "--human-store" in command and command[command.index("--out") + 1] == str(run)
    assert float(command[command.index("--spend-ceiling") + 1]) == pytest.approx(12.85, abs=1e-3)

    graph = json.loads((run / "graph.json").read_text())
    assert any(edge["tier"] == "yellow" for edge in graph["edges"])  # doubts before the answers
    result = resume(manual_doc, run)  # the resumed command line, run here with a client that refuses calls
    assert not any(edge.tier is Tier.YELLOW for edge in result.graph.edges)  # every doubt answered "No"
    assert result.status == "awaiting_approval"

    ready = client.get(f"{PATH}/questions").json()
    assert ready["can_approve"]
    assert client.post(f"{PATH}/approve", json={"decision": "approve"}).status_code == 200
    approved = resume(manual_doc, run)
    assert approved.status in ("approved", "incomplete")
    record = json.loads((run / "state" / "gate_approval.json").read_text())
    assert record["answers"][-1]["answered_by"]["kind"] == "human"


def digest(folder: Path) -> str:
    return hashlib.sha256(b"".join(path.read_bytes() for path in sorted(folder.rglob("*")) if path.is_file())).hexdigest()


def test_answering_a_campaign_version_works_on_a_copy(setup):
    client, settings, _ = setup
    original = settings.campaign / "test_pump" / "runs" / "v3_r1"
    before = digest(original)
    questions = client.get("/api/manuals/test_pump/versions/runs~v3_r1/questions").json()
    assert questions["copy_needed"]
    first = questions["open"][0]["question_id"]
    answered = client.post(f"/api/manuals/test_pump/versions/runs~v3_r1/questions/{first}/answer",
                           json={"option_id": "accept"}).json()
    assert answered["version_id"] == "workspace~risposte-1" and answered["answered"] == 1
    copy = settings.workspace / "test_pump" / "runs" / "risposte-1"
    assert json.loads((copy / "origin.json").read_text())["from"].endswith("runs/v3_r1")
    assert digest(original) == before  # the campaign run is untouched
    approval = json.loads((copy / "state" / "gate_approval.json").read_text())
    assert approval["answers"] == [] and approval["pending"]  # the automatic approval stays behind
    versions = client.get("/api/manuals/test_pump").json()["versions"]
    assert any(version["copied_from"] for version in versions)
