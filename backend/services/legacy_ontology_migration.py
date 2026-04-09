from __future__ import annotations

import copy
from typing import Any


def _as_string(value: Any) -> str:
    return str(value or "").strip()


def _clone(value: Any) -> Any:
    return copy.deepcopy(value)


def _migrate_printer_nodes(raw_nodes: dict[str, Any]) -> dict[str, Any]:
    nodes = _clone(raw_nodes) if isinstance(raw_nodes, dict) else {}
    if "Printer" not in nodes:
        return nodes

    printer_items = nodes.pop("Printer")
    if "Asset" in nodes:
        return nodes

    migrated_assets = []
    for index, item in enumerate(printer_items if isinstance(printer_items, list) else [], start=1):
        if not isinstance(item, dict):
            continue
        migrated = _clone(item)
        migrated["asset_id"] = _as_string(
            migrated.get("asset_id") or migrated.get("printer_id") or f"ASSET-{index:03d}"
        )
        migrated["description"] = _as_string(migrated.get("description") or migrated.get("name"))
        migrated["brand"] = _as_string(migrated.get("brand") or migrated.get("manufacturer"))
        migrated["model"] = _as_string(migrated.get("model"))
        migrated.pop("printer_id", None)
        migrated.pop("manufacturer", None)
        migrated_assets.append(migrated)

    nodes["Asset"] = migrated_assets
    return nodes


def _normalize_relations(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    raw_relations = ontology.get("relations")
    if not isinstance(raw_relations, list):
        raw_relations = ontology.get("relationships", [])
    if not isinstance(raw_relations, list):
        return []

    normalized_relations = []
    for rel in raw_relations:
        if not isinstance(rel, dict):
            continue
        normalized = _clone(rel)
        if not _as_string(normalized.get("name")) and _as_string(normalized.get("type")):
            normalized["name"] = _as_string(normalized["type"])
        if "type" in normalized:
            normalized.pop("type", None)
        normalized.setdefault("from_type", "")
        normalized.setdefault("to_type", "")
        normalized.setdefault("evidence", [])
        normalized_relations.append(normalized)
    return normalized_relations


def migrate_legacy_ontology(raw: dict[str, Any]) -> dict[str, Any]:
    ont = _clone(raw) if isinstance(raw, dict) else {}
    metadata = ont.setdefault("metadata", {})
    ont["nodes"] = _migrate_printer_nodes(ont.get("nodes", {}))
    ont["relations"] = _normalize_relations(ont)
    ont.pop("relationships", None)

    ont.setdefault("ontology_name", metadata.get("ontology_name", "Ontology graph"))
    ont.setdefault("version", metadata.get("version", "1.0"))
    ont.setdefault("language", metadata.get("language", "en"))
    ont.setdefault("source_type", metadata.get("source_type", ""))
    ont.setdefault("source_title", metadata.get("source_title", ""))

    metadata["ontology_name"] = ont["ontology_name"]
    metadata["version"] = ont["version"]
    metadata["language"] = ont["language"]
    metadata["source_type"] = ont["source_type"]
    metadata["source_title"] = ont["source_title"]
    metadata["total_nodes"] = sum(len(items) for items in ont.get("nodes", {}).values())
    metadata["total_relationships"] = len(ont.get("relations", []))
    return ont
