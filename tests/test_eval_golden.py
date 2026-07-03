from __future__ import annotations

import json
import subprocess
import sys


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
    assert report["summary"]["fixture_count"] == 3
    assert {item["fixture_id"] for item in report["fixtures"]} == {
        "ambiguous_conveyor_manual",
        "clean_pump_manual",
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
        assert fixture["ontology"]["schema_compliant"] is True
        assert fixture["export_checks"]["passed"] is True
