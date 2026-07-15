from __future__ import annotations

import re
from copy import deepcopy

from backend.models import OntologyEvidence, OntologyRelationInstance, Severity
from backend.services.ontology_semantics import (
    corrective_actions_match,
    failure_modes_match,
    infer_component_match_for_failure_mode,
    is_corrective_action_candidate,
    is_failure_mode_candidate,
    prefer_more_informative_text,
    semantically_equivalent,
    symptoms_match,
)

_SEQUENTIAL_ID_RE = re.compile(r"^(SYM|FM|CA)-\d+$")
_DESCRIPTIVE_ID_RE = re.compile(r"^(sym|fm|ca)_[a-z0-9_]+$")


def _is_sequential_id(value: str) -> bool:
    return bool(_SEQUENTIAL_ID_RE.match(str(value or "").strip()))


def _is_descriptive_id(value: str) -> bool:
    return bool(_DESCRIPTIVE_ID_RE.match(str(value or "").strip()))


def _severity_rank(value: str) -> int:
    order = {
        Severity.LOW.value: 1,
        Severity.MEDIUM.value: 2,
        Severity.HIGH.value: 3,
        Severity.CRITICAL.value: 4,
    }
    return order.get(str(value or ""), 0)


def _relation_key(relation: dict) -> tuple[str, str, str]:
    return (
        str(relation.get("name", "")).strip(),
        str(relation.get("from_id", "")).strip(),
        str(relation.get("to_id", "")).strip(),
    )


def _evidence_entry(pages: list[int]) -> list[dict]:
    evidence: list[dict] = []
    seen: set[int] = set()
    for raw_page in pages:
        try:
            page = int(raw_page or 0)
        except (TypeError, ValueError):
            page = 0
        if page <= 0 or page in seen:
            continue
        seen.add(page)
        evidence.append(OntologyEvidence(
            source_page=page,
            source_reference=f"PAGE {page}",
            quote="",
        ).model_dump())
    return evidence


def _sanitize_base_ontology(base_ontology: dict) -> dict:
    sanitized = deepcopy(base_ontology)
    nodes = sanitized.setdefault("nodes", {})
    relations = [
        relation for relation in sanitized.setdefault("relations", [])
        if isinstance(relation, dict)
    ]

    may_pairs = {
        (str(rel.get("from_id", "")).strip(), str(rel.get("to_id", "")).strip())
        for rel in relations
        if str(rel.get("name", "")).strip() == "MAY_INDICATE"
    }
    resolved_pairs = {
        (str(rel.get("from_id", "")).strip(), str(rel.get("to_id", "")).strip())
        for rel in relations
        if str(rel.get("name", "")).strip() == "RESOLVED_BY"
    }
    indicates_pairs = {
        (str(rel.get("from_id", "")).strip(), str(rel.get("to_id", "")).strip())
        for rel in relations
        if str(rel.get("name", "")).strip() == "INDICATES"
    }

    resolved_failure_mode_ids = {failure_mode_id for failure_mode_id, _ in resolved_pairs}
    kept_failure_mode_ids = {
        failure_mode_id
        for _, failure_mode_id in may_pairs
        if failure_mode_id in resolved_failure_mode_ids
    }
    # ErrorCode → FailureMode chains are first-class diagnostic knowledge and have
    # no symptom-triplet path that could re-add them after pruning: keep every
    # FailureMode indicated by an ErrorCode (resolved or not) so INDICATES edges
    # survive and unresolved ones surface as declared gaps instead of vanishing.
    kept_failure_mode_ids |= {
        failure_mode_id for _, failure_mode_id in indicates_pairs
    }
    kept_symptom_ids = {
        symptom_id
        for symptom_id, failure_mode_id in may_pairs
        if failure_mode_id in kept_failure_mode_ids
    }
    kept_action_ids = {
        action_id
        for failure_mode_id, action_id in resolved_pairs
        if failure_mode_id in kept_failure_mode_ids
    }
    keep_ids_by_type = {
        "Symptom": kept_symptom_ids,
        "FailureMode": kept_failure_mode_ids,
        "CorrectiveAction": kept_action_ids,
    }

    for node_type, keep_ids in keep_ids_by_type.items():
        id_field = {
            "Symptom": "symptom_id",
            "FailureMode": "failure_mode_id",
            "CorrectiveAction": "action_id",
            "Component": "component_id",
            "ErrorCode": "error_code_id",
        }[node_type]
        nodes[node_type] = [
            item for item in nodes.get(node_type, [])
            if str(item.get(id_field, "")).strip() in keep_ids
        ]

    valid_ids = {
        str(item.get("asset_id", "")).strip()
        for item in nodes.get("Asset", [])
        if isinstance(item, dict)
    }
    valid_ids.update({
        str(item.get("symptom_id", "")).strip()
        for item in nodes.get("Symptom", [])
        if isinstance(item, dict)
    })
    valid_ids.update({
        str(item.get("failure_mode_id", "")).strip()
        for item in nodes.get("FailureMode", [])
        if isinstance(item, dict)
    })
    valid_ids.update({
        str(item.get("action_id", "")).strip()
        for item in nodes.get("CorrectiveAction", [])
        if isinstance(item, dict)
    })
    valid_ids.update({
        str(item.get("component_id", "")).strip()
        for item in nodes.get("Component", [])
        if isinstance(item, dict)
    })
    valid_ids.update({
        str(item.get("error_code_id", "")).strip()
        for item in nodes.get("ErrorCode", [])
        if isinstance(item, dict)
    })
    sanitized["relations"] = [
        relation for relation in relations
        if str(relation.get("from_id", "")).strip() in valid_ids
        and str(relation.get("to_id", "")).strip() in valid_ids
    ]
    return sanitized


_ID_FIELD_BY_TYPE: dict[str, str] = {
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
}


def _find_node_by_semantics(items: list[dict], candidate: dict, node_type: str) -> dict | None:
    for existing in items:
        if node_type == "Symptom" and symptoms_match(
            str(existing.get("name", "")),
            str(existing.get("description", "")),
            str(candidate.get("name", "")),
            str(candidate.get("description", "")),
        ):
            return existing
        if node_type == "FailureMode" and failure_modes_match(
            str(existing.get("name", "")),
            str(existing.get("description", "")),
            str(existing.get("material_context", "")),
            str(candidate.get("name", "")),
            str(candidate.get("description", "")),
            str(candidate.get("material_context", "")),
        ):
            return existing
        if node_type == "CorrectiveAction" and corrective_actions_match(
            str(existing.get("name", "")),
            str(existing.get("description", "")),
            str(existing.get("instruction_text", "")),
            str(candidate.get("name", "")),
            str(candidate.get("description", "")),
            str(candidate.get("instruction_text", "")),
        ):
            return existing

    id_field = _ID_FIELD_BY_TYPE.get(node_type)
    candidate_id = str(candidate.get(id_field, "")).strip() if id_field else ""
    if not _is_sequential_id(candidate_id):
        return None

    candidate_text = " ".join(
        str(candidate.get(field, "") or "")
        for field in ("name", "description", "material_context", "instruction_text")
    ).strip()
    for existing in items:
        existing_id = str(existing.get(id_field, "")).strip() if id_field else ""
        if not _is_descriptive_id(existing_id):
            continue
        existing_text = " ".join(
            str(existing.get(field, "") or "")
            for field in ("name", "description", "material_context", "instruction_text")
        ).strip()
        if not existing_text or not candidate_text:
            continue
        if semantically_equivalent(
            existing_text,
            candidate_text,
            min_ratio=0.68,
            min_overlap=0.55,
        ):
            return existing
    return None


def _merge_node_fields(existing: dict, candidate: dict, node_type: str) -> None:
    for field in ("name", "description"):
        existing[field] = prefer_more_informative_text(str(existing.get(field, "")), str(candidate.get(field, "")))

    if node_type == "Symptom":
        if _severity_rank(candidate.get("severity")) > _severity_rank(existing.get("severity")):
            existing["severity"] = candidate.get("severity", existing.get("severity"))
        return

    if node_type == "FailureMode":
        existing["material_context"] = prefer_more_informative_text(
            str(existing.get("material_context", "")),
            str(candidate.get("material_context", "")),
        )
        return

    if node_type == "CorrectiveAction":
        existing["instruction_text"] = prefer_more_informative_text(
            str(existing.get("instruction_text", "")),
            str(candidate.get("instruction_text", "")),
        )
        if candidate.get("source_page") and (
            not existing.get("source_page") or int(candidate["source_page"]) < int(existing["source_page"])
        ):
            existing["source_page"] = candidate["source_page"]
        if not str(existing.get("source_reference", "")).strip():
            source_page = existing.get("source_page") or candidate.get("source_page")
            if source_page:
                existing["source_reference"] = f"PAGE {source_page}"
        for field in ("source_type", "source_title"):
            if not str(existing.get(field, "")).strip() and str(candidate.get(field, "")).strip():
                existing[field] = candidate[field]


def _upsert_node(nodes: dict, node_type: str, candidate: dict) -> str:
    node_items = nodes.setdefault(node_type, [])
    id_field = next((key for key in candidate.keys() if key.endswith("_id")), "")
    candidate_id = str(candidate.get(id_field, "")).strip() if id_field else ""
    if candidate_id:
        for existing in node_items:
            if str(existing.get(id_field, "")).strip() == candidate_id:
                _merge_node_fields(existing, candidate, node_type)
                return candidate_id

    existing = _find_node_by_semantics(node_items, candidate, node_type)
    if existing is not None:
        _merge_node_fields(existing, candidate, node_type)
        return str(existing.get(id_field, "")).strip()

    node_items.append(deepcopy(candidate))
    return candidate_id


def merge_validated_triplets(base_ontology: dict, validated_triplets: list) -> dict:
    merged = _sanitize_base_ontology(base_ontology)
    nodes = merged.setdefault("nodes", {})
    nodes.setdefault("Symptom", [])
    nodes.setdefault("FailureMode", [])
    nodes.setdefault("CorrectiveAction", [])
    relations = merged.setdefault("relations", [])
    relation_keys = {_relation_key(rel) for rel in relations if isinstance(rel, dict)}

    failure_mode_evidence_pages: dict[str, list[int]] = {}

    for triplet in validated_triplets:
        symptom_dict = triplet.symptom.model_dump()
        symptom_dict["severity"] = triplet.symptom.severity.value
        symptom_evidence_page = int(getattr(triplet.symptom, "evidence_page", 0) or 0)
        symptom_id = _upsert_node(nodes, "Symptom", symptom_dict)

        failure_mode_id_map: dict[str, str] = {}
        for failure_mode in triplet.failure_modes:
            if not is_failure_mode_candidate(
                failure_mode.name,
                failure_mode.description,
                failure_mode.material_context,
            ):
                continue
            failure_mode_dict = failure_mode.model_dump(exclude={"linked_symptom_id"})
            fm_evidence_page = int(getattr(failure_mode, "evidence_page", 0) or 0)
            resolved_failure_mode_id = _upsert_node(nodes, "FailureMode", failure_mode_dict)
            failure_mode_id_map[failure_mode.failure_mode_id] = resolved_failure_mode_id
            if fm_evidence_page > 0:
                failure_mode_evidence_pages.setdefault(resolved_failure_mode_id, []).append(fm_evidence_page)
            relation = OntologyRelationInstance(
                name="MAY_INDICATE",
                from_type="Symptom",
                from_id=symptom_id,
                to_type="FailureMode",
                to_id=resolved_failure_mode_id,
                evidence=_evidence_entry([symptom_evidence_page, fm_evidence_page]),
            ).model_dump()
            key = _relation_key(relation)
            if key not in relation_keys:
                relations.append(relation)
                relation_keys.add(key)

        for corrective_action in triplet.corrective_actions:
            resolved_failure_mode_id = failure_mode_id_map.get(corrective_action.linked_failure_mode_id)
            if not resolved_failure_mode_id:
                continue
            if not is_corrective_action_candidate(
                corrective_action.name,
                corrective_action.description,
                corrective_action.instruction_text,
            ):
                continue
            action_dict = corrective_action.model_dump(exclude={"linked_failure_mode_id"})
            if not str(action_dict.get("source_reference", "")).strip():
                source_page = action_dict.get("source_page")
                action_dict["source_reference"] = f"PAGE {source_page}" if source_page else "PAGE UNKNOWN"
            action_id = _upsert_node(nodes, "CorrectiveAction", action_dict)
            ca_source_page = int(action_dict.get("source_page") or 0)
            relation = OntologyRelationInstance(
                name="RESOLVED_BY",
                from_type="FailureMode",
                from_id=resolved_failure_mode_id,
                to_type="CorrectiveAction",
                to_id=action_id,
                evidence=_evidence_entry([ca_source_page]),
            ).model_dump()
            key = _relation_key(relation)
            if key not in relation_keys:
                relations.append(relation)
                relation_keys.add(key)
            if not merged.get("source_type"):
                merged["source_type"] = corrective_action.source_type
            if not merged.get("source_title"):
                merged["source_title"] = corrective_action.source_title

    assets = nodes.get("Asset", [])
    components = nodes.get("Component", [])
    primary_asset_id = str((assets[0] if assets else {}).get("asset_id", "")).strip()
    if primary_asset_id and components:
        linked_component_ids = {
            str(rel.get("to_id", "")).strip()
            for rel in relations
            if str(rel.get("name", "")).strip() == "HAS_COMPONENT"
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
            ).model_dump()
            key = _relation_key(relation)
            if key not in relation_keys:
                relations.append(relation)
                relation_keys.add(key)

    if components:
        affected_failure_mode_ids = {
            str(rel.get("from_id", "")).strip()
            for rel in relations
            if str(rel.get("name", "")).strip() == "AFFECTS"
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
            failure_mode["material_context"] = component_id
            relation = OntologyRelationInstance(
                name="AFFECTS",
                from_type="FailureMode",
                from_id=failure_mode_id,
                to_type="Component",
                to_id=component_id,
                evidence=_evidence_entry(failure_mode_evidence_pages.get(failure_mode_id, [])),
            ).model_dump()
            key = _relation_key(relation)
            if key not in relation_keys:
                relations.append(relation)
                relation_keys.add(key)

    return merged
