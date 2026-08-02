from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def _load_eval_module():
    path = Path(__file__).resolve().parent.parent / "scripts" / "eval_golden.py"
    spec = importlib.util.spec_from_file_location("eval_golden_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _triplet(symptom: str, pairs: list[tuple[str, str]], codes_by_fm: dict[str, list[str]] | None = None) -> dict:
    """Build a minimal projected-triplet dict: one FM per (fm, ca) pair, paired by id."""
    codes_by_fm = codes_by_fm or {}
    failure_modes = []
    corrective_actions = []
    for index, (fm_name, ca_name) in enumerate(pairs):
        fm_id = f"fm_{index}"
        failure_modes.append({
            "failure_mode_id": fm_id, "name": fm_name, "description": "",
            "material_context": "", "linked_symptom_id": "sym_x",
            "error_codes": codes_by_fm.get(fm_name, []),
        })
        if ca_name:
            corrective_actions.append({
                "action_id": f"ca_{index}", "name": ca_name, "description": "",
                "instruction_text": "", "linked_failure_mode_id": fm_id,
            })
    return {
        "symptom": {"symptom_id": "sym_x", "name": symptom, "description": ""},
        "failure_modes": failure_modes,
        "corrective_actions": corrective_actions,
    }


def test_soft_match_rejects_empty_actual():
    eg = _load_eval_module()
    # The old substring rule made "" match any expectation, which silently
    # disabled the error-code comparison.
    assert not eg._soft_match("E1", "")
    assert eg._soft_match("", "anything")
    assert eg._soft_match("drain hose blocked", "The drain hose is blocked.")


def test_code_match_is_token_exact():
    eg = _load_eval_module()
    assert not eg._code_match("E1", "E17")
    assert eg._code_match("E1", "E1 E4")
    assert not eg._code_match("E4", "")


def test_wrong_fm_ca_pairing_is_a_miss():
    eg = _load_eval_module()
    # FM and CA both exist under the symptom, but cross-paired: the expected
    # chain must NOT match through a concatenated bag-of-words.
    triplet = _triplet("No draining", [
        ("drain motor does not act", "Replace computer sequencer"),
        ("wire unit broken", "Replace the drain motor"),
    ])
    expected = [{"symptom": "No draining", "failure_mode": "drain motor does not act",
                 "corrective_action": "replace the drain motor"}]
    result = eg._match_triplets(expected, [triplet])
    assert result["matched"] == 0

    correctly_paired = _triplet("No draining", [
        ("drain motor does not act", "Replace the drain motor"),
    ])
    result = eg._match_triplets(expected, [correctly_paired])
    assert result["matched"] == 1


def test_expected_error_code_requires_wired_code():
    eg = _load_eval_module()
    triplet = _triplet("Machine does not drain", [("drain hose blocked", "Remove the blockage")])
    expected = [{"error_code": "E1", "symptom": "Machine does not drain",
                 "failure_mode": "drain hose blocked", "corrective_action": "remove the blockage"}]
    # No INDICATES wiring → the code is missing from the chain → miss.
    assert eg._match_triplets(expected, [triplet])["matched"] == 0
    wired = _triplet("Machine does not drain", [("drain hose blocked", "Remove the blockage")],
                     codes_by_fm={"drain hose blocked": ["E1"]})
    assert eg._match_triplets(expected, [wired])["matched"] == 1


def test_error_code_rooted_expected_matches_graph_chain():
    eg = _load_eval_module()
    ontology = {
        "nodes": {
            "ErrorCode": [{"error_code_id": "err_e4", "name": "E4", "code": "E4", "description": ""}],
            "FailureMode": [{"failure_mode_id": "fm_valve", "name": "Water inlet valve blocked",
                             "description": "", "material_context": ""}],
            "CorrectiveAction": [{"action_id": "ca_clean", "name": "Clean the water inlet valve",
                                  "description": "", "instruction_text": ""}],
        },
        "relations": [
            {"name": "INDICATES", "from_id": "err_e4", "to_id": "fm_valve"},
            {"name": "RESOLVED_BY", "from_id": "fm_valve", "to_id": "ca_clean"},
        ],
    }
    expected = [{"error_code": "E4", "failure_mode": "water inlet valve blocked",
                 "corrective_action": "clean the water inlet valve"}]
    result = eg._match_triplets(expected, [], ontology=ontology)
    assert result["matched"] == 1
    assert result["matches"][0]["source"] == "graph_error_code"


def test_expected_gap_rejects_resolved_by_even_when_projection_is_actionless():
    eg = _load_eval_module()
    actionless_projection = _triplet(
        "Water inlet failure",
        [("temperature sensor open circuit", "")],
        codes_by_fm={"temperature sensor open circuit": ["E6"]},
    )
    ontology = {
        "nodes": {
            "ErrorCode": [
                {"error_code_id": "ec_e6", "name": "E6", "code": "E6", "description": ""}
            ],
            "FailureMode": [
                {
                    "failure_mode_id": "fm_sensor",
                    "name": "Temperature sensor open circuit",
                    "description": "",
                    "material_context": "",
                }
            ],
            "CorrectiveAction": [
                {
                    "action_id": "ca_check",
                    "name": "Check the thermistor",
                    "description": "",
                    "instruction_text": "",
                }
            ],
        },
        "relations": [
            {"name": "INDICATES", "from_id": "ec_e6", "to_id": "fm_sensor"},
            {"name": "RESOLVED_BY", "from_id": "fm_sensor", "to_id": "ca_check"},
        ],
    }
    expected = [{
        "error_code": "E6",
        "failure_mode": "temperature sensor open circuit",
        "expected_gap": "failure_mode_without_action",
    }]

    result = eg._match_triplets(expected, [actionless_projection], ontology=ontology)
    assert result["matched"] == 1
    assert not result["expected_gaps"]["passed"]
    assert result["expected_gaps"]["violations"][0]["source"] == "graph_resolved_by"


def test_expected_gap_passes_without_action_and_omission_is_not_negative():
    eg = _load_eval_module()
    actionless = _triplet("No draining", [("drain path blocked", "")])
    gap = [{
        "symptom": "No draining",
        "failure_mode": "drain path blocked",
        "expected_gap": "failure_mode_without_action",
    }]
    result = eg._match_triplets(gap, [actionless])
    assert result["matched"] == 1
    assert result["expected_gaps"]["passed"]

    # A legacy omission remains "action not scored"; it is not a negative
    # assertion and therefore does not create a gap violation.
    with_action = _triplet("No draining", [("drain path blocked", "replace the drain hose")])
    result = eg._match_triplets(
        [{"symptom": "No draining", "failure_mode": "drain path blocked"}],
        [with_action],
    )
    assert result["matched"] == 1
    assert result["expected_gaps"]["expected"] == 0


def test_expected_gap_validation_and_sibling_cause_disambiguation():
    eg = _load_eval_module()
    with_action = {
        "failure_mode": "failed sensor",
        "corrective_action": "replace sensor",
        "expected_gap": "failure_mode_without_action",
    }
    try:
        eg._match_triplets([with_action], [])
    except ValueError as exc:
        assert "mutually exclusive" in str(exc)
    else:
        raise AssertionError("expected invalid gap annotation to be rejected")

    sibling = _triplet(
        "Manipulator crashes on power down",
        [("faulty motor holding brake", "replace the motor")],
    )
    expected = [{
        "symptom": "Manipulator crashes on power down",
        "failure_mode": "faulty power supply to the brake",
        "expected_gap": "failure_mode_without_action",
    }]
    result = eg._match_triplets(expected, [sibling])
    assert result["expected_gaps"]["passed"]

    actionless_sibling = _triplet(
        "Manipulator crashes on power down",
        [("faulty motor holding brake", "")],
    )
    result = eg._match_triplets(expected, [actionless_sibling])
    assert result["matched"] == 0


def test_forbidden_chain_violation_is_detected():
    eg = _load_eval_module()
    contaminated = _triplet("No draining", [("machine not level", "Level the machine")])
    result = eg._match_triplets([], [contaminated],
                                forbidden=[{"symptom": "No draining", "failure_mode": "machine not level"}])
    assert not result["forbidden"]["passed"]
    assert len(result["forbidden"]["violations"]) == 1

    clean = _triplet("No draining", [("drain motor does not act", "Replace the drain motor")])
    result = eg._match_triplets([], [clean],
                                forbidden=[{"symptom": "No draining", "failure_mode": "machine not level"}])
    assert result["forbidden"]["passed"]


def test_forbidden_rules_do_not_soft_match_generic_phrases():
    eg = _load_eval_module()
    # "machine does not spin" shares only stopword-ish tokens with "the machine
    # does not fill with water": a forbidden rule must not flag it (observed as
    # 5 false violations in the first real gpt-5.4 run).
    valid = _triplet("No water filling", [("water inlet valve blocked", "Clean the water inlet valve")])
    result = eg._match_triplets([], [valid],
                                forbidden=[{"symptom": "machine does not spin",
                                            "failure_mode": "water inlet valve"}])
    assert result["forbidden"]["passed"], result["forbidden"]["violations"]

    contaminated = _triplet("Machine does not spin", [("water inlet valve blocked", "Replace the valve")])
    result = eg._match_triplets([], [contaminated],
                                forbidden=[{"symptom": "machine does not spin",
                                            "failure_mode": "water inlet valve"}])
    assert not result["forbidden"]["passed"]


def test_paraphrased_fm_is_grounded_via_relation_quote():
    eg = _load_eval_module()
    page_texts = [
        "If there is no voltage at the water inlet valve but voltage exists at the "
        "output of the computer sequencer, replace the wire unit.",
    ]
    # FM name is a paraphrase (not in the text); the relation evidence quote is
    # verbatim, so the chain must be classified grounded, not unsupported.
    triplet = _triplet("No water filling", [("Wire unit disconnected in inlet circuit", "Replace the wire unit")])
    ontology = {
        "nodes": {},
        "relations": [
            {
                "name": "MAY_INDICATE", "from_id": "sym_x", "to_id": "fm_0",
                "evidence": [{"source_page": 18, "source_reference": "PAGE 18",
                              "quote": "no voltage at the water inlet valve"}],
            },
            {
                "name": "RESOLVED_BY", "from_id": "fm_0", "to_id": "ca_0",
                "evidence": [{"source_page": 18, "source_reference": "PAGE 18",
                              "quote": "replace the wire unit"}],
            },
        ],
    }
    result = eg._match_triplets([], [triplet], ontology=ontology, page_texts=page_texts)
    assert result["chains"]["extra_grounded"] == 1
    assert result["chains"]["unsupported"] == 0

    # Without the quote, the paraphrased name alone stays unsupported.
    result = eg._match_triplets([], [triplet], page_texts=page_texts)
    assert result["chains"]["unsupported"] == 1


def test_quality_gates_floor_and_unsupported_rate():
    eg = _load_eval_module()
    expected = {"expected_quality_gates": {
        "min_prediction_count": 1,
        "min_recall": 0.75,
        "max_unsupported_rate": 0.0,
    }}
    ok = eg._quality_gates_result(
        expected,
        {"recall": 0.8, "chains": {"total": 1, "unsupported_rate": 0.0}},
    )
    assert (
        ok["passed"]
        and ok["min_prediction_count"]["passed"]
        and ok["min_recall"]["passed"]
        and ok["max_unsupported_rate"]["passed"]
    )

    low_recall = eg._quality_gates_result(
        expected,
        {"recall": 0.5, "chains": {"total": 1, "unsupported_rate": 0.0}},
    )
    assert not low_recall["passed"] and not low_recall["min_recall"]["passed"]

    hallucinating = eg._quality_gates_result(
        expected,
        {"recall": 1.0, "chains": {"total": 1, "unsupported_rate": 0.1}},
    )
    assert not hallucinating["passed"]

    empty = eg._quality_gates_result({}, {"recall": 0.0, "chains": {"total": 0}})
    assert not empty["passed"] and not empty["configuration"]["passed"]

    no_predictions = eg._quality_gates_result(
        expected,
        {"recall": 1.0, "chains": {"total": 0, "unsupported_rate": 0.0}},
    )
    assert not no_predictions["passed"]
    assert not no_predictions["min_prediction_count"]["passed"]


def test_machine_logs_ingestion_view_is_blinded():
    eg = _load_eval_module()
    views = eg._machine_log_views()

    assert views["ingestion_rows"], "machine_logs.csv must contain regression rows"
    assert set(views["label_columns"]) == set(eg.MACHINE_LOG_LABEL_COLUMNS)
    assert not set(views["ingestion_columns"]) & set(eg.MACHINE_LOG_LABEL_COLUMNS)
    assert all(
        not set(row) & set(eg.MACHINE_LOG_LABEL_COLUMNS)
        for row in views["ingestion_rows"]
    )
    assert len(views["ingestion_rows"]) == len(views["label_rows"])


def test_all_checked_in_fixtures_make_actionless_expectations_explicit():
    expected_dir = Path(__file__).resolve().parent / "golden" / "expected"
    for path in expected_dir.glob("*.json"):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        gates = fixture.get("expected_quality_gates") or {}
        assert gates.get("min_prediction_count", 0) > 0, path.name
        for item in fixture.get("expected_triplets") or []:
            if not str(item.get("corrective_action") or "").strip():
                assert item.get("expected_gap") == "failure_mode_without_action", (
                    path.name,
                    item,
                )


def test_gate_failures_include_quality_gates():
    eg = _load_eval_module()
    report = {"fixtures": [{
        "fixture_id": "fx",
        "triplets": {"forbidden": {"violations": []}},
        "quality_gates": {"min_recall": {"expected": 0.75, "actual": 0.5, "passed": False}, "passed": False},
    }]}
    failures = eg._report_gate_failures(report)
    assert any("min_recall" in failure for failure in failures)


def test_gate_failures_include_expected_gap_violations():
    eg = _load_eval_module()
    report = {"fixtures": [{
        "fixture_id": "fx",
        "scoping": {"must_keep_passed": True},
        "export_checks": {"passed": True},
        "ontology": {
            "schema_issues_by_severity": {"error": 0},
            "dangling_relations": 0,
            "human_review": {"matched": True},
        },
        "triplets": {
            "forbidden": {"violations": []},
            "expected_gaps": {"violations": [{"failure_mode": "failed sensor"}]},
        },
        "quality_gates": {"passed": True},
    }]}
    failures = eg._report_gate_failures(report)
    assert any("expected-gap" in failure for failure in failures)


def test_gate_failures_include_structural_contracts():
    eg = _load_eval_module()
    report = {"fixtures": [{
        "fixture_id": "fx",
        "scoping": {"must_keep_passed": False},
        "export_checks": {"passed": False},
        "ontology": {
            "schema_issues_by_severity": {"error": 2},
            "dangling_relations": 1,
            "human_review": {"matched": False},
        },
        "triplets": {"forbidden": {"violations": []}},
        "quality_gates": {"passed": True},
    }]}

    failures = eg._report_gate_failures(report)
    assert len(failures) == 5
    assert any("must-keep" in failure for failure in failures)
    assert any("dangling" in failure for failure in failures)


def test_recall_floor_replaces_baseline_recall_comparison(tmp_path):
    eg = _load_eval_module()

    def _fixture(recall, gates):
        return {
            "fixture_id": "fx",
            "triplets": {"recall": recall, "chains": {"unsupported_rate": 0.0}},
            "ontology": {"schema_compliant": True, "human_review": {"matched": True}},
            "quality_gates": gates,
        }

    baseline_path = tmp_path / "report.json"
    baseline_path.write_text(json.dumps({"fixtures": [_fixture(0.85, {})]}), encoding="utf-8")

    # Without a floor, 0.725 < 0.85 is a regression (variance false-alarm).
    without_floor = {"fixtures": [_fixture(0.725, {})]}
    assert eg._baseline_regressed(without_floor, baseline_path)

    # With a floor, the absolute gate replaces the comparison.
    with_floor = {"fixtures": [_fixture(
        0.725, {"min_recall": {"expected": 0.7, "actual": 0.725, "passed": True}, "passed": True},
    )]}
    assert not eg._baseline_regressed(with_floor, baseline_path)


def test_extra_chains_are_split_into_grounded_and_unsupported():
    eg = _load_eval_module()
    page_texts = [
        "No draining: if the drain motor does not act and voltage exists, replace the drain motor.",
    ]
    grounded = _triplet("No draining", [("drain motor does not act", "replace the drain motor")])
    hallucinated = _triplet("No draining", [("quantum flux destabilized", "recalibrate the flux capacitor")])
    result = eg._match_triplets([], [grounded, hallucinated], page_texts=page_texts)
    chains = result["chains"]
    assert chains["extra_grounded"] == 1
    assert chains["unsupported"] == 1
    statuses = {c["failure_mode_name"]: c["status"] for c in result["actual_chains"]}
    assert statuses["drain motor does not act"] == "extra_grounded"
    assert statuses["quantum flux destabilized"] == "unsupported"


def test_one_actual_chain_cannot_satisfy_two_expected_items():
    eg = _load_eval_module()
    actual = _triplet("No draining", [("drain hose blocked", "remove the blockage")])
    expected = [
        {"symptom": "No draining", "failure_mode": "drain hose blocked",
         "corrective_action": "remove the blockage"},
        {"symptom": "No draining", "failure_mode": "blocked drain hose",
         "corrective_action": "remove blockage"},
    ]

    result = eg._match_triplets(expected, [actual])
    assert result["matched"] == 1
    assert len(result["unmatched_expected"]) == 1


def test_eval_golden_mock_runs_all_fixtures_and_writes_report(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/eval_golden.py",
            "--mode",
            "mock",
            "--output-dir",
            str(tmp_path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    report_path = result.stdout.strip().splitlines()[-1]
    report = json.loads(open(report_path, encoding="utf-8").read())

    assert report["mode"] == "mock"
    expected_ids = {
        path.stem
        for path in (Path(__file__).resolve().parent / "golden" / "expected").glob("*.json")
    }
    assert report["summary"]["fixture_count"] == len(expected_ids)
    assert {item["fixture_id"] for item in report["fixtures"]} == expected_ids
    for fixture in report["fixtures"]:
        assert "scoping" in fixture
        assert "ontology" in fixture
        assert "triplets" in fixture
        assert "export_checks" in fixture
        assert "metrics" in fixture
        assert "trace" in fixture
        assert fixture["trace"]
        # The fixture-driven mock responses make the mock run a real quality
        # gate: full recall and a compliant schema are the deterministic
        # baseline, so any drop is a pipeline regression, not noise.
        assert fixture["triplets"]["recall"] == 1.0, (
            f"{fixture['fixture_id']}: recall dropped to {fixture['triplets']['recall']}"
            f" — unmatched: {fixture['triplets']['unmatched_expected']}"
        )
        assert fixture["triplets"]["approx_precision"] <= 1.0
        # Chain-level gates: deterministic mocks must produce fully matched,
        # fully supported chains and no forbidden (contaminated) chains.
        assert fixture["triplets"]["chains"]["unsupported"] == 0, (
            f"{fixture['fixture_id']}: unsupported chains "
            f"{[c for c in fixture['triplets']['actual_chains'] if c['status'] == 'unsupported']}"
        )
        assert fixture["triplets"]["forbidden"]["passed"] is True, (
            f"{fixture['fixture_id']}: forbidden chain violations "
            f"{fixture['triplets']['forbidden']['violations']}"
        )
        assert fixture["triplets"]["expected_gaps"]["passed"] is True, (
            f"{fixture['fixture_id']}: expected-gap violations "
            f"{fixture['triplets']['expected_gaps']['violations']}"
        )
        assert fixture["artifacts"], "expected audit artifacts to be written"
        assert fixture["quality_gates"]["passed"] is True, (
            f"{fixture['fixture_id']}: quality gates failed {fixture['quality_gates']}"
        )
        assert fixture["ontology"]["schema_compliant"] is True
        assert fixture["ontology"]["human_review"]["matched"] is True, (
            f"{fixture['fixture_id']}: human review requirement mismatch "
            f"(expected={fixture['ontology']['human_review']['expected_required']}, "
            f"actual={fixture['ontology']['human_review']['actual_required']})"
        )
        assert fixture["export_checks"]["passed"] is True
