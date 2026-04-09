from __future__ import annotations

from typing import Any

from backend.models import (
    ExportOntologyInstance,
    ExportOntologyMetadata,
    ExportOntologyRelationship,
)
from backend.services.legacy_ontology_migration import migrate_legacy_ontology
from backend.services.ontology_semantics import infer_asset_type, normalize_asset_node


REQUIRED_METADATA_FIELDS = (
    "product_name",
    "product_short_name",
    "product_type",
    "domain_topics",
)

REQUIRED_NODE_FIELDS: dict[str, tuple[str, ...]] = {
    "Asset": ("asset_id", "name", "description", "brand", "model"),
    "Component": ("component_id", "name", "description", "category"),
    "Symptom": ("symptom_id", "name", "description", "severity"),
    "FailureMode": ("failure_mode_id", "name", "description", "material_context"),
    "CorrectiveAction": ("action_id", "name", "description", "instruction_text"),
    "ErrorCode": ("error_code_id", "name", "description", "code"),
}

REQUIRED_RELATION_TYPES = (
    "MAY_INDICATE",
    "RESOLVED_BY",
    "AFFECTS",
    "INDICATES",
)

OPTIONAL_RELATION_TYPES = (
    "HAS_COMPONENT",
    "GENERATES_ERROR",
)

ALLOWED_RELATION_TYPES = set(REQUIRED_RELATION_TYPES + OPTIONAL_RELATION_TYPES)

RELATION_REQUIREMENTS = (
    ("MAY_INDICATE", "Symptom", "FailureMode"),
    ("RESOLVED_BY", "FailureMode", "CorrectiveAction"),
)


def _as_string(value: Any) -> str:
    return str(value or "").strip()


def _normalize_nodes(raw_nodes: Any) -> dict[str, list[dict[str, Any]]]:
    normalized: dict[str, list[dict[str, Any]]] = {key: [] for key in REQUIRED_NODE_FIELDS}
    if not isinstance(raw_nodes, dict):
        return normalized

    for node_type, required_fields in REQUIRED_NODE_FIELDS.items():
        items = raw_nodes.get(node_type, [])
        if not isinstance(items, list):
            continue
        cleaned_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized_item = dict(item)
            for field in required_fields:
                normalized_item[field] = item.get(field, "")
            cleaned_items.append(normalized_item)
        normalized[node_type] = cleaned_items
    return normalized


def _normalize_relationships(raw_relations: Any) -> list[ExportOntologyRelationship]:
    if not isinstance(raw_relations, list):
        return []

    relationships: list[ExportOntologyRelationship] = []
    for rel in raw_relations:
        if not isinstance(rel, dict):
            continue
        rel_type = _as_string(rel.get("name") or rel.get("type"))
        from_id = _as_string(rel.get("from_id") or rel.get("from") or rel.get("source"))
        to_id = _as_string(rel.get("to_id") or rel.get("to") or rel.get("target"))
        if not (rel_type and from_id and to_id):
            continue
        relationships.append(
            ExportOntologyRelationship(
                type=rel_type,
                from_id=from_id,
                to_id=to_id,
                evidence=rel.get("evidence", []),
            )
        )
    return relationships


def _prune_non_traversable_nodes(
    nodes: dict[str, list[dict[str, Any]]],
    relationships: list[ExportOntologyRelationship],
) -> tuple[dict[str, list[dict[str, Any]]], list[ExportOntologyRelationship]]:
    pruned_nodes = {node_type: list(items) for node_type, items in nodes.items()}

    valid_ids = {
        str(item.get(required_fields[0], "")).strip()
        for node_type, required_fields in REQUIRED_NODE_FIELDS.items()
        for item in pruned_nodes.get(node_type, [])
        if isinstance(item, dict)
    }
    pruned_relationships = [
        rel for rel in relationships
        if rel.from_id in valid_ids and rel.to_id in valid_ids
    ]
    return pruned_nodes, pruned_relationships


def _build_metadata(migrated: dict[str, Any], nodes: dict[str, list[dict[str, Any]]]) -> ExportOntologyMetadata:
    asset = normalize_asset_node(
        (nodes.get("Asset") or [{}])[0],
        source_title=_as_string(migrated.get("source_title")),
        source_type=_as_string(migrated.get("source_type")),
    )
    raw_metadata = migrated.get("metadata", {})

    product_name = _as_string(raw_metadata.get("product_name") or asset.get("name") or migrated.get("source_title"))
    product_short_name = _as_string(
        raw_metadata.get("product_short_name") or asset.get("model") or product_name
    )
    product_type = _as_string(
        raw_metadata.get("product_type")
        or infer_asset_type(
            source_title=product_name or _as_string(migrated.get("source_title")),
            source_type=_as_string(migrated.get("source_type")),
            current_value=_as_string(asset.get("asset_type")),
        )
        or "technical asset"
    )

    raw_topics = raw_metadata.get("domain_topics")
    if isinstance(raw_topics, list):
        domain_topics = [_as_string(topic) for topic in raw_topics if _as_string(topic)]
    else:
        domain_topics = []
    if not domain_topics and product_type:
        domain_topics = [product_type]

    return ExportOntologyMetadata(
        product_name=product_name,
        product_short_name=product_short_name,
        product_type=product_type,
        domain_topics=domain_topics,
    )


def build_contract_ontology(raw_ontology: dict[str, Any]) -> dict[str, Any]:
    migrated = migrate_legacy_ontology(raw_ontology)
    nodes = _normalize_nodes(migrated.get("nodes", {}))
    metadata = _build_metadata(migrated, nodes)
    relationships = _normalize_relationships(migrated.get("relations", []))
    nodes, relationships = _prune_non_traversable_nodes(nodes, relationships)
    contract = ExportOntologyInstance(
        metadata=metadata,
        nodes=nodes,
        relationships=relationships,
    )
    return contract.model_dump()


def validate_contract_ontology(contract_ontology: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    metadata = contract_ontology.get("metadata")
    if not isinstance(metadata, dict):
        issues.append("metadata is required and must be an object.")
        metadata = {}

    for field in REQUIRED_METADATA_FIELDS:
        value = metadata.get(field)
        if field == "domain_topics":
            if not isinstance(value, list) or not any(_as_string(item) for item in value):
                issues.append("metadata.domain_topics is required and must contain at least one non-empty string.")
        elif not _as_string(value):
            issues.append(f"metadata.{field} is required.")

    nodes = contract_ontology.get("nodes")
    if not isinstance(nodes, dict):
        issues.append("nodes is required and must be an object.")
        nodes = {}

    all_node_ids: dict[str, str] = {}
    for node_type, required_fields in REQUIRED_NODE_FIELDS.items():
        items = nodes.get(node_type)
        if not isinstance(items, list):
            issues.append(f"nodes.{node_type} is required and must be an array.")
            continue
        if node_type == "ErrorCode" and items == []:
            continue
        id_field = required_fields[0]
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                issues.append(f"nodes.{node_type}[{index}] must be an object.")
                continue
            for field in required_fields:
                if not _as_string(item.get(field)):
                    issues.append(f"nodes.{node_type}[{index}].{field} is required.")
            node_id = _as_string(item.get(id_field))
            if not node_id:
                continue
            if node_id in all_node_ids:
                issues.append(f"Duplicate node id '{node_id}' found in {node_type} and {all_node_ids[node_id]}.")
            else:
                all_node_ids[node_id] = node_type

    relationships = contract_ontology.get("relationships")
    if not isinstance(relationships, list):
        issues.append("relationships is required and must be an array.")
        relationships = []

    relation_types_present: set[str] = set()
    for index, rel in enumerate(relationships):
        if not isinstance(rel, dict):
            issues.append(f"relationships[{index}] must be an object.")
            continue
        rel_type = _as_string(rel.get("type"))
        from_id = _as_string(rel.get("from_id"))
        to_id = _as_string(rel.get("to_id"))
        if not rel_type:
            issues.append(f"relationships[{index}].type is required.")
            continue
        if rel_type not in ALLOWED_RELATION_TYPES:
            issues.append(f"relationships[{index}].type '{rel_type}' is not allowed by ontology_schema.JSON.")
        if not from_id:
            issues.append(f"relationships[{index}].from_id is required.")
        if not to_id:
            issues.append(f"relationships[{index}].to_id is required.")
        if from_id and from_id not in all_node_ids:
            issues.append(f"relationships[{index}] references missing from_id '{from_id}'.")
        if to_id and to_id not in all_node_ids:
            issues.append(f"relationships[{index}] references missing to_id '{to_id}'.")
        if rel_type:
            relation_types_present.add(rel_type)

    for rel_type, from_type, to_type in RELATION_REQUIREMENTS:
        if nodes.get(from_type) and nodes.get(to_type) and rel_type not in relation_types_present:
            issues.append(
                f"relationships must contain at least one '{rel_type}' edge when both {from_type} and {to_type} nodes exist."
            )

    return issues


def build_and_validate_contract_ontology(raw_ontology: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    contract = build_contract_ontology(raw_ontology)
    return contract, validate_contract_ontology(contract)
