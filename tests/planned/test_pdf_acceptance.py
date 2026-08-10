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
    preparation = foundation_client.get(
        f"/api/sources/{source['source_id']}/pdf/preparation"
    )
    assert preparation.status_code == 200
    assert preparation.json()["mode"] == "automatic_all_pages"
    assert preparation.json()["page_count"] == preparation.json()["included_page_count"] == 1
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source["source_id"]},
    ).json()
    assert evidence
    assert all(item["workspace_id"] == workspace["workspace_id"] for item in evidence)


def test_ac_pdf_002(foundation_client, machine_payload):
    workspace, source = _prepared_source(foundation_client, machine_payload)
    assert foundation_client.get("/api/workspace").json()["workspace"]["status"] == "awaiting_review"
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source["source_id"]},
    ).json()
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
    workspace, source = _prepared_source(foundation_client, machine_payload, two_pages=True)
    source_id = source["source_id"]
    first = foundation_client.get(f"/api/sources/{source_id}/pdf/preparation").json()
    assert first["page_count"] == first["included_page_count"] == 2
    assert first["excluded_page_count"] == 0
    assert first["scope_version"] == 1
    second = foundation_client.get(f"/api/sources/{source_id}/pdf/preparation").json()
    assert second == first
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source_id},
    ).json()
    assert {item["locator"]["page"] for item in evidence} == {1, 2}
    assert foundation_client.get(f"/api/sources/{source_id}/pdf/preview").status_code == 404
    assert foundation_client.post(f"/api/sources/{source_id}/pdf/scope", json={}).status_code == 405


def test_i03_evidence_bridge_keeps_pdf_dependency_inside_adapter(
    foundation_client,
    machine_payload,
):
    workspace, source = _prepared_source(foundation_client, machine_payload)
    evidence_payload = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source["source_id"]},
    ).json()
    from backend.domain.evidence import EvidenceUnit

    evidence = [EvidenceUnit.model_validate(item) for item in evidence_payload]
    projected = evidence_units_to_legacy_pages(evidence)
    assert projected[0]["page_number"] == 1
    assert "Troubleshooting" in projected[0]["text"]
    assert "source_page" not in evidence_payload[0]


def test_i03_evidence_bridge_reconstructs_block_order_and_emits_stable_anchors(
    foundation_client,
    machine_payload,
):
    workspace, source = _prepared_source(foundation_client, machine_payload)
    payload = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source["source_id"]},
    ).json()
    from backend.domain.evidence import EvidenceUnit

    base = EvidenceUnit.model_validate(payload[0])

    def block(evidence_id: str, block_index: int, text: str):
        locator = base.locator.model_copy(update={
            "quote": text,
            "block_index": block_index,
            "table_index": None,
            "row_index": None,
            "ocr_region_index": None,
        })
        content = base.content.model_copy(update={
            "observation": text,
            "semantic_texts": {"observation": text},
        })
        return base.model_copy(update={
            "evidence_id": evidence_id,
            "locator": locator,
            "content": content,
        })

    projected = evidence_units_to_legacy_pages([
        block("ev_cccccccccccc", 2, "Third physical block"),
        block("ev_aaaaaaaaaaaa", 0, "First physical block"),
        block("ev_bbbbbbbbbbbb", 1, "Second physical block"),
    ])
    text = projected[0]["text"]

    assert text.index("First physical block") < text.index("Second physical block")
    assert text.index("Second physical block") < text.index("Third physical block")
    assert projected[0]["evidence_anchors"] == [
        "ev_aaaaaaaaaaaa",
        "ev_bbbbbbbbbbbb",
        "ev_cccccccccccc",
    ]
    assert "[[EVIDENCE_ID: ev_aaaaaaaaaaaa]]" in text


def test_i03_evidence_ids_are_cross_type_registered(foundation_client, machine_payload):
    workspace, source = _prepared_source(foundation_client, machine_payload)
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source["source_id"]},
    ).json()
    ids = {item["evidence_id"] for item in evidence}
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
                f"/api/workspaces/{workspace['workspace_id']}/evidence"
            ).json()
        }
    )


def test_ac_pdf_004(foundation_client, machine_payload, monkeypatch):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
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
    uploaded = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/sources",
        data={"authority": "normative"},
        files={"file": (G1_FIXTURE.name, G1_FIXTURE.read_bytes(), "application/pdf")},
    )
    assert uploaded.status_code == 200
    source = uploaded.json()["source"]
    preparation = uploaded.json()["preparation"]
    assert preparation["page_count"] == preparation["included_page_count"] == 5
    report = foundation_client.get(
        f"/api/foundation/runs/{preparation['run_id']}/accounting"
    ).json()
    raw_units = report["raw_units"]
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
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence",
        params={"source_id": source["source_id"]},
    ).json()
    assert any(
        "OCR_LOW_CONFIDENCE" in item["quality_flags"]
        for item in evidence
        if item["locator"].get("ocr_region_index") == 1
    )
