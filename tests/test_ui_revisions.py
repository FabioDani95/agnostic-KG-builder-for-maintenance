import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.ui.api import UiSettings, create_app
from tests.test_ui_graph_document import fixture_graph
from tests.ui_support import INFO


@pytest.fixture
def editor_api(tmp_path, monkeypatch):
    from backend.kg_v3.llm import ModelClient

    def no_model(*args, **kwargs):
        raise AssertionError("The graph editor must not create a model client")

    monkeypatch.setattr(ModelClient, "__init__", no_model)
    manual = tmp_path / "campaign" / "pump"
    run = manual / "runs" / "v3_r1"
    run.mkdir(parents=True)
    (manual / "info.yaml").write_text(INFO)
    (run / "graph.json").write_text(json.dumps(fixture_graph()))
    (run / "report.json").write_text(json.dumps({"status": "approved"}))
    app = create_app(
        UiSettings(campaign=tmp_path / "campaign", workspace=tmp_path / "workspace", ledger=tmp_path / "ledger")
    )
    with TestClient(app) as client:
        yield client, run, tmp_path


PATH = "/api/manuals/pump/versions/runs~v3_r1"


def input_body(client, path=PATH, value="Loud noise"):
    editor = client.get(path + "/editor")
    assert editor.status_code == 200, editor.text
    return {
        "preconditions": editor.json()["preconditions"],
        "draft_generation": 1,
        "operations": [{"op": "node.set_name", "node_id": "sym", "value": value}],
    }


def accept_body(client, path=PATH, value="Loud noise", request="request_abcdefgh"):
    body = input_body(client, path, value)
    preview = client.post(path + "/validate-edits", json=body)
    assert preview.status_code == 200, preview.text
    p = preview.json()
    assert p["has_changes"] and p["can_accept"]
    return {
        **body,
        "request_id": request,
        "preview_hash": p["preview_hash"],
        "note": "test",
        "acceptance": {"decision": "accept_changes", "acknowledged_issue_ids": p["required_acknowledgements"]},
    }


def test_preview_readonly_noop_and_two_generations(editor_api):
    client, run, root = editor_api
    original = (run / "graph.json").read_bytes()
    body = accept_body(client)
    assert not (root / "workspace").exists()
    created = client.post(PATH + "/revisions", json=body)
    assert created.status_code == 201, created.text
    data = created.json()
    v = data["version"]
    assert v["kind"] == "revision" and v["status"] == "approved" and v["decided_by"] == "human"
    assert v["cost_usd"] == 0 and v["seconds"] is None and not v["replay"]
    new_path = "/api/manuals/pump/versions/" + v["version_id"]
    graph = client.get(new_path + "/graph").json()
    assert graph["version"] == "kg-v3-graph-3" and not graph["edges"][0]["trusted"]
    assert "report" not in graph
    assert (run / "graph.json").read_bytes() == original
    folder = root / "workspace/pump/revisions" / v["version_id"].split("~")[1]
    assert json.loads((folder / "base-graph.json").read_text()) == json.loads(original)
    assert (folder / "acceptance.json").exists()
    second = client.post(
        new_path + "/revisions", json=accept_body(client, new_path, "Another noise", "request_ijklmnop")
    )
    assert second.status_code == 201, second.text
    assert second.json()["parent_version_id"] == v["version_id"]
    assert len(client.get("/api/manuals/pump").json()["versions"]) == 3
    assert len(client.get("/api/runs").json()) == 1
    assert client.post(new_path + "/approve", json={"decision": "approve"}).status_code == 409
    assert client.get(new_path + "/changes").status_code == 200


def test_idempotence_restart_and_conflict(editor_api):
    client, run, root = editor_api
    body = accept_body(client)
    first = client.post(PATH + "/revisions", json=body)
    (run / "graph.json").write_text(json.dumps({**fixture_graph(), "changed": True}))
    retry = client.post(PATH + "/revisions", json=body)
    assert retry.status_code == 200 and retry.json() == first.json()
    changed = {**body, "note": "different"}
    assert client.post(PATH + "/revisions", json=changed).status_code == 409
    assert client.get("/api/manuals/pump/revision-requests/" + body["request_id"]).json()["status"] == "saved"
    with TestClient(
        create_app(UiSettings(campaign=root / "campaign", workspace=root / "workspace", ledger=root / "ledger"))
    ) as restarted:
        assert (
            restarted.get("/api/manuals/pump/revision-requests/" + body["request_id"]).json()["result"] == first.json()
        )


def test_preconditions_noop_schema_and_ack(editor_api):
    client, run, root = editor_api
    body = accept_body(client)
    assert client.post(PATH + "/revisions", json={**body, "preview_hash": "bad"}).status_code == 409
    assert (
        client.post(
            PATH + "/revisions",
            json={**body, "acceptance": {"decision": "accept_changes", "acknowledged_issue_ids": []}},
        ).status_code
        == 422
    )
    no_op = {**body, "operations": []}
    p = client.post(
        PATH + "/validate-edits", json={k: no_op[k] for k in ("preconditions", "draft_generation", "operations")}
    ).json()
    assert not p["has_changes"]
    assert client.post(PATH + "/revisions", json={**no_op, "preview_hash": p["preview_hash"]}).status_code == 422
    assert not (root / "workspace/pump/revisions").exists()
    (run / "graph.json").write_text(json.dumps({**fixture_graph(), "changed": True}))
    assert client.post(PATH + "/revisions", json=body).status_code == 409


def test_concurrent_retries_and_children(editor_api):
    client, run, root = editor_api
    body = accept_body(client)
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(lambda _: client.post(PATH + "/revisions", json=body), range(2)))
    assert sorted(r.status_code for r in responses) == [200, 201]
    other = {**body, "request_id": "request_child_two"}
    assert client.post(PATH + "/revisions", json=other).status_code == 201
    assert [
        v["revision_number"] for v in client.get("/api/manuals/pump").json()["versions"] if v["kind"] == "revision"
    ] == [2, 1]


def test_crash_before_publish_ignores_incomplete(editor_api, monkeypatch):
    client, run, root = editor_api
    body = accept_body(client)
    from pathlib import Path

    original = Path.rename

    def fail(self, target):
        if self.name.startswith(".tmp-"):
            raise OSError("simulated crash")
        return original(self, target)

    monkeypatch.setattr(Path, "rename", fail)
    with pytest.raises(OSError, match="simulated crash"):
        client.post(PATH + "/revisions", json=body)
    assert len(client.get("/api/manuals/pump").json()["versions"]) == 1
    assert not list((root / "workspace/pump/revisions").iterdir())


def test_revision_package_preserves_bytes_and_cannot_launch_jobs(editor_api, monkeypatch):
    import io
    import zipfile

    from backend.ui.jobs import Jobs

    client, run, root = editor_api
    original = (run / "graph.json").read_bytes()
    monkeypatch.setattr(Jobs, "start", lambda *args: pytest.fail("Editor must not start a job"))
    result = client.post(PATH + "/revisions", json=accept_body(client)).json()
    path = "/api/manuals/pump/versions/" + result["version"]["version_id"]
    package = client.get(path + "/provenance.zip")
    assert package.status_code == 200
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        assert archive.read("base-graph.json") == original
        assert json.loads(archive.read("acceptance.json"))["decision"] == "accept_changes"
        assert json.loads(archive.read("source-report.json")) == {"historical": True}
    for suffix in ("apply", "approve", "events"):
        method = client.get if suffix == "events" else client.post
        assert method(path + "/" + suffix).status_code in (409, 422)
    assert client.get(path + "/report").status_code == 404


def test_pdf_identity_index_freezing_and_changed_source(editor_api):
    import fitz

    from backend.ui.evidence import Evidence

    client, run, root = editor_api
    pdf_path = run.parent.parent / "manual.pdf"
    with fitz.open() as pdf:
        pdf.new_page().insert_text((60, 60), "Noise means wear. Replace bearing.")
        pdf.save(pdf_path)
    reader = Evidence(root / "cache-never-written")
    doc = reader.document(pdf_path.parent)
    evidence = reader.segment(pdf_path.parent, doc.segments()[0].segment_id)
    raw = fixture_graph()
    raw["edges"][0]["occurrences"][0]["evidence"] = [evidence]
    (run / "graph.json").write_text(json.dumps(raw))
    original_pdf = pdf_path.read_bytes()
    editor = client.get(PATH + "/editor").json()
    assert editor["source"]["segments_available"] and editor["source"]["pdf_available"]
    segments = client.get(PATH + "/source-segments?q=Noise&page=1").json()
    assert segments["available"] and segments["items"][0]["text"] == evidence["text"]
    assert not (root / "workspace").exists()
    accepted = client.post(PATH + "/revisions", json=accept_body(client)).json()
    path = "/api/manuals/pump/versions/" + accepted["version"]["version_id"]
    folder = root / "workspace/pump/revisions" / accepted["version"]["version_id"].split("~")[1]
    assert (folder / "source.pdf").read_bytes() == original_pdf
    assert client.get(path + "/pages/1.png").status_code == 200
    stale = input_body(client)
    with fitz.open() as pdf:
        pdf.new_page().insert_text((60, 60), "Entirely changed source content.")
        pdf.save(pdf_path)
    assert client.post(PATH + "/validate-edits", json=stale).status_code == 409
    changed = client.get(PATH + "/editor").json()
    assert not changed["source"]["segments_available"] and not changed["source"]["pdf_available"]
    assert client.get(path + "/source-segments").json()["items"][0]["text"] == evidence["text"]
    assert (folder / "source.pdf").read_bytes() == original_pdf


def test_process_and_review_changes_are_preconditions(editor_api, monkeypatch):
    from backend.ui import revisions

    client, run, root = editor_api
    body = accept_body(client)
    monkeypatch.setattr(revisions, "process_alive", lambda folder: True)
    assert client.post(PATH + "/revisions", json=body).status_code == 409
    assert not (root / "workspace/pump/revisions").exists()
    monkeypatch.setattr(revisions, "process_alive", lambda folder: False)
    (run / "people.json").write_text('{"new_context":true}')
    assert client.post(PATH + "/revisions", json=body).status_code == 409


def test_typed_values_survive_acceptance_and_reopening(editor_api, monkeypatch):
    from backend.ui import revisions
    from backend.ui.graph_document import schema

    client, run, root = editor_api
    ontology = schema()
    fields = next(n["properties"] for n in ontology["nodes"] if n["name"] == "Symptom")
    fields.extend(
        [
            {"name": "count", "type": "number", "required": False},
            {"name": "enabled", "type": "boolean", "required": False},
            {"name": "list", "type": "array", "items": "string", "required": False},
            {"name": "nullable", "type": "string", "required": False},
        ]
    )
    monkeypatch.setattr(revisions, "schema", lambda: ontology)
    body = input_body(client)
    body["operations"] += [
        {"op": "node.set_property", "node_id": "sym", "field": field, "value": value}
        for field, value in [
            ("count", 0),
            ("enabled", False),
            ("list", []),
            ("nullable", None),
            ("description", "First line\nSecond line"),
        ]
    ]
    preview = client.post(PATH + "/validate-edits", json=body).json()
    created = client.post(
        PATH + "/revisions",
        json={
            **body,
            "request_id": "request_typed_values",
            "preview_hash": preview["preview_hash"],
            "acceptance": {
                "decision": "accept_changes",
                "acknowledged_issue_ids": preview["required_acknowledgements"],
            },
        },
    )
    assert created.status_code == 201, created.text
    path = "/api/manuals/pump/versions/" + created.json()["version"]["version_id"]
    props = client.get(path + "/editor").json()["graph"]["nodes"][1]["properties"]
    assert props["count"] == 0 and props["enabled"] is False and props["list"] == []
    assert props["nullable"] is None and props["description"] == "First line\nSecond line"


def test_integrity_bypass_cannot_publish(editor_api):
    client, run, root = editor_api
    body = input_body(client)
    body["operations"] = [
        {
            "op": "edge.add",
            "temp_id": "tmp_edge_invalid",
            "relation_type": "MAY_INDICATE",
            "from": "missing",
            "to": "cause",
            "occurrences": [{}],
        }
    ]
    preview = client.post(PATH + "/validate-edits", json=body).json()
    assert not preview["can_accept"]
    assert any(i["code"] == "ORPHAN_EDGE" for i in preview["issues"])
    result = client.post(
        PATH + "/revisions",
        json={
            **body,
            "request_id": "request_bad_graph",
            "preview_hash": preview["preview_hash"],
            "acceptance": {
                "decision": "accept_changes",
                "acknowledged_issue_ids": preview["required_acknowledgements"],
            },
        },
    )
    assert result.status_code == 422 and result.json()["detail"]["code"] == "VALIDATION_FAILED"
    assert not (root / "workspace/pump/revisions").exists()


def test_request_reports_in_progress_and_survives_completion(editor_api, monkeypatch):
    import threading

    from backend.ui.revisions import Revisions

    client, _, _ = editor_api
    body = accept_body(client, request="request_in_progress")
    entered, release = threading.Event(), threading.Event()
    accept = Revisions._accept

    def paused(self, *args):
        entered.set()
        assert release.wait(10)
        return accept(self, *args)

    monkeypatch.setattr(Revisions, "_accept", paused)
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(client.post, PATH + "/revisions", json=body)
        assert entered.wait(10)
        try:
            assert (
                client.get("/api/manuals/pump/revision-requests/" + body["request_id"]).json()["status"]
                == "in_progress"
            )
        finally:
            release.set()
        assert future.result().status_code == 201
    assert client.get("/api/manuals/pump/revision-requests/" + body["request_id"]).json()["status"] == "saved"


def test_invalid_editor_dto_returns_translatable_target(editor_api):
    client, _, _ = editor_api
    body = input_body(client)
    body["operations"][0]["certificate"] = {"trusted": True}
    error = client.post(PATH + "/validate-edits", json=body)
    assert error.status_code == 422
    assert error.json()["detail"]["code"] == "INVALID_OPERATION"
    assert "certificate" in error.json()["detail"]["target"]["field"]


def test_source_questions_remain_in_inbox_after_revision_acceptance(editor_api):
    client, run, root = editor_api
    question = {
        "question_id": "source_doubt",
        "kind": "relation_check",
        "title": "Is this relation supported?",
        "source": [{"segment_id": "p1.b1", "page": 1, "text": "Noise means wear"}],
        "proposal": ["Noise means wear"],
        "default_option_id": "accept",
        "options": [{"option_id": value, "label": value, "effect": value} for value in ("accept", "reject", "correct")],
    }
    state = run / "state"
    state.mkdir()
    gate = {"questions": [question], "pending": ["source_doubt"], "answers": []}
    (state / "gate_doubts.json").write_text(json.dumps(gate))
    (run / "report.json").write_text(json.dumps({"status": "awaiting_approval"}))
    original = (state / "gate_doubts.json").read_bytes()
    body = accept_body(client)
    created = client.post(PATH + "/revisions", json=body)
    assert created.status_code == 201, created.text
    path = "/api/manuals/pump/versions/" + created.json()["version"]["version_id"]
    assert client.get(path + "/editor").json()["source_review"]["questions"][0]["question_id"] == "source_doubt"
    row = client.get("/api/manuals").json()[0]
    assert row["latest"]["kind"] == "revision"
    assert row["activities"][0]["version_id"] == "runs~v3_r1"
    assert row["activities"][0]["open_questions"] == 1
    assert (state / "gate_doubts.json").read_bytes() == original


def test_catalog_separates_human_confirmation_rejection_and_verification(editor_api):
    client, _, _ = editor_api
    body = input_body(client)
    p = client.post(PATH + "/validate-edits", json=body).json()
    occurrence = p["graph"]["edges"][0]["occurrences"][0]
    for decision, request in (("confirm", "request_confirm_count"), ("reject", "request_reject_count")):
        proposal = {
            **body,
            "operations": body["operations"]
            + [
                {
                    "op": "occurrence." + decision,
                    "edge_id": "edge",
                    "occurrence_id": occurrence["id"],
                    "content_hash": occurrence["content_hash"],
                    "reason": "test",
                }
            ],
        }
        preview = client.post(PATH + "/validate-edits", json=proposal).json()
        result = client.post(
            PATH + "/revisions",
            json={
                **proposal,
                "request_id": request,
                "preview_hash": preview["preview_hash"],
                "acceptance": {
                    "decision": "accept_changes",
                    "acknowledged_issue_ids": preview["required_acknowledgements"],
                },
            },
        )
        assert result.status_code == 201, result.text
        version = result.json()["version"]
        assert version["verified"] == 0 and version["doubtful"] == 0
        assert version["human_confirmed"] == (1 if decision == "confirm" else 0)
        assert version["rejected"] == (1 if decision == "reject" else 0)


def test_editor_capabilities_do_not_resume_runs_or_require_pdf(editor_api):
    client, run, root = editor_api
    current = client.get(PATH + "/editor").json()
    assert current["capabilities"]["can_edit"]
    assert not current["source"]["pdf_available"]
    (run / "people.json").write_text(
        json.dumps(
            {
                "answers": {
                    "q": {
                        "question_id": "q",
                        "option_id": "accept",
                        "answered_by": {"kind": "human", "name": "operator"},
                    }
                }
            }
        )
    )
    blocked = client.get(PATH + "/editor").json()
    assert blocked["capabilities"]["edit_reason"] == "UNAPPLIED_ANSWERS"
    assert not blocked["capabilities"]["can_edit"]
    assert not (root / "workspace").exists()
    (run / "people.json").unlink()
    (run / "graph.json").write_text(json.dumps({"version": "unsupported"}))
    version = client.get("/api/manuals/pump").json()["versions"][0]
    assert not version["can_edit"] and version["edit_reason"] == "GRAPH_UNAVAILABLE"
    assert client.get(PATH + "/editor").status_code == 422
