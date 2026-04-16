import json
from pathlib import Path

from backend.services import ontology_export_store


RAW_ONTOLOGY = {
    "ontology_name": "DiagnosticOntology",
    "version": "V0",
    "language": "en",
    "source_type": "Service manual",
    "source_title": "Laser Printer Manual",
    "nodes": {
        "Asset": [
            {
                "asset_id": "ASSET-001",
                "name": "Laser Printer",
                "description": "Desktop printer",
                "brand": "BambuLab",
                "model": "P1P",
            }
        ],
        "Component": [
            {
                "component_id": "CMP-001",
                "name": "Nozzle",
                "description": "Extrusion nozzle",
                "category": "Toolhead",
            }
        ],
        "Symptom": [
            {
                "symptom_id": "SYM-001",
                "name": "No extrusion",
                "description": "No material comes out of the nozzle",
                "severity": "High",
            }
        ],
        "FailureMode": [
            {
                "failure_mode_id": "FM-001",
                "name": "Clogged nozzle",
                "description": "The nozzle is blocked",
                "material_context": "Nozzle",
            }
        ],
        "CorrectiveAction": [
            {
                "action_id": "CA-001",
                "name": "Clear the nozzle",
                "description": "Remove the blockage",
                "instruction_text": "1. Heat the nozzle.\n2. Clean the nozzle.",
            }
        ],
        "ErrorCode": [],
    },
    "relations": [
        {"name": "HAS_COMPONENT", "from_id": "ASSET-001", "to_id": "CMP-001"},
        {"name": "AFFECTS", "from_id": "FM-001", "to_id": "CMP-001"},
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
    return output_dir, generated_dir, latest_dir


def test_persist_exported_ontology_writes_bundle_in_output(tmp_path, monkeypatch):
    output_dir, generated_dir, latest_dir = _patch_export_roots(tmp_path, monkeypatch)

    export_info = ontology_export_store.persist_exported_ontology(
        RAW_ONTOLOGY,
        pdf_id="pdf-001",
        manual_filename="Bambu Lab P1P Manual.pdf",
    )

    target_path = Path(export_info["target_path"])
    assert target_path == output_dir / "bambu_lab_p1p_manual" / "ontology.json"
    assert target_path.exists()
    assert export_info["download_filename"] == "bambu_lab_p1p_manual_ontology.json"
    assert (latest_dir / "ontology.json").exists()
    assert (generated_dir / "pdf-001.path").read_text(encoding="utf-8") == str(target_path)

    payload = json.loads(target_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["total_nodes"] == 5
    assert payload["metadata"]["total_relationships"] == 4


def test_persist_export_metrics_writes_summary_json_next_to_ontology(tmp_path, monkeypatch):
    output_dir, _, latest_dir = _patch_export_roots(tmp_path, monkeypatch)
    export_info = ontology_export_store.persist_exported_ontology(
        RAW_ONTOLOGY,
        manual_filename="Bambu Lab P1P Manual.pdf",
    )
    metrics_payload = {
        "stages": {
            "extraction": {"details": {"triplet_count": 130}},
            "export": {"details": {"validated_triplets": 126}},
        },
        "totals": {
            "duration_seconds": 765,
            "estimated_cost_usd": 2.18,
            "total_tokens": 312450,
            "by_model": {
                "gpt-5.4": {"label": "GPT-5.4", "total_tokens": 300000},
                "gpt-5.4-mini": {"label": "GPT-5.4 Mini", "total_tokens": 12450},
            },
        },
    }

    metrics_info = ontology_export_store.persist_export_metrics(
        metrics_payload,
        ontology_export_store.prepare_exported_ontology(RAW_ONTOLOGY),
        export_info,
        manual_filename="Bambu Lab P1P Manual.pdf",
    )

    target_path = Path(metrics_info["target_path"])
    assert target_path == output_dir / "bambu_lab_p1p_manual" / "metrics.json"
    assert target_path.exists()
    assert (latest_dir / "metrics.json").exists()

    payload = json.loads(target_path.read_text(encoding="utf-8"))
    assert payload["context"]["kg_id"] == "bambu_lab_p1p_manual"
    assert payload["context"]["source_manual"] == "Bambu Lab P1P Manual.pdf"
    assert payload["extraction_performance"]["triplets_validated"] == 126
    assert payload["extraction_performance"]["total_automation_time"] == "12m 45s"
    assert payload["model_usage"]["primary_model"] == "GPT-5.4"
    assert payload["model_usage"]["secondary_model"] == "GPT-5.4 Mini"
    assert payload["file_links"]["ontology"] == "./bambu_lab_p1p_manual/ontology.json"
