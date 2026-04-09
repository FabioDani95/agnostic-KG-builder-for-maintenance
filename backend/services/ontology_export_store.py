from __future__ import annotations

import copy
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from backend.services.ontology_contract import build_and_validate_contract_ontology

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_DIR = ROOT_DIR / "data" / "generated"
LATEST_ONTOLOGY_PATH = GENERATED_DIR / "latest_ontology.json"
LEGACY_ONTOLOGY_PATH = ROOT_DIR / "ontology.json"


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized.strip().lower()).strip("_")
    return slug or "unknown"


def normalize_file_version(value: str | None) -> str:
    raw = str(value or "").strip().upper()
    match = re.fullmatch(r"V(\d+)", raw)
    if match:
        return f"V{int(match.group(1))}"
    return "V0"


def bump_file_version(value: str | None) -> str:
    current = normalize_file_version(value)
    return f"V{int(current[1:]) + 1}"


def _primary_asset_node(ontology: dict[str, Any]) -> dict[str, Any]:
    nodes = ontology.get("nodes", {})
    items = nodes.get("Asset", [])
    if items:
        return items[0]
    return {}


def build_export_filename(ontology: dict[str, Any]) -> str:
    asset = _primary_asset_node(ontology)
    product = (
        str(asset.get("model") or "").strip()
        or str(asset.get("name") or "").strip()
        or Path(str(ontology.get("source_title") or "ontology")).stem
    )
    brand = (
        str(asset.get("manufacturer") or "").strip()
        or str(asset.get("brand") or "").strip()
        or "unknown"
    )
    version = normalize_file_version(
        ontology.get("metadata", {}).get("file_version")
        or ontology.get("version")
    )
    return f"{_slugify(product)}_{_slugify(brand)}_{version}.json"


def prepare_exported_ontology(
    ontology: dict[str, Any],
    version: str | None = None,
) -> dict[str, Any]:
    prepared, issues = build_and_validate_contract_ontology(copy.deepcopy(ontology))
    if issues:
        raise ValueError("Exported ontology is not compliant: " + " | ".join(issues))

    metadata = prepared.setdefault("metadata", {})
    file_version = normalize_file_version(version or metadata.get("file_version"))
    metadata["version"] = file_version
    metadata["file_version"] = file_version
    metadata["total_nodes"] = sum(len(items) for items in prepared.get("nodes", {}).values())
    metadata["total_relationships"] = len(prepared.get("relationships", []))
    return prepared


def ontology_path_for_pdf(pdf_id: str) -> Path:
    manifest_path = GENERATED_DIR / f"{pdf_id}.path"
    if manifest_path.exists():
        return Path(manifest_path.read_text(encoding="utf-8").strip())
    return GENERATED_DIR / f"{pdf_id}_ontology.json"


def persist_exported_ontology(ontology: dict[str, Any], pdf_id: str | None = None) -> dict[str, str]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    prepared = prepare_exported_ontology(ontology, version="V0")
    filename = build_export_filename(prepared)
    target_path = GENERATED_DIR / filename

    payload = json.dumps(prepared, indent=2, ensure_ascii=False)
    for path in (target_path, LATEST_ONTOLOGY_PATH, LEGACY_ONTOLOGY_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")

    if pdf_id:
        manifest_path = GENERATED_DIR / f"{pdf_id}.path"
        manifest_path.write_text(str(target_path), encoding="utf-8")

    return {
        "target_path": str(target_path),
        "filename": filename,
        "latest_path": str(LATEST_ONTOLOGY_PATH),
        "legacy_path": str(LEGACY_ONTOLOGY_PATH),
        "version": prepared.get("metadata", {}).get("version", ""),
    }
