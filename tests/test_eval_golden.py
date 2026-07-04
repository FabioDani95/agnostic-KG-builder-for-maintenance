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
        "symptom": {"name": symptom, "description": ""},
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
        "relations": [{
            "name": "MAY_INDICATE", "from_id": "sym_x", "to_id": "fm_0",
            "evidence": [{"source_page": 18, "source_reference": "PAGE 18",
                          "quote": "replace the wire unit"}],
        }],
    }
    result = eg._match_triplets([], [triplet], ontology=ontology, page_texts=page_texts)
    assert result["chains"]["extra_grounded"] == 1
    assert result["chains"]["unsupported"] == 0

    # Without the quote, the paraphrased name alone stays unsupported.
    result = eg._match_triplets([], [triplet], page_texts=page_texts)
    assert result["chains"]["unsupported"] == 1


def test_extra_chains_are_split_into_grounded_and_unsupported():
    eg = _load_eval_module()
    page_texts = [
        "If the drain motor does not act and voltage exists, replace the drain motor.",
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
    assert report["summary"]["fixture_count"] == 4
    assert {item["fixture_id"] for item in report["fixtures"]} == {
        "ambiguous_conveyor_manual",
        "clean_pump_manual",
        "haier_lma4120_washer_manual",
        "noisy_table_robot_manual",
    }
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
        assert fixture["artifacts"], "expected audit artifacts to be written"
        assert fixture["ontology"]["schema_compliant"] is True
        assert fixture["ontology"]["human_review"]["matched"] is True, (
            f"{fixture['fixture_id']}: human review requirement mismatch "
            f"(expected={fixture['ontology']['human_review']['expected_required']}, "
            f"actual={fixture['ontology']['human_review']['actual_required']})"
        )
        assert fixture["export_checks"]["passed"] is True
