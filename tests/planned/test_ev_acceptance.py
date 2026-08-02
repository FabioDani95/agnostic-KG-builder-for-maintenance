from __future__ import annotations

import sqlite3

import pytest

from backend.domain.evidence import EvidenceUnit
from backend.domain.runs import DispositionError, DispositionOutcome, Retryability
from backend.storage.database import operational_db_path
from backend.storage.repositories.raw_units import RawUnitRepository
from tests.planned.source_fixtures import upload_pdf


def test_g1_pdf_evidence_contract_support(foundation_client, machine_payload):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "manual.pdf",
        "SERIAL: HP7-000042\nPump vibration is resolved by tightening the coupling.",
    ).json()["source"]
    payload = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    ).json()
    units = [EvidenceUnit.model_validate(item) for item in payload["evidence_units"]]
    assert units
    assert all(item.eligible_for_semantic_processing for item in units)
    assert all(item.raw_ref.source_id == source["source_id"] for item in units)
    assert all(item.provenance_refs[0].raw_hash for item in units)


def test_i03_onboarding_assertion_is_operator_input_evidence(
    foundation_client,
    machine_payload,
):
    created = foundation_client.post("/api/workspace", json=machine_payload).json()
    workspace = created["workspace"]
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/evidence"
    ).json()
    operator_units = [item for item in evidence if item["source_kind"] == "operator_input"]
    assert len(operator_units) == 1
    assert operator_units[0]["record_role"] == "asset_master"
    assert operator_units[0]["locator"]["assertion_id"] == created["assertion"]["assertion_id"]
    assert operator_units[0]["locator"]["decision_id"] == created["assertion"]["decision_id"]


def test_ac_ev_001(foundation_client, machine_payload):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "ledger-manual.pdf",
        "SERIAL: HP7-000042\nInspect the coupling and reset motor alarm E017.",
    ).json()["source"]
    scoped = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    )
    assert scoped.status_code == 200
    payload = scoped.json()
    report = payload["accounting"]
    assert payload["run"]["state"] == "awaiting_review"
    assert report["balanced"] is True
    assert report["unclassified_total"] == 0
    source_report = report["sources"][0]
    assert source_report["inventory"] == source_report["classified"]
    assert source_report["top_level"]["inventory"] == 1
    assert source_report["top_level"]["balanced"] is True
    assert source_report["child_aggregate"]["balanced"] is True
    assert all(group["balanced"] for group in source_report["parent_groups"])
    assert payload["run"]["manifest"]["ledger_hash"] == report["ledger_hash"]

    endpoint = foundation_client.get(
        f"/api/foundation/runs/{payload['run']['run_id']}/accounting"
    )
    assert endpoint.status_code == 200
    assert endpoint.json()["ledger_hash"] == report["ledger_hash"]


def test_i06_disposition_retry_is_append_only(foundation_client, machine_payload):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "retry-ledger.pdf",
        "SERIAL: HP7-000042\nA deterministic maintenance instruction.",
    ).json()["source"]
    payload = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    ).json()
    raw_unit_id = payload["accounting"]["raw_units"][0]["raw_unit_id"]
    run_id = payload["run"]["run_id"]
    repository = RawUnitRepository()
    repository.append_disposition(
        run_id=run_id,
        raw_unit_id=raw_unit_id,
        outcome=DispositionOutcome.PROCESSED,
        reason_code="RETRY_PROCESSING_COMPLETED",
    )
    attempts = repository.dispositions_for(run_id, raw_unit_id)
    assert [item.attempt for item in attempts] == [1, 2]
    assert repository.accounting_report(run_id)["balanced"] is True

    with sqlite3.connect(operational_db_path()) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE raw_unit_dispositions SET reason_code = 'MUTATED' WHERE disposition_id = ?",
                (attempts[0].disposition_id,),
            )


def test_i08_accounting_separates_actionable_failure_retryability(
    foundation_client,
    machine_payload,
):
    workspace = foundation_client.post("/api/workspace", json=machine_payload).json()["workspace"]
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "actionable-failure.pdf",
        "SERIAL: HP7-000042\nInspect the hydraulic safety circuit.",
    ).json()["source"]
    payload = foundation_client.post(
        f"/api/sources/{source['source_id']}/pdf/scope",
        json={"included_pages": [1], "excluded_pages": {}, "operator": "FD"},
    ).json()
    raw_unit_id = payload["accounting"]["raw_units"][0]["raw_unit_id"]
    RawUnitRepository().append_disposition(
        run_id=payload["run"]["run_id"],
        raw_unit_id=raw_unit_id,
        outcome=DispositionOutcome.FAILED,
        reason_code="ADAPTER_TRANSIENT_FAILURE",
        retryability=Retryability.SAME_RUN,
        error=DispositionError(
            code="PDF_ADAPTER_TEMPORARY",
            title="Lettura temporaneamente interrotta",
            object_ref=raw_unit_id,
            cause="Il parser locale ha interrotto il tentativo corrente.",
            preserved="File originale, RawUnit e primo tentativo restano immutati.",
            action="Riprova la sola RawUnit dallo stesso run.",
            technical_detail="fixture failure injection",
        ),
    )
    report = foundation_client.get(
        f"/api/foundation/runs/{payload['run']['run_id']}/accounting"
    ).json()
    assert report["balanced"] is True
    assert len(report["attention"]["retryable_same_run"]) == 1
    assert report["attention"]["new_run_required"] == []
    assert report["attention"]["terminal_failures"] == []
    error = report["attention"]["retryable_same_run"][0]["disposition"]["error"]
    assert set(error) == {
        "code",
        "title",
        "object_ref",
        "cause",
        "preserved",
        "action",
        "technical_detail",
    }
