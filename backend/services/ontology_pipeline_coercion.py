"""Coercion and normalization of raw LLM output into OntologyInstance."""

from __future__ import annotations

import logging
import re
from copy import deepcopy
from typing import Any

from backend.models import (
    HumanBindingAnswer,
    HumanRequiredField,
    OntologyEvidence,
    OntologyInstance,
    OntologyRelationDefinition,
    OntologyRelationInstance,
    OntologySchemaDefinition,
)
from backend.services.ontology_semantics import (
    infer_asset_type,
    infer_component_match_for_failure_mode,
    is_workspace_canonical_asset_identity,
    normalize_asset_node,
    normalize_severity,
    resolve_material_context,
)
from backend.services.pdf_service import format_text_with_pages

logger = logging.getLogger(__name__)


_GENERAL_MATERIAL_CONTEXT_VALUES = {
    "asset",
    "asset_level",
    "asset level",
    "general",
    "system",
    "whole_asset",
    "whole asset",
    "machine",
}


def _is_general_material_context(value: str) -> bool:
    normalized = re.sub(r"[\s-]+", "_", str(value or "").strip().lower())
    return normalized in {
        re.sub(r"[\s-]+", "_", item)
        for item in _GENERAL_MATERIAL_CONTEXT_VALUES
    }


def _empty_instance(
    schema: OntologySchemaDefinition,
    source_type: str,
    source_title: str,
) -> OntologyInstance:
    return OntologyInstance(
        ontology_name=schema.ontology_name,
        version=schema.version,
        language="en",
        source_type=source_type,
        source_title=source_title,
        nodes={node.name: [] for node in schema.nodes},
        relations=[],
    )


def _extract_first_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else 0


def _node_id_property(node_def) -> str:
    for prop in node_def.properties:
        if prop.unique:
            return prop.name
    return f"{node_def.name.lower()}_id"


def _node_richness(node: dict[str, Any]) -> int:
    return sum(1 for value in node.values() if value not in ("", [], {}, None))


def _default_asset_node(
    source_title: str,
    source_type: str,
    asset_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    identity = asset_identity or {}
    return {
        "asset_id": str(identity.get("asset_id") or "ASSET-001"),
        "name": str(identity.get("name") or source_title or "Unknown Asset"),
        "description": str(
            identity.get("description")
            or identity.get("name")
            or source_title
            or "Technical asset extracted from manual context"
        ),
        "brand": str(identity.get("brand") or ""),
        "model": str(identity.get("model") or ""),
        "asset_type": str(identity.get("asset_type") or infer_asset_type(source_title, source_type)),
    }


def _primary_asset_node_name(schema: OntologySchemaDefinition) -> str | None:
    node_names = {node.name for node in schema.nodes}
    if "Asset" in node_names:
        return "Asset"
    return None


def _relation_exists(relations: list[OntologyRelationInstance], candidate: OntologyRelationInstance) -> bool:
    for rel in relations:
        if (
            rel.name == candidate.name
            and rel.from_type == candidate.from_type
            and rel.from_id == candidate.from_id
            and rel.to_type == candidate.to_type
            and rel.to_id == candidate.to_id
        ):
            return True
    return False


def _normalize_ontology_instance(
    ontology: OntologyInstance,
    schema: OntologySchemaDefinition,
    source_type: str,
    source_title: str,
    asset_identity: dict[str, Any] | None = None,
) -> OntologyInstance:
    normalized = deepcopy(ontology.model_dump())
    nodes = normalized.setdefault("nodes", {})
    id_remap: dict[str, str] = {}
    identity = asset_identity or {}
    canonical_asset_id = str(identity.get("asset_id", "") or "").strip()
    has_canonical_asset = is_workspace_canonical_asset_identity(identity)
    for node_def in schema.nodes:
        node_list = nodes.setdefault(node_def.name, [])
        if node_def.name == "Asset" and has_canonical_asset:
            for node in node_list:
                if not isinstance(node, dict):
                    continue
                extracted_id = str(node.get("asset_id", "") or "").strip()
                if extracted_id and extracted_id != canonical_asset_id:
                    id_remap[extracted_id] = canonical_asset_id
            # The Asset is workspace-owned context, never PDF-extracted output.
            # Ignore model variants and inject exactly the confirmed node.
            nodes[node_def.name] = [
                _default_asset_node(
                    source_title,
                    source_type,
                    asset_identity=asset_identity,
                )
            ]
            continue
        seen_ids: dict[str, int] = {}
        id_prop = _node_id_property(node_def)
        deduped: list[dict[str, Any]] = []
        for node in node_list:
            if not isinstance(node, dict):
                continue
            original_node_id = str(node.get(id_prop, "")).strip()
            if node_def.name == "Asset":
                node = normalize_asset_node(
                    node,
                    source_title,
                    source_type,
                    asset_identity=asset_identity,
                )
            node_id = str(node.get(id_prop, "")).strip()
            if not node_id:
                continue
            if original_node_id and original_node_id != node_id:
                id_remap[original_node_id] = node_id
            existing_index = seen_ids.get(node_id)
            if existing_index is not None:
                if _node_richness(node) > _node_richness(deduped[existing_index]):
                    deduped[existing_index] = node
                continue
            seen_ids[node_id] = len(deduped)
            if node_def.name == "CorrectiveAction":
                source_ref = str(node.get("source_reference", "")).strip()
                if not source_ref:
                    source_page = node.get("source_page")
                    if source_page:
                        node["source_reference"] = f"PAGE {source_page}"
            deduped.append(node)
        nodes[node_def.name] = deduped

    primary_asset_type = _primary_asset_node_name(schema)
    if primary_asset_type and not nodes.get(primary_asset_type):
        if primary_asset_type == "Asset":
            nodes[primary_asset_type].append(
                _default_asset_node(source_title, source_type, asset_identity=asset_identity)
            )

    asset_node_ids = {
        str(asset.get("asset_id", "")).strip()
        for asset in nodes.get("Asset", [])
        if isinstance(asset, dict) and str(asset.get("asset_id", "")).strip()
    }
    for failure_mode in nodes.get("FailureMode", []):
        if not isinstance(failure_mode, dict):
            continue
        material_context = str(failure_mode.get("material_context", "") or "").strip()
        if material_context and not _is_general_material_context(material_context):
            failure_mode["material_context"] = resolve_material_context(
                material_context,
                nodes.get("Component", []),
                asset_node_ids,
            )
    for symptom in nodes.get("Symptom", []):
        if isinstance(symptom, dict) and str(symptom.get("severity", "") or "").strip():
            symptom["severity"] = normalize_severity(str(symptom["severity"]))

    relations = []
    for rel in normalized.get("relations", []):
        if isinstance(rel, dict):
            rel = dict(rel)
            rel["from_id"] = id_remap.get(str(rel.get("from_id", "")).strip(), rel.get("from_id", ""))
            rel["to_id"] = id_remap.get(str(rel.get("to_id", "")).strip(), rel.get("to_id", ""))
        try:
            relation = OntologyRelationInstance.model_validate(rel)
        except Exception:
            continue
        # Drop AFFECTS edges whose target is a general material-context sentinel
        # (e.g. "asset_level") OR the Asset node itself: both mean "no specific
        # component" and would otherwise become a blocking domain/range or
        # dangling-target error.
        if relation.name == "AFFECTS" and (
            _is_general_material_context(relation.to_id)
            or relation.to_id in asset_node_ids
        ):
            continue
        if not _relation_exists(relations, relation):
            relations.append(relation)

    assets = nodes.get("Asset", [])
    components = nodes.get("Component", [])
    primary_asset_id = str((assets[0] if assets else {}).get("asset_id", "")).strip()
    if primary_asset_id and components:
        linked_component_ids = {
            rel.to_id
            for rel in relations
            if rel.name == "HAS_COMPONENT" and rel.from_type == "Asset" and rel.to_type == "Component"
        }
        for component in components:
            component_id = str(component.get("component_id", "")).strip()
            if not component_id or component_id in linked_component_ids:
                continue
            relation = OntologyRelationInstance(
                name="HAS_COMPONENT",
                from_type="Asset",
                from_id=primary_asset_id,
                to_type="Component",
                to_id=component_id,
                evidence=[],
            )
            if not _relation_exists(relations, relation):
                relations.append(relation)

    # GENERATES_ERROR is fully derivable: there is one canonical Asset and every
    # ErrorCode belongs to it by definition — mirror the HAS_COMPONENT auto-link
    # so KPI wiring never depends on the LLM remembering to emit it.
    error_codes = nodes.get("ErrorCode", [])
    if primary_asset_id and error_codes:
        linked_error_code_ids = {
            rel.to_id
            for rel in relations
            if rel.name == "GENERATES_ERROR" and rel.from_type == "Asset" and rel.to_type == "ErrorCode"
        }
        for error_code in error_codes:
            error_code_id = str(error_code.get("error_code_id", "")).strip()
            if not error_code_id or error_code_id in linked_error_code_ids:
                continue
            relation = OntologyRelationInstance(
                name="GENERATES_ERROR",
                from_type="Asset",
                from_id=primary_asset_id,
                to_type="ErrorCode",
                to_id=error_code_id,
                evidence=[],
            )
            if not _relation_exists(relations, relation):
                relations.append(relation)

    if components:
        affected_failure_mode_ids = {
            rel.from_id
            for rel in relations
            if rel.name == "AFFECTS" and rel.from_type == "FailureMode" and rel.to_type == "Component"
        }
        for failure_mode in nodes.get("FailureMode", []):
            failure_mode_id = str(failure_mode.get("failure_mode_id", "")).strip()
            if not failure_mode_id or failure_mode_id in affected_failure_mode_ids:
                continue
            component_id = infer_component_match_for_failure_mode(
                failure_mode_name=str(failure_mode.get("name", "")),
                failure_mode_description=str(failure_mode.get("description", "")),
                failure_mode_material_context=str(failure_mode.get("material_context", "")),
                components=components,
            )
            if not component_id:
                continue
            relation = OntologyRelationInstance(
                name="AFFECTS",
                from_type="FailureMode",
                from_id=failure_mode_id,
                to_type="Component",
                to_id=component_id,
                evidence=[],
            )
            if not _relation_exists(relations, relation):
                relations.append(relation)

    normalized["source_type"] = source_type
    normalized["source_title"] = source_title
    normalized["relations"] = [rel.model_dump() for rel in relations]
    return OntologyInstance.model_validate(normalized)


def _apply_human_answers(
    ontology: OntologyInstance,
    answers: list[HumanBindingAnswer],
) -> OntologyInstance:
    updated = deepcopy(ontology.model_dump())
    answer_map = {a.field_key: a.value for a in answers}
    for node_type, node_list in updated["nodes"].items():
        for node in node_list:
            for key, value in answer_map.items():
                # Wildcard key: applies to ALL nodes of this type missing the property.
                # Format: "{node_type}::*::{prop_name}"
                wildcard_match = re.match(rf"^{re.escape(node_type)}::\*::(.+)$", key)
                if wildcard_match:
                    prop_name = wildcard_match.group(1)
                    if not node.get(prop_name):
                        node[prop_name] = value
                    continue
                # Specific key: applies only to the exact node by id.
                specific_match = re.match(rf"^{re.escape(node_type)}::(.+?)::(.+)$", key)
                if not specific_match:
                    continue
                node_id, prop_name = specific_match.groups()
                id_keys = [k for k in node.keys() if k.endswith("_id")]
                if any(str(node.get(id_key)) == node_id for id_key in id_keys):
                    node[prop_name] = value
    return OntologyInstance.model_validate(updated)


def _schema_node_map(schema: OntologySchemaDefinition) -> dict[str, Any]:
    return {node.name: node for node in schema.nodes}


def _schema_relation_map(schema: OntologySchemaDefinition) -> dict[str, OntologyRelationDefinition]:
    return {rel.name: rel for rel in schema.relations}


def _collect_node_index(ontology: OntologyInstance, schema: OntologySchemaDefinition) -> dict[str, set[str]]:
    node_map = _schema_node_map(schema)
    index: dict[str, set[str]] = {}
    for node_type, items in ontology.nodes.items():
        node_def = node_map.get(node_type)
        if not node_def:
            continue
        id_prop = _node_id_property(node_def)
        index[node_type] = {str(item.get(id_prop, "")).strip() for item in items if item.get(id_prop)}
    return index


def _make_human_field(
    node_type: str,
    node_id: str,
    property_name: str,
    reason: str,
    prompt: str,
    suggested_value: str = "",
) -> HumanRequiredField:
    return HumanRequiredField(
        field_key=f"{node_type}::{node_id}::{property_name}",
        prompt=prompt,
        target_type=node_type,
        target_id=node_id,
        property_name=property_name,
        reason=reason,
        suggested_value=suggested_value,
    )


def _human_prompt_for_property(node_type: str, property_name: str, entity_label: str) -> tuple[str, str]:
    readable_node = f"{node_type} {entity_label}".strip()
    prompts = {
        "brand": f"Provide the brand for {readable_node}.",
        "model": f"Provide the model for {readable_node}.",
        "asset_type": f"Provide the asset type for {readable_node}.",
        "category": f"Provide the category for {readable_node}.",
        "severity": f"Provide the severity for {readable_node}.",
        "material_context": f"Provide the material context for {readable_node}.",
        "source_type": f"Provide the source type for {readable_node}.",
        "source_title": f"Provide the source title for {readable_node}.",
        "source_reference": f"Provide the source reference for {readable_node} (for example PAGE 42).",
        "code": f"Provide the machine error code value for {readable_node}.",
    }
    reasons = {
        "source_reference": "Required by the export contract to preserve provenance.",
        "severity": "Required to keep the symptom actionable during diagnosis.",
    }
    return (
        prompts.get(property_name, f"Provide {property_name} for {readable_node}."),
        reasons.get(property_name, "Required by ontology schema but missing from the draft."),
    )


def _coerce_nodes(raw_nodes: Any, schema: OntologySchemaDefinition) -> dict[str, list[dict[str, Any]]]:
    node_defs = _schema_node_map(schema)
    nodes = {name: [] for name in node_defs}
    if not isinstance(raw_nodes, dict):
        return nodes

    for node_type, node_def in node_defs.items():
        raw_items = raw_nodes.get(node_type, [])
        if not isinstance(raw_items, list):
            continue
        id_prop = _node_id_property(node_def)
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            normalized = {prop.name: item.get(prop.name, [] if prop.type == "array" else "") for prop in node_def.properties}
            if not normalized.get(id_prop):
                continue
            nodes[node_type].append(normalized)
    return nodes


def _build_name_index(nodes: dict[str, list[dict[str, Any]]], schema: OntologySchemaDefinition) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for node_type, items in nodes.items():
        node_def = _schema_node_map(schema).get(node_type)
        if not node_def:
            continue
        id_prop = _node_id_property(node_def)
        resolved: dict[str, str] = {}
        for item in items:
            node_id = str(item.get(id_prop, "")).strip()
            if not node_id:
                continue
            for key in ("name", "model", "brand", "manufacturer", "asset_type", id_prop):
                value = str(item.get(key, "")).strip()
                if value:
                    resolved[value.lower()] = node_id
        index[node_type] = resolved
    return index


def _resolve_node_id(node_type: str, raw_value: Any, name_index: dict[str, dict[str, str]]) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    type_index = name_index.get(node_type, {})
    return type_index.get(value.lower(), value)


def _coerce_evidence(raw_evidence: Any) -> list[OntologyEvidence]:
    if not isinstance(raw_evidence, list):
        return []
    evidence: list[OntologyEvidence] = []
    for item in raw_evidence:
        if not isinstance(item, dict):
            continue
        page = _extract_first_int(item.get("source_page"))
        source_reference = str(item.get("source_reference", "")).strip()
        if not source_reference and page:
            source_reference = f"PAGE {page}"
        evidence.append(OntologyEvidence(
            source_page=page,
            source_reference=source_reference,
            quote=str(item.get("quote", "")).strip(),
            source_anchor=str(item.get("source_anchor", "")).strip(),
        ))
    return evidence


def _coerce_relations(
    raw_relations: Any,
    nodes: dict[str, list[dict[str, Any]]],
    schema: OntologySchemaDefinition,
) -> list[dict[str, Any]]:
    if not isinstance(raw_relations, list):
        return []
    rel_defs = _schema_relation_map(schema)
    name_index = _build_name_index(nodes, schema)
    relations: list[dict[str, Any]] = []
    for item in raw_relations:
        if not isinstance(item, dict):
            continue
        rel_name = str(item.get("name") or item.get("type") or item.get("relation") or "").strip()
        if not rel_name:
            continue
        rel_def = rel_defs.get(rel_name)
        from_type = str(item.get("from_type") or item.get("domain") or (rel_def.domain if rel_def else "")).strip()
        to_type = str(item.get("to_type") or item.get("range") or (rel_def.range if rel_def else "")).strip()
        from_id = _resolve_node_id(from_type, item.get("from_id") or item.get("from") or item.get("source"), name_index)
        to_id = _resolve_node_id(to_type, item.get("to_id") or item.get("to") or item.get("target"), name_index)
        if not (rel_name and from_type and to_type and from_id and to_id):
            continue
        relations.append({
            "name": rel_name,
            "from_type": from_type,
            "from_id": from_id,
            "to_type": to_type,
            "to_id": to_id,
            "evidence": [ev.model_dump() for ev in _coerce_evidence(item.get("evidence", []))],
        })
    return relations


def _coerce_raw_ontology_data(
    data: dict[str, Any],
    schema: OntologySchemaDefinition,
    source_type: str,
    source_title: str,
) -> dict[str, Any]:
    nodes = _coerce_nodes(data.get("nodes", {}), schema)
    relations = _coerce_relations(data.get("relations", []), nodes, schema)
    return {
        "ontology_name": data.get("ontology_name", schema.ontology_name),
        "version": data.get("version", schema.version),
        "language": data.get("language", "en"),
        "source_type": data.get("source_type", source_type),
        "source_title": data.get("source_title", source_title),
        "nodes": nodes,
        "relations": relations,
    }


def _substantive_node_count(ontology: OntologyInstance) -> int:
    return sum(
        len(items or [])
        for node_type, items in ontology.nodes.items()
        if node_type != "Asset"
    )


def _retry_regression_reason(
    previous: OntologyInstance,
    candidate: OntologyInstance,
) -> str | None:
    prev_substantive = _substantive_node_count(previous)
    cand_substantive = _substantive_node_count(candidate)
    prev_relations = len(previous.relations or [])
    cand_relations = len(candidate.relations or [])

    if prev_substantive <= 0:
        return None
    if cand_substantive == 0:
        return (
            "candidate removed all substantive nodes "
            f"({prev_substantive} -> 0)"
        )
    if prev_substantive >= 12 and cand_substantive <= max(2, prev_substantive // 5):
        return (
            "candidate removed most substantive nodes "
            f"({prev_substantive} -> {cand_substantive})"
        )
    if (
        prev_relations >= 20
        and cand_relations <= max(1, prev_relations // 10)
        and cand_substantive < prev_substantive
    ):
        return (
            "candidate removed most relations "
            f"({prev_relations} -> {cand_relations}) while shrinking node coverage"
        )
    return None


def _compact_nodes_for_relation_pass(ontology: OntologyInstance) -> dict[str, list[dict[str, Any]]]:
    field_map = {
        "Asset": ("asset_id", "name"),
        "Component": ("component_id", "name", "description", "category"),
        "Symptom": ("symptom_id", "name", "description", "severity"),
        "FailureMode": ("failure_mode_id", "name", "description", "material_context"),
        "CorrectiveAction": ("action_id", "name", "description", "instruction_text"),
        "ErrorCode": ("error_code_id", "name", "description", "code"),
    }
    compact: dict[str, list[dict[str, Any]]] = {}
    for node_type, items in ontology.nodes.items():
        fields = field_map.get(node_type, ())
        if not fields or not items:
            continue
        compact[node_type] = [
            {field: item.get(field, "") for field in fields}
            for item in items
            if isinstance(item, dict)
        ]
    return compact


def _compact_existing_relations_for_relation_pass(
    relations: list[OntologyRelationInstance],
) -> list[dict[str, str]]:
    compact: list[dict[str, str]] = []
    for relation in relations or []:
        if relation.name == "HAS_COMPONENT":
            continue
        compact.append({
            "name": relation.name,
            "from_id": relation.from_id,
            "to_id": relation.to_id,
        })
    return compact


def _should_run_relation_pass(ontology: OntologyInstance) -> bool:
    counts = {node_type: len(items or []) for node_type, items in ontology.nodes.items()}
    return any((
        counts.get("Symptom", 0) and counts.get("FailureMode", 0),
        counts.get("FailureMode", 0) and counts.get("Component", 0),
        counts.get("FailureMode", 0) and counts.get("CorrectiveAction", 0),
        counts.get("Asset", 0) and counts.get("ErrorCode", 0),
        counts.get("ErrorCode", 0) and counts.get("FailureMode", 0),
    ))


def _split_text_with_pages(text_with_pages: str) -> list[dict[str, Any]]:
    matches = list(re.finditer(r"(?m)^--- PAGE (\d+) ---$", text_with_pages))
    if not matches:
        return []

    pages: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text_with_pages)
        page_text = text_with_pages[start:end].strip()
        if not page_text:
            continue
        pages.append({
            "page_number": int(match.group(1)),
            "text": page_text,
        })
    return pages


def _relation_pass_search_terms(ontology: OntologyInstance) -> list[str]:
    field_map = {
        "Asset": ("name",),
        "Component": ("name",),
        "Symptom": ("name",),
        "FailureMode": ("name", "material_context"),
        "CorrectiveAction": ("name",),
        "ErrorCode": ("code", "name"),
    }
    terms: list[str] = []
    seen: set[str] = set()
    for node_type, items in ontology.nodes.items():
        fields = field_map.get(node_type, ())
        for item in items or []:
            if not isinstance(item, dict):
                continue
            for field in fields:
                value = re.sub(r"\s+", " ", str(item.get(field, "")).strip())
                lowered = value.lower()
                min_length = 2 if field == "code" else 4
                if len(lowered) < min_length or lowered in seen:
                    continue
                seen.add(lowered)
                terms.append(lowered)
    return sorted(terms, key=len, reverse=True)


def _build_relation_pass_text(
    text_with_pages: str,
    ontology: OntologyInstance,
    *,
    max_pages: int = 12,
    min_pages: int = 3,
) -> str:
    parsed_pages = _split_text_with_pages(text_with_pages)
    if len(parsed_pages) <= max_pages:
        return text_with_pages

    search_terms = _relation_pass_search_terms(ontology)
    if not search_terms:
        return text_with_pages

    page_lookup = {page["page_number"]: page for page in parsed_pages}
    exact_scores: dict[int, int] = {}
    for page in parsed_pages:
        haystack = page["text"].lower()
        exact_scores[page["page_number"]] = sum(1 for term in search_terms if term in haystack)

    matched_pages = [page_number for page_number, score in exact_scores.items() if score > 0]
    if not matched_pages:
        return text_with_pages

    selected_page_numbers: set[int] = set()
    for page_number in sorted(matched_pages, key=lambda item: (-exact_scores[item], item)):
        for candidate in (page_number - 1, page_number, page_number + 1):
            if candidate not in page_lookup or candidate in selected_page_numbers:
                continue
            selected_page_numbers.add(candidate)
            if len(selected_page_numbers) >= max_pages:
                break
        if len(selected_page_numbers) >= max_pages:
            break

    if len(selected_page_numbers) < min_pages:
        return text_with_pages

    selected_pages = [
        page_lookup[page_number]
        for page_number in sorted(selected_page_numbers)
    ]
    compact_text = format_text_with_pages(selected_pages)
    if len(compact_text) >= int(len(text_with_pages) * 0.95):
        return text_with_pages

    logger.info(
        "[ontology] Relation pass using %d/%d pages (%d -> %d chars)",
        len(selected_pages),
        len(parsed_pages),
        len(text_with_pages),
        len(compact_text),
    )
    return compact_text


# A missing required property is asked per-node up to this group size; from this
# size on, the group collapses into one wildcard field whose answer is broadcast
# to every node of that type missing the property.
