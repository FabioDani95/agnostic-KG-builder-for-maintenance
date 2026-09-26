"""Read-only artifact audit and synthetic offline probes; never calls a provider.

Run from the repository with KG_LLM_MODE=mock. This is analysis tooling, not an
implementation of the proposed pipeline or a scientific extraction benchmark.
PDF inventories are read from frozen SQLite artifacts, never regenerated.
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ["KG_LLM_MODE"] = "mock"
PILOT = ROOT / "paper/experiments/dev_luna_20260925"


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from pydantic import ValidationError

    from backend.adapters.pdf import evidence_units_to_legacy_pages
    from backend.domain.diagnostic_bundles import DiagnosticBundleCandidate, DiagnosticChunkOutput
    from backend.domain.evidence import EvidenceUnit
    from backend.services import ontology_pipeline as pipeline
    from backend.services.cutplan_service import has_supported_language_content
    from backend.services.diagnostic_bundle_compiler import compile_diagnostic_bundles
    from backend.services.ontology_contract import _normalize_relationships
    from backend.services.ontology_schema_service import load_ontology_schema
    from backend.services.ontology_workflow import _run_chunk_with_retry, _split_pages_by_section

    results = {
        "kind": "offline_analysis_not_extraction_quality_validation",
        "real_api_calls": 0,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "audit_script_sha256": digest(Path(__file__)),
        "gold_sha256": digest(ROOT / "artifacts/acceptance/g3/diagnostic_benchmark_20260812/golden.json"),
        "runtime": {name: importlib.metadata.version(name) for name in ("openai", "pymupdf", "pydantic")},
        "runtime_note": "Local runtime differs from pilot. No PDF inventory regeneration or provider call is performed.",
        "artifact_hash_mismatches": [],
        "manuals": {},
        "probes": {},
    }
    manifest = read(PILOT / "artifact_manifest.json")["files"]
    results["artifact_hashes_checked"] = len(manifest)
    for name, spec in manifest.items():
        if digest(PILOT / name) != spec["sha256"]:
            results["artifact_hash_mismatches"].append(name)
    for spec in read(PILOT / "manifest.json")["manuals"]:
        name = spec["manual_id"]
        run = PILOT / "runs/real" / name
        graph = read(run / "graph.json")
        response = read(run / "generation_response.json")
        ledger = graph["diagnostic_compilation_ledger"]
        db = run / "operational.db"
        with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as conn:
            payloads = conn.execute("SELECT payload_json FROM evidence_units ORDER BY evidence_id").fetchall()
        evidence = [EvidenceUnit.model_validate_json(p[0]) for p in payloads]
        evidence = [e for e in evidence if e.locator.kind == "pdf"]
        pages = evidence_units_to_legacy_pages(evidence)
        page_map = {p["page_number"]: p for p in pages}
        replayed, changed = 0, []
        for entry in ledger["records"]:
            if not entry.get("candidate"):
                continue
            candidate = DiagnosticBundleCandidate.model_validate(entry["candidate"])
            replay = compile_diagnostic_bundles(
                [candidate], source_type="technical PDF", source_title=spec["file_name"], evidence_units=evidence,
            ).report.entries[0]
            replayed += 1
            if replay.disposition.value != entry["disposition"]:
                changed.append({"branch": entry["branch_lineage_id"], "before": entry["disposition"], "after": replay.disposition.value})
        selected_pages = graph["pdf_extraction_scope"]["selected_pages"]
        results["manuals"][name] = {
            "pdf_hash_verified": digest(ROOT / "paper/manuals/files" / spec["file_name"]) == spec["sha256"],
            "graph_matches_generation_response": graph == response["sources"][0]["subgraph"],
            "scope_counts": {k: len(graph["pdf_extraction_scope"][k]) for k in ("selected_pages", "diagnostic_pages", "structural_pages", "retrieval_pages")},
            "node_types": dict(Counter(n["node_type"] for n in graph["nodes"])),
            "review_codes": dict(Counter(r["code"] for r in graph["review_queue"])),
            "candidate_count": ledger["candidate_count"],
            "typed_candidates": replayed,
            "synthetic_records": sum(not r.get("candidate") for r in ledger["records"]),
            "dispositions": dict(Counter(r["disposition"] for r in ledger["records"])),
            "replay_changed_dispositions": changed,
            "inspection_steps_in_candidates": sum(len((r.get("candidate") or {}).get("inspection_steps", [])) for r in ledger["records"]),
            "inspection_steps_in_publish_candidates": sum(len((r.get("candidate") or {}).get("inspection_steps", [])) for r in ledger["records"] if r["disposition"] == "publish"),
            "failed_chunks": [
                {k: c.get(k) for k in ("input_pages", "error_type", "finish_reason", "candidate_count", "provider_response_id", "raw_sha256", "candidate_input_anchors")}
                for c in ledger["chunks"] if not c["parsed"]
            ],
            "key_pages": {
                str(n): {
                    "selected": n in selected_pages,
                    "canonical_units": sum(e.locator.page == n for e in evidence),
                    "rendered_anchors": len(page_map.get(n, {}).get("evidence_anchors", [])),
                    "language_filter_pass": has_supported_language_content(page_map.get(n, {}).get("text", ""), 0.3),
                }
                for n in ({"eastman_e554": [37, 38, 39], "danfoss_apf": [64], "graco_check_mate_200": [11], "hypertherm_powermax30_air": [65, 77, 85, 228]}[name])
            },
        }
        if name == "danfoss_apf":
            for e in evidence:
                if e.evidence_id == "ev_e5afd58033ce44902f2fb94c0b62":
                    results["probes"]["danfoss_wrong_anchor"] = {"anchor": e.evidence_id, "text": e.locator.quote, "cited_quote": "the individual modules.", "literal_match": "the individual modules." in e.locator.quote}

    def span(anchor, quote):
        return {"source_anchor": anchor, "source_page": 1, "quote": quote}

    # Every span is literal, but the indicator comes from the wrong source row.
    wrong_branch = {
        "record_anchor": "ev_row_a", "branch_anchor": "ev_row_b",
        "record_window_id": "", "allowed_source_anchors": ["ev_row_a", "ev_row_b"],
        "indicators": [{"kind": "symptom", "code": None, "name": "Pump stops", "description": "Pump stops", "severity": "High", "claim_evidence": [span("ev_row_a", "Pump stops")], "failure_link_evidence": [span("ev_row_b", "Motor overheats because the fan is broken.")]}],
        "failure": {"name": "Broken fan", "description": "The fan is broken", "material_context": None, "claim_evidence": [span("ev_row_b", "fan is broken")]},
        "actions": [{"name": "Replace fan", "description": "Replace the fan", "instruction_text": "Replace the fan.", "action_kind": "replacement", "claim_evidence": [span("ev_row_b", "Replace the fan.")], "resolution_link_evidence": [span("ev_row_b", "Motor overheats because the fan is broken. Replace the fan.")]}],
        "inspection_steps": [], "affected_component": None, "resolution_status": "action_stated",
    }
    text = "--- PAGE 1 ---\n[[EVIDENCE_ID: ev_row_a]]\nPump stops because the filter is clogged. Clean the filter.\n\n[[EVIDENCE_ID: ev_row_b]]\nMotor overheats because the fan is broken. Replace the fan."
    compiled = compile_diagnostic_bundles([wrong_branch], source_type="technical PDF", source_title="synthetic", text_with_pages=text)
    results["probes"]["literal_quotes_do_not_prove_relation"] = {
        "synthetic": True, "disposition": compiled.report.entries[0].disposition.value,
        "relations_emitted": len(compiled.ontology.relations), "explanation": "Pump stops is linked to the broken fan of a different row; all cited strings exist.",
    }
    invalid = copy.deepcopy(wrong_branch)
    invalid["indicators"] = []
    envelope = {"schema_version": "1.0", "source_language": "en", "records": [wrong_branch, invalid]}
    try:
        DiagnosticChunkOutput.model_validate(envelope)
        rejected, locations = False, []
    except ValidationError as exc:
        rejected, locations = True, [list(e["loc"]) for e in exc.errors()]
    results["probes"]["mixed_record_validation"] = {
        "envelope_rejected": rejected, "invalid_locations": locations,
        "first_record_individually_schema_valid": isinstance(DiagnosticBundleCandidate.model_validate(wrong_branch), DiagnosticBundleCandidate),
    }
    attempts = []

    def fake_parse(**kwargs):
        attempts.append(1)
        raise RuntimeError("connection error: synthetic offline transport failure")

    state = {"source_type": "technical PDF", "source_title": "synthetic", "text_with_pages": text, "model_name": "gpt-6-luna", "reasoning_effort": "low", "schema": load_ontology_schema()}
    with patch.object(pipeline, "_get_client", return_value=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=fake_parse)))):
        returned = asyncio.run(_run_chunk_with_retry(lambda: pipeline._call_diagnostic_bundle_llm(state), attempts=3, base_delay_seconds=0))
    results["probes"]["typed_transport_error_bypasses_outer_retry"] = {"configured_attempts": 3, "actual_fake_attempts": len(attempts), "parsed": returned["diagnostic_contract_report"]["parsed"]}
    chunks = _split_pages_by_section([{"page_number": i, "text": "x" * 100} for i in range(1, 10)], [], max_chars=10000, max_pages=4, overlap_pages=1)
    results["probes"]["overlap_exceeds_page_limit"] = {"configured_pages": 4, "chunk_pages": [[p["page_number"] for p in c[0]] for c in chunks]}
    path = ROOT / "paper/experiments/dev_luna_20260925/analyze_results.py"
    spec = importlib.util.spec_from_file_location("audit_frozen_analyzer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    analyzer = module.load_analyzer()
    pairs = [
        ("fan works", "fan does not work"),
        ("Replace the seal", "Do not replace the seal"),
        ("Pump output is low on down-stroke", "Pump output is low on up-stroke"),
        ("Replace the seal", "Check the seal"),
    ]
    results["probes"]["historical_scorer_contrasts"] = [{"expected": a, "actual": b, "score": analyzer.similarity(a, b), "passes_055": analyzer.similarity(a, b) >= analyzer.MATCH_FLOOR} for a, b in pairs]
    legacy_input = {"name": "INDICATES", "from_id": "symptom", "to_id": "failure", "branch_lineage_id": "synthetic_branch", "record_lineage_id": "synthetic_record", "evidence": []}
    legacy_output = _normalize_relationships([legacy_input])[0].model_dump()
    results["probes"]["legacy_export_discards_lineage"] = {"input_lineage": legacy_input["branch_lineage_id"], "output_keys": sorted(legacy_output), "branch_lineage_preserved": legacy_output.get("branch_lineage_id") == legacy_input["branch_lineage_id"]}
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
