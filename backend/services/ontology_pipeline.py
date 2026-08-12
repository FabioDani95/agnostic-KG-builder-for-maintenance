from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, TypedDict

from httpx import Timeout
from langgraph.graph import END, StateGraph

from backend.app_config import (
    get_confidence_config,
    get_ontology_config,
)
from backend.app_config import (
    get_effective_reflective_loop_config as get_reflective_loop_config,
)
from backend.config import settings
from backend.models import (
    ConfidenceReport,
    GraphIssue,
    HumanBindingAnswer,
    HumanRequiredField,
    OntologyInstance,
    OntologyPipelineResponse,
    OntologySchemaDefinition,
    PipelineIssue,
    SuggestedRelation,
)
from backend.prompts.diagnostic_bundle_prompt import build_diagnostic_bundle_prompt
from backend.prompts.ontology_prompt import (
    build_ontology_extraction_prompt,
    build_ontology_re_extraction_prompt,
    build_ontology_relation_extraction_prompt,
    build_ontology_validation_prompt,
)
from backend.services.candidate_mining_service import (
    mine_candidates,
    render_candidates_prompt_block,
)
from backend.services.cutplan_service import evidence_has_diagnostic_candidate
from backend.services.language_utils import normalize_language_code
from backend.services.llm_gateway import chat_reasoning_kwargs, chat_temperature_kwargs, get_client
from backend.services.llm_guardrails import (
    enforce_llm_limits,
    llm_timeout_message,
)
from backend.services.ontology_pipeline_coercion import (
    _apply_human_answers,
    _build_relation_pass_text,
    _coerce_raw_ontology_data,
    _coerce_relations,
    _collect_node_index,
    _compact_existing_relations_for_relation_pass,
    _compact_nodes_for_relation_pass,
    _empty_instance,
    _normalize_ontology_instance,
    _retry_regression_reason,
    _should_run_relation_pass,
    _substantive_node_count,
)
from backend.services.ontology_pipeline_parsing import (
    _extract_json_object,
    _parse_json_completion_with_retry,
    _record_parse_repair,
    _reset_parse_repair_events,
    consume_parse_repair_events,
)
from backend.services.ontology_pipeline_validation import _validate_schema
from backend.services.ontology_schema_service import (
    dump_ontology_schema_json,
    load_ontology_schema,
)
from backend.services.ontology_semantics import is_workspace_canonical_asset_identity
from backend.services.run_metrics import aggregate_usage, usage_from_response
from backend.services.type_consistency_service import evaluate_type_consistency

logger = logging.getLogger(__name__)

_DIAGNOSTIC_PAGE_RE = re.compile(r"(?m)^--- PAGE\s+(\d+)\s+---\s*$")
_DIAGNOSTIC_ANCHOR_RE = re.compile(
    r"\[\[EVIDENCE_ID:\s*([^\]]+)\]\]\s*(.*?)(?=\n\s*\[\[EVIDENCE_ID:|\Z)",
    flags=re.DOTALL,
)


class PipelineState(TypedDict, total=False):
    source_type: str
    source_title: str
    asset_identity: dict[str, Any]
    target_language: str
    text_with_pages: str
    model_name: str
    reasoning_effort: str | None
    extraction_role: str
    relation_first: bool
    diagnostic_call_options: dict[str, Any]
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
    resolution_completion_report: dict[str, Any]
    diagnostic_contract_report: dict[str, Any]
    llm_usage: list[dict[str, Any]]


def _get_client(timeout_seconds: int = 300):
    return get_client(timeout=Timeout(timeout_seconds, connect=10.0), max_retries=0)


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
        "This identity is operator-confirmed context owned by the system.",
        f"- asset_id: {asset_id}",
        f"- name: {asset_name}",
    ]
    for key in ("brand", "model", "asset_type"):
        value = str(identity.get(key, "") or "").strip()
        if value:
            lines.append(f"- {key}: {value}")
    lines.extend([
        "Rules:",
        "- Do not extract or emit an Asset node; the system injects it deterministically.",
        "- Do not emit HAS_COMPONENT or GENERATES_ERROR; the system derives those root relations.",
        "- Product, brand, and model mentions in the manual must not alter this identity.",
    ])
    return "\n".join(lines)


def _has_canonical_asset_identity(asset_identity: dict[str, Any] | None) -> bool:
    return is_workspace_canonical_asset_identity(asset_identity)


def _diagnostic_input_inventory(text_with_pages: str) -> dict[str, Any]:
    pages = [int(value) for value in _DIAGNOSTIC_PAGE_RE.findall(text_with_pages)]
    candidate_anchors = [
        match.group(1).strip()
        for match in _DIAGNOSTIC_ANCHOR_RE.finditer(text_with_pages)
        if evidence_has_diagnostic_candidate(match.group(2).strip())
    ]
    return {
        "input_pages": sorted(set(pages)),
        "candidate_input_anchors": sorted(set(candidate_anchors)),
    }


def _call_diagnostic_bundle_llm(state: PipelineState) -> PipelineState:
    """Extract typed records, validate evidence, then compile ontology claims."""
    from backend.domain.diagnostic_bundles import DiagnosticChunkOutput
    from backend.services.diagnostic_bundle_compiler import compile_diagnostic_bundles

    started = time.perf_counter()
    system_prompt = build_diagnostic_bundle_prompt(
        source_type=state["source_type"],
        source_title=state["source_title"],
    )
    call_options = dict(state.get("diagnostic_call_options") or {})
    max_output_tokens = int(call_options.get("max_output_tokens") or (
        get_ontology_config().get("diagnostic_bundle_max_output_tokens", 8000)
    ))
    cfg = _ontology_cfg(max_output_tokens)
    for key in (
        "timeout_seconds",
        "max_input_chars",
        "estimated_max_input_tokens",
    ):
        if int(call_options.get(key, 0) or 0) > 0:
            cfg[key] = int(call_options[key])
    operation = str(
        call_options.get("operation") or "diagnostic_bundle_extraction"
    ).strip()
    escalation_reason = str(call_options.get("escalation_reason") or "").strip()
    call_role = "escalation" if escalation_reason else "primary"
    input_inventory = _diagnostic_input_inventory(state["text_with_pages"])
    enforce_llm_limits(
        phase="Typed diagnostic bundle extraction",
        cfg=cfg,
        system_text=system_prompt,
        user_text=state["text_with_pages"],
    )
    client = _get_client(cfg["timeout_seconds"])
    model_name = state["model_name"] or settings.MODEL_NAME
    try:
        response = client.chat.completions.parse(
            model=model_name,
            **chat_reasoning_kwargs(model_name, state.get("reasoning_effort")),
            **chat_temperature_kwargs(model_name, 0.0),
            max_completion_tokens=cfg["max_output_tokens"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state["text_with_pages"]},
            ],
            response_format=DiagnosticChunkOutput,
        )
    except Exception as exc:
        logger.warning("[ontology] Typed diagnostic response failed closed: %s", exc)
        completion = getattr(exc, "completion", None)
        usage_entries: list[dict[str, Any]] = []
        if completion is not None:
            failed_usage = usage_from_response(completion, operation)
            failed_usage.update({
                "reasoning_effort": state.get("reasoning_effort") or "default",
                "call_role": call_role,
                "escalation_reason": escalation_reason,
            })
            usage_entries.append(failed_usage)
        error_text = str(exc).casefold()
        finish_reason = (
            "length"
            if "length limit" in error_text or "finish_reason='length'" in error_text
            else "error"
        )
        report = {
            **input_inventory,
            "schema_version": "1.0",
            "provider_model": model_name,
            "provider_reasoning_effort": state.get("reasoning_effort") or "default",
            "call_role": call_role,
            "escalation_reason": escalation_reason,
            "provider_response_id": "",
            "finish_reason": finish_reason,
            "parsed": False,
            "refusal": False,
            "raw_sha256": "",
            "records": [],
            "candidate_count": 0,
            "publish_count": 0,
            "unresolved_count": 1,
            "drop_reasons": {"structured_response_error": 1},
            "error_type": type(exc).__name__,
            "escalation_recommended": True,
        }
        result = {
            "ontology": _empty_instance(
                state["schema"], state["source_type"], state["source_title"],
            ),
            "diagnostic_contract_report": report,
        }
        if usage_entries:
            result["llm_usage"] = [*state.get("llm_usage", []), *usage_entries]
        return result

    choice = response.choices[0]
    message = choice.message
    usage = usage_from_response(response, operation)
    usage.update({
        "reasoning_effort": state.get("reasoning_effort") or "default",
        "call_role": call_role,
        "escalation_reason": escalation_reason,
    })
    raw = str(message.content or "")
    parsed = getattr(message, "parsed", None)
    refusal = str(getattr(message, "refusal", "") or "").strip()
    finish_reason = str(getattr(choice, "finish_reason", "") or "")
    if parsed is None or refusal:
        report = {
            **input_inventory,
            "schema_version": "1.0",
            "provider_model": getattr(response, "model", model_name) or model_name,
            "provider_reasoning_effort": state.get("reasoning_effort") or "default",
            "call_role": call_role,
            "escalation_reason": escalation_reason,
            "provider_response_id": str(getattr(response, "id", "") or ""),
            "finish_reason": finish_reason,
            "parsed": False,
            "refusal": bool(refusal),
            "refusal_text": refusal[:500],
            "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw else "",
            "records": [],
            "candidate_count": 0,
            "publish_count": 0,
            "unresolved_count": 1,
            "drop_reasons": {"provider_refusal_or_missing_parse": 1},
            "escalation_recommended": not bool(refusal),
        }
        return {
            "ontology": _empty_instance(
                state["schema"], state["source_type"], state["source_title"],
            ),
            "diagnostic_contract_report": report,
            "llm_usage": [*state.get("llm_usage", []), usage],
        }

    canonical_raw = raw or parsed.model_dump_json()
    provider_model = getattr(response, "model", model_name) or model_name
    try:
        compilation = compile_diagnostic_bundles(
            parsed,
            source_type=state["source_type"],
            source_title=state["source_title"],
            text_with_pages=state["text_with_pages"],
            schema=state["schema"],
            language=parsed.source_language,
        )
        ontology = _normalize_ontology_instance(
            ontology=compilation.ontology,
            schema=state["schema"],
            source_type=state["source_type"],
            source_title=state["source_title"],
            asset_identity=state.get("asset_identity"),
        )
    except Exception as exc:
        # A provider-valid payload can still fail the deterministic evidence
        # compiler or ontology normalization. Preserve the paid call in usage,
        # emit no claims, and expose a bounded Terra-recovery signal instead of
        # aborting the complete multi-chunk PDF run.
        candidate_count = len(parsed.records)
        logger.warning(
            "[ontology] Typed diagnostic compiler failed closed: %s",
            exc,
        )
        report = {
            **input_inventory,
            "schema_version": parsed.schema_version,
            "source_language": parsed.source_language,
            "provider_model": provider_model,
            "provider_reasoning_effort": state.get("reasoning_effort") or "default",
            "call_role": call_role,
            "escalation_reason": escalation_reason,
            "provider_response_id": str(getattr(response, "id", "") or ""),
            "finish_reason": finish_reason,
            "parsed": True,
            "refusal": False,
            "raw_sha256": hashlib.sha256(canonical_raw.encode("utf-8")).hexdigest(),
            "records": [],
            "candidate_count": candidate_count,
            "publish_count": 0,
            "unresolved_count": max(1, candidate_count),
            "drop_reasons": {
                "diagnostic_compiler_error": max(1, candidate_count),
            },
            "error_type": type(exc).__name__,
            "escalation_recommended": True,
        }
        return {
            "ontology": _empty_instance(
                state["schema"], state["source_type"], state["source_title"],
            ),
            "diagnostic_contract_report": report,
            "llm_usage": [*state.get("llm_usage", []), usage],
        }

    compilation_report = compilation.report.model_dump(mode="json")
    entries = compilation_report.get("entries", [])
    publish_count = int(
        compilation_report.get("disposition_counts", {}).get("publish", 0) or 0
    )
    unresolved_count = sum(
        int(compilation_report.get("disposition_counts", {}).get(key, 0) or 0)
        for key in ("gap", "review")
    )
    report = {
        **input_inventory,
        "schema_version": parsed.schema_version,
        "source_language": parsed.source_language,
        "provider_model": provider_model,
        "provider_reasoning_effort": state.get("reasoning_effort") or "default",
        "call_role": call_role,
        "escalation_reason": escalation_reason,
        "provider_response_id": str(getattr(response, "id", "") or ""),
        "finish_reason": finish_reason,
        "parsed": True,
        "refusal": False,
        "raw_sha256": hashlib.sha256(canonical_raw.encode("utf-8")).hexdigest(),
        "records": entries,
        "candidate_count": int(compilation_report.get("unique_candidates", 0) or 0),
        "duplicate_candidate_count": int(
            compilation_report.get("duplicate_candidates", 0) or 0
        ),
        "publish_count": publish_count,
        "unresolved_count": unresolved_count,
        "disposition_counts": compilation_report.get("disposition_counts", {}),
        "drop_reasons": compilation_report.get("dropped_items_by_reason", {}),
        "escalation_recommended": bool(
            finish_reason == "length"
            or unresolved_count
            or (not parsed.records)
            or (parsed.records and publish_count == 0)
        ),
    }
    logger.info(
        "[ontology] Typed diagnostic extraction: %d candidate(s), %d publishable, %d unresolved (%.1fs)",
        len(parsed.records),
        publish_count,
        unresolved_count,
        time.perf_counter() - started,
    )
    return {
        "ontology": ontology,
        "diagnostic_contract_report": report,
        "llm_usage": [*state.get("llm_usage", []), usage],
    }


def _call_extractor_llm(state: PipelineState) -> PipelineState:
    if state.get("relation_first") and state.get("extraction_role") == "diagnostic":
        return _call_diagnostic_bundle_llm(state)
    started = time.perf_counter()
    has_canonical_asset = _has_canonical_asset_identity(state.get("asset_identity"))
    prompt_blocks = [
        state.get("candidates_block", ""),
        _asset_identity_prompt_block(state.get("asset_identity")) if has_canonical_asset else "",
    ]
    system_prompt = build_ontology_extraction_prompt(
        schema_json=state["schema_json"],
        source_type=state["source_type"],
        source_title=state["source_title"],
        candidate_candidates_block="\n\n".join(block for block in prompt_blocks if block),
        extract_asset=not has_canonical_asset,
        extraction_role=state.get("extraction_role", "legacy"),
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
    if state.get("relation_first"):
        # Keep the spend envelope bounded to one call per role chunk. A
        # truncated candidate draft becomes an explicit gap, not a second
        # full-size completion.
        retry_tokens = cfg["max_output_tokens"]

    def _run_completion(max_output_tokens: int):
        try:
            model_name = state["model_name"] or settings.MODEL_NAME
            response = client.chat.completions.create(
                model=model_name,
                **chat_reasoning_kwargs(model_name, state.get("reasoning_effort")),
                **chat_temperature_kwargs(model_name, 0.0),
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
    if state.get("relation_first"):
        logger.info("[ontology] Relation pass skipped (relation-first extraction contract)")
        return {}
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
        model_name = state["model_name"] or settings.MODEL_NAME
        response = client.chat.completions.create(
            model=model_name,
            **chat_reasoning_kwargs(model_name, state.get("reasoning_effort")),
            **chat_temperature_kwargs(model_name, 0.0),
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
    # The prompt forbids creating nodes ("use only the node IDs listed"), so a
    # candidate whose endpoints do not exist is an invented id: enforce the
    # rule deterministically instead of letting it dangle into a blocking
    # relation_missing_source/target error.
    node_index = _collect_node_index(ontology, state["schema"])
    known_ids = {node_id for ids in node_index.values() for node_id in ids}
    dropped_unknown = [
        rel for rel in candidate_relations
        if rel["from_id"] not in known_ids or rel["to_id"] not in known_ids
    ]
    if dropped_unknown:
        logger.info(
            "[ontology] Relation pass dropped %d relation(s) referencing unknown node ids",
            len(dropped_unknown),
        )
        candidate_relations = [
            rel for rel in candidate_relations
            if rel["from_id"] in known_ids and rel["to_id"] in known_ids
        ]
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
        asset_identity=state.get("asset_identity"),
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
    if state.get("relation_first"):
        logger.info("[ontology] LLM semantic validation skipped (deterministic publication policy)")
        return {"semantic_issues": []}
    loop_cfg = get_reflective_loop_config()
    max_retries = int(loop_cfg.get("max_retries", 0))
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
        model_name = state["model_name"] or settings.MODEL_NAME
        response = client.chat.completions.create(
            model=model_name,
            **chat_reasoning_kwargs(model_name, state.get("reasoning_effort")),
            **chat_temperature_kwargs(model_name, 0.0),
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
    has_canonical_asset = _has_canonical_asset_identity(state.get("asset_identity"))
    prompt_blocks = [
        state.get("candidates_block", ""),
        _asset_identity_prompt_block(state.get("asset_identity")) if has_canonical_asset else "",
    ]
    system_prompt = build_ontology_re_extraction_prompt(
        schema_json=state["schema_json"],
        source_type=state["source_type"],
        source_title=state["source_title"],
        issues_summary=issues_summary,
        previous_ontology_json=previous_ontology_json,
        candidate_candidates_block="\n\n".join(block for block in prompt_blocks if block),
        extract_asset=not has_canonical_asset,
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
    logger.info("[ontology] Re-extraction attempt %d/%d", retry_count, get_reflective_loop_config().get("max_retries", 0))
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
            model_name = state["model_name"] or settings.MODEL_NAME
            response = client.chat.completions.create(
                model=model_name,
                **chat_reasoning_kwargs(model_name, state.get("reasoning_effort")),
                **chat_temperature_kwargs(model_name, 0.0),
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

    from backend.services.ontology_patch_service import apply_ontology_patch, is_ontology_patch

    if is_ontology_patch(data):
        # Patch path: the model only returns what the issues require; the
        # deterministic merge keeps everything else verbatim. Output size
        # scales with the issue list instead of the document, which removes
        # the truncation → keep-previous fallback observed on real manuals.
        data, patch_report = apply_ontology_patch(previous_ontology.model_dump(), data)
        logger.info("[ontology] Re-extraction returned a patch; applied: %s", patch_report)

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
    max_retries = int(loop_cfg.get("max_retries", 0))
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

    # Schema validation flows into graph reasoning, then confidence scoring.
    # Resolution completion now runs once at run level (after chunk merge) in
    # ontology_workflow, where it can see the full scoped text.
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
    reasoning_effort: str | None = None,
    asset_identity: dict[str, Any] | None = None,
    extraction_role: str = "legacy",
    relation_first: bool = False,
    on_event=None,
    diagnostic_call_options: dict[str, Any] | None = None,
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
        "reasoning_effort": reasoning_effort,
        "extraction_role": extraction_role,
        "relation_first": relation_first,
        "diagnostic_call_options": diagnostic_call_options or {},
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
        "diagnostic_contract_report": {},
        "resolution_completion_report": {},
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
    diagnostic_contract_report = result.get("diagnostic_contract_report", {})
    resolution_completion_report = result.get("resolution_completion_report", {})
    llm_usage = result.get("llm_usage", [])
    is_schema_compliant = not schema_issues and not human_fields
    blocking_schema_issues = [
        issue for issue in schema_issues
        if str(issue.severity).strip().lower() != "warning"
    ]

    if needs_human_review:
        status = "needs_human_review"
    elif blocking_schema_issues:
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
        is_ready_for_human_review=not blocking_schema_issues,
        retry_count=retry_count,
        graph_issues=graph_issues,
        suggested_relations=suggested_relations,
        confidence_report=confidence_report,
        diagnostic_contract_report=diagnostic_contract_report,
        resolution_completion_report=resolution_completion_report,
    )
    parse_repair_events = consume_parse_repair_events()
    llm_call_entries = []
    for raw_entry in llm_usage:
        entry = dict(raw_entry)
        entry.setdefault("reasoning_effort", reasoning_effort or "default")
        entry.setdefault("call_role", "primary")
        entry.setdefault("escalation_reason", "")
        llm_call_entries.append(entry)
    return response, {
        **aggregate_usage(llm_usage),
        "retry_count": retry_count,
        "parse_repair_events": parse_repair_events,
        "mining_summary": mining_result.to_summary(),
        "resolution_completion": resolution_completion_report,
        "diagnostic_contract": diagnostic_contract_report,
        "llm_call_entries": llm_call_entries,
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
    blocking_schema_issues = [
        issue for issue in schema_issues
        if str(issue.severity).strip().lower() != "warning"
    ]
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
        status="blocked" if blocking_schema_issues else ("needs_human" if human_fields else "ready"),
        ontology=updated,
        semantic_issues=[],
        schema_issues=schema_issues,
        human_required_fields=human_fields,
        is_schema_compliant=not schema_issues and not human_fields,
        is_ready_for_human_review=not blocking_schema_issues,
        confidence_report=confidence_report,
        resolution_completion_report={},
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


def normalize_ontology_instance(ontology: OntologyInstance) -> OntologyInstance:
    """Public deterministic normalization pass (ids, severity, material_context, inferred relations)."""
    schema = load_ontology_schema()
    return _normalize_ontology_instance(
        ontology=ontology,
        schema=schema,
        source_type=ontology.source_type,
        source_title=ontology.source_title,
    )
