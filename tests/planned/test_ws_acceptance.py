from __future__ import annotations

import sqlite3

from backend.storage.database import operational_db_path
from tests.planned.source_fixtures import pdf_bytes, upload_pdf


def test_i01_confirmed_asset_is_unique_and_resumable(foundation_client, machine_payload):
    created = foundation_client.post("/api/workspace", json=machine_payload)
    assert created.status_code == 201
    first = created.json()
    assert first["workspace"]["status"] == "sources_required"
    assert first["workspace"]["asset"]["name"] == "Hydraulic Press 7"
    assert first["workspace"]["ontology_sha256"] == (
        "81f2d894e8b4c3c0ba3bb2e7149941ae91b704ebd8a8b8dedef91b79bd1508db"
    )
    assert first["assertion"]["observation_basis"] == "nameplate"
    assert first["workspace"]["workspace_id"] != first["workspace"]["asset"]["asset_id"]
    assert first["workspace"]["created_at"].endswith("Z")

    reopened = foundation_client.get("/api/workspace")
    assert reopened.status_code == 200
    assert reopened.json()["workspace"]["workspace_id"] == first["workspace"]["workspace_id"]

    resumed = foundation_client.post("/api/workspace", json=machine_payload)
    assert resumed.status_code == 201
    assert resumed.json()["resumed"] is True
    assert resumed.json()["workspace"]["asset"]["asset_id"] == first["workspace"]["asset"]["asset_id"]

    changed = {**machine_payload, "asset": {**machine_payload["asset"], "model": "OTHER-1"}}
    conflict = foundation_client.post("/api/workspace", json=changed)
    assert conflict.status_code == 409


def test_i01_placeholder_fails_before_persistence(foundation_client, machine_payload):
    invalid = {**machine_payload, "asset": {**machine_payload["asset"], "brand": "unknown"}}
    response = foundation_client.post("/api/workspace", json=invalid)
    assert response.status_code == 422
    assert foundation_client.get("/api/workspace").json() is None


def test_i01_migration_and_cross_type_id_registry(foundation_client, machine_payload):
    response = foundation_client.post("/api/workspace", json=machine_payload)
    assert response.status_code == 201
    with sqlite3.connect(operational_db_path()) as connection:
        migrations = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        ids = connection.execute(
            "SELECT entity_id, entity_type FROM entity_ids"
        ).fetchall()
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    assert migrations[0] == ("001_operational_core",)
    assert ("001_source_registry",) in migrations
    assert len({entity_id for entity_id, _ in ids}) == len(ids)
    assert {
        "workspace",
        "asset",
        "assertion",
        "decision",
    }.issubset({entity_type for _, entity_type in ids})
    assert journal_mode == "wal"


def _workspace(foundation_client, machine_payload):
    response = foundation_client.post("/api/workspace", json=machine_payload)
    assert response.status_code == 201
    return response.json()["workspace"]


def test_ac_ws_001(foundation_client, machine_payload):
    workspace = _workspace(foundation_client, machine_payload)
    response = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "other-machine.pdf",
        "SERIAL: OTHER-999\nBRAND: OtherWorks\nMODEL: ZX-2",
    )
    assert response.status_code == 200
    source = response.json()["source"]
    assert source["status"] == "quarantined"
    assert source["active_assessment"]["outcome"] == "incompatible"
    reopened = foundation_client.get("/api/workspace").json()
    assert reopened["workspace"]["asset"]["asset_id"] == workspace["asset"]["asset_id"]


def test_ac_ws_004(foundation_client, machine_payload, tmp_path):
    workspace = _workspace(foundation_client, machine_payload)
    text = "SERIAL: HP7-000042\nBRAND: ExampleWorks\nMODEL: HP-700"
    payload = pdf_bytes(text)
    first = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/sources",
        data={"authority": "normative"},
        files={"file": ("manual.pdf", payload, "application/pdf")},
    )
    second = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/sources",
        data={"authority": "normative"},
        files={"file": ("manual-copy.pdf", payload, "application/pdf")},
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["source"]["source_id"] == second.json()["source"]["source_id"]
    assert second.json()["duplicate"] is True
    assert second.json()["raw_cache_hit"] is True
    raw_files = [item for item in (tmp_path / "raw").rglob("*") if item.is_file()]
    assert len(raw_files) == 1
    source_id = first.json()["source"]["source_id"]
    first_scope = foundation_client.post(
        f"/api/sources/{source_id}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    )
    second_scope = foundation_client.post(
        f"/api/sources/{source_id}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    )
    first_ids = {item["evidence_id"] for item in first_scope.json()["evidence_units"]}
    second_ids = {item["evidence_id"] for item in second_scope.json()["evidence_units"]}
    assert first_ids == second_ids
    assert len(second_ids) == len(second_scope.json()["evidence_units"])


def test_ac_ws_005(foundation_client, machine_payload):
    workspace = _workspace(foundation_client, machine_payload)
    workspace_id = workspace["workspace_id"]
    compatible = upload_pdf(
        foundation_client,
        workspace_id,
        "compatible.pdf",
        "SERIAL: HP7-000042\nBRAND: ExampleWorks\nMODEL: HP-700",
    ).json()["source"]
    uncertain = upload_pdf(
        foundation_client,
        workspace_id,
        "uncertain.pdf",
        "BRAND: ExampleWorks\nMODEL: HP-700\nApplicable to the HP family.",
    ).json()["source"]
    incompatible = upload_pdf(
        foundation_client,
        workspace_id,
        "incompatible.pdf",
        "SERIAL: HP9-999999\nBRAND: ExampleWorks\nMODEL: HP-900",
    ).json()["source"]

    assert compatible["active_assessment"]["outcome"] == "compatible"
    assert compatible["status"] == "accepted"
    assert uncertain["active_assessment"]["outcome"] == "uncertain"
    assert uncertain["status"] == "quarantined"
    assert incompatible["active_assessment"]["outcome"] == "incompatible"
    assert incompatible["status"] == "quarantined"
    assert all(
        claim["locator"]["quote"]
        for source in (compatible, uncertain, incompatible)
        for claim in source["active_assessment"]["observed_claims"]
    )

    blocked = foundation_client.post(
        f"/api/sources/{incompatible['source_id']}/assessment/resolve",
        json={
            "action": "confirm",
            "reason": "Operator wants to force this incompatible machine.",
            "observation_basis": "direct_observation",
            "operator": "FD",
            "evidence_seen": [incompatible["asset_assessment_id"]],
        },
    )
    assert blocked.status_code == 409

    resolved = foundation_client.post(
        f"/api/sources/{uncertain['source_id']}/assessment/resolve",
        json={
            "action": "confirm",
            "reason": "Applicability confirmed against the inspected machine nameplate.",
            "observation_basis": "nameplate",
            "operator": "FD",
            "evidence_seen": [uncertain["asset_assessment_id"]],
        },
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "accepted"
    assert resolved.json()["active_assessment"]["decided_by"]["operator_assertion_id"]

    reopened = foundation_client.post(
        f"/api/sources/{uncertain['source_id']}/assessment/reopen"
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "quarantined"
    assert reopened.json()["active_assessment"]["outcome"] == "uncertain"

    inventory = foundation_client.get(f"/api/workspaces/{workspace_id}/sources").json()
    uploaded_inventory = [item for item in inventory if item["source_kind"] != "operator_input"]
    assert len(uploaded_inventory) == 3
    assert {item["status"] for item in uploaded_inventory} == {"accepted", "quarantined"}
