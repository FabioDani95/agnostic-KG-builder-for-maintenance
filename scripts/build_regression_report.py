#!/usr/bin/env python3
"""Build the actual checkpoint regression report from JUnit and golden output."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def git_value(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def junit_summary(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    return {
        "tests": sum(int(suite.attrib.get("tests", 0)) for suite in suites),
        "failures": sum(int(suite.attrib.get("failures", 0)) for suite in suites),
        "errors": sum(int(suite.attrib.get("errors", 0)) for suite in suites),
        "skipped": sum(int(suite.attrib.get("skipped", 0)) for suite in suites),
        "time_seconds": round(
            sum(float(suite.attrib.get("time", 0.0)) for suite in suites),
            3,
        ),
    }


def artifact_ref(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def build_report(
    *,
    junit_path: Path,
    golden_path: Path,
    command: str,
    ruff_command: str,
    contract_command: str,
    e2e_command: str,
) -> dict[str, Any]:
    suite = junit_summary(junit_path)
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    return {
        "status": (
            "passed"
            if suite["failures"] == 0 and suite["errors"] == 0
            else "failed"
        ),
        "timestamp_utc": utc_now(),
        "commit": git_value("rev-parse", "HEAD"),
        "working_tree_dirty": bool(git_value("status", "--porcelain")),
        "historical_reconciliation": {
            "imported_baseline": 313,
            "spec_checker_delta": 1,
            "removed_editor_tests_delta": -17,
            "read_only_no_mutation_delta": 4,
            "historical_checkpoint": 301,
            "equation": "313 + 1 - 17 + 4 = 301",
        },
        "current_suite": {
            **suite,
            "count_label": "actual_current_suite",
            "command": command,
            "artifact": artifact_ref(junit_path),
        },
        "golden_mock": {
            "fixture_count": golden["summary"]["fixture_count"],
            "average_triplet_recall": golden["summary"]["average_triplet_recall"],
            "schema_compliant_count": golden["summary"]["schema_compliant_count"],
            "command": "python3 scripts/eval_golden.py --mode mock --fail-on-regression",
            "artifact": artifact_ref(golden_path),
        },
        "additional_gates": {
            "ruff": ruff_command,
            "contract": contract_command,
            "console_e2e": e2e_command,
        },
        "links": {
            "junit": artifact_ref(junit_path),
            "golden_json": artifact_ref(golden_path),
            "golden_markdown": artifact_ref(golden_path.with_name("report.md")),
        },
        "secrets_included": False,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    suite = report["current_suite"]
    golden = report["golden_mock"]
    links = report["links"]
    markdown_links = {
        key: os.path.relpath(REPO_ROOT / value, start=path.parent)
        for key, value in links.items()
    }
    text = "\n".join(
        [
            "# G1 regression report",
            "",
            f"- status: `{report['status']}`",
            f"- timestamp UTC: `{report['timestamp_utc']}`",
            f"- commit: `{report['commit']}`",
            f"- historical reconciliation: `{report['historical_reconciliation']['equation']}`",
            (
                f"- actual current suite: `{suite['tests']}` tests, "
                f"`{suite['failures']}` failures, `{suite['errors']}` errors, "
                f"`{suite['skipped']}` skipped"
            ),
            f"- current command: `{suite['command']}`",
            (
                f"- golden mock: `{golden['fixture_count']}` fixtures, "
                f"average recall `{golden['average_triplet_recall']}`"
            ),
            f"- [JUnit]({markdown_links['junit']})",
            f"- [Golden JSON]({markdown_links['golden_json']})",
            f"- [Golden Markdown]({markdown_links['golden_markdown']})",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", required=True)
    parser.add_argument("--golden-report", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--ruff-command", required=True)
    parser.add_argument("--contract-command", required=True)
    parser.add_argument("--e2e-command", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    junit_path = (REPO_ROOT / args.junit).resolve()
    golden_path = (REPO_ROOT / args.golden_report).resolve()
    output = (REPO_ROOT / args.output).resolve()
    report = build_report(
        junit_path=junit_path,
        golden_path=golden_path,
        command=args.command,
        ruff_command=args.ruff_command,
        contract_command=args.contract_command,
        e2e_command=args.e2e_command,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_markdown(output.with_suffix(".md"), report)
    print(output)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
