"""Deterministic, ontology-preserving consolidation across extraction chunks.

The automatic path is deliberately conservative: it collapses only identity
equivalents that can be justified without machine-, vendor-, or manual-specific
vocabulary.  Broader semantic similarities are reported for review and are not
silently merged.
"""

from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any

from backend.models import OntologyInstance, OntologyNodeDefinition
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_semantics import (
    corrective_actions_match,
    failure_modes_match,
    normalize_semantic_text,
    symptoms_match,
)


def _id_property(node_def: OntologyNodeDefinition) -> str:
    unique = next((prop.name for prop in node_def.properties if prop.unique), "")
    if unique:
        return unique
    conventional = f"{node_def.name.lower()}_id"
    if any(prop.name == conventional for prop in node_def.properties):
        return conventional
    return next((prop.name for prop in node_def.properties if prop.name.endswith("_id")), "id")


def _singular_token(token: str) -> str:
    """Return a conservative English-schema singular form.

    The ontology language is English.  These transformations only remove
    unambiguous, common inflections and never add domain vocabulary.
    """
    if len(token) > 5 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 5 and token.endswith(("ches", "shes", "xes", "zes")):
        return token[:-2]
    if len(token) > 4 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def _surface(value: Any, *, singular: bool = False) -> str:
    normalized = normalize_semantic_text(str(value or ""))
    if not singular:
        return normalized
    return " ".join(_singular_token(token) for token in normalized.split())


def _compatible(left: Any, right: Any) -> bool:
    left_norm = _surface(left)
    right_norm = _surface(right)
    return not left_norm or not right_norm or left_norm == right_norm


def _safe_identity_equivalent(node_type: str, left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_name = _surface(left.get("name"), singular=True)
    right_name = _surface(right.get("name"), singular=True)
    if not left_name or left_name != right_name:
        return False

    if node_type == "Component":
        return _compatible(left.get("category"), right.get("category"))
    if node_type == "Symptom":
        return symptoms_match(
            str(left.get("name", "")),
            str(left.get("description", "")),
            str(right.get("name", "")),
            str(right.get("description", "")),
        )
    if node_type == "FailureMode":
        return _compatible(left.get("material_context"), right.get("material_context")) and failure_modes_match(
            str(left.get("name", "")),
            str(left.get("description", "")),
            str(left.get("material_context", "")),
            str(right.get("name", "")),
            str(right.get("description", "")),
            str(right.get("material_context", "")),
        )
    if node_type == "CorrectiveAction":
        # Similar action titles are not enough: different procedures must not be
        # collapsed.  Require the normalized instructions to be identical.
        return bool(_surface(left.get("instruction_text"))) and _surface(
            left.get("instruction_text")
        ) == _surface(right.get("instruction_text"))
    if node_type == "ErrorCode":
        return bool(_surface(left.get("code"))) and _surface(left.get("code")) == _surface(right.get("code"))
    return False


def _is_ambiguous_candidate(node_type: str, left: dict[str, Any], right: dict[str, Any]) -> bool:
    if node_type == "Symptom":
        return symptoms_match(
            str(left.get("name", "")), str(left.get("description", "")),
            str(right.get("name", "")), str(right.get("description", "")),
        )
    if node_type == "FailureMode":
        return failure_modes_match(
            str(left.get("name", "")), str(left.get("description", "")), str(left.get("material_context", "")),
            str(right.get("name", "")), str(right.get("description", "")), str(right.get("material_context", "")),
        )
    if node_type == "CorrectiveAction":
        return corrective_actions_match(
            str(left.get("name", "")), str(left.get("description", "")), str(left.get("instruction_text", "")),
            str(right.get("name", "")), str(right.get("description", "")), str(right.get("instruction_text", "")),
        )
    if node_type == "Component":
        left_tokens = set(_surface(left.get("name"), singular=True).split())
        right_tokens = set(_surface(right.get("name"), singular=True).split())
        return bool(left_tokens and right_tokens) and len(left_tokens & right_tokens) / min(
            len(left_tokens), len(right_tokens)
        ) >= 0.8
    if node_type == "ErrorCode":
        return _surface(left.get("code")) == _surface(right.get("code")) != ""
    return False


def _richness(value: Any) -> int:
    if isinstance(value, list):
        return sum(_richness(item) for item in value)
    if isinstance(value, dict):
        return sum(_richness(item) for item in value.values())
    return len(str(value or "").strip())


def _merge_node(primary: dict[str, Any], duplicate: dict[str, Any], *, id_property: str) -> dict[str, Any]:
    merged = deepcopy(primary)
    for key, candidate in duplicate.items():
        if key == id_property:
            continue
        current = merged.get(key)
        if isinstance(current, list) and isinstance(candidate, list):
            merged[key] = list(dict.fromkeys([*current, *candidate]))
        elif not current or _richness(candidate) > _richness(current):
            merged[key] = deepcopy(candidate)
    return merged


def canonicalize_ontology_instance(
    ontology: OntologyInstance,
    *,
    max_ambiguous_groups: int = 50,
) -> tuple[OntologyInstance, dict[str, Any]]:
    """Consolidate safe duplicates and return an auditable report.

    The configured ontology supplies node types and ID properties.  Nothing in
    this function depends on a manufacturer, asset class, manual, page number,
    or acceptance-gold term.
    """
    schema = load_ontology_schema()
    payload = deepcopy(ontology.model_dump())
    id_remap: dict[tuple[str, str], str] = {}
    merged_groups: list[dict[str, Any]] = []
    ambiguous_pairs: list[tuple[str, str, str]] = []

    for node_def in schema.nodes:
        node_type = node_def.name
        id_property = _id_property(node_def)
        raw_nodes = [node for node in payload.get("nodes", {}).get(node_type, []) if isinstance(node, dict)]
        if node_type == "Asset" or len(raw_nodes) < 2:
            continue

        retained: list[dict[str, Any]] = []
        group_ids: dict[str, list[str]] = {}
        for candidate in sorted(raw_nodes, key=lambda item: str(item.get(id_property, ""))):
            candidate_id = str(candidate.get(id_property, "")).strip()
            match_index = next(
                (
                    index
                    for index, current in enumerate(retained)
                    if _safe_identity_equivalent(node_type, current, candidate)
                ),
                None,
            )
            if match_index is None:
                retained.append(candidate)
                if candidate_id:
                    group_ids[candidate_id] = [candidate_id]
                continue

            canonical = retained[match_index]
            canonical_id = str(canonical.get(id_property, "")).strip()
            if not canonical_id or not candidate_id:
                retained.append(candidate)
                continue
            retained[match_index] = _merge_node(canonical, candidate, id_property=id_property)
            id_remap[(node_type, candidate_id)] = canonical_id
            group_ids.setdefault(canonical_id, [canonical_id]).append(candidate_id)

        payload["nodes"][node_type] = retained
        for canonical_id, source_ids in sorted(group_ids.items()):
            if len(source_ids) > 1:
                merged_groups.append(
                    {
                        "node_type": node_type,
                        "canonical_id": canonical_id,
                        "source_ids": source_ids,
                        "reason": "normalized identity plus compatible type semantics",
                    }
                )

        for left, right in combinations(retained, 2):
            if not _is_ambiguous_candidate(node_type, left, right):
                continue
            left_id = str(left.get(id_property, "")).strip()
            right_id = str(right.get(id_property, "")).strip()
            if left_id and right_id:
                ambiguous_pairs.append((node_type, left_id, right_id))

    # Report connected candidate clusters rather than every pair. A generic
    # token such as "cable" can otherwise create a quadratic review queue even
    # though no automatic merge is made. Clustering changes triage only; every
    # original node and the pair count remain auditable.
    adjacency: dict[tuple[str, str], set[str]] = {}
    for node_type, left_id, right_id in ambiguous_pairs:
        adjacency.setdefault((node_type, left_id), set()).add(right_id)
        adjacency.setdefault((node_type, right_id), set()).add(left_id)
    ambiguous_groups: list[dict[str, Any]] = []
    visited: set[tuple[str, str]] = set()
    for node_type, node_id in sorted(adjacency):
        if (node_type, node_id) in visited:
            continue
        stack = [node_id]
        cluster: set[str] = set()
        while stack:
            current = stack.pop()
            key = (node_type, current)
            if key in visited:
                continue
            visited.add(key)
            cluster.add(current)
            stack.extend(sorted(adjacency.get(key, set()) - cluster))
        if len(cluster) > 1:
            ambiguous_groups.append({
                "node_type": node_type,
                "node_ids": sorted(cluster),
                "reason": "semantic similarity requires human or selective-model decision",
            })

    ambiguous_groups_truncated = len(ambiguous_groups) > max_ambiguous_groups
    ambiguous_groups = ambiguous_groups[:max_ambiguous_groups]

    # FailureMode.material_context is an ontology link in property form and
    # must follow the same safe Component ID remapping as relation endpoints.
    for failure_mode in payload.get("nodes", {}).get("FailureMode", []):
        if not isinstance(failure_mode, dict):
            continue
        material_context = str(failure_mode.get("material_context", "") or "").strip()
        failure_mode["material_context"] = id_remap.get(
            ("Component", material_context), material_context
        )

    relation_by_key: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for relation in payload.get("relations", []):
        relation = deepcopy(relation)
        from_type = str(relation.get("from_type", ""))
        to_type = str(relation.get("to_type", ""))
        relation["from_id"] = id_remap.get((from_type, str(relation.get("from_id", ""))), relation.get("from_id", ""))
        relation["to_id"] = id_remap.get((to_type, str(relation.get("to_id", ""))), relation.get("to_id", ""))
        key = (
            str(relation.get("name", "")), from_type, str(relation.get("from_id", "")),
            to_type, str(relation.get("to_id", "")),
        )
        existing = relation_by_key.get(key)
        if existing is None:
            relation_by_key[key] = relation
            continue
        evidence_keys = {
            (item.get("source_page"), item.get("source_reference"), item.get("quote"), item.get("source_anchor"))
            for item in existing.get("evidence", [])
            if isinstance(item, dict)
        }
        for item in relation.get("evidence", []):
            if not isinstance(item, dict):
                continue
            evidence_key = (
                item.get("source_page"), item.get("source_reference"), item.get("quote"), item.get("source_anchor")
            )
            if evidence_key not in evidence_keys:
                existing.setdefault("evidence", []).append(item)
                evidence_keys.add(evidence_key)

    payload["relations"] = list(relation_by_key.values())
    result = OntologyInstance.model_validate(payload)
    return result, {
        "policy": "deterministic_conservative_v1",
        "auto_merged_count": len(id_remap),
        "auto_merged_groups": merged_groups,
        "ambiguous_group_count": len(ambiguous_groups),
        "ambiguous_candidate_pair_count": len(ambiguous_pairs),
        "ambiguous_groups": ambiguous_groups,
        "ambiguous_groups_truncated": ambiguous_groups_truncated,
    }
