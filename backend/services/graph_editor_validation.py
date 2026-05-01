from __future__ import annotations

import copy
import re
from typing import Any

from modify.graph import _find_node_id_key, _node_id


def _as_string(value: Any) -> str:
    return str(value or "").strip()


def _node_index(ontology: dict[str, Any]) -> dict[str, str]:
    index: dict[str, str] = {}
    for node_type, items in ontology.get("nodes", {}).items():
        for item in items:
            node_id = _node_id(item)
            if node_id:
                index[node_id] = node_type
    return index


def _node_id_key_from_schema(node_type: str, schema: dict[str, Any]) -> str:
    for prop in schema.get("node_types", {}).get(node_type, []):
        name = str(prop.get("name") or "")
        if name.endswith("_id"):
            return name
    return f"{node_type.lower()}_id"


def _node_id_prefix(node_type: str) -> str:
    known = {
        "Asset": "ASSET",
        "Component": "CMP",
        "Symptom": "SYM",
        "FailureMode": "FM",
        "CorrectiveAction": "CA",
        "ErrorCode": "ERR",
    }
    if node_type in known:
        return known[node_type]
    letters = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", node_type)
    prefix = "".join(part[0] for part in letters if part) or node_type[:3]
    return prefix.upper()


def _next_node_id(ontology: dict[str, Any], node_type: str) -> str:
    prefix = _node_id_prefix(node_type)
    existing = set(_node_index(ontology))
    max_seen = 0
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$", re.IGNORECASE)
    for node_id in existing:
        match = pattern.match(node_id)
        if match:
            max_seen = max(max_seen, int(match.group(1)))

    candidate_index = max_seen + 1
    while True:
        candidate = f"{prefix}-{candidate_index:03d}"
        if candidate not in existing:
            return candidate
        candidate_index += 1


def _coerce_property_value(prop: dict[str, Any] | None, value: Any) -> Any:
    if not prop:
        return value
    if prop.get("type") != "array":
        return value
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    if isinstance(value, str):
        return [
            item.strip()
            for item in re.split(r"[\n,]+", value)
            if item.strip()
        ]
    if value in (None, ""):
        return []
    return [str(value).strip()]


def _schema_props_by_name(schema: dict[str, Any], node_type: str) -> dict[str, dict[str, Any]]:
    return {
        str(prop.get("name")): prop
        for prop in schema.get("node_types", {}).get(node_type, [])
        if prop.get("name")
    }


def find_node(ontology: dict[str, Any], node_id: str) -> tuple[str, dict[str, Any]] | None:
    for node_type, items in ontology.get("nodes", {}).items():
        for item in items:
            if _node_id(item) == node_id:
                return node_type, item
    return None


def validate_node_update(
    ontology: dict[str, Any],
    schema: dict[str, Any],
    node_id: str,
    new_attrs: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if not isinstance(new_attrs, dict):
        raise ValueError("attributes must be an object.")

    found = find_node(ontology, node_id)
    if not found:
        raise ValueError("Node not found.")
    node_type, existing = found
    updated = copy.deepcopy(existing)
    id_key = _find_node_id_key(existing)

    for key, value in new_attrs.items():
        if key == id_key:
            continue
        updated[key] = value

    schema_props = schema.get("node_types", {}).get(node_type, [])
    schema_props_by_name = _schema_props_by_name(schema, node_type)

    for prop in schema_props:
        prop_name = prop["name"]
        if prop_name in updated:
            updated[prop_name] = _coerce_property_value(prop, updated.get(prop_name))
        if not prop.get("required"):
            continue
        value = updated.get(prop_name)
        if prop.get("type") == "array":
            if not isinstance(value, list) or not value:
                raise ValueError(f"{node_type}.{prop_name} is required and must be a non-empty array.")
            continue
        if not _as_string(value):
            raise ValueError(f"{node_type}.{prop_name} is required.")

    for key, value in list(updated.items()):
        updated[key] = _coerce_property_value(schema_props_by_name.get(key), value)

    return node_type, updated


def validate_node_create(
    ontology: dict[str, Any],
    schema: dict[str, Any],
    node_type: str,
    attrs: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if not isinstance(attrs, dict):
        raise ValueError("attributes must be an object.")

    node_types = schema.get("node_types", {})
    if node_type not in node_types:
        raise ValueError(f"Node type '{node_type}' is not defined in ontology_schema.JSON.")

    existing_ids = set(_node_index(ontology))
    props = node_types.get(node_type, [])
    props_by_name = _schema_props_by_name(schema, node_type)
    id_key = _node_id_key_from_schema(node_type, schema)

    normalized: dict[str, Any] = {}
    for prop in props:
        prop_name = prop["name"]
        normalized[prop_name] = _coerce_property_value(prop, attrs.get(prop_name, ""))

    for key, value in attrs.items():
        normalized.setdefault(key, _coerce_property_value(props_by_name.get(key), value))

    if not _as_string(normalized.get(id_key)):
        normalized[id_key] = _next_node_id(ontology, node_type)

    node_id = _as_string(normalized.get(id_key))
    if not node_id:
        raise ValueError(f"{node_type}.{id_key} is required.")
    if node_id in existing_ids:
        raise ValueError(f"Node id '{node_id}' already exists.")

    for prop in props:
        if not prop.get("required"):
            continue
        prop_name = prop["name"]
        value = normalized.get(prop_name)
        if prop.get("type") == "array":
            if not isinstance(value, list) or not value:
                raise ValueError(f"{node_type}.{prop_name} is required and must be a non-empty array.")
            continue
        if not _as_string(value):
            raise ValueError(f"{node_type}.{prop_name} is required.")

    return node_id, normalized


def validate_relationship_add(
    ontology: dict[str, Any],
    schema: dict[str, Any],
    relation_type: str,
    from_id: str,
    to_id: str,
) -> tuple[str, str]:
    relation_type = _as_string(relation_type)
    from_id = _as_string(from_id)
    to_id = _as_string(to_id)
    if not relation_type or not from_id or not to_id:
        raise ValueError("type, from_id, to_id required")
    if from_id == to_id:
        raise ValueError("Self-loops are not allowed.")

    node_index = _node_index(ontology)
    from_type = node_index.get(from_id)
    to_type = node_index.get(to_id)
    if not from_type:
        raise ValueError(f"Source node '{from_id}' does not exist.")
    if not to_type:
        raise ValueError(f"Target node '{to_id}' does not exist.")

    rel_constraints = schema.get("relation_constraints", {})
    if relation_type not in rel_constraints:
        raise ValueError(f"Relationship type '{relation_type}' is not defined in ontology_schema.JSON.")

    constraint = rel_constraints[relation_type]
    allowed_domains = constraint.get("domain") or []
    allowed_ranges = constraint.get("range") or []
    if allowed_domains and from_type not in allowed_domains:
        raise ValueError(f"{relation_type} must start from {', '.join(allowed_domains)}.")
    if allowed_ranges and to_type not in allowed_ranges:
        raise ValueError(f"{relation_type} must point to {', '.join(allowed_ranges)}.")

    for rel in ontology.get("relations", []):
        existing_type = _as_string(rel.get("name") or rel.get("type"))
        if existing_type == relation_type and _as_string(rel.get("from_id")) == from_id and _as_string(rel.get("to_id")) == to_id:
            raise ValueError("Duplicate relationship.")

    return from_type, to_type
