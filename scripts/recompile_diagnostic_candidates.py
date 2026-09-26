"""Recompile saved candidates against canonical evidence without model calls.

This is a compiler/windowing probe, not a new extraction or full graph replay.
Original candidate, graph and database files are opened read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from backend.domain.diagnostic_bundles import DiagnosticChunkOutput
    from backend.domain.evidence import EvidenceUnit
    from backend.domain.locators import PdfLocator
    from backend.services.diagnostic_bundle_compiler import compile_diagnostic_bundles
    from backend.services.diagnostic_record_windowing import build_diagnostic_record_windows
    from backend.services.ontology_pipeline import _bind_candidates_to_record_windows, _record_windows

    graph = json.loads(args.graph.read_text())
    with sqlite3.connect((args.source_run / "operational.db").resolve().as_uri() + "?mode=ro", uri=True) as conn:
        units = [EvidenceUnit.model_validate_json(row[0]) for row in conn.execute("SELECT payload_json FROM evidence_units")]
    units = [unit for unit in units if isinstance(unit.locator, PdfLocator) and unit.source_id == graph["source_id"]]
    windows = _record_windows({"record_windows": [w.model_dump(mode="json") for w in build_diagnostic_record_windows(units)]})
    comparisons = []
    for index, original in enumerate(graph["diagnostic_compilation_ledger"]["records"]):
        if not original.get("candidate") or original.get("accounting_state") == "duplicate_verified_occurrence":
            continue
        envelope = DiagnosticChunkOutput.model_validate({"schema_version": "1.1", "source_language": "en", "records": [original["candidate"]]})
        bound = _bind_candidates_to_record_windows(envelope, windows, strict=False)
        compiled = compile_diagnostic_bundles(bound, source_type="technical PDF", source_title=graph["source_name"], evidence_units=units, record_windows=windows)
        entry = compiled.report.entries[0].model_dump(mode="json")
        comparisons.append({"original_index": index, "before": original["disposition"], "after": entry["disposition"], "original_branch_id": original["branch_lineage_id"], "entry": entry})
    result = {
        "mode": "offline_candidate_recompilation_not_full_extraction",
        "api_calls_made": 0, "gold_used": False,
        "graph_sha256": hashlib.sha256(args.graph.read_bytes()).hexdigest(),
        "code_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "backend").rglob("*.py"))},
        "window_count": len(windows),
        "transitions": dict(Counter(f"{c['before']}->{c['after']}" for c in comparisons)),
        "comparisons": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"windows": len(windows), "transitions": result["transitions"]}))


if __name__ == "__main__":
    main()
