"""Prepare prediction-free source packets and independent annotation forms."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "paper/evaluation/gold_review_v1"
SCOPES = {
    "eastman_e554": [37, 38, 39],
    "danfoss_apf": [64],
    "graco_check_mate_200": [11],
    "hypertherm_powermax30_air": [*range(65, 78), *range(82, 105), 228],
}
CONTEXT = {"eastman_e554": [], "danfoss_apf": [], "graco_check_mate_200": [9, 10, 12, 13, 14], "hypertherm_powermax30_air": [78, 79, 80, 81]}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    if DEST.exists():
        raise RuntimeError("Review packet already exists; create a new version instead of overwriting annotations")
    manifest = json.loads((ROOT / "paper/experiments/robustness_20260925/manifest.json").read_text())
    historical = ROOT / "artifacts/acceptance/g3/diagnostic_benchmark_20260812/golden.json"
    old = json.loads(historical.read_text())
    for manual in manifest["manuals"]:
        key = manual["manual_id"]
        path = ROOT / "paper/manuals/files" / manual["file_name"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != manual["sha256"]:
            raise RuntimeError("PDF digest mismatch")
        destination = DEST / key
        destination.mkdir(parents=True)
        pages = sorted(set(SCOPES[key] + CONTEXT[key]))
        with fitz.open(path) as source, fitz.open() as subset:
            units = []
            for number in pages:
                page = source[number - 1]
                subset.insert_pdf(source, from_page=number - 1, to_page=number - 1)
                units.append({"physical_page": number, "packet_page": len(units) + 1, "role": "scope" if number in SCOPES[key] else "context_only", "native_text_unverified": page.get_text("text"), "blocks": [{"bbox": list(block[:4]), "text": block[4]} for block in page.get_text("blocks") if block[6] == 0]})
            subset.save(destination / "source_pages.pdf")
        write(destination / "source_inventory.json", {"manual_id": key, "pdf_sha256": manual["sha256"], "scope_pages": SCOPES[key], "context_pages": CONTEXT[key], "pages": units, "native_text_is_gold": False})
        form = {"schema_version": "gold-diagnostic-1.0", "annotation_version": "proposed-v1", "document_id": key, "document_sha256": manual["sha256"], "validation_status": "unannotated", "scope_pages": SCOPES[key], "scope_exhaustive": True, "source_only_annotation": True, "annotator_id": None, "branches": [], "equivalences": {}, "adjudication": {"reviewer_id": None, "decisions": []}}
        for annotator in ("A", "B"):
            write(destination / f"annotation_{annotator}.json", form)
        old_manual = next((item for item in old["manuals"] if item["manual_id"] == key), None)
        write(destination / "historical_proposals_for_adjudicator.json", {"status": "historical_unverified_not_gold", "origin_sha256": hashlib.sha256(historical.read_bytes()).hexdigest(), "claims": old_manual["expected_claims"] if old_manual else [], "show_after_independent_annotation": True})
    write(DEST / "manifest.json", {"status": "awaiting_two_independent_technical_annotations", "predictions_loaded": False, "gold_original_sha256": hashlib.sha256(historical.read_bytes()).hexdigest(), "source_scopes": SCOPES, "context_pages": CONTEXT})


if __name__ == "__main__":
    main()
