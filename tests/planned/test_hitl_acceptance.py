from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.domain.runs import RunState
from backend.storage.database import operational_db_path
from backend.storage.repositories.operational_runs import OperationalRunRepository
from tests.planned.source_fixtures import upload_pdf


def test_ac_hitl_004(foundation_client, machine_payload):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "restart.pdf",
        "SERIAL: HP7-000042\nInspect the pressure relief valve.",
    ).json()["source"]
    payload = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    ).json()
    run_id = payload["run"]["run_id"]

    from backend.main import create_app

    restarted = TestClient(create_app())
    restored = restarted.get(
        f"/api/foundation/runs/{run_id}/accounting"
    )
    assert restored.status_code == 200
    assert restored.json()["balanced"] is True
    assert restored.json()["run_state"] == "awaiting_review"
    assert restarted.get("/api/workspace").json()["workspace"]["status"] == "awaiting_review"


def test_i06_run_transition_guards_service_and_database(
    foundation_client,
    machine_payload,
):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "states.pdf",
        "SERIAL: HP7-000042\nState transition fixture.",
    ).json()["source"]
    payload = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    ).json()
    run_id = payload["run"]["run_id"]
    with pytest.raises(ValueError, match="Invalid run transition"):
        OperationalRunRepository().transition(run_id, RunState.PUBLISHED)

    with sqlite3.connect(operational_db_path()) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="invalid Run state transition"):
            connection.execute(
                "UPDATE runs SET state = 'published' WHERE run_id = ?",
                (run_id,),
            )
