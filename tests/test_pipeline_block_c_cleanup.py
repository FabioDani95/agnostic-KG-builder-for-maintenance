"""Regression tests for the block-C cleanup (2026-07-14):

- re-exporting the same bundle bumps the file version (V0 -> V1 -> ...)
- an already-prepared contract payload is persisted without a second prepare
- cycle detection is SCC-based (one issue per cycle group, self-loops included)
- relation suggestions return up to top-K candidates per source node
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.models import OntologyInstance
from backend.services import ontology_export_store
from backend.services.graph_reasoning import (
    build_nx_graph,
    detect_invalid_cycles,
    suggest_missing_relations,
)
from backend.services.ontology_schema_service import load_ontology_schema


RAW_ONTOLOGY = {
    "ontology_name": "DiagnosticOntology",
    "version": "V0",
    "language": "en",
    "source_type": "Service manual",
    "source_title": "Demo Manual",
    "nodes": {
        "Asset": [{
            "asset_id": "ASSET-001", "name": "Demo", "description": "d",
            "brand": "Demo", "model": "M1",
        }],
        "Component": [],
        "Symptom": [{
            "symptom_id": "SYM-001", "name": "No power",
            "description": "Unit does not start", "severity": "High",
        }],
        "FailureMode": [{
            "failure_mode_id": "FM-001", "name": "Fuse blown",
            "description": "Main fuse blown", "material_context": "asset_level",
        }],
        "CorrectiveAction": [{
            "action_id": "CA-001", "name": "Replace fuse",
            "description": "Replace the fuse", "instruction_text": "1. Replace the fuse.",
        }],
        "ErrorCode": [],
    },
    "relations": [
        {"name": "MAY_INDICATE", "from_id": "SYM-001", "to_id": "FM-001"},
        {"name": "RESOLVED_BY", "from_id": "FM-001", "to_id": "CA-001"},
    ],
}


def _patch_export_roots(tmp_path, monkeypatch):
    output_dir = tmp_path / "output"
    generated_dir = tmp_path / "generated"
    latest_dir = output_dir / "latest"
    monkeypatch.setattr(ontology_export_store, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(ontology_export_store, "GENERATED_DIR", generated_dir)
    monkeypatch.setattr(ontology_export_store, "LATEST_OUTPUT_DIR", latest_dir)
    monkeypatch.setattr(ontology_export_store, "LATEST_ONTOLOGY_PATH", latest_dir / "ontology.json")
    monkeypatch.setattr(ontology_export_store, "LATEST_METRICS_PATH", latest_dir / "metrics.json")
    return output_dir


def test_reexport_bumps_file_version(tmp_path, monkeypatch):
    _patch_export_roots(tmp_path, monkeypatch)

    first = ontology_export_store.persist_exported_ontology(
        dict(RAW_ONTOLOGY), manual_filename="demo_manual.pdf",
    )
    second = ontology_export_store.persist_exported_ontology(
        dict(RAW_ONTOLOGY), manual_filename="demo_manual.pdf",
    )

    assert first["version"] == "V0"
    assert second["version"] == "V1"
    payload = json.loads(Path(second["target_path"]).read_text(encoding="utf-8"))
    assert payload["metadata"]["file_version"] == "V1"


def test_prepared_payload_is_persisted_without_second_prepare(tmp_path, monkeypatch):
    _patch_export_roots(tmp_path, monkeypatch)
    prepared = ontology_export_store.prepare_exported_ontology(dict(RAW_ONTOLOGY))
    assert prepared["metadata"]["export_status"] in ("ok", "warning")
    relationship_count = len(prepared["relationships"])

    calls = {"prepare": 0}
    original_prepare = ontology_export_store.prepare_exported_ontology

    def _counting_prepare(*args, **kwargs):
        calls["prepare"] += 1
        return original_prepare(*args, **kwargs)

    monkeypatch.setattr(ontology_export_store, "prepare_exported_ontology", _counting_prepare)

    export_info = ontology_export_store.persist_exported_ontology(
        prepared, manual_filename="demo_manual.pdf",
    )

    assert calls["prepare"] == 0  # no re-prepare of an already prepared payload
    payload = json.loads(Path(export_info["target_path"]).read_text(encoding="utf-8"))
    assert len(payload["relationships"]) == relationship_count
    assert payload["metadata"]["file_version"] == "V0"


def _cyclic_ontology() -> OntologyInstance:
    data = json.loads(json.dumps(RAW_ONTOLOGY))
    data["relations"] = [
        {"name": "MAY_INDICATE", "from_type": "Symptom", "from_id": "SYM-001",
         "to_type": "FailureMode", "to_id": "FM-001", "evidence": []},
        # Back-edge closing a 2-node cycle: FM -> SYM on top of SYM -> FM.
        {"name": "MAY_INDICATE", "from_type": "FailureMode", "from_id": "FM-001",
         "to_type": "Symptom", "to_id": "SYM-001", "evidence": []},
    ]
    return OntologyInstance.model_validate(data)


def test_cycle_detection_reports_scc_groups_and_self_loops():
    ontology = _cyclic_ontology()
    graph = build_nx_graph(ontology)
    graph.add_edge("CA-001", "CA-001", relation_name="RESOLVED_BY")

    issues = detect_invalid_cycles(graph)

    cycle_groups = [set(issue.affected_nodes) for issue in issues]
    assert {"SYM-001", "FM-001"} in cycle_groups
    assert {"CA-001"} in cycle_groups


def test_suggestions_return_multiple_candidates_per_source():
    data = json.loads(json.dumps(RAW_ONTOLOGY))
    data["nodes"]["Symptom"] = [{
        "symptom_id": "sym_pump_noise", "name": "Hydraulic pump noise",
        "description": "Loud noise from the hydraulic pump area", "severity": "Medium",
    }]
    data["nodes"]["FailureMode"] = [
        {"failure_mode_id": "fm_pump_worn", "name": "Hydraulic pump worn",
         "description": "Hydraulic pump internals worn", "material_context": "asset_level"},
        {"failure_mode_id": "fm_pump_cavitation", "name": "Hydraulic pump cavitation",
         "description": "Cavitation in the hydraulic pump", "material_context": "asset_level"},
    ]
    data["relations"] = []
    ontology = OntologyInstance.model_validate(data)

    suggestions = suggest_missing_relations(ontology, load_ontology_schema())

    may_indicate_targets = {
        suggestion.to_id
        for suggestion in suggestions
        if suggestion.relation_name == "MAY_INDICATE"
        and suggestion.from_id == "sym_pump_noise"
    }
    # Both plausible parallel causes are proposed, not only the single best one.
    assert {"fm_pump_worn", "fm_pump_cavitation"} <= may_indicate_targets
