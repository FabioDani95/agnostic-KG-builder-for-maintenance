#!/usr/bin/env python3
"""Replay persisted typed candidates through the deterministic compiler only."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.domain.diagnostic_bundles import DiagnosticBundleCandidate  # noqa: E402
from backend.domain.evidence import EvidenceUnit  # noqa: E402
from backend.domain.locators import PdfLocator  # noqa: E402
from backend.services.diagnostic_bundle_compiler import (  # noqa: E402
    compile_diagnostic_bundles,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _evidence(path: Path) -> list[EvidenceUnit]:
    with sqlite3.connect(path) as connection:
        payloads = connection.execute(
            "SELECT payload_json FROM evidence_units ORDER BY created_at, evidence_id"
        ).fetchall()
    units = [EvidenceUnit.model_validate_json(payload) for (payload,) in payloads]
    return [unit for unit in units if isinstance(unit.locator, PdfLocator)]


def _reason_codes(entry: dict[str, Any]) -> list[str]:
    return [
        str(reason.get("code") or "")
        for reason in entry.get("drop_reasons", []) or []
        if str(reason.get("code") or "")
    ]


def replay(run_dir: Path, *, slug: str) -> dict[str, Any]:
    response_path = run_dir / "generation_response.json"
    database_path = run_dir / "operational.db"
    response = json.loads(response_path.read_text(encoding="utf-8"))
    subgraph = response["sources"][0]["subgraph"]
    records = subgraph["diagnostic_compilation_ledger"]["records"]
    evidence = _evidence(database_path)
    before = Counter(str(record.get("disposition") or "") for record in records)
    after: Counter[str] = Counter()
    changed: list[dict[str, Any]] = []
    replayed = 0

    for position, record in enumerate(records):
        candidate_payload = record.get("candidate")
        frozen_disposition = str(record.get("disposition") or "")
        if not candidate_payload:
            after[frozen_disposition] += 1
            continue
        candidate = DiagnosticBundleCandidate.model_validate(candidate_payload)
        compilation = compile_diagnostic_bundles(
            [candidate],
            source_type="technical PDF",
            source_title=slug,
            evidence_units=evidence,
        )
        replayed += 1
        replay_entry = compilation.report.entries[0]
        replay_disposition = replay_entry.disposition.value
        after[replay_disposition] += 1
        before_reasons = _reason_codes(record)
        after_reasons = [reason.code for reason in replay_entry.drop_reasons]
        if (
            frozen_disposition != replay_disposition
            or before_reasons != after_reasons
        ):
            changed.append({
                "position": position,
                "window_id": str(record.get("record_window_id") or ""),
                "before": frozen_disposition,
                "after": replay_disposition,
                "before_reasons": before_reasons,
                "after_reasons": after_reasons,
                "candidate_replayed": True,
                "resolved_evidence_ids": replay_entry.resolved_evidence_ids,
            })

    keys = sorted(set(before) | set(after))
    delta = {
        key: after[key] - before[key]
        for key in keys
        if after[key] != before[key]
    }
    return {
        "run_dir": str(run_dir.resolve()),
        "generation_response_sha256": _sha256(response_path),
        "operational_db_sha256": _sha256(database_path),
        "record_count": len(records),
        "candidate_replayed_count": replayed,
        "before": dict(sorted(before.items())),
        "after": dict(sorted(after.items())),
        "disposition_delta": delta,
        "changed_record_count": len(changed),
        "changed_records": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True, metavar="SLUG=RUN_DIR")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manuals: dict[str, Any] = {}
    for value in args.run:
        slug, separator, raw_path = value.partition("=")
        if not separator or not slug.strip() or not raw_path.strip():
            parser.error("--run must use SLUG=RUN_DIR")
        manuals[slug.strip()] = replay(Path(raw_path.strip()), slug=slug.strip())
    payload = {
        "schema_version": "diagnostic-compiler-post-campaign-replay-v1",
        "real_calls": 0,
        "manuals": manuals,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "real_calls": 0,
        "manuals": {
            slug: {
                "before": result["before"],
                "after": result["after"],
                "changed": result["changed_record_count"],
            }
            for slug, result in manuals.items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
