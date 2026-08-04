from __future__ import annotations

import csv
import io
import sqlite3
from pathlib import Path

from openpyxl import Workbook

from backend.storage.database import operational_db_path

HARDENING_FIXTURES = Path(__file__).parents[1] / "fixtures" / "csv_hardening"


def _workspace(client, machine_payload) -> str:
    response = client.post("/api/workspace", json=machine_payload)
    assert response.status_code == 201
    return response.json()["workspace"]["workspace_id"]


def _upload(client, workspace_id: str, name: str, payload: bytes, media_type: str):
    response = client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": "operational"},
        files={"file": (name, payload, media_type)},
    )
    assert response.status_code == 200, response.text
    return response.json()["source"]


def _start(client, workspace_id: str):
    response = client.post(f"/api/workspaces/{workspace_id}/g2/preparation")
    assert response.status_code == 200, response.text
    return response.json()


def _confirm(client, profile_id: str):
    response = client.post(f"/api/g2/profiles/{profile_id}/confirm")
    assert response.status_code == 200, response.text
    return response.json()


def test_g2_csv_is_automatic_idempotent_and_balanced(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload(
        foundation_client,
        workspace_id,
        "events.csv",
        (
            "event_timestamp,component,symptom_observation,diagnosis,action_taken,language\n"
            "2026-01-01T10:00:00Z,pump,noise,bearing wear,replaced bearing,EN\n"
            "2026-01-02T10:00:00Z,valve,leak,seal damage,replaced seal,IT\n"
        ).encode(),
        "text/csv",
    )
    first = _start(foundation_client, workspace_id)
    second = _start(foundation_client, workspace_id)

    assert first["mode"] == "automatic_with_exceptions"
    assert first["state"] == "ready"
    assert first["can_complete"] is True
    assert first["counts"]["records"] == 2
    assert first["counts"]["evidence"] == 2
    assert first["counts"]["open_exceptions"] == 0
    assert second["profiles"][0]["profile_id"] == first["profiles"][0]["profile_id"]
    assert second["profiles"][0]["run_id"] == first["profiles"][0]["run_id"]

    run_id = first["profiles"][0]["run_id"]
    accounting = foundation_client.get(f"/api/foundation/runs/{run_id}/accounting").json()
    assert accounting["balanced"] is True
    assert accounting["unclassified_total"] == 0
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": source["source_id"]}
    ).json()
    assert len(evidence) == 2
    assert evidence[0]["content"]["semantic_texts"]["symptom"]
    assert evidence[0]["provenance_refs"][0]["locator"]["kind"] == "table_row"

    completed = _confirm(foundation_client, first["profiles"][0]["profile_id"])
    assert completed["completed"] is True
    assert completed["profiles"][0]["confirmed"] is True
    assert foundation_client.get(
        f"/api/workspaces/{workspace_id}/g2/preparation"
    ).json()["completed"] is True


def test_g2_csv_detects_semicolon_and_preserves_latin1(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload(
        foundation_client,
        workspace_id,
        "eventi-latin1.csv",
        (
            "event_timestamp;component;symptom_observation;action_taken;language\n"
            "2026-01-01T10:00:00Z;pompa;temperatura è alta;pulita valvola;IT\n"
        ).encode("latin-1"),
        "text/csv",
    )
    result = _start(foundation_client, workspace_id)
    assert result["state"] == "ready"
    assert result["counts"]["records"] == 1
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": source["source_id"]}
    ).json()
    assert evidence[0]["content"]["observation"] == "temperatura è alta"
    assert evidence[0]["language"]["qualification"] == "unqualified_it"


def test_g2_csv_preserves_standard_escaped_quotes_when_sniffer_disables_doublequote(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    class FalseDoubleQuoteDialect(csv.Dialect):
        delimiter = ";"
        quotechar = '"'
        escapechar = None
        doublequote = False
        skipinitialspace = False
        lineterminator = "\n"
        quoting = csv.QUOTE_MINIMAL

    monkeypatch.setattr(
        "backend.adapters.structured.csv_adapter.csv.Sniffer.sniff",
        lambda *_args, **_kwargs: FalseDoubleQuoteDialect,
    )
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload(
        foundation_client,
        workspace_id,
        "escaped-quotes.csv",
        (
            "event_timestamp;component;symptom_observation;diagnosis;action_taken;data_integrity_record\n"
            '"2026-01-01T10:00:00Z";"pump";"noise";"bearing wear";"replaced bearing";'
            '"Anzeige ""Wert instabil""; HMI marker"\n'
        ).encode(),
        "text/csv",
    )
    result = _start(foundation_client, workspace_id)

    assert result["state"] == "ready"
    assert result["counts"]["records"] == 1
    assert result["counts"]["evidence"] == 1
    assert result["counts"]["isolated_records"] == 0
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": source["source_id"]}
    ).json()
    assert evidence[0]["attributes"]["data_integrity_record"] == 'Anzeige "Wert instabil"; HMI marker'


def test_g2_csv_isolates_short_and_long_rows(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    _upload(
        foundation_client,
        workspace_id,
        "righe-irregolari.csv",
        (
            "event_id,symptom_observation,action_taken\n"
            "E1,noise,inspect\n"
            "E2,leak\n"
            "E3,heat,cool,unexpected\n"
        ).encode(),
        "text/csv",
    )
    result = _start(foundation_client, workspace_id)
    warning = next(
        item for item in result["exceptions"]
        if item["exception_kind"] == "csv_row_shape_mismatch"
    )
    assert result["state"] == "ready"
    assert warning["status"] == "acknowledged"
    assert warning["payload"]["total"] == 2
    assert result["counts"]["records"] == 3
    assert result["counts"]["evidence"] == 1
    assert result["counts"]["isolated_records"] == 2
    accounting = foundation_client.get(
        f"/api/foundation/runs/{result['profiles'][0]['run_id']}/accounting"
    ).json()
    assert accounting["balanced"] is True
    assert len(accounting["attention"]["terminal_failures"]) == 2
    assert {
        item["disposition"]["reason_code"]
        for item in accounting["raw_units"]
        if item["disposition"]["outcome"] == "failed"
    } == {"CSV_COLUMN_COUNT_MISMATCH"}


def test_g2_binary_csv_is_blocked_without_affecting_the_workspace(
    foundation_client,
    machine_payload,
):
    workspace_id = _workspace(foundation_client, machine_payload)
    valid_source = _upload(
        foundation_client,
        workspace_id,
        "valido.csv",
        b"symptom_observation,action_taken\nnoise,inspect bearing\n",
        "text/csv",
    )
    _upload(
        foundation_client,
        workspace_id,
        "corrotto.csv",
        b"\x00\xff\x00\xfe\x00\x01\x00\x02" * 20,
        "text/csv",
    )
    result = _start(foundation_client, workspace_id)
    issue = next(
        item for item in result["exceptions"]
        if item["exception_kind"] == "csv_decode_blocked"
    )
    assert result["state"] == "needs_attention"
    assert issue["status"] == "open"
    assert result["counts"]["evidence"] == 1
    valid_profile = next(
        item for item in result["profiles"] if item["source_id"] == valid_source["source_id"]
    )
    assert valid_profile["state"] == "prepared"


def test_g2_mapping_opens_only_one_decision_then_resumes(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload(
        foundation_client,
        workspace_id,
        "ambiguous.csv",
        b"event_id,description\nE-1,abnormal pump vibration\nE-2,valve leakage\n",
        "text/csv",
    )
    started = _start(foundation_client, workspace_id)
    open_issues = [item for item in started["exceptions"] if item["status"] == "open"]
    assert started["state"] == "needs_attention"
    assert len(open_issues) == 1
    assert open_issues[0]["exception_kind"] == "mapping_ambiguous"

    resolved = foundation_client.post(
        f"/api/g2/exceptions/{open_issues[0]['exception_id']}/resolve",
        json={"role": "observation"},
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["state"] == "ready"
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": source["source_id"]}
    ).json()
    assert {item["content"]["observation"] for item in evidence} == {
        "abnormal pump vibration",
        "valve leakage",
    }


def test_g2_jsonl_isolates_only_the_malformed_line(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    _upload(
        foundation_client,
        workspace_id,
        "observations.jsonl",
        (
            '{"event_id":"A","symptom_observation":"noise","action_taken":"inspect"}\n'
            '{"event_id":"BROKEN","symptom_observation":\n'
            '{"event_id":"B","symptom_observation":"heat","action_taken":"cool"}\n'
        ).encode(),
        "application/x-ndjson",
    )
    result = _start(foundation_client, workspace_id)
    warning = next(item for item in result["exceptions"] if item["exception_kind"] == "malformed_jsonl_line")

    assert result["state"] == "ready"
    assert warning["status"] == "acknowledged"
    assert warning["payload"]["line"] == 2
    assert result["counts"]["records"] == 3
    assert result["counts"]["evidence"] == 2
    assert result["counts"]["isolated_records"] == 1
    accounting = foundation_client.get(
        f"/api/foundation/runs/{result['profiles'][0]['run_id']}/accounting"
    ).json()
    assert accounting["balanced"] is True
    assert len(accounting["attention"]["terminal_failures"]) == 1
    malformed = next(item for item in accounting["raw_units"] if item["locator"].get("line") == 2)
    assert malformed["disposition"]["outcome"] == "failed"


def test_g2_xlsx_inventories_hidden_sheet_and_formula_without_cache(
    foundation_client,
    machine_payload,
):
    workspace_id = _workspace(foundation_client, machine_payload)
    workbook = Workbook()
    visible = workbook.active
    visible.title = "Events"
    visible.append(["event_id", "symptom_observation"])
    visible.append(["A", "normal row"])
    visible.append(["B", "=A2"])
    hidden = workbook.create_sheet("Archive")
    hidden.append(["event_id", "symptom_observation"])
    hidden.append(["OLD", "archived row"])
    hidden.sheet_state = "hidden"
    payload = io.BytesIO()
    workbook.save(payload)
    _upload(
        foundation_client,
        workspace_id,
        "maintenance.xlsx",
        payload.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    started = _start(foundation_client, workspace_id)
    hidden_issue = next(item for item in started["exceptions"] if item["exception_kind"] == "hidden_sheet")
    formula_issue = next(
        item for item in started["exceptions"] if item["exception_kind"] == "formula_without_cached_value"
    )
    assert hidden_issue["status"] == "open"
    assert formula_issue["status"] == "acknowledged"
    assert len(started["profiles"][0]["structures"]) == 2

    resolved = foundation_client.post(
        f"/api/g2/exceptions/{hidden_issue['exception_id']}/resolve",
        json={"included": False, "acknowledge": True},
    )
    assert resolved.status_code == 200, resolved.text
    result = resolved.json()
    assert result["state"] == "ready"
    assert result["counts"]["records"] == 3
    assert result["counts"]["evidence"] == 1
    assert result["counts"]["isolated_records"] == 2


def test_g2_join_is_explicit_and_adds_lookup_lineage(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    events = _upload(
        foundation_client,
        workspace_id,
        "events.csv",
        (
            "event_id,component_id,symptom_observation,action_taken\n"
            "E1,C1,noise,inspect\nE2,C2,leak,replace seal\nE3,C1,heat,cool\n"
        ).encode(),
        "text/csv",
    )
    _upload(
        foundation_client,
        workspace_id,
        "components.csv",
        b"component_id,component_name\nC1,Pump\nC2,Valve\n",
        "text/csv",
    )
    started = _start(foundation_client, workspace_id)
    assert started["state"] == "needs_attention"
    assert len([item for item in started["joins"] if item["status"] == "proposed"]) == 1
    join = next(item for item in started["joins"] if item["status"] == "proposed")
    assert join["spec"]["cardinality"] == "n:1"
    assert join["spec"]["unmatched_policy"] == "preserve_primary"
    assert join["preview"]["matched_records"] == 3

    decided = foundation_client.post(
        f"/api/g2/joins/{join['join_spec_id']}/decision", json={"action": "approve"}
    )
    assert decided.status_code == 200, decided.text
    assert decided.json()["state"] == "ready"
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": events["source_id"]}
    ).json()
    assert len(evidence) == 3
    assert all([item["role"] for item in unit["provenance_refs"]] == ["primary", "lookup"] for unit in evidence)
    assert {unit["attributes"]["lookup.component_name"] for unit in evidence} == {"Pump", "Valve"}

    with sqlite3.connect(operational_db_path()) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM audit_events WHERE workspace_id = ? AND event_kind = 'join_decided'",
            (workspace_id,),
        ).fetchone()[0] == 1


def test_g2_csv_multiline_record_keeps_physical_line_range(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload(
        foundation_client,
        workspace_id,
        "multiline.csv",
        (
            'event_id,symptom_observation,action_taken\n'
            'E1,"noise on first line\nand second line",inspect\n'
            'E2,leak,replace seal\n'
        ).encode(),
        "text/csv",
    )
    result = _start(foundation_client, workspace_id)
    assert result["counts"]["records"] == 2
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": source["source_id"]}
    ).json()
    multiline = next(item for item in evidence if "second line" in item["content"]["observation"])
    assert multiline["locator"]["line_start"] == 2
    assert multiline["locator"]["line_end"] == 3


def test_g2_json_preserves_precision_and_special_jsonpath(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload(
        foundation_client,
        workspace_id,
        "precision.json",
        (
            '{"plant records":[{"event_id":"E1","measurement":0.123456789012345678901234567890,'
            '"symptom_observation":"pressure drift"}]}'
        ).encode(),
        "application/json",
    )
    result = _start(foundation_client, workspace_id)
    assert result["state"] == "ready"
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": source["source_id"]}
    ).json()
    assert evidence[0]["attributes"]["measurement"] == "0.123456789012345678901234567890"
    assert evidence[0]["locator"]["json_path"] == "$['plant records'][0]"


def test_g2_duplicate_json_key_blocks_before_overwrite(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    _upload(
        foundation_client,
        workspace_id,
        "duplicate-key.json",
        b'{"events":[{"event_id":"E1","event_id":"E2","symptom_observation":"noise"}]}',
        "application/json",
    )
    result = _start(foundation_client, workspace_id)
    issue = next(item for item in result["exceptions"] if item["exception_kind"] == "json_structure_blocked")
    assert issue["status"] == "open"
    assert result["state"] == "needs_attention"
    assert result["counts"]["evidence"] == 0


def test_g2_capacity_fixture_processes_ten_thousand_rows(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    rows = ["event_id,symptom_observation,action_taken"]
    rows.extend(f"E{index:05d},symptom {index},action {index}" for index in range(10_000))
    _upload(
        foundation_client,
        workspace_id,
        "ds004-10000.csv",
        ("\n".join(rows) + "\n").encode(),
        "text/csv",
    )
    result = _start(foundation_client, workspace_id)
    assert result["state"] == "ready"
    assert result["counts"]["records"] == 10_000
    assert result["counts"]["evidence"] == 10_000
    assert len(result["profiles"][0]["structures"][0]["preview"]) == 20
    accounting = foundation_client.get(
        f"/api/foundation/runs/{result['profiles'][0]['run_id']}/accounting"
    ).json()
    assert accounting["balanced"] is True
    assert accounting["unclassified_total"] == 0


def test_g2_csv_maps_versioned_italian_and_german_headers(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    italian = HARDENING_FIXTURES / "multilingual_it_semicolon.csv"
    german = HARDENING_FIXTURES / "multilingual_de_pipe.csv"
    business = HARDENING_FIXTURES / "business_headers_with_spaces.csv"
    italian_source = _upload(foundation_client, workspace_id, italian.name, italian.read_bytes(), "text/csv")
    german_source = _upload(foundation_client, workspace_id, german.name, german.read_bytes(), "text/csv")
    business_source = _upload(foundation_client, workspace_id, business.name, business.read_bytes(), "text/csv")

    result = _start(foundation_client, workspace_id)

    assert result["state"] == "ready"
    assert result["counts"]["evidence"] == 3
    for profile in result["profiles"]:
        mapping = profile["mapping"]["structures"]["csv:main"]
        assert {config["role"] for config in mapping.values()} >= {
            "occurred_at", "component", "observation", "cause", "action", "error_code",
        }
    italian_evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": italian_source["source_id"]}
    ).json()
    german_evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": german_source["source_id"]}
    ).json()
    business_evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": business_source["source_id"]}
    ).json()
    assert italian_evidence[0]["language"]["qualification"] == "unqualified_it"
    assert german_evidence[0]["language"]["qualification"] == "unqualified_de"
    assert business_evidence[0]["language"]["qualification"] == "qualified_en"
    assert all(
        item["ingestion"]["mapping_fingerprint"]
        for item in [*italian_evidence, *german_evidence, *business_evidence]
    )


def test_g2_csv_maps_common_multilingual_operational_headers(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    _upload(
        foundation_client,
        workspace_id,
        "ro-events.csv",
        (
            "opened_at;subsystem;alert_code;symptom_reported;process_measurement;"
            "root_cause;corrective_action;work_outcome;restart_test\n"
            "2026-01-01T10:00:00;RO membrane;RO-COND-310;"
            "permeate conductivity above target;28,6 µS/cm;"
            "Membrane fouling;Eseguito CIP;Conducibilità rientrata;Test conforme\n"
        ).encode(),
        "text/csv",
    )
    result = _start(foundation_client, workspace_id)

    assert result["state"] == "ready"
    mapping = result["profiles"][0]["mapping"]["structures"]["csv:main"]
    assert mapping["opened_at"]["role"] == "occurred_at"
    assert mapping["alert_code"]["role"] == "error_code"
    assert mapping["symptom_reported"]["role"] == "observation"
    assert mapping["process_measurement"]["role"] == "measurement"
    assert mapping["work_outcome"]["role"] == "outcome"
    # Aliases read restart_test as an outcome too, but a role belongs to one
    # column: the second holder keeps its content as plain data instead of
    # being concatenated into the first one's field.
    assert mapping["restart_test"]["role"] == "attribute"
    assert mapping["restart_test"]["included"] is True


def test_g2_csv_queues_multiple_ambiguous_diagnostic_columns(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    fixture = HARDENING_FIXTURES / "ambiguous_diagnostic_columns.csv"
    _upload(foundation_client, workspace_id, fixture.name, fixture.read_bytes(), "text/csv")

    first = _start(foundation_client, workspace_id)
    assert first["state"] == "needs_attention"
    assert len([item for item in first["exceptions"] if item["status"] == "open"]) == 1
    assert len([item for item in first["exceptions"] if item["status"] == "queued"]) == 1
    open_exception = next(item for item in first["exceptions"] if item["status"] == "open")

    second = foundation_client.post(
        f"/api/g2/exceptions/{open_exception['exception_id']}/resolve", json={"role": "observation"}
    )
    assert second.status_code == 200, second.text
    assert second.json()["state"] == "needs_attention"
    next_exception = next(item for item in second.json()["exceptions"] if item["status"] == "open")
    final = foundation_client.post(
        f"/api/g2/exceptions/{next_exception['exception_id']}/resolve", json={"role": "attribute"}
    )
    assert final.status_code == 200, final.text
    assert final.json()["state"] == "ready"


def test_g2_csv_does_not_map_role_aliases_by_suffix(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload(
        foundation_client,
        workspace_id,
        "role-collision.csv",
        (
            "component,symptom_observation,diagnosis,intervento_eseguito,esito_intervento,"
            "origine_segnalazione,codice_allarme\n"
            "pump,low pressure,leak,Sostituito raccordo,Anomalia risolta,Allarme PLC,PN-1203\n"
        ).encode(),
        "text/csv",
    )

    result = _start(foundation_client, workspace_id)

    assert result["state"] == "ready"
    mapping = result["profiles"][0]["mapping"]["structures"]["csv:main"]
    assert mapping["intervento_eseguito"]["role"] == "action"
    assert mapping["esito_intervento"]["role"] == "outcome"
    assert mapping["origine_segnalazione"]["role"] == "attribute"
    evidence = foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": source["source_id"]}
    ).json()[0]
    assert evidence["content"]["action"] == "Sostituito raccordo"
    assert evidence["content"]["outcome"] == "Anomalia risolta"
