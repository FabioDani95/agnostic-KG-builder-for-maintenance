from __future__ import annotations

import json
import logging
import re
import time
from copy import deepcopy
from typing import Any, TypedDict

from httpx import Timeout
from langgraph.graph import END, StateGraph
from openai import OpenAI

from backend.app_config import (
    get_confidence_config,
    get_ontology_config,
    get_effective_reflective_loop_config as get_reflective_loop_config,
)
from backend.config import settings
from backend.models import (
    ConfidenceReport,
    GraphIssue,
    HumanBindingAnswer,
    HumanRequiredField,
    OntologyEvidence,
    OntologyInstance,
    OntologyPipelineResponse,
    OntologyRelationDefinition,
    OntologyRelationInstance,
    OntologySchemaDefinition,
    PipelineIssue,
    SuggestedRelation,
)
from backend.prompts.ontology_prompt import (
    build_ontology_extraction_prompt,
    build_ontology_relation_extraction_prompt,
    build_ontology_re_extraction_prompt,
    build_ontology_validation_prompt,
)
from backend.services.llm_guardrails import (
    enforce_llm_limits,
    llm_timeout_message,
)
from backend.services.candidate_mining_service import (
    mine_candidates,
    render_candidates_prompt_block,
)
from backend.services.language_utils import normalize_language_code
from backend.services.type_consistency_service import evaluate_type_consistency
from backend.services.ontology_schema_service import (
    dump_ontology_schema_json,
    load_ontology_schema,
)
from backend.services.ontology_semantics import infer_asset_type, normalize_asset_node
from backend.services.ontology_semantics import infer_component_match_for_failure_mode
from backend.services.pdf_service import format_text_with_pages
from backend.services.run_metrics import aggregate_usage, usage_from_response

logger = logging.getLogger(__name__)


class PipelineState(TypedDict, total=False):
    source_type: str
    source_title: str
    asset_identity: dict[str, Any]
    target_language: str
    text_with_pages: str
    model_name: str
    schema: OntologySchemaDefinition
    schema_json: str
    candidates_block: str
    ontology: OntologyInstance
    semantic_issues: list[PipelineIssue]
    schema_issues: list[PipelineIssue]
    human_required_fields: list[HumanRequiredField]
    # Reflective loop state
    retry_count: int
    last_issues: list[PipelineIssue]
    needs_human_review: bool
    # Graph reasoning state
    graph_issues: list[GraphIssue]
    suggested_relations: list[SuggestedRelation]
    # Confidence scoring state (Step 3)
    confidence_report: ConfidenceReport | None
    llm_usage: list[dict[str, Any]]


def _get_client(timeout_seconds: int = 300) -> OpenAI:
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=Timeout(timeout_seconds, connect=10.0),
    )


def _ontology_cfg(max_output_tokens: int) -> dict[str, int]:
    raw = get_ontology_config()
    return {
        "timeout_seconds": int(raw.get("timeout_seconds", 360)),
        "max_input_chars": int(raw.get("max_input_chars", 220000)),
        "estimated_max_input_tokens": int(raw.get("estimated_max_input_tokens", 55000)),
        "max_output_tokens": max_output_tokens,
    }


def _asset_identity_prompt_block(asset_identity: dict[str, Any] | None) -> str:
    identity = asset_identity or {}
    asset_id = str(identity.get("asset_id", "") or "").strip()
    asset_name = str(identity.get("name", "") or "").strip()
    if not (asset_id and asset_name):
        return ""

    lines = [
        "## Canonical Asset Identity",
        "Use this exact asset identity across the whole ontology draft.",
        f"- asset_id: {asset_id}",
        f"- name: {asset_name}",
    ]
    for key in ("brand", "model", "asset_type"):
        value = str(identity.get(key, "") or "").strip()
        if value:
            lines.append(f"- {key}: {value}")
    lines.extend([
        "Rules:",
        "- Emit exactly one Asset node for the document.",
        "- Reuse the exact asset_id above for every Asset relation anchor.",
        "- Do not invent alternative Asset IDs or alternative root-asset names for the same manual.",
    ])
    return "\n".join(lines)


_PARSE_REPAIR_EVENTS: list[dict[str, Any]] = []


def _reset_parse_repair_events() -> None:
    _PARSE_REPAIR_EVENTS.clear()


def consume_parse_repair_events() -> list[dict[str, Any]]:
    events = list(_PARSE_REPAIR_EVENTS)
    _PARSE_REPAIR_EVENTS.clear()
    return events


def _record_parse_repair(strategy: str, original_error: str) -> None:
    event = {"strategy": strategy, "original_error": original_error}
    _PARSE_REPAIR_EVENTS.append(event)
    logger.warning("[ontology] JSON parse repaired via %s (original: %s)", strategy, original_error)


def _extract_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object from an LLM response with progressive repair fallbacks.

    Strategy ladder:
      1. Strict json.loads on the trimmed text.
      2. Substring between first '{' and last '}' (unchanged legacy behavior).
      3. json_repair library if available (best-effort semantic repair).
      4. Lightweight regex repair (strip trailing commas, add commas between
         adjacent closing/opening tokens).

    Each non-strict path records a parse_repair event consumable via
    consume_parse_repair_events() so run_metrics / supervisor_log can surface it.
    """
    raw = raw.strip()
    if not raw:
        raise json.JSONDecodeError("Empty LLM response", raw, 0)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as strict_err:
        original_error = str(strict_err)

        candidate = raw
        first_brace = raw.find("{")
        last_brace = raw.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            candidate = raw[first_brace : last_brace + 1]
            try:
                parsed = json.loads(candidate)
                _record_parse_repair("substring_extraction", original_error)
                return parsed
            except json.JSONDecodeError:
                pass

        try:
            from json_repair import repair_json  # type: ignore

            repaired = repair_json(candidate, return_objects=False)
            parsed = json.loads(repaired)
            if isinstance(parsed, dict):
                _record_parse_repair("json_repair_library", original_error)
                return parsed
        except ImportError:
            pass
        except (json.JSONDecodeError, ValueError):
            pass

        regex_repaired = _regex_repair_json(candidate)
        if regex_repaired is not None:
            try:
                parsed = json.loads(regex_repaired)
                if isinstance(parsed, dict):
                    _record_parse_repair("regex_repair", original_error)
                    return parsed
            except json.JSONDecodeError:
                pass

        raise strict_err


def _completion_hit_output_limit(
    *,
    usage: dict[str, Any],
    finish_reason: str | None,
    max_output_tokens: int,
) -> bool:
    completion_tokens = int((usage or {}).get("completion", 0) or 0)
    return str(finish_reason or "").lower() == "length" or completion_tokens >= int(max_output_tokens or 0)


class _JsonCompletionRetryExhausted(json.JSONDecodeError):
    def __init__(self, msg: str, doc: str, pos: int, *, usages: list[dict[str, Any]]):
        super().__init__(msg, doc, pos)
        self.usages = list(usages)


def _parse_json_completion_with_retry(
    *,
    phase_label: str,
    run_completion,
    initial_max_output_tokens: int,
    retry_max_output_tokens: int,
    empty_visible_output: set[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run a JSON-producing completion, retrying once when the visible output was truncated.

    Two failure signatures are retried with a larger completion budget:
    1. visible output is just an empty JSON object at the completion limit
    2. JSON parsing fails and the completion appears to have hit the output limit
    """
    empty_visible_output = empty_visible_output or {"{}"}

    def _parse_with_repair_tracking(payload: str) -> tuple[dict[str, Any], bool]:
        before = len(_PARSE_REPAIR_EVENTS)
        parsed = _extract_json_object(payload)
        return parsed, len(_PARSE_REPAIR_EVENTS) > before

    def _parse_retry_result(
        payload: str,
        retry_usage: dict[str, Any],
        retry_finish_reason: str | None,
        *,
        retried_max_output_tokens: int,
    ) -> tuple[dict[str, Any], bool]:
        parsed, repaired = _parse_with_repair_tracking(payload)
        retry_hit_limit = _completion_hit_output_limit(
            usage=retry_usage,
            finish_reason=retry_finish_reason,
            max_output_tokens=retried_max_output_tokens,
        )
        if retry_hit_limit and (payload.strip() in empty_visible_output or repaired):
            raise json.JSONDecodeError(
                "Retry output still appears truncated at the completion limit",
                payload,
                0,
            )
        return parsed, repaired

    raw, usage, finish_reason = run_completion(initial_max_output_tokens)
    usages = [usage]
    hit_limit = _completion_hit_output_limit(
        usage=usage,
        finish_reason=finish_reason,
        max_output_tokens=initial_max_output_tokens,
    )

    if raw.strip() in empty_visible_output and hit_limit and retry_max_output_tokens > initial_max_output_tokens:
        logger.warning(
            "[ontology] %s returned empty visible JSON at completion limit (%d tokens, finish_reason=%s); retrying once with max_output_tokens=%d",
            phase_label,
            initial_max_output_tokens,
            finish_reason or "unknown",
            retry_max_output_tokens,
        )
        raw, retry_usage, retry_finish_reason = run_completion(retry_max_output_tokens)
        usages.append(retry_usage)
        try:
            parsed, _ = _parse_retry_result(
                raw,
                retry_usage,
                retry_finish_reason,
                retried_max_output_tokens=retry_max_output_tokens,
            )
        except json.JSONDecodeError as exc:
            raise _JsonCompletionRetryExhausted(exc.msg, exc.doc, exc.pos, usages=usages) from exc
        return parsed, usages

    try:
        parsed, repaired = _parse_with_repair_tracking(raw)
    except json.JSONDecodeError:
        if not hit_limit or retry_max_output_tokens <= initial_max_output_tokens:
            raise
        logger.warning(
            "[ontology] %s JSON parse failed at completion limit (%d tokens, finish_reason=%s); retrying once with max_output_tokens=%d",
            phase_label,
            initial_max_output_tokens,
            finish_reason or "unknown",
            retry_max_output_tokens,
        )
        raw, retry_usage, retry_finish_reason = run_completion(retry_max_output_tokens)
        usages.append(retry_usage)
        try:
            parsed, _ = _parse_retry_result(
                raw,
                retry_usage,
                retry_finish_reason,
                retried_max_output_tokens=retry_max_output_tokens,
            )
        except json.JSONDecodeError as exc:
            raise _JsonCompletionRetryExhausted(exc.msg, exc.doc, exc.pos, usages=usages) from exc
        return parsed, usages

    if repaired and hit_limit and retry_max_output_tokens > initial_max_output_tokens:
        logger.warning(
            "[ontology] %s JSON required repair at completion limit (%d tokens, finish_reason=%s); retrying once with max_output_tokens=%d",
            phase_label,
            initial_max_output_tokens,
            finish_reason or "unknown",
            retry_max_output_tokens,
        )
        raw, retry_usage, retry_finish_reason = run_completion(retry_max_output_tokens)
        usages.append(retry_usage)
        try:
            parsed, _ = _parse_retry_result(
                raw,
                retry_usage,
                retry_finish_reason,
                retried_max_output_tokens=retry_max_output_tokens,
            )
        except json.JSONDecodeError as exc:
            raise _JsonCompletionRetryExhausted(exc.msg, exc.doc, exc.pos, usages=usages) from exc
        return parsed, usages

    return parsed, usages


def _regex_repair_json(text: str) -> str | None:
    """Best-effort regex repair for the most common LLM JSON mistakes."""
    if not text:
        return None
    repaired = re.sub(r",\s*([\]\}])", r"\1", text)
    repaired = re.sub(r"([\]\}\"])\s*\n\s*(?=[\"\{\[])", r"\1,\n", repaired)
    open_braces = repaired.count("{")
    close_braces = repaired.count("}")
    if open_braces > close_braces:
        repaired = repaired + ("}" * (open_braces - close_braces))
    open_brackets = repaired.count("[")
    close_brackets = repaired.count("]")
    if open_brackets > close_brackets:
        repaired = repaired + ("]" * (open_brackets - close_brackets))
    return repaired


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
            identity.get("name") or source_title or "Technical asset extracted from manual context"
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
    for node_def in schema.nodes:
        node_list = nodes.setdefault(node_def.name, [])
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


def _validate_schema(ontology: OntologyInstance, schema: OntologySchemaDefinition) -> tuple[list[PipelineIssue], list[HumanRequiredField]]:
    issues: list[PipelineIssue] = []
    human_required_fields: list[HumanRequiredField] = []
    node_map = _schema_node_map(schema)
    node_index = _collect_node_index(ontology, schema)
    substantive_node_count = _substantive_node_count(ontology)

    if substantive_node_count == 0:
        issues.append(PipelineIssue(
            severity="error",
            code="empty_draft_content",
            message="Ontology draft contains only the Asset node and no extracted diagnostic content.",
            target_type="ontology",
            fix_hint="Rerun the draft with broader page coverage or review the extraction prompt/output.",
        ))

    asset_count = len(ontology.nodes.get("Asset", []) or [])
    if asset_count > 1:
        issues.append(PipelineIssue(
            severity="error",
            code="multiple_assets_detected",
            message=f"Ontology draft contains {asset_count} Asset nodes; exactly one canonical Asset is allowed.",
            target_type="Asset",
            fix_hint="Collapse duplicate Asset variants to the single scoping-selected asset identity and remap relations.",
        ))

    for node_type, items in ontology.nodes.items():
        node_def = node_map.get(node_type)
        if not node_def:
            issues.append(PipelineIssue(
                severity="error",
                code="unknown_node_type",
                message=f"Unknown node type {node_type}.",
                target_type=node_type,
            ))
            continue

        id_prop = _node_id_property(node_def)
        seen_ids: set[str] = set()
        for item in items:
            node_id = str(item.get(id_prop, "")).strip()
            if not node_id:
                issues.append(PipelineIssue(
                    severity="error",
                    code="missing_id",
                    message=f"{node_type} is missing unique identifier {id_prop}.",
                    target_type=node_type,
                    property_name=id_prop,
                ))
                continue
            if node_id in seen_ids:
                issues.append(PipelineIssue(
                    severity="error",
                    code="duplicate_id",
                    message=f"Duplicate {node_type} identifier {node_id}.",
                    target_type=node_type,
                    target_id=node_id,
                    property_name=id_prop,
                ))
                continue
            seen_ids.add(node_id)

            for prop in node_def.properties:
                val = item.get(prop.name)
                if prop.required and (val is None or (isinstance(val, str) and not val.strip())):
                    if prop.name == id_prop:
                        issues.append(PipelineIssue(
                            severity="error",
                            code="missing_id",
                            message=f"{node_type} is missing unique identifier {id_prop}.",
                            target_type=node_type,
                            target_id=node_id,
                            property_name=id_prop,
                            fix_hint="Regenerate the draft or repair the node identity before exporting.",
                        ))
                        continue

                    entity_label = str(item.get("name") or node_id or node_type).strip()
                    prompt, reason = _human_prompt_for_property(node_type, prop.name, entity_label)
                    suggested_value = ""
                    if prop.name == "source_type":
                        suggested_value = str(ontology.source_type or "").strip()
                    elif prop.name == "source_title":
                        suggested_value = str(ontology.source_title or "").strip()
                    elif prop.name == "source_reference" and item.get("source_page"):
                        suggested_value = f"PAGE {item['source_page']}"

                    human_required_fields.append(_make_human_field(
                        node_type=node_type,
                        node_id=node_id,
                        property_name=prop.name,
                        reason=reason,
                        prompt=prompt,
                        suggested_value=suggested_value,
                    ))

    component_ids = {
        str(item.get("component_id", "")).strip()
        for item in ontology.nodes.get("Component", [])
        if isinstance(item, dict) and str(item.get("component_id", "")).strip()
    }
    for fm in ontology.nodes.get("FailureMode", []):
        if not isinstance(fm, dict):
            continue
        material_context = str(fm.get("material_context", "") or "").strip()
        if not material_context:
            continue
        if material_context not in component_ids:
            issues.append(PipelineIssue(
                severity="warning",
                code="material_context_not_linked",
                message=(
                    f"FailureMode '{fm.get('name', fm.get('failure_mode_id', ''))}' has "
                    f"material_context='{material_context}' which is not a Component.component_id."
                ),
                target_type="FailureMode",
                target_id=str(fm.get("failure_mode_id", "")).strip(),
                property_name="material_context",
                fix_hint=(
                    "Either set material_context to an existing Component.component_id, "
                    "add the missing Component node and link it here, or leave the field "
                    "empty and emit an AFFECTS relation to represent the link instead."
                ),
            ))

    relation_defs = {rel.name: rel for rel in schema.relations}
    for rel in ontology.relations:
        rel_def: OntologyRelationDefinition | None = relation_defs.get(rel.name)
        if rel_def is None:
            issues.append(PipelineIssue(
                severity="error",
                code="unknown_relation",
                message=f"Unknown relation {rel.name}.",
                target_type="relation",
                target_id=rel.name,
            ))
            continue
        if rel.from_type != rel_def.domain or rel.to_type != rel_def.range:
            issues.append(PipelineIssue(
                severity="error",
                code="relation_domain_range_mismatch",
                message=f"{rel.name} must connect {rel_def.domain} -> {rel_def.range}.",
                target_type="relation",
                target_id=rel.name,
            ))
        if rel.from_id not in node_index.get(rel.from_type, set()):
            issues.append(PipelineIssue(
                severity="error",
                code="relation_missing_source",
                message=f"Relation {rel.name} references missing source node {rel.from_id}.",
                target_type="relation",
                target_id=rel.name,
            ))
        if rel.to_id not in node_index.get(rel.to_type, set()):
            issues.append(PipelineIssue(
                severity="error",
                code="relation_missing_target",
                message=f"Relation {rel.name} references missing target node {rel.to_id}.",
                target_type="relation",
                target_id=rel.name,
            ))

    # Deduplicate by (node_type, property_name): if multiple nodes of the same type
    # are missing the same property, show a single field that applies to all of them.
    deduped_human_fields: dict[str, HumanRequiredField] = {}
    for field in human_required_fields:
        group_key = f"{field.target_type}::*::{field.property_name}"
        if group_key not in deduped_human_fields:
            # Represent the group with a wildcard key so _apply_human_answers broadcasts the value.
            grouped = field.model_copy(update={"field_key": group_key, "target_id": "*"})
            deduped_human_fields[group_key] = grouped
    return issues, list(deduped_human_fields.values())


def _call_extractor_llm(state: PipelineState) -> PipelineState:
    started = time.perf_counter()
    prompt_blocks = [state.get("candidates_block", ""), _asset_identity_prompt_block(state.get("asset_identity"))]
    system_prompt = build_ontology_extraction_prompt(
        schema_json=state["schema_json"],
        source_type=state["source_type"],
        source_title=state["source_title"],
        candidate_candidates_block="\n\n".join(block for block in prompt_blocks if block),
    )
    cfg = _ontology_cfg(get_ontology_config().get("extraction_max_output_tokens", 8000))
    enforce_llm_limits(
        phase="Ontology draft",
        cfg=cfg,
        system_text=system_prompt,
        user_text=state["text_with_pages"],
    )
    client = _get_client(cfg["timeout_seconds"])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["text_with_pages"]},
    ]

    retry_tokens = max(
        int(get_ontology_config().get("extraction_retry_max_output_tokens", 20000)),
        cfg["max_output_tokens"] + 4000,
    )

    def _run_completion(max_output_tokens: int):
        try:
            response = client.chat.completions.create(
                model=state["model_name"] or settings.MODEL_NAME,
                temperature=0.0,
                max_completion_tokens=max_output_tokens,
                messages=messages,
            )
        except Exception as exc:
            msg = str(exc).lower()
            if "timeout" in msg:
                raise RuntimeError(llm_timeout_message("Ontology draft", cfg["timeout_seconds"])) from exc
            raise RuntimeError(f"Ontology draft failed before completion: {exc}") from exc
        return (
            response.choices[0].message.content or "{}",
            usage_from_response(response, "ontology_draft"),
            getattr(response.choices[0], "finish_reason", None),
        )

    usages: list[dict[str, Any]] = []
    try:
        data, usages = _parse_json_completion_with_retry(
            phase_label="Draft",
            run_completion=_run_completion,
            initial_max_output_tokens=cfg["max_output_tokens"],
            retry_max_output_tokens=retry_tokens,
        )
    except json.JSONDecodeError as exc:
        usages = list(getattr(exc, "usages", usages))
        logger.warning(
            "[ontology] Draft JSON parse failed after retry; returning an empty chunk result instead of aborting the whole run: %s",
            exc,
        )
        _record_parse_repair("fallback_empty_draft_chunk", str(exc))
        return {
            "ontology": _empty_instance(state["schema"], state["source_type"], state["source_title"]),
            "llm_usage": [*state.get("llm_usage", []), *usages],
        }

    ontology = OntologyInstance.model_validate(_coerce_raw_ontology_data(
        data=data,
        schema=state["schema"],
        source_type=state["source_type"],
        source_title=state["source_title"],
    ))
    ontology = _normalize_ontology_instance(
        ontology=ontology,
        schema=state["schema"],
        source_type=state["source_type"],
        source_title=state["source_title"],
        asset_identity=state.get("asset_identity"),
    )
    logger.info("[ontology] Extraction draft generated (%.1fs)", time.perf_counter() - started)
    return {
        "ontology": ontology,
        "llm_usage": [*state.get("llm_usage", []), *usages],
    }


def _normalize_node(state: PipelineState) -> PipelineState:
    ontology = _normalize_ontology_instance(
        ontology=state["ontology"],
        schema=state["schema"],
        source_type=state["source_type"],
        source_title=state["source_title"],
        asset_identity=state.get("asset_identity"),
    )
    return {"ontology": ontology}


def _relation_extract_node(state: PipelineState) -> PipelineState:
    """Second pass: infer only ontology relations from the already-extracted nodes."""
    ontology = state["ontology"]
    if not _should_run_relation_pass(ontology):
        logger.info("[ontology] Relation pass skipped (insufficient candidate node types)")
        return {}

    started = time.perf_counter()
    candidate_nodes_json = json.dumps(
        _compact_nodes_for_relation_pass(ontology),
        ensure_ascii=False,
        indent=2,
    )
    existing_relations_json = json.dumps(
        _compact_existing_relations_for_relation_pass(ontology.relations),
        ensure_ascii=False,
        indent=2,
    )
    system_prompt = build_ontology_relation_extraction_prompt(
        candidate_nodes_json=candidate_nodes_json,
        existing_relations_json=existing_relations_json,
    )
    cfg = _ontology_cfg(get_ontology_config().get("relation_extraction_max_output_tokens", 6000))
    relation_pass_text = _build_relation_pass_text(state["text_with_pages"], ontology)
    enforce_llm_limits(
        phase="Ontology relation pass",
        cfg=cfg,
        system_text=system_prompt,
        user_text=relation_pass_text,
    )
    client = _get_client(cfg["timeout_seconds"])
    try:
        response = client.chat.completions.create(
            model=state["model_name"] or settings.MODEL_NAME,
            temperature=0.0,
            max_completion_tokens=cfg["max_output_tokens"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": relation_pass_text},
            ],
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "timeout" in msg:
            raise RuntimeError(llm_timeout_message("Ontology relation pass", cfg["timeout_seconds"])) from exc
        raise RuntimeError(f"Ontology relation pass failed before completion: {exc}") from exc

    raw = response.choices[0].message.content or '{"relations":[]}'
    usage = usage_from_response(response, "ontology_relation_extraction")
    try:
        data = _extract_json_object(raw)
    except Exception:
        logger.warning("[ontology] Failed to parse relation pass response; keeping existing relations")
        return {
            "llm_usage": [*state.get("llm_usage", []), usage],
        }

    candidate_relations = _coerce_relations(
        data.get("relations", []),
        ontology.model_dump().get("nodes", {}),
        state["schema"],
    )
    if not candidate_relations:
        logger.info("[ontology] Relation pass returned no additional relations")
        return {
            "llm_usage": [*state.get("llm_usage", []), usage],
        }

    merged = ontology.model_dump()
    merged["relations"] = [
        *merged.get("relations", []),
        *candidate_relations,
    ]
    normalized = _normalize_ontology_instance(
        ontology=OntologyInstance.model_validate(merged),
        schema=state["schema"],
        source_type=state["source_type"],
        source_title=state["source_title"],
    )
    logger.info(
        "[ontology] Relation pass completed (%.1fs) — +%d candidate relations",
        time.perf_counter() - started,
        len(candidate_relations),
    )
    return {
        "ontology": normalized,
        "llm_usage": [*state.get("llm_usage", []), usage],
    }


def _semantic_validate_node(state: PipelineState) -> PipelineState:
    loop_cfg = get_reflective_loop_config()
    max_retries = int(loop_cfg.get("max_retries", 2))
    if max_retries == 0:
        logger.info("[ontology] Semantic validation skipped (max_retries=0)")
        return {"semantic_issues": []}

    started = time.perf_counter()
    system_prompt = build_ontology_validation_prompt(state["schema_json"])
    user_payload = (
        "MANUAL TEXT\n"
        f"{state['text_with_pages']}\n\n"
        "ONTOLOGY INSTANCE\n"
        f"{json.dumps(state['ontology'].model_dump(), ensure_ascii=False, indent=2)}"
    )
    cfg = _ontology_cfg(get_ontology_config().get("validation_max_output_tokens", 3000))
    enforce_llm_limits(
        phase="Ontology semantic validation",
        cfg=cfg,
        system_text=system_prompt,
        user_text=user_payload,
    )
    client = _get_client(cfg["timeout_seconds"])
    try:
        response = client.chat.completions.create(
            model=state["model_name"] or settings.MODEL_NAME,
            temperature=0.0,
            max_completion_tokens=cfg["max_output_tokens"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "timeout" in msg:
            raise RuntimeError(llm_timeout_message("Ontology semantic validation", cfg["timeout_seconds"])) from exc
        raise RuntimeError(f"Ontology semantic validation failed before completion: {exc}") from exc
    raw = response.choices[0].message.content or '{"issues":[]}'
    usage = usage_from_response(response, "ontology_validation")
    try:
        data = _extract_json_object(raw)
    except Exception:
        logger.warning("[ontology] Failed to parse semantic validation response")
        return {
            "semantic_issues": [],
            "llm_usage": [*state.get("llm_usage", []), usage],
        }

    issues = []
    for item in data.get("issues", []):
        if not isinstance(item, dict):
            continue
        issues.append(PipelineIssue.model_validate({
            "severity": str(item.get("severity") or "warning"),
            "code": str(item.get("code") or "semantic_issue"),
            "message": str(item.get("message") or ""),
            "target_type": str(item.get("target_type") or ""),
            "target_id": str(item.get("target_id") or ""),
            "property_name": str(item.get("property_name") or ""),
            "fix_hint": str(item.get("fix_hint") or ""),
        }))
    type_issues, type_reports = evaluate_type_consistency(state["ontology"])
    if type_issues:
        logger.info(
            "[ontology] TypeConsistency flagged %d symptom/failure-mode duplicates (of %d MAY_INDICATE pairs)",
            len(type_issues),
            len(type_reports),
        )
        issues.extend(type_issues)
    logger.info("[ontology] Semantic validation completed (%.1fs)", time.perf_counter() - started)
    return {
        "semantic_issues": issues,
        "llm_usage": [*state.get("llm_usage", []), usage],
    }


def _schema_validate_node(state: PipelineState) -> PipelineState:
    issues, human_fields = _validate_schema(state["ontology"], state["schema"])
    return {
        "schema_issues": issues,
        "human_required_fields": human_fields,
    }


def _graph_validate_node(state: PipelineState) -> PipelineState:
    """Run structural graph analysis using NetworkX (Step 2 of agentic roadmap)."""
    from backend.services.graph_reasoning import run_graph_analysis
    graph_issues, suggested_relations = run_graph_analysis(state["ontology"], state["schema"])
    return {
        "graph_issues": graph_issues,
        "suggested_relations": suggested_relations,
    }


def _confidence_score_node(state: PipelineState) -> PipelineState:
    """Compute schema-aware confidence scores for adaptive HITL (Step 3 of roadmap).

    Runs after schema_validate and graph_validate so that retry_count, semantic_issues,
    schema_issues, and human_required_fields are all finalized — the scorer only reads
    the state and never mutates the ontology.
    """
    from backend.services.confidence import score_ontology

    cfg = get_confidence_config()
    if not cfg.get("enabled", True):
        logger.info("[ontology] Confidence scoring disabled via config")
        return {"confidence_report": None}

    started = time.perf_counter()
    report = score_ontology(
        ontology=state["ontology"],
        schema=state["schema"],
        semantic_issues=state.get("semantic_issues", []),
        schema_issues=state.get("schema_issues", []),
        human_required_fields=state.get("human_required_fields", []),
        retry_count=state.get("retry_count", 0),
        config=cfg,
    )
    logger.info(
        "[ontology] Confidence scoring completed (%.1fs) — %d entries",
        time.perf_counter() - started,
        len(report.entries),
    )
    return {"confidence_report": report}


def _format_issues_summary(issues: list[PipelineIssue]) -> str:
    lines = []
    for i, issue in enumerate(issues, start=1):
        parts = [f"{i}. [{issue.severity.upper()}] {issue.code}: {issue.message}"]
        if issue.target_type:
            parts.append(f"   target_type: {issue.target_type}")
        if issue.target_id:
            parts.append(f"   target_id: {issue.target_id}")
        if issue.property_name:
            parts.append(f"   property_name: {issue.property_name}")
        if issue.fix_hint:
            parts.append(f"   fix_hint: {issue.fix_hint}")
        lines.append("\n".join(parts))
    return "\n\n".join(lines)


def _re_extract_node(state: PipelineState) -> PipelineState:
    """Re-run extraction incorporating structured feedback from semantic validation."""
    started = time.perf_counter()
    loop_cfg = get_reflective_loop_config()
    re_extract_max_tokens = int(loop_cfg.get("re_extract_max_output_tokens", 9000))

    issues_to_fix = state.get("last_issues", [])
    issues_summary = _format_issues_summary(issues_to_fix)
    previous_ontology_json = json.dumps(
        state["ontology"].model_dump(), ensure_ascii=False, indent=2
    )
    prompt_blocks = [state.get("candidates_block", ""), _asset_identity_prompt_block(state.get("asset_identity"))]
    system_prompt = build_ontology_re_extraction_prompt(
        schema_json=state["schema_json"],
        source_type=state["source_type"],
        source_title=state["source_title"],
        issues_summary=issues_summary,
        previous_ontology_json=previous_ontology_json,
        candidate_candidates_block="\n\n".join(block for block in prompt_blocks if block),
    )
    cfg = _ontology_cfg(re_extract_max_tokens)
    enforce_llm_limits(
        phase="Ontology re-extraction",
        cfg=cfg,
        system_text=system_prompt,
        user_text=state["text_with_pages"],
    )
    client = _get_client(cfg["timeout_seconds"])
    retry_count = state.get("retry_count", 0)
    previous_ontology = state["ontology"]
    logger.info("[ontology] Re-extraction attempt %d/%d", retry_count, get_reflective_loop_config().get("max_retries", 2))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["text_with_pages"]},
    ]

    retry_tokens = max(
        int(get_ontology_config().get("extraction_retry_max_output_tokens", 20000)),
        cfg["max_output_tokens"] + 4000,
    )

    def _run_completion(max_output_tokens: int):
        try:
            response = client.chat.completions.create(
                model=state["model_name"] or settings.MODEL_NAME,
                temperature=0.0,
                max_completion_tokens=max_output_tokens,
                messages=messages,
            )
        except Exception as exc:
            msg = str(exc).lower()
            if "timeout" in msg:
                raise RuntimeError(llm_timeout_message("Ontology re-extraction", cfg["timeout_seconds"])) from exc
            raise RuntimeError(f"Ontology re-extraction failed before completion: {exc}") from exc
        return (
            response.choices[0].message.content or "{}",
            usage_from_response(response, "ontology_re_extraction"),
            getattr(response.choices[0], "finish_reason", None),
        )

    usages: list[dict[str, Any]] = []
    try:
        data, usages = _parse_json_completion_with_retry(
            phase_label="Re-extraction",
            run_completion=_run_completion,
            initial_max_output_tokens=cfg["max_output_tokens"],
            retry_max_output_tokens=retry_tokens,
        )
    except json.JSONDecodeError as exc:
        usages = list(getattr(exc, "usages", usages))
        logger.warning(
            "[ontology] Re-extraction JSON parse failed after retry; keeping previous ontology: %s",
            exc,
        )
        _record_parse_repair("fallback_keep_previous_on_reextract_parse_failure", str(exc))
        return {
            "ontology": previous_ontology,
            "retry_count": retry_count + 1,
            "llm_usage": [*state.get("llm_usage", []), *usages],
        }

    ontology = OntologyInstance.model_validate(_coerce_raw_ontology_data(
        data=data,
        schema=state["schema"],
        source_type=state["source_type"],
        source_title=state["source_title"],
    ))
    ontology = _normalize_ontology_instance(
        ontology=ontology,
        schema=state["schema"],
        source_type=state["source_type"],
        source_title=state["source_title"],
        asset_identity=state.get("asset_identity"),
    )
    regression_reason = _retry_regression_reason(previous_ontology, ontology)
    if regression_reason:
        logger.warning(
            "[ontology] Discarding catastrophic retry regression: %s. Keeping previous ontology (%d substantive nodes, %d relations).",
            regression_reason,
            _substantive_node_count(previous_ontology),
            len(previous_ontology.relations or []),
        )
        return {
            "ontology": previous_ontology,
            "retry_count": retry_count + 1,
            "llm_usage": [*state.get("llm_usage", []), *usages],
        }
    logger.info("[ontology] Re-extraction completed (%.1fs)", time.perf_counter() - started)
    return {
        "ontology": ontology,
        "retry_count": retry_count + 1,
        "llm_usage": [*state.get("llm_usage", []), *usages],
    }


def _flag_human_review_node(state: PipelineState) -> PipelineState:
    """Mark the pipeline state for human review after max retries are exhausted."""
    issues = state.get("last_issues", [])
    logger.warning(
        "[ontology] Max retries exhausted (%d issues unresolved). Flagging for human review.",
        len(issues),
    )
    return {"needs_human_review": True}


def _route_after_semantic_validate(state: PipelineState) -> str:
    """Conditional routing after semantic_validate.

    - No actionable issues  → schema_validate (happy path)
    - Issues found, retries remaining → re_extract
    - Issues found, retries exhausted → human_review
    """
    loop_cfg = get_reflective_loop_config()
    max_retries = int(loop_cfg.get("max_retries", 2))
    if max_retries == 0:
        # Reflective loop disabled — preserve original linear behaviour.
        return "schema_validate"

    retry_on_severity = str(loop_cfg.get("retry_on_severity", "error")).lower()
    issues: list[PipelineIssue] = state.get("semantic_issues", [])

    # Filter issues by configured severity threshold.
    severity_rank = {"error": 2, "warning": 1}
    threshold = severity_rank.get(retry_on_severity, 2)
    actionable = [
        issue for issue in issues
        if severity_rank.get(str(issue.severity).lower(), 0) >= threshold
    ]

    if not actionable:
        return "schema_validate"

    retry_count = state.get("retry_count", 0)
    if retry_count < max_retries:
        return "re_extract"

    return "human_review"


def _update_last_issues(state: PipelineState) -> PipelineState:
    """Carry semantic_issues into last_issues so the re_extract node can read them."""
    return {"last_issues": state.get("semantic_issues", [])}


def _build_graph():
    graph = StateGraph(PipelineState)

    # Core nodes
    graph.add_node("extract", _call_extractor_llm)
    graph.add_node("normalize", _normalize_node)
    graph.add_node("relation_extract", _relation_extract_node)
    graph.add_node("semantic_validate", _semantic_validate_node)
    graph.add_node("capture_issues", _update_last_issues)
    graph.add_node("schema_validate", _schema_validate_node)
    graph.add_node("graph_validate", _graph_validate_node)
    graph.add_node("confidence_score", _confidence_score_node)

    # Reflective loop nodes
    graph.add_node("re_extract", _re_extract_node)
    graph.add_node("human_review", _flag_human_review_node)

    # Entry point and linear spine
    graph.set_entry_point("extract")
    graph.add_edge("extract", "normalize")
    graph.add_edge("normalize", "relation_extract")
    graph.add_edge("relation_extract", "semantic_validate")

    # Capture issues before routing so re_extract can access them even after state changes
    graph.add_edge("semantic_validate", "capture_issues")

    # Conditional routing after semantic validation
    graph.add_conditional_edges(
        "capture_issues",
        _route_after_semantic_validate,
        {
            "schema_validate": "schema_validate",
            "re_extract": "re_extract",
            "human_review": "human_review",
        },
    )

    # Re-extraction feeds back into normalize → semantic_validate
    graph.add_edge("re_extract", "normalize")

    # Human review routes to schema_validate
    graph.add_edge("human_review", "schema_validate")

    # Schema validation flows into graph reasoning, then confidence scoring
    graph.add_edge("schema_validate", "graph_validate")
    graph.add_edge("graph_validate", "confidence_score")
    graph.add_edge("confidence_score", END)

    return graph.compile()


_GRAPH = _build_graph()


def build_initial_ontology(
    text_with_pages: str,
    source_type: str,
    source_title: str,
    target_language: str,
    model_name: str,
    asset_identity: dict[str, Any] | None = None,
    on_event=None,
) -> tuple[OntologyPipelineResponse, dict[str, Any]]:
    schema = load_ontology_schema()
    normalized_target_language = normalize_language_code(target_language)
    _reset_parse_repair_events()
    mining_result = mine_candidates(text_with_pages)
    candidates_block = render_candidates_prompt_block(mining_result)
    if candidates_block:
        logger.info(
            "[ontology] Pre-LLM mining: %d component candidates, %d error-code candidates",
            len(mining_result.components),
            len(mining_result.error_codes),
        )
    if on_event:
        comp_count = len(mining_result.components)
        ec_count = len(mining_result.error_codes)
        on_event({"type": "progress", "phase": "ontology_draft",
                  "message": (
                      f"Pre-mining complete — {comp_count} component candidate(s), "
                      f"{ec_count} error-code candidate(s). Running ontology extraction…"
                  )})
    result = _GRAPH.invoke({
        "text_with_pages": text_with_pages,
        "source_type": source_type,
        "source_title": source_title,
        "asset_identity": asset_identity or {},
        "target_language": normalized_target_language,
        "model_name": model_name,
        "schema": schema,
        "schema_json": dump_ontology_schema_json(),
        "candidates_block": candidates_block,
        "ontology": _empty_instance(schema, source_type, source_title),
        "semantic_issues": [],
        "schema_issues": [],
        "human_required_fields": [],
        # Reflective loop initial state
        "retry_count": 0,
        "last_issues": [],
        "needs_human_review": False,
        # Graph reasoning initial state
        "graph_issues": [],
        "suggested_relations": [],
        # Confidence scoring initial state
        "confidence_report": None,
        "llm_usage": [],
    })
    ontology = result["ontology"]
    semantic_issues = result.get("semantic_issues", [])
    schema_issues = result.get("schema_issues", [])
    human_fields = result.get("human_required_fields", [])
    retry_count = result.get("retry_count", 0)
    needs_human_review = result.get("needs_human_review", False)
    graph_issues = result.get("graph_issues", [])
    suggested_relations = result.get("suggested_relations", [])
    confidence_report = result.get("confidence_report")
    llm_usage = result.get("llm_usage", [])
    is_schema_compliant = not schema_issues and not human_fields

    if needs_human_review:
        status = "needs_human_review"
    elif schema_issues:
        status = "blocked"
    elif human_fields:
        status = "needs_human"
    else:
        status = "ready"

    if retry_count:
        logger.info("[ontology] Reflective loop completed: %d re-extraction attempt(s).", retry_count)

    if on_event:
        total_nodes = sum(
            len(v) for v in (ontology.nodes or {}).values() if isinstance(v, list)
        )
        on_event({
            "type": "progress",
            "phase": "ontology_draft",
            "message": (
                f"Ontology draft complete — {total_nodes} node(s), "
                f"{len(result.get('suggested_relations', []))} suggested relation(s), "
                f"status: {status}."
                + (f" {len(human_fields)} required field(s) need your input." if human_fields else "")
            ),
            "status": status,
            "node_count": total_nodes,
            "human_fields_count": len(human_fields),
            "schema_issues_count": len(schema_issues),
        })

    response = OntologyPipelineResponse(
        status=status,
        ontology=ontology,
        semantic_issues=semantic_issues,
        schema_issues=schema_issues,
        human_required_fields=human_fields,
        is_schema_compliant=is_schema_compliant,
        is_ready_for_human_review=not schema_issues,
        retry_count=retry_count,
        graph_issues=graph_issues,
        suggested_relations=suggested_relations,
        confidence_report=confidence_report,
    )
    parse_repair_events = consume_parse_repair_events()
    return response, {
        **aggregate_usage(llm_usage),
        "retry_count": retry_count,
        "parse_repair_events": parse_repair_events,
        "mining_summary": mining_result.to_summary(),
    }


def apply_human_binding(
    ontology: OntologyInstance,
    answers: list[HumanBindingAnswer],
) -> OntologyPipelineResponse:
    from backend.services.confidence import score_ontology

    schema = load_ontology_schema()
    updated = _apply_human_answers(ontology, answers)
    updated = _normalize_ontology_instance(
        ontology=updated,
        schema=schema,
        source_type=updated.source_type,
        source_title=updated.source_title,
    )
    schema_issues, human_fields = _validate_schema(updated, schema)
    confidence_cfg = get_confidence_config()
    confidence_report = None
    if confidence_cfg.get("enabled", True):
        confidence_report = score_ontology(
            ontology=updated,
            schema=schema,
            schema_issues=schema_issues,
            human_required_fields=human_fields,
            config=confidence_cfg,
        )
    return OntologyPipelineResponse(
        status="blocked" if schema_issues else ("needs_human" if human_fields else "ready"),
        ontology=updated,
        semantic_issues=[],
        schema_issues=schema_issues,
        human_required_fields=human_fields,
        is_schema_compliant=not schema_issues and not human_fields,
        is_ready_for_human_review=not schema_issues,
        confidence_report=confidence_report,
    )


def validate_ontology_instance(
    ontology: OntologyInstance,
) -> tuple[list[PipelineIssue], list[HumanRequiredField]]:
    schema = load_ontology_schema()
    normalized = _normalize_ontology_instance(
        ontology=ontology,
        schema=schema,
        source_type=ontology.source_type,
        source_title=ontology.source_title,
    )
    return _validate_schema(normalized, schema)


def ontology_export_payload(ontology: OntologyInstance) -> str:
    from backend.services.ontology_export_store import prepare_exported_ontology

    return json.dumps(
        prepare_exported_ontology(ontology.model_dump()),
        indent=2,
        ensure_ascii=False,
    )
