from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor

from backend.adapters.pdf import PdfAdapter
from backend.services.pdf_auto_preparation import PdfAutoPreparationService
from backend.storage.database import operational_db_path
from backend.storage.raw_store import RawStore
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.raw_units import RawUnitRepository
from backend.storage.repositories.sources import SourceRepository
from backend.storage.repositories.workspaces import WorkspaceRepository
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
    assert source["status"] == "accepted"
    assert source["active_assessment"]["reason_codes"] == [
        "OPERATOR_SELECTED_SUPPORTED_FILE"
    ]
    reopened = foundation_client.get("/api/workspace").json()
    assert reopened["workspace"]["asset"]["asset_id"] == workspace["asset"]["asset_id"]


def test_g1_workspace_home_lists_and_reopens_the_current_workspace(
    foundation_client,
    machine_payload,
):
    assert foundation_client.get("/api/workspaces").json() == []
    workspace = _workspace(foundation_client, machine_payload)
    uploaded = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "home-manual.pdf",
        "Hydraulic press maintenance instructions",
    )
    assert uploaded.status_code == 200

    home = foundation_client.get("/api/workspaces")
    assert home.status_code == 200
    assert home.json() == [
        {
            "workspace_id": workspace["workspace_id"],
            "asset_name": "Hydraulic Press 7",
            "brand": "ExampleWorks",
            "model": "HP-700",
            "status": "awaiting_review",
            "document_count": 1,
            "updated_at": uploaded.json()["source"]["created_at"],
        }
    ]

    reopened = foundation_client.get(f"/api/workspaces/{workspace['workspace_id']}")
    assert reopened.status_code == 200
    assert reopened.json()["workspace"]["workspace_id"] == workspace["workspace_id"]
    assert reopened.json()["resumed"] is True
    assert foundation_client.get("/api/workspaces/ws_missing").status_code == 404


def test_g1_workspace_home_can_create_a_second_workspace(
    foundation_client,
    machine_payload,
):
    first = _workspace(foundation_client, machine_payload)
    second_payload = {
        **machine_payload,
        "asset": {
            **machine_payload["asset"],
            "name": "Conveyor 2",
            "description": "Packaging conveyor in production line two.",
            "model": "CV-200",
        },
        "identifiers": [
            {
                "namespace": "manufacturer_serial",
                "value": "CV2-0007",
                "kind": "serial",
            }
        ],
    }
    created = foundation_client.post("/api/workspaces", json=second_payload)
    assert created.status_code == 201
    assert created.json()["resumed"] is False
    second = created.json()["workspace"]
    assert second["workspace_id"] != first["workspace_id"]
    assert second["asset"]["name"] == "Conveyor 2"

    home = foundation_client.get("/api/workspaces").json()
    assert {item["workspace_id"] for item in home} == {
        first["workspace_id"],
        second["workspace_id"],
    }
    assert {item["document_count"] for item in home} == {0}
    assert foundation_client.get("/api/workspace").json()["workspace"]["workspace_id"] == first[
        "workspace_id"
    ]


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
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"]["title"] == "Documento già caricato"
    assert second.json()["detail"]["technical_detail"].startswith(
        "DUPLICATE_SOURCE_SHA256 "
    )
    raw_files = [item for item in (tmp_path / "raw").rglob("*") if item.is_file()]
    assert len(raw_files) == 1
    source_id = first.json()["source"]["source_id"]
    first_preparation = first.json()["preparation"]
    assert first_preparation["mode"] == "automatic_all_pages"
    assert first_preparation["page_count"] == 1
    assert first_preparation["included_page_count"] == 1
    assert first_preparation["excluded_page_count"] == 0
    assert first_preparation["scope_version"] == 1
    assert first_preparation["balanced"] is True
    assert first_preparation["unclassified_total"] == 0
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source_id},
    ).json()
    assert len({item["evidence_id"] for item in evidence}) == len(evidence)
    assert foundation_client.post(f"/api/sources/{source_id}/pdf/scope", json={}).status_code == 405


def test_g1_uploads_multiple_pdfs_and_csvs_without_manual_gates(
    foundation_client,
    machine_payload,
):
    workspace = _workspace(foundation_client, machine_payload)
    workspace_id = workspace["workspace_id"]
    uploads = [
        ("manual-a.pdf", pdf_bytes("Pump inspection procedure A"), "application/pdf"),
        ("manual-b.pdf", pdf_bytes("Motor inspection procedure B"), "application/pdf"),
        ("events-a.csv", b"timestamp,event\n2026-01-01,inspection-a\n", "text/csv"),
        ("events-b.csv", b"timestamp,event\n2026-01-02,inspection-b\n", "text/csv"),
    ]
    registrations = []
    for file_name, payload, media_type in uploads:
        response = foundation_client.post(
            f"/api/workspaces/{workspace_id}/sources",
            data={"authority": "operational"},
            files={"file": (file_name, payload, media_type)},
        )
        assert response.status_code == 200
        registrations.append(response.json())

    assert len({item["source"]["source_id"] for item in registrations}) == 4
    pdf_preparations = [item["preparation"] for item in registrations[:2]]
    assert all(item["mode"] == "automatic_all_pages" for item in pdf_preparations)
    assert all(item["page_count"] == item["included_page_count"] == 1 for item in pdf_preparations)
    assert all(item["excluded_page_count"] == 0 for item in pdf_preparations)
    assert all(item["balanced"] is True for item in pdf_preparations)
    assert all(item["preparation"] is None for item in registrations[2:])
    inventory = foundation_client.get(f"/api/workspaces/{workspace_id}/sources").json()
    assert len([item for item in inventory if item["source_kind"] != "operator_input"]) == 4


def test_g1_repeated_pdf_upload_is_concurrent_and_idempotent(
    foundation_client,
    machine_payload,
):
    workspace = _workspace(foundation_client, machine_payload)
    workspace_id = workspace["workspace_id"]
    payload = pdf_bytes("Concurrent automatic preparation")

    def upload_once():
        return foundation_client.post(
            f"/api/workspaces/{workspace_id}/sources",
            data={"authority": "operational"},
            files={"file": ("same.pdf", payload, "application/pdf")},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: upload_once(), range(2)))

    assert sorted(response.status_code for response in responses) == [200, 409]
    registration = next(response.json() for response in responses if response.status_code == 200)
    duplicate = next(response.json() for response in responses if response.status_code == 409)
    assert registration["preparation"]["scope_version"] == 1
    assert duplicate["detail"]["title"] == "Documento già caricato"
    inventory = foundation_client.get(f"/api/workspaces/{workspace_id}/sources").json()
    assert len([item for item in inventory if item["source_kind"] != "operator_input"]) == 1


def test_g1_restore_reuses_legacy_pdf_inventory_without_reparsing(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace_payload = _workspace(foundation_client, machine_payload)
    workspace_id = workspace_payload["workspace_id"]
    payload = pdf_bytes("Legacy persisted PDF inventory")
    original_prepare = PdfAutoPreparationService.prepare
    monkeypatch.setattr(PdfAutoPreparationService, "prepare", lambda self, **kwargs: None)
    uploaded = foundation_client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": "normative"},
        files={"file": ("legacy.pdf", payload, "application/pdf")},
    )
    assert uploaded.status_code == 200
    source_id = uploaded.json()["source"]["source_id"]

    workspace = WorkspaceRepository().get()
    source = SourceRepository().get(source_id)
    adapter_result = PdfAdapter().inspect(
        path=RawStore().resolve(source.raw_relpath or ""),
        workspace=workspace,
        source=source,
        scope_version=1,
    )
    RawUnitRepository().register_inventory(adapter_result.raw_units)
    EvidenceRepository().save_scope(
        workspace_id=workspace_id,
        source_id=source_id,
        included_pages=[1],
        excluded_pages={},
        operator="legacy-operator",
        evidence_units=adapter_result.evidence_units,
    )
    assert foundation_client.delete(f"/api/sources/{source_id}").status_code == 204

    monkeypatch.setattr(PdfAutoPreparationService, "prepare", original_prepare)

    def unexpected_reparse(*args, **kwargs):
        raise AssertionError("Persisted PDF inventory must be reused on restore")

    monkeypatch.setattr(PdfAdapter, "inspect", unexpected_reparse)
    restored = foundation_client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": "normative"},
        files={"file": ("legacy.pdf", payload, "application/pdf")},
    )
    assert restored.status_code == 200
    assert restored.json()["source"]["source_id"] == source_id
    assert restored.json()["preparation"]["page_count"] == 1
    assert restored.json()["preparation"]["scope_version"] == 2
    assert restored.json()["preparation"]["balanced"] is True


def test_ac_ws_005(foundation_client, machine_payload):
    workspace = _workspace(foundation_client, machine_payload)
    workspace_id = workspace["workspace_id"]
    uploads = [
        ("manual.pdf", pdf_bytes("Any maintenance document"), "application/pdf"),
        ("events.csv", b"timestamp,event\n2026-01-01,inspection\n", "text/csv"),
        ("notes.json", b'{"note":"bearing replaced"}', "application/json"),
    ]
    sources = []
    for file_name, payload, media_type in uploads:
        response = foundation_client.post(
            f"/api/workspaces/{workspace_id}/sources",
            data={"authority": "operational"},
            files={"file": (file_name, payload, media_type)},
        )
        assert response.status_code == 200
        sources.append(response.json()["source"])

    assert {source["status"] for source in sources} == {"accepted"}
    assert {
        source["active_assessment"]["reason_codes"][0]
        for source in sources
    } == {"OPERATOR_SELECTED_SUPPORTED_FILE"}

    removed = foundation_client.delete(f"/api/sources/{sources[1]['source_id']}")
    assert removed.status_code == 204
    inventory = foundation_client.get(f"/api/workspaces/{workspace_id}/sources").json()
    assert {item["file_name"] for item in inventory if item["source_kind"] != "operator_input"} == {
        "manual.pdf",
        "notes.json",
    }
    assert foundation_client.get(f"/api/sources/{sources[1]['source_id']}/content").status_code == 404

    restored = foundation_client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": "operational"},
        files={"file": uploads[1]},
    )
    assert restored.status_code == 200
    assert restored.json()["source"]["status"] == "accepted"
    assert restored.json()["source"]["source_id"] == sources[1]["source_id"]
    inventory = foundation_client.get(f"/api/workspaces/{workspace_id}/sources").json()
    assert len([item for item in inventory if item["source_kind"] != "operator_input"]) == 3
