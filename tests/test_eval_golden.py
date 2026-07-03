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
