#!/usr/bin/env python3
"""Create a reproducible acceptance result without mutating normative sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acceptance-id", required=True)
    parser.add_argument("--status", choices=["passed", "failed", "support"], required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--assertion", action="append", default=[])
    parser.add_argument("--raw-artifact", action="append", default=[])
    parser.add_argument("--dataset")
    parser.add_argument("--dataset-hash")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    raw_artifacts = []
    for item in args.raw_artifact:
        path = (REPO_ROOT / item).resolve()
        raw_artifacts.append(
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    payload = {
        "acceptance_id": args.acceptance_id,
        "status": args.status,
        "timestamp_utc": utc_now(),
        "commit": _git("rev-parse", "HEAD"),
        "working_tree_dirty": bool(_git("status", "--porcelain")),
        "command": args.command,
        "dataset": (
            {"id": args.dataset, "sha256": args.dataset_hash}
            if args.dataset
            else None
        ),
        "assertions": [{"description": item, "passed": args.status != "failed"} for item in args.assertion],
        "raw_artifacts": raw_artifacts,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "secrets_included": False,
        },
    }
    output = (REPO_ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
