from __future__ import annotations

import json

from scripts.build_regression_report import build_report, junit_summary


def test_ac_reg_002(tmp_path, monkeypatch):
    junit = tmp_path / "suite.xml"
    junit.write_text(
        '<testsuites><testsuite tests="347" failures="0" errors="0" skipped="2" time="4.2"/></testsuites>',
        encoding="utf-8",
    )
    golden = tmp_path / "report.json"
    golden.write_text(
        json.dumps(
            {
                "summary": {
                    "fixture_count": 9,
                    "average_triplet_recall": 1.0,
                    "schema_compliant_count": 9,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "scripts.build_regression_report.git_value",
        lambda *args: "commit-under-test" if "rev-parse" in args else "",
    )
    report = build_report(
        junit_path=junit,
        golden_path=golden,
        command="python3 -m pytest -q",
        ruff_command="python3 -m ruff check .",
        contract_command="python3 scripts/check_spec_consistency.py",
        e2e_command="npm run test:e2e",
    )
    assert junit_summary(junit)["tests"] == 347
    assert report["historical_reconciliation"]["historical_checkpoint"] == 301
    assert report["current_suite"]["tests"] == 347
    assert report["current_suite"]["count_label"] == "actual_current_suite"
    assert report["golden_mock"]["fixture_count"] == 9
    assert report["golden_mock"]["average_triplet_recall"] == 1.0


def test_root_opens_the_workspace_home(foundation_client):
    redirect = foundation_client.get("/", follow_redirects=False)
    response = foundation_client.get("/")

    assert redirect.status_code == 307
    assert redirect.headers["location"] == "/home.html"
    assert redirect.headers["cache-control"] == "no-store"
    assert response.status_code == 200
    assert str(response.url).endswith("/home.html")
    assert "Workspace · Maintenance KG Builder" in response.text
