from __future__ import annotations

import copy
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.services.ontology_contract import build_and_validate_contract_ontology

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
GENERATED_DIR = ROOT_DIR / "data" / "generated"
LATEST_OUTPUT_DIR = OUTPUT_DIR / "latest"
LATEST_ONTOLOGY_PATH = LATEST_OUTPUT_DIR / "ontology.json"
LATEST_METRICS_PATH = LATEST_OUTPUT_DIR / "metrics.json"
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


def _manual_stem(manual_filename: str | None) -> str:
    if not manual_filename:
        return ""
    return Path(str(manual_filename)).stem.strip()


def build_export_bundle_name(
    ontology: dict[str, Any],
    manual_filename: str | None = None,
) -> str:
    manual_stem = _manual_stem(manual_filename)
    if manual_stem:
        return _slugify(manual_stem)

    asset = _primary_asset_node(ontology)
    candidate = (
        str(ontology.get("source_title") or "").strip()
        or str(asset.get("model") or "").strip()
        or str(asset.get("name") or "").strip()
        or str(ontology.get("metadata", {}).get("product_name") or "").strip()
        or "ontology"
    )
    return _slugify(Path(candidate).stem)


def build_export_directory(
    ontology: dict[str, Any],
    manual_filename: str | None = None,
) -> Path:
    return OUTPUT_DIR / build_export_bundle_name(ontology, manual_filename=manual_filename)


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
    return LATEST_ONTOLOGY_PATH


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _top_model_labels(metrics_payload: dict[str, Any]) -> tuple[str | None, str | None]:
    buckets = list(((metrics_payload.get("totals") or {}).get("by_model") or {}).values())
    ranked = sorted(
        buckets,
        key=lambda item: (-int(item.get("total_tokens", 0) or 0), str(item.get("label", ""))),
    )
    primary = str(ranked[0].get("label", "")).strip() if ranked else ""
    secondary = str(ranked[1].get("label", "")).strip() if len(ranked) > 1 else ""
    return (primary or None, secondary or None)


def _format_duration(seconds: float | int | None) -> str:
    total_seconds = max(0, int(round(float(seconds or 0))))
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def build_metrics_export_document(
    metrics_payload: dict[str, Any],
    ontology: dict[str, Any],
    export_info: dict[str, str],
    *,
    manual_filename: str | None = None,
) -> dict[str, Any]:
    totals = metrics_payload.get("totals", {}) or {}
    stages = metrics_payload.get("stages", {}) or {}
    export_stage = stages.get("export", {}) or {}
    extraction_stage = stages.get("extraction", {}) or {}
    metadata = ontology.get("metadata", {}) or {}
    primary_model, secondary_model = _top_model_labels(metrics_payload)
    bundle_name = export_info["directory_name"]
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    validated_triplets = int(
        export_stage.get("details", {}).get("validated_triplets")
        or extraction_stage.get("details", {}).get("triplet_count")
        or 0
    )

    return {
        "context": {
            "kg_id": bundle_name,
            "version": str(metadata.get("version") or metadata.get("file_version") or "V0"),
            "ontology_ref": (
                str(metadata.get("product_name") or "").strip()
                or str(metadata.get("product_short_name") or "").strip()
                or bundle_name
            ),
            "source_manual": str(manual_filename or "").strip(),
            "extraction_timestamp": timestamp,
        },
        "extraction_performance": {
            "status": "EXTRACTION COMPLETE",
            "triplets_validated": validated_triplets,
            "total_automation_time": _format_duration(totals.get("duration_seconds", 0)),
            "estimated_cost_usd": round(float(totals.get("estimated_cost_usd", 0) or 0), 6),
            "llm_tokens": int(totals.get("total_tokens", 0) or 0),
        },
        "model_usage": {
            "primary_model": primary_model,
            "secondary_model": secondary_model,
        },
        "file_links": {
            "metrics": f"./{bundle_name}/metrics.json",
            "ontology": f"./{bundle_name}/ontology.json",
        },
        "pipeline_metrics": metrics_payload,
    }


def persist_exported_ontology(
    ontology: dict[str, Any],
    pdf_id: str | None = None,
    *,
    manual_filename: str | None = None,
) -> dict[str, str]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    prepared = prepare_exported_ontology(ontology, version="V0")
    export_dir = build_export_directory(prepared, manual_filename=manual_filename)
    target_path = export_dir / "ontology.json"

    _write_json(target_path, prepared)
    _write_json(LATEST_ONTOLOGY_PATH, prepared)

    if pdf_id:
        manifest_path = GENERATED_DIR / f"{pdf_id}.path"
        manifest_path.write_text(str(target_path), encoding="utf-8")

    return {
        "target_path": str(target_path),
        "directory": str(export_dir),
        "directory_name": export_dir.name,
        "filename": target_path.name,
        "download_filename": f"{export_dir.name}_ontology.json",
        "metrics_path": str(export_dir / "metrics.json"),
        "metrics_filename": "metrics.json",
        "latest_path": str(LATEST_ONTOLOGY_PATH),
        "latest_metrics_path": str(LATEST_METRICS_PATH),
        "version": prepared.get("metadata", {}).get("version", ""),
    }


def persist_export_metrics(
    metrics_payload: dict[str, Any],
    ontology: dict[str, Any],
    export_info: dict[str, str],
    *,
    manual_filename: str | None = None,
) -> dict[str, str]:
    metrics_document = build_metrics_export_document(
        metrics_payload,
        ontology,
        export_info,
        manual_filename=manual_filename,
    )
    target_path = Path(export_info["metrics_path"])
    _write_json(target_path, metrics_document)
    _write_json(LATEST_METRICS_PATH, metrics_document)
    return {
        "target_path": str(target_path),
        "filename": target_path.name,
        "latest_path": str(LATEST_METRICS_PATH),
    }
