from __future__ import annotations

import json
import sqlite3

from backend.adapters import pdf as pdf_adapter
from backend.services import pdf_auto_preparation
from backend.storage.database import operational_db_path
from tests.planned.source_fixtures import upload_pdf


def _legacy_prepared_source(foundation_client, machine_payload, monkeypatch):
    current_version = pdf_adapter.ADAPTER_VERSION
    assert current_version == "pdf-v3"
    monkeypatch.setattr(pdf_adapter, "ADAPTER_VERSION", "pdf-v2")
    monkeypatch.setattr(pdf_auto_preparation, "ADAPTER_VERSION", "pdf-v2")

    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    response = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "legacy-layout-manual.pdf",
        "Troubleshooting alarm E17. Inspect the drive cable and reconnect it.",
    )
    assert response.status_code == 200
    source = response.json()["source"]
    preparation = response.json()["preparation"]
    assert preparation["adapter_version"] == "pdf-v2"
    assert preparation["scope_version"] == 1

    monkeypatch.setattr(pdf_adapter, "ADAPTER_VERSION", current_version)
    monkeypatch.setattr(pdf_auto_preparation, "ADAPTER_VERSION", current_version)
    return workspace, source, preparation


def _source_counts(source_id: str) -> dict[str, int]:
    with sqlite3.connect(operational_db_path()) as connection:
        return {
            "raw_units": connection.execute(
                "SELECT COUNT(*) FROM raw_units WHERE source_id = ?", (source_id,)
            ).fetchone()[0],
            "evidence_units": connection.execute(
                "SELECT COUNT(*) FROM evidence_units WHERE source_id = ?", (source_id,)
            ).fetchone()[0],
            "scopes": connection.execute(
                "SELECT COUNT(*) FROM pdf_scopes WHERE source_id = ?", (source_id,)
            ).fetchone()[0],
            "runs": connection.execute(
                """
                SELECT COUNT(*)
                FROM runs r JOIN run_sources rs ON rs.run_id = r.run_id
                WHERE rs.source_id = ?
                """,
                (source_id,),
            ).fetchone()[0],
        }


def test_obsolete_pdf_inventory_is_regenerated_without_deleting_history(
    foundation_client,
    machine_payload,
    monkeypatch,
) -> None:
    workspace, source, legacy = _legacy_prepared_source(
        foundation_client, machine_payload, monkeypatch
    )
    source_id = source["source_id"]

    with sqlite3.connect(operational_db_path()) as connection:
        old_raw_ids = {
            row[0]
            for row in connection.execute(
                "SELECT raw_unit_id FROM raw_units WHERE source_id = ? AND adapter_version = 'pdf-v2'",
                (source_id,),
            )
        }
        old_evidence_ids = {
            row[0]
            for row in connection.execute(
                "SELECT evidence_id FROM evidence_units WHERE source_id = ?", (source_id,)
            )
        }
    assert old_raw_ids
    assert old_evidence_ids

    migrated_response = foundation_client.get(f"/api/sources/{source_id}/pdf/preparation")
    assert migrated_response.status_code == 200
    migrated = migrated_response.json()
    assert migrated["adapter_version"] == "pdf-v3"
    assert migrated["scope_version"] == 2
    assert migrated["scope_id"] != legacy["scope_id"]
    assert migrated["run_id"] != legacy["run_id"]
    assert migrated["balanced"] is True
    assert migrated["unclassified_total"] == 0

    with sqlite3.connect(operational_db_path()) as connection:
        connection.row_factory = sqlite3.Row
        raw_rows = connection.execute(
            "SELECT raw_unit_id, adapter_version FROM raw_units WHERE source_id = ?",
            (source_id,),
        ).fetchall()
        current_raw_ids = {
            row["raw_unit_id"] for row in raw_rows if row["adapter_version"] == "pdf-v3"
        }
        assert old_raw_ids.issubset({row["raw_unit_id"] for row in raw_rows})
        assert current_raw_ids
        assert old_raw_ids.isdisjoint(current_raw_ids)

        evidence_rows = connection.execute(
            "SELECT evidence_id, payload_json FROM evidence_units WHERE source_id = ?",
            (source_id,),
        ).fetchall()
        persisted_versions = {
            json.loads(row["payload_json"])["ingestion"]["adapter_version"]
            for row in evidence_rows
        }
        assert persisted_versions == {"pdf-v2", "pdf-v3"}
        assert old_evidence_ids.issubset({row["evidence_id"] for row in evidence_rows})

        scopes = connection.execute(
            "SELECT scope_id, supersedes FROM pdf_scopes WHERE source_id = ? ORDER BY version",
            (source_id,),
        ).fetchall()
        assert [row["scope_id"] for row in scopes] == [legacy["scope_id"], migrated["scope_id"]]
        assert scopes[1]["supersedes"] == legacy["scope_id"]
        old_run_state = connection.execute(
            "SELECT state FROM runs WHERE run_id = ?", (legacy["run_id"],)
        ).fetchone()[0]
        assert old_run_state == "superseded"

    active_evidence = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source_id},
    ).json()
    assert active_evidence
    assert {
        item["ingestion"]["adapter_version"] for item in active_evidence
    } == {"pdf-v3"}
    assert old_evidence_ids.isdisjoint({item["evidence_id"] for item in active_evidence})

    accounting = foundation_client.get(
        f"/api/foundation/runs/{migrated['run_id']}/accounting"
    ).json()
    obsolete_rows = [
        item for item in accounting["raw_units"] if item["adapter_version"] == "pdf-v2"
    ]
    assert obsolete_rows
    assert all(item["disposition"]["outcome"] == "excluded" for item in obsolete_rows)
    assert all(
        item["disposition"]["reason_code"] == "PDF_ADAPTER_VERSION_OBSOLETE"
        for item in obsolete_rows
    )


def test_current_pdf_preparation_is_idempotent_after_migration(
    foundation_client,
    machine_payload,
    monkeypatch,
) -> None:
    _, source, _ = _legacy_prepared_source(foundation_client, machine_payload, monkeypatch)
    source_id = source["source_id"]
    first = foundation_client.get(f"/api/sources/{source_id}/pdf/preparation").json()
    before = _source_counts(source_id)

    def unexpected_inspection(*args, **kwargs):
        raise AssertionError("A current balanced preparation must not re-read the PDF")

    monkeypatch.setattr(pdf_adapter.PdfAdapter, "inspect", unexpected_inspection)
    second_response = foundation_client.get(f"/api/sources/{source_id}/pdf/preparation")

    assert second_response.status_code == 200
    assert second_response.json() == first
    assert _source_counts(source_id) == before
