#!/usr/bin/env python3
"""Validate G1 artifacts and emit the pending Product Owner checkpoint."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIMARY = [
    "artifacts/acceptance/ac-ont-001/result.json",
    "artifacts/acceptance/ac-ws-001/result.json",
    "artifacts/acceptance/ac-ws-004/result.json",
    "artifacts/acceptance/ac-ws-005/result.json",
    "artifacts/acceptance/ac-pdf-001/result.json",
    "artifacts/acceptance/ac-pdf-002/result.json",
    "artifacts/acceptance/ac-pdf-003/result.json",
    "artifacts/acceptance/ac-sec-003/result.json",
    "artifacts/acceptance/ac-pdf-004/result.json",
]
SUPPORT = [
    "artifacts/acceptance/support/i01/ac-ont-003/result.json",
    "artifacts/acceptance/support/i02/ac-ux-002/result.json",
    "artifacts/acceptance/support/i03/ac-ev-002/result.json",
    "artifacts/acceptance/support/i03/ac-ws-002/result.json",
    "artifacts/acceptance/support/i05/ac-reg-001/result.json",
    "artifacts/acceptance/support/i06/ac-ev-001/result.json",
    "artifacts/acceptance/support/i06/ac-hitl-004/result.json",
    "artifacts/acceptance/support/i07/ac-ev-001/result.json",
    "artifacts/acceptance/support/i08/ac-ev-001/result.json",
    "artifacts/acceptance/support/i08/ac-ux-009/result.json",
    "artifacts/acceptance/support/i08/ac-reg-002/result.json",
]


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


def artifact_entry(relative_path: str, required_status: str) -> dict:
    path = REPO_ROOT / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload["status"] != required_status:
        raise RuntimeError(
            f"{relative_path}: expected {required_status}, found {payload['status']}"
        )
    return {
        "acceptance_id": payload["acceptance_id"],
        "status": payload["status"],
        "path": relative_path,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> int:
    primary = [artifact_entry(path, "passed") for path in PRIMARY]
    support = [artifact_entry(path, "support") for path in SUPPORT]
    regression_path = REPO_ROOT / "artifacts" / "regression" / "g1" / "result.json"
    regression = json.loads(regression_path.read_text(encoding="utf-8"))
    if regression["status"] != "passed":
        raise RuntimeError("G1 regression report is not passed")

    checker = json.loads(
        subprocess.run(
            [
                "python3",
                "scripts/check_spec_consistency.py",
                "--format",
                "json",
                "--require-status",
                "READY_FOR_PLANNING",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    now = utc_now()
    commit = git_value("rev-parse", "HEAD")
    coverage = {
        "checkpoint": "G1",
        "status": "ready_for_product_owner",
        "timestamp_utc": now,
        "commit": commit,
        "working_tree_dirty": bool(git_value("status", "--porcelain")),
        "increments_completed_in_order": [
            "I01",
            "I02",
            "I03",
            "I04",
            "I05",
            "I06",
            "I07",
            "I08",
        ],
        "primary_validation": primary,
        "support_validation_not_promoted_to_primary": support,
        "regression": {
            "path": "artifacts/regression/g1/result.json",
            "actual_current_suite": regression["current_suite"],
            "golden_mock": regression["golden_mock"],
        },
        "specification_guard": {
            "status": checker["readiness"]["derived_status"],
            "package_digest": checker["readiness"]["package_digest"],
            "issues": checker["issues"],
            "normative_files_modified_by_g1": False,
            "comparison_command": (
                "diff against /tmp/log-kg-builder-pre-g1.qLSIEE/untracked.tar "
                "for SPECIFICHE_MVP.md and docs/specs; git diff -- ontology_schema.JSON"
            ),
        },
        "pre_g1_worktree_snapshot": {
            "path": "/tmp/log-kg-builder-pre-g1.qLSIEE",
            "tracked_patch_sha256": (
                "6988a2e67b7e6fc67ad1ecfc792e4af813166f4b58ec33f688ea55bbd478b3a5"
            ),
            "status_sha256": (
                "ec2ed198872ef4c46f2b43969453e488276f5ff5d519db1e1a2684d6d9fd4c95"
            ),
            "untracked_archive_sha256": (
                "85fa5d87c87bf210702fb095a1551d3a0874c3072cf6693acac469b86e8dd394"
            ),
        },
    }
    coverage_path = REPO_ROOT / "artifacts" / "acceptance" / "g1" / "coverage.json"
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_path.write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    gate = {
        "checkpoint": "G1",
        "status": "pending_product_owner",
        "timestamp_utc": now,
        "commit": commit,
        "coverage_artifact": "artifacts/acceptance/g1/coverage.json",
        "product_owner_checks": [
            "Confermare una singola macchina e ricaricare la pagina.",
            "Verificare che un documento incompatibile resti messo da parte e non venga usato.",
            "Scegliere e approvare le cinque pagine del PDF G1.",
            "Aprire il controllo del documento e filtrare gli elementi elaborati.",
            "Aprire pagina 5 e trovare G1_TABLE_5_ROW_61_MARKER a tabella 5/riga 61.",
            "Verificare zero elementi senza esito e la voce Totali verificati impostata a Sì.",
            "Provocare il caricamento di un formato non supportato e verificare che l'errore dica cosa fare.",
            "Ricaricare la pagina e verificare che elaborazione e conteggi siano invariati.",
        ],
        "allowed_product_owner_decisions": [
            "correggere G1",
            "proseguire a G2",
        ],
        "decision": None,
        "decided_at": None,
    }
    gate_path = REPO_ROOT / "artifacts" / "user-gates" / "g1" / "result.json"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(
        json.dumps(gate, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(coverage_path)
    print(gate_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
