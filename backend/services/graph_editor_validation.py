from __future__ import annotations

import copy
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
    for prop in schema_props:
        if not prop.get("required"):
            continue
        prop_name = prop["name"]
        value = updated.get(prop_name)
        if prop.get("type") == "array":
            if not isinstance(value, list) or not value:
                raise ValueError(f"{node_type}.{prop_name} is required and must be a non-empty array.")
            continue
        if not _as_string(value):
            raise ValueError(f"{node_type}.{prop_name} is required.")

    return node_type, updated


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
