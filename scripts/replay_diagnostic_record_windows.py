#!/usr/bin/env python3
"""Replay deterministic diagnostic windowing from immutable operational DBs."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.domain.evidence import EvidenceUnit  # noqa: E402
from backend.services.diagnostic_record_windowing import (  # noqa: E402
    build_diagnostic_record_windows,
)


def _load_evidence(path: Path) -> list[EvidenceUnit]:
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT payload_json FROM evidence_units ORDER BY created_at, evidence_id"
        ).fetchall()
    return [EvidenceUnit.model_validate_json(payload) for (payload,) in rows]


def replay(path: Path) -> dict[str, Any]:
    evidence = _load_evidence(path)
    windows = build_diagnostic_record_windows(evidence)
    evidence_ids = {str(unit.evidence_id) for unit in evidence}
    root_ids = {window.record_anchor for window in windows}
    canonical_text = {
        str(unit.evidence_id): str(unit.content.observation or unit.locator.quote or "")
        for unit in evidence
    }
    invariant_checks = {
        "unique_window_ids": len({window.window_id for window in windows}) == len(windows),
        "unique_branch_occurrences": (
            len({(window.branch_anchor, window.branch_ordinal) for window in windows})
            == len(windows)
        ),
        "all_anchors_exist": all(
            anchor in evidence_ids
            for window in windows
            for anchor in window.allowed_source_anchors
        ),
        "root_is_allowed": all(
            window.record_anchor in window.allowed_source_anchors for window in windows
        ),
        "bounded_support": all(len(window.allowed_source_anchors) <= 16 for window in windows),
        "scope_is_anchor_bounded": all(
            set(window.allowed_evidence_spans).issubset(window.allowed_source_anchors)
            for window in windows
        ),
        "scope_is_literal": all(
            span in canonical_text.get(anchor, "")
            for window in windows
            for anchor, spans in window.allowed_evidence_spans.items()
            for span in spans
        ),
        "atomic_pairing_only": all(
            window.structure_status in {"atomic", "ambiguous_pairing"}
            for window in windows
        ),
    }
    return {
        "database": str(path.resolve()),
        "evidence_unit_count": len(evidence),
        "window_count": len(windows),
        "window_kinds": dict(Counter(window.window_kind for window in windows)),
        "record_root_count": len(root_ids),
        "cross_page_window_count": sum(
            len(window.page_numbers) > 1 for window in windows
        ),
        "inherited_root_window_count": sum(window.inherited_root for window in windows),
        "atomized_physical_row_count": len({
            window.branch_anchor
            for window in windows
            if window.branch_count > 1
        }),
        "ambiguous_pairing_window_count": sum(
            window.structure_status == "ambiguous_pairing" for window in windows
        ),
        "max_allowed_anchors": max(
            (len(window.allowed_source_anchors) for window in windows), default=0
        ),
        "invariants": invariant_checks,
        "passed": bool(windows) and all(invariant_checks.values()),
        "windows": [window.model_dump(mode="json") for window in windows],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manual",
        action="append",
        required=True,
        metavar="ID=OPERATIONAL_DB",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manuals: dict[str, Any] = {}
    for value in args.manual:
        manual_id, separator, raw_path = value.partition("=")
        if not separator or not manual_id.strip() or not raw_path.strip():
            parser.error("--manual must use ID=OPERATIONAL_DB")
        manuals[manual_id.strip()] = replay(Path(raw_path.strip()))
    payload = {
        "schema_version": "diagnostic-record-window-replay-v2",
        "manuals": manuals,
        "passed": all(item["passed"] for item in manuals.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "passed": payload["passed"],
        "manuals": {
            key: {
                "window_count": item["window_count"],
                "window_kinds": item["window_kinds"],
                "passed": item["passed"],
            }
            for key, item in manuals.items()
        },
    }, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
