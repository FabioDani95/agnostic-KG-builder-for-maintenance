from __future__ import annotations

from pathlib import Path

import fitz

from backend.adapters.pdf import evidence_units_to_legacy_pages
from backend.services.pdf_service import extract_text_by_page
from backend.storage.database import operational_db_path
from tests.planned.source_fixtures import upload_pdf

REPO_ROOT = Path(__file__).resolve().parents[2]
G1_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "manuals" / "g1_pdf_inventory.pdf"
G1_MARKER = "G1_TABLE_5_ROW_61_MARKER"


def _prepared_source(foundation_client, machine_payload, *, two_pages: bool = False):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    if two_pages:
        document = fitz.open()
        document.new_page().insert_text((72, 72), "SERIAL: HP7-000042\nTroubleshooting motor alarm E017")
        document.new_page().insert_text((72, 72), "Unrelated warranty and legal notices")
        payload = document.tobytes()
        document.close()
        uploaded = foundation_client.post(
            f"/api/workspaces/{workspace['workspace_id']}/sources",
            data={"authority": "normative"},
            files={"file": ("manual.pdf", payload, "application/pdf")},
        )
    else:
        uploaded = upload_pdf(
            foundation_client,
            workspace["workspace_id"],
            "manual.pdf",
            "SERIAL: HP7-000042\nTroubleshooting: motor alarm E017. Reset the drive.",
        )
    assert uploaded.status_code == 200
    return workspace, uploaded.json()["source"]


def test_ac_pdf_001(foundation_client, machine_payload):
    workspace, source = _prepared_source(foundation_client, machine_payload)
    preview = foundation_client.get(f"/api/sources/{source['source_id']}/pdf/preview")
    assert preview.status_code == 200
    payload = preview.json()
    assert payload["pages"]
    assert payload["raw_units"]
    assert all(item["source_id"] == source["source_id"] for item in payload["raw_units"])
    assert workspace["workspace_id"] == payload["evidence_units"][0]["workspace_id"]


def test_ac_pdf_002(foundation_client, machine_payload):
    workspace, source = _prepared_source(foundation_client, machine_payload)
    scoped = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    )
    assert scoped.status_code == 200
    assert foundation_client.get("/api/workspace").json()["workspace"]["status"] == "awaiting_review"
    evidence = scoped.json()["evidence_units"]
    assert evidence
    for item in evidence:
        assert item["source_id"] == source["source_id"]
        assert item["locator"]["kind"] == "pdf"
        assert item["locator"]["page"] == 1
        assert item["locator"]["extraction_method"] in {"native_text", "ocr", "table"}
        assert item["locator"]["quote"]
        assert len(item["provenance_refs"]) == 1
        assert item["provenance_refs"][0]["role"] == "primary"
    listed = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source["source_id"]},
    )
    assert listed.json() == evidence


def test_ac_pdf_003(foundation_client, machine_payload):
    _, source = _prepared_source(foundation_client, machine_payload, two_pages=True)
    source_id = source["source_id"]
    first = foundation_client.post(
        f"/api/sources/{source_id}/pdf/scope",
        json={
            "included_pages": [1],
            "excluded_pages": {"2": "Non-maintenance legal notice"},
            "operator": "FD",
        },
    )
    assert first.status_code == 200
    assert {item["locator"]["page"] for item in first.json()["evidence_units"]} == {1}
    reopened = foundation_client.get(f"/api/sources/{source_id}/pdf/preview").json()
    assert reopened["current_scope"]["version"] == 1
    assert [item["included"] for item in reopened["pages"]] == [True, False]

    second = foundation_client.post(
        f"/api/sources/{source_id}/pdf/scope",
        json={"included_pages": [1, 2], "excluded_pages": {}, "operator": "FD"},
    )
    assert second.status_code == 200
    assert second.json()["current_scope"]["version"] == 2
    assert {item["locator"]["page"] for item in second.json()["evidence_units"]} == {1, 2}

    third = foundation_client.post(
        f"/api/sources/{source_id}/pdf/scope",
        json={
            "included_pages": [2],
            "excluded_pages": {"1": "Operator narrowed the troubleshooting scope"},
            "operator": "FD",
        },
    )
    assert third.status_code == 200
    assert third.json()["current_scope"]["version"] == 3
    assert {item["locator"]["page"] for item in third.json()["evidence_units"]} == {2}


def test_i03_evidence_bridge_keeps_pdf_dependency_inside_adapter(
    foundation_client,
    machine_payload,
):
    _, source = _prepared_source(foundation_client, machine_payload)
    evidence_payload = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    ).json()["evidence_units"]
    from backend.domain.evidence import EvidenceUnit

    evidence = [EvidenceUnit.model_validate(item) for item in evidence_payload]
    projected = evidence_units_to_legacy_pages(evidence)
    assert projected[0]["page_number"] == 1
    assert "Troubleshooting" in projected[0]["text"]
    assert "source_page" not in evidence_payload[0]


def test_i03_evidence_ids_are_cross_type_registered(foundation_client, machine_payload):
    _, source = _prepared_source(foundation_client, machine_payload)
    response = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    )
    ids = {item["evidence_id"] for item in response.json()["evidence_units"]}
    import sqlite3

    with sqlite3.connect(operational_db_path()) as connection:
        registered = {
            row[0]
            for row in connection.execute("SELECT entity_id FROM entity_ids WHERE entity_type = 'evidence'")
        }
    assert ids.issubset(registered)
    assert len(registered) == len(
        {
            row["evidence_id"]
            for row in foundation_client.get(
                f"/api/workspaces/{response.json()['evidence_units'][0]['workspace_id']}/evidence"
            ).json()
        }
    )


def test_ac_pdf_004(foundation_client, machine_payload, monkeypatch):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    uploaded = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/sources",
        data={"authority": "normative"},
        files={
            "file": (
                G1_FIXTURE.name,
                G1_FIXTURE.read_bytes(),
                "application/pdf",
            )
        },
    )
    assert uploaded.status_code == 200
    source = uploaded.json()["source"]
    assert source["status"] == "accepted"

    def low_confidence_fixture(path: str):
        pages = extract_text_by_page(path)
        pages[0].update(
            {
                "text_source": "ocr",
                "ocr_status": "applied",
                "ocr_confidence": 0.25,
                "ocr_regions": [
                    {
                        "text": "Uncertain OCR region: inspect motor alarm E017.",
                        "confidence": 0.25,
                    }
                ],
            }
        )
        return pages

    monkeypatch.setattr(
        "backend.adapters.pdf.extract_text_by_page",
        low_confidence_fixture,
    )
    preview = foundation_client.get(f"/api/sources/{source['source_id']}/pdf/preview")
    assert preview.status_code == 200
    raw_units = preview.json()["raw_units"]
    pages = [item for item in raw_units if item["unit_kind"] == "pdf_page"]
    tables = [item for item in raw_units if item["unit_kind"] == "table"]
    table_rows = [item for item in raw_units if item["unit_kind"] == "table_row"]
    ocr_regions = [item for item in raw_units if item["unit_kind"] == "ocr_region"]
    assert len(pages) == 5
    assert len(tables) == 5
    assert len(table_rows) == 77
    assert len(ocr_regions) == 1
    page_ids = {item["raw_unit_id"] for item in pages}
    assert all(
        item["parent_raw_unit_id"] in page_ids
        for item in raw_units
        if item["unit_kind"] != "pdf_page"
    )
    marker = [
        item
        for item in table_rows
        if G1_MARKER in item["locator"]["quote"]
    ]
    assert len(marker) == 1
    assert marker[0]["locator"]["page"] == 5
    assert marker[0]["locator"]["table_index"] == 5
    assert marker[0]["locator"]["row_index"] == 61
    assert "OCR_LOW_CONFIDENCE" in ocr_regions[0]["quality_flags"]

    scoped = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1, 2, 3, 4, 5], "excluded_pages": {}, "operator": "FD"},
    )
    assert scoped.status_code == 200
    payload = scoped.json()
    report = payload["accounting"]
    assert report["balanced"] is True
    assert report["unclassified_total"] == 0
    assert report["sources"][0]["top_level"]["inventory"] == 5
    assert report["sources"][0]["child_aggregate"]["balanced"] is True
    assert len(report["sources"][0]["parent_groups"]) == 5
    assert all(group["balanced"] for group in report["sources"][0]["parent_groups"])
    marker_ledger = [
        item for item in report["raw_units"] if G1_MARKER in item["locator"]["quote"]
    ]
    assert marker_ledger[0]["disposition"]["outcome"] == "processed"
    low_ocr_ledger = [
        item for item in report["raw_units"] if item["unit_kind"] == "ocr_region"
    ]
    assert low_ocr_ledger[0]["disposition"]["outcome"] == "quarantined"
    assert any(
        "OCR_LOW_CONFIDENCE" in item["quality_flags"]
        for item in payload["evidence_units"]
        if item["locator"].get("ocr_region_index") == 1
    )
