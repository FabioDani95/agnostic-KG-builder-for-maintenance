"""Traceability entry points for AC-TAB-001..005."""

from tests.planned import test_g2_acceptance as scenarios


def test_ac_tab_001(foundation_client, machine_payload):
    scenarios.test_g2_csv_multiline_record_keeps_physical_line_range(
        foundation_client, machine_payload
    )


def test_ac_tab_001_encoding(foundation_client, machine_payload):
    scenarios.test_g2_csv_detects_semicolon_and_preserves_latin1(
        foundation_client, machine_payload
    )


def test_ac_tab_001_row_shape(foundation_client, machine_payload):
    scenarios.test_g2_csv_isolates_short_and_long_rows(
        foundation_client, machine_payload
    )


def test_ac_tab_001_binary(foundation_client, machine_payload):
    scenarios.test_g2_binary_csv_is_blocked_without_affecting_the_workspace(
        foundation_client, machine_payload
    )


def test_ac_tab_002(foundation_client, machine_payload):
    scenarios.test_g2_xlsx_inventories_hidden_sheet_and_formula_without_cache(
        foundation_client, machine_payload
    )


def test_ac_tab_003(foundation_client, machine_payload):
    scenarios.test_g2_jsonl_isolates_only_the_malformed_line(
        foundation_client, machine_payload
    )


def test_ac_tab_004(foundation_client, machine_payload):
    scenarios.test_g2_mapping_opens_only_one_decision_then_resumes(
        foundation_client, machine_payload
    )


def test_ac_tab_005(foundation_client, machine_payload):
    scenarios.test_g2_capacity_fixture_processes_ten_thousand_rows(
        foundation_client, machine_payload
    )
