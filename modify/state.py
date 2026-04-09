from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional

from backend.services.ontology_export_store import (
    GENERATED_DIR as EXPORT_GENERATED_DIR,
    LEGACY_ONTOLOGY_PATH as EXPORT_LEGACY_PATH,
    LATEST_ONTOLOGY_PATH as EXPORT_LATEST_PATH,
    build_export_filename,
    bump_file_version,
    normalize_file_version,
    prepare_exported_ontology,
)
from backend.services.legacy_ontology_migration import migrate_legacy_ontology
from .config import LEGACY_ONTOLOGY_PATH, ONTOLOGY_PATH

# ---------------------------------------------------------------------------
# In-memory working state
# ---------------------------------------------------------------------------
_working_ontology: Optional[Dict[str, Any]] = None
_has_unsaved_changes: bool = False


def _clone(value: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(value)


def _normalize_ontology(raw: Dict[str, Any]) -> Dict[str, Any]:
    return migrate_legacy_ontology(_clone(raw))


def _resolve_read_path(path: Path | None = None) -> Path:
    candidate = path or ONTOLOGY_PATH
    if candidate.exists():
        return candidate
    if path is None and LEGACY_ONTOLOGY_PATH.exists():
        return LEGACY_ONTOLOGY_PATH
    raise FileNotFoundError(f"Ontology JSON non trovato in {candidate}")


def relation_items(ontology: Dict[str, Any]) -> list[Dict[str, Any]]:
    return ontology.setdefault("relations", [])


def ontology_version(ontology: Dict[str, Any]) -> str:
    return normalize_file_version(ontology.get("metadata", {}).get("file_version") or ontology.get("version"))


def load_ontology(path: Path | None = None) -> Dict[str, Any]:
    ontology_path = _resolve_read_path(path)
    with ontology_path.open("r", encoding="utf-8") as f:
        return _normalize_ontology(json.load(f))


def _bump_version(current_version: str) -> str:
    return bump_file_version(current_version)


def save_ontology_to_path(ontology: Dict[str, Any], path: Path) -> Dict[str, Any]:
    ont = _normalize_ontology(ontology)
    new_ver = _bump_version(ontology_version(ont))
    ont = prepare_exported_ontology(ont, version=new_ver)
    ont["metadata"]["total_nodes"] = sum(len(items) for items in ont.get("nodes", {}).values())
    ont["metadata"]["total_relationships"] = len(ont.get("relationships", []))

    EXPORT_GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    target_path = EXPORT_GENERATED_DIR / build_export_filename(ont)
    payload = json.dumps(ont, indent=2, ensure_ascii=False)

    for out_path in (target_path, EXPORT_LATEST_PATH, EXPORT_LEGACY_PATH):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")

    return {
        "ok": True,
        "version": new_ver,
        "saved_as": target_path.name,
        "target_path": str(target_path),
        "total_nodes": ont["metadata"]["total_nodes"],
        "total_relationships": ont["metadata"]["total_relationships"],
    }


def get_working_ontology() -> Dict[str, Any]:
    global _working_ontology
    if _working_ontology is None:
        _working_ontology = _clone(load_ontology())
    return _working_ontology


def _mark_dirty() -> None:
    global _has_unsaved_changes
    _has_unsaved_changes = True


def is_dirty() -> bool:
    return _has_unsaved_changes


def clear_dirty() -> None:
    global _has_unsaved_changes
    _has_unsaved_changes = False


def save_to_disk() -> Dict[str, Any]:
    ont = get_working_ontology()
    result = save_ontology_to_path(ont, ONTOLOGY_PATH)
    clear_dirty()
    return result
