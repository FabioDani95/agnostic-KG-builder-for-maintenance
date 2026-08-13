"""Reusable ontology-drafting workflow used by the multi-agent pipeline."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re as _re
import time
from copy import deepcopy

from fastapi import HTTPException

from backend.app_config import (
    get_coverage_completion_config,
    get_diagnostic_escalation_config,
    get_ontology_config,
    get_pdf_generation_cost_guard_config,
    get_resolution_completion_config,
)
from backend.models import OntologyDraftRequest, OntologyPipelineResponse, OntologyRelationInstance
from backend.services.cutplan_service import extract_asset_identity
from backend.services.ontology_pipeline import _normalize_ontology_instance, build_initial_ontology
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_semantics import WORKSPACE_CANONICAL_ASSET_MARKER, normalize_asset_node
from backend.services.pdf_service import format_text_with_pages
from backend.services.run_metrics import merge_usage_summaries, record_stage_metrics

logger = logging.getLogger(__name__)

_STATUS_RANK = {"blocked": 3, "needs_human_review": 2, "needs_human": 1, "ready": 0}
_DIAGNOSTIC_RECOVERY_CODES = {
    "ambiguous_source_anchor",
    "check_action_conflict",
    "declared_ambiguous",
    "diagnostic_compiler_error",
    "lineage_anchor_outside_bundle",
    "missing_actions",
    "missing_failure",
    "missing_indicator_failure_evidence",
    "missing_resolution_evidence",
    "provider_refusal_or_missing_parse",
    "quote_not_in_anchored_evidence",
    "record_window_missing_disposition",
    "resolved_anchor_outside_record_window",
    "source_anchor_outside_record_window",
    "source_page_mismatch",
    "structured_response_error",
    "unknown_source_anchor",
}


def _canonical_report_key(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _model_matches_family(actual: str, expected: str) -> bool:
    actual = str(actual or "").strip().lower()
    expected = str(expected or "").strip().lower()
    return bool(expected and (actual == expected or actual.startswith(f"{expected}-")))


def _diagnostic_escalation_reason(report: dict | None) -> str | None:
    """Return a bounded semantic-recovery reason, never a refusal retry."""
    report = report or {}
    if not report or bool(report.get("refusal")):
        return None
    if not bool(report.get("escalation_recommended")):
        return None
    if str(report.get("finish_reason") or "").strip().lower() in {"length", "incomplete"}:
        return "incomplete_output"
    if not bool(report.get("parsed")):
        return "structured_parse_failed"
    if int(report.get("candidate_count", 0) or 0) == 0:
        return "zero_diagnostic_candidates"
    recovery_codes = {
        str(code) for code, count in (report.get("drop_reasons") or {}).items()
        if int(count or 0) > 0
    }
    if int(report.get("unresolved_count", 0) or 0) > 0:
        if recovery_codes & _DIAGNOSTIC_RECOVERY_CODES:
            return "invalid_or_ambiguous_candidates"
        return None
    if int(report.get("publish_count", 0) or 0) == 0:
        return "zero_publishable_candidates"
    return "contract_recovery_recommended"


def _diagnostic_escalation_priority(report: dict | None) -> int:
    """Prioritize hard contract failures over merely low-yield chunks."""

    report = report or {}
    reason = _diagnostic_escalation_reason(report)
    if reason is None:
        return 0
    finish_reason = str(report.get("finish_reason") or "").strip().lower()
    if finish_reason in {"length", "incomplete"} or reason == "incomplete_output":
        return 500
    if not bool(report.get("parsed")) or reason == "structured_parse_failed":
        return 400
    if reason == "invalid_or_ambiguous_candidates":
        return 300
    if reason == "zero_publishable_candidates":
        return 200
    if reason == "zero_diagnostic_candidates":
        return 100
    return 50


def _diagnostic_report_score(report: dict | None) -> tuple[int, int, int, int, int]:
    report = report or {}
    dispositions = [
        str(record.get("disposition") or "")
        for record in (report.get("records") or [])
        if isinstance(record, dict)
    ]
    # For selective recovery, a grounded publish is best, a traceable gap is
    # safer than an unresolved review, and an exclusion never suppresses a
    # prior diagnostic observation merely by having zero unresolved records.
    disposition_rank = {"publish": 4, "gap": 3, "review": 2, "exclude": 1}
    return (
        max((disposition_rank.get(value, 0) for value in dispositions), default=0),
        int(report.get("publish_count", 0) or 0),
        int(bool(report.get("parsed"))),
        -int(report.get("unresolved_count", 0) or 0),
        int(report.get("candidate_count", 0) or 0),
    )


def _prefer_escalated_diagnostic_report(primary: dict, escalated: dict) -> bool:
    """Adopt Terra only when its compiled contract is strictly better."""
    return _diagnostic_report_score(escalated) > _diagnostic_report_score(primary)


def _published_branch_ids(report: dict | None) -> set[str]:
    return {
        str(record.get("branch_lineage_id") or "").strip()
        for record in ((report or {}).get("records") or [])
        if isinstance(record, dict)
        and str(record.get("disposition") or "") == "publish"
        and str(record.get("branch_lineage_id") or "").strip()
    }


def _diagnostic_report_summary(report: dict | None) -> dict:
    report = report or {}
    return {
        "provider_model": str(report.get("provider_model") or ""),
        "provider_reasoning_effort": str(
            report.get("provider_reasoning_effort") or "default"
        ),
        "provider_response_id": str(report.get("provider_response_id") or ""),
        "finish_reason": str(report.get("finish_reason") or ""),
        "parsed": bool(report.get("parsed")),
        "raw_sha256": str(report.get("raw_sha256") or ""),
        "candidate_count": int(report.get("candidate_count", 0) or 0),
        "publish_count": int(report.get("publish_count", 0) or 0),
        "unresolved_count": int(report.get("unresolved_count", 0) or 0),
        "drop_reasons": dict(report.get("drop_reasons") or {}),
    }


def _with_diagnostic_escalation_metadata(
    result: OntologyPipelineResponse,
    *,
    reason: str,
    attempted: bool,
    selected: str,
    primary_report: dict,
    escalated_report: dict | None = None,
    skip_reason: str = "",
) -> OntologyPipelineResponse:
    report = dict(result.diagnostic_contract_report or {})
    report["escalation"] = {
        "attempted": attempted,
        "reason": reason,
        "selected": selected,
        "skip_reason": skip_reason,
        "primary": _diagnostic_report_summary(primary_report),
        "escalated": _diagnostic_report_summary(escalated_report) if escalated_report else {},
    }
    # Full attempt payloads are immutable audit evidence.  The selected report
    # controls publication, while rejected/recovered candidates remain
    # inspectable rather than disappearing behind a digest.
    report["attempts"] = [
        {"role": "primary", "report": deepcopy(primary_report)},
        *(
            [{"role": "escalated", "report": deepcopy(escalated_report)}]
            if escalated_report
            else []
        ),
    ]
    return result.model_copy(update={"diagnostic_contract_report": report})


def _merge_escalated_chunk_metrics(primary: dict, escalated: dict) -> dict:
    merged = merge_usage_summaries([primary, escalated])
    merged.update({
        "retry_count": int(primary.get("retry_count", 0) or 0)
        + int(escalated.get("retry_count", 0) or 0),
        "parse_repair_events": [
            *(primary.get("parse_repair_events") or []),
            *(escalated.get("parse_repair_events") or []),
        ],
        "llm_call_entries": [
            *(primary.get("llm_call_entries") or []),
            *(escalated.get("llm_call_entries") or []),
        ],
    })
    for key in ("chunk_index", "chunk_pages", "section_count", "extraction_role"):
        if key in primary:
            merged[key] = primary[key]
    return merged


def _chunk_call_ledger_entries(metrics: dict, default_reasoning_effort: str) -> list[dict]:
    call_count = int(metrics.get("llm_calls", 0) or 0)
    if not call_count:
        return []
    call_entries = [
        dict(entry)
        for entry in (metrics.get("llm_call_entries") or [])
        if isinstance(entry, dict)
    ]
    if call_entries:
        return [{
            **entry,
            "reasoning_effort": str(
                entry.get("reasoning_effort") or default_reasoning_effort or "default"
            ),
            "call_role": str(entry.get("call_role") or "primary"),
            "escalation_reason": str(entry.get("escalation_reason") or ""),
            "extraction_role": str(metrics.get("extraction_role") or "legacy"),
            "chunk_index": int(metrics.get("chunk_index", 0) or 0),
            "aggregate_call_count": 1,
        } for entry in call_entries]

    models_for_chunk = list(metrics.get("models") or [])
    operations_for_chunk = list(metrics.get("operations") or [])
    return [{
        "operation": (
            operations_for_chunk[0]
            if len(operations_for_chunk) == 1
            else "ontology_chunk"
        ),
        "model": models_for_chunk[0] if len(models_for_chunk) == 1 else "",
        "prompt": int(metrics.get("prompt_tokens", 0) or 0),
        "cached_prompt": int(metrics.get("cached_prompt_tokens", 0) or 0),
        "cache_write_prompt": int(
            metrics.get("cache_write_prompt_tokens", 0) or 0
        ),
        "non_cached_prompt": int(metrics.get("non_cached_prompt_tokens", 0) or 0),
        "completion": int(metrics.get("completion_tokens", 0) or 0),
        "total": int(metrics.get("total_tokens", 0) or 0),
        "estimated_cost_usd": float(metrics.get("estimated_cost_usd", 0) or 0),
        "reasoning_effort": default_reasoning_effort or "default",
        "call_role": "primary",
        "escalation_reason": "",
        "extraction_role": str(metrics.get("extraction_role") or "legacy"),
        "chunk_index": int(metrics.get("chunk_index", 0) or 0),
        "aggregate_call_count": call_count,
    }]


def _normalize_node_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse spaces for fuzzy dedup."""
    value = str(name or "").lower().strip()
    value = _re.sub(r"[^\w\s]", " ", value)
    return _re.sub(r"\s+", " ", value).strip()


def _canonical_asset_identity(store: dict) -> dict[str, object]:
    graph_state = store.get("graph_state") or {}
    source_type = str(store.get("source_type") or graph_state.get("source_type") or "").strip()
    source_title = str(store.get("source_title") or graph_state.get("source_title") or "").strip()
    filename = str(store.get("filename") or graph_state.get("filename") or "").strip()

    for candidate in (
        store.get("asset_identity"),
        (store.get("cut_plan") or {}).get("product_info"),
        ((graph_state.get("scoping_metadata") or {}).get("product_info")),
    ):
        if isinstance(candidate, dict) and candidate:
            identity = extract_asset_identity(
                candidate,
                fallback_name=source_title,
                source_type=source_type,
                filename=filename,
            )
            if identity.get("name"):
                if store.get("asset_identity_is_canonical") is True:
                    identity[WORKSPACE_CANONICAL_ASSET_MARKER] = True
                    description = str(candidate.get("description", "") or "").strip()
                    if description:
                        identity["description"] = description
                return identity

    if source_title or filename:
        return extract_asset_identity(
            {},
            fallback_name=source_title,
            source_type=source_type,
            filename=filename,
        )
    return {}


def _diagnostic_record_windows(store: dict) -> list[dict]:
    """Validate advisory pre-LLM record windows for audit telemetry only."""

    rendered: list[dict] = []
    for raw in store.get("diagnostic_record_windows", []) or []:
        if not isinstance(raw, dict):
            continue
        window_id = str(raw.get("window_id") or "").strip()
        record_anchor = str(raw.get("record_anchor") or "").strip()
        text = str(raw.get("text_with_pages") or "").strip()
        anchors = sorted({
            str(value).strip()
            for value in (raw.get("allowed_source_anchors") or [])
            if str(value).strip()
        })
        pages = sorted({
            int(value)
            for value in (raw.get("page_numbers") or [])
            if int(value) > 0
        })
        if not (window_id and record_anchor and text and anchors and pages):
            continue
        rendered.append({
            **raw,
            "window_id": window_id,
            "record_anchor": record_anchor,
            "allowed_source_anchors": anchors,
            "page_numbers": pages,
            "text_with_pages": text,
        })
    return sorted(rendered, key=lambda item: item["window_id"])


def _diagnostic_evidence_for_pages(
    evidence_units: list,
    pages: list[dict],
) -> list:
    """Limit compiler evidence to the exact physical pages shown to the model."""

    allowed_pages = {int(page["page_number"]) for page in pages}
    return [
        unit
        for unit in evidence_units
        if int(getattr(getattr(unit, "locator", None), "page", 0) or 0)
        in allowed_pages
    ]


def _render_diagnostic_windows(windows: list[dict]) -> str:
    parts: list[str] = []
    for window in windows:
        metadata = {
            "window_id": window["window_id"],
            "record_anchor": window["record_anchor"],
            "allowed_source_anchors": window["allowed_source_anchors"],
            "page_numbers": window["page_numbers"],
        }
        parts.extend([
            "=== RECORD_WINDOW " + window["window_id"] + " ===",
            "SYSTEM_WINDOW_METADATA: "
            + json.dumps(metadata, sort_keys=True, ensure_ascii=False),
            window["text_with_pages"],
        ])
    return "\n\n".join(parts)


def _diagnostic_output_token_limit(windows: list[dict], ontology_cfg: dict) -> int:
    default = int(ontology_cfg.get("diagnostic_bundle_max_output_tokens", 8000))
    if windows and all(
        window.get("window_kind") == "table_row"
        and window.get("structure_status") == "atomic"
        for window in windows
    ):
        return min(
            default,
            int(ontology_cfg.get("diagnostic_atomic_table_max_output_tokens", 3000)),
        )
    return default


def _merge_pipeline_results(
    results: list[OntologyPipelineResponse],
    *,
    asset_identity: dict[str, str] | None = None,
) -> OntologyPipelineResponse:
    """Merge chunk-level ontology results into one normalized run-level payload."""
    if len(results) == 1:
        return results[0]

    # IDs can legally be equal strings only in malformed legacy model output.
    # Keep remaps type-keyed so such a collision cannot corrupt relation
    # endpoints before strict validation reports it.
    id_remap: dict[tuple[str, str], str] = {}
    merged_nodes: dict[str, list[dict]] = {}
    name_to_id: dict[str, dict[str, str]] = {}

    def _node_id(node: dict, node_type: str) -> str:
        id_field = {
            "Asset": "asset_id",
            "Component": "component_id",
            "Symptom": "symptom_id",
            "FailureMode": "failure_mode_id",
            "CorrectiveAction": "action_id",
            "ErrorCode": "error_code_id",
        }.get(node_type, "id")
        return str(node.get(id_field, node.get("id", ""))).strip()

    def _with_node_id(node: dict, node_type: str, node_id: str) -> dict:
        """Copy a richer duplicate while preserving the canonical identifier."""
        id_field = {
            "Asset": "asset_id",
            "Component": "component_id",
            "Symptom": "symptom_id",
            "FailureMode": "failure_mode_id",
            "CorrectiveAction": "action_id",
            "ErrorCode": "error_code_id",
        }.get(node_type, "id")
        canonical = dict(node)
        canonical[id_field] = node_id
        return canonical

    def _node_name(node: dict) -> str:
        return str(node.get("name", node.get("title", ""))).strip()

    def _node_richness(node: dict) -> int:
        return sum(1 for value in node.values() if value not in ("", [], {}, None))

    def _fill_missing_fields(primary: dict, secondary: dict) -> dict:
        """Keep `primary` but fill its empty fields from `secondary`.

        Duplicate nodes across chunks often carry complementary detail (one has
        the description, the other the category): a plain "richer wins" replace
        silently drops the loser's fields.
        """
        filled = dict(primary)
        for key, value in secondary.items():
            if filled.get(key) in ("", [], {}, None) and value not in ("", [], {}, None):
                filled[key] = value
        return filled

    for result in results:
        typed_diagnostic = bool(
            (result.diagnostic_contract_report or {}).get("schema_version")
        )
        for node_type, node_list in result.ontology.nodes.items():
            if node_type not in merged_nodes:
                merged_nodes[node_type] = []
                name_to_id[node_type] = {}

            for node in node_list:
                original_node_id = _node_id(node, node_type)
                if node_type == "Asset":
                    node = normalize_asset_node(
                        node,
                        source_title=result.ontology.source_title,
                        source_type=result.ontology.source_type,
                        asset_identity=asset_identity,
                    )
                node_id = _node_id(node, node_type)
                node_name = _normalize_node_name(_node_name(node))
                if not node_id:
                    continue
                if original_node_id and original_node_id != node_id:
                    id_remap[(node_type, original_node_id)] = node_id

                existing_by_id = next(
                    (
                        existing for existing in merged_nodes[node_type]
                        if _node_id(existing, node_type) == node_id
                    ),
                    None,
                )
                if existing_by_id is not None:
                    if _node_richness(node) > _node_richness(existing_by_id):
                        primary, secondary = node, existing_by_id
                    else:
                        primary, secondary = existing_by_id, node
                    index = merged_nodes[node_type].index(existing_by_id)
                    merged_nodes[node_type][index] = _fill_missing_fields(primary, secondary)
                    continue

                # A normalized label is not a record identity. Typed bundles
                # keep branch-local IDs until the conservative global
                # canonicalizer can compare context and neighbourhood.
                if (
                    not typed_diagnostic
                    and node_name
                    and node_name in name_to_id[node_type]
                ):
                    canonical_id = name_to_id[node_type][node_name]
                    if node_id != canonical_id:
                        id_remap[(node_type, node_id)] = canonical_id
                        existing_by_name = next(
                            (
                                existing for existing in merged_nodes[node_type]
                                if _node_id(existing, node_type) == canonical_id
                            ),
                            None,
                        )
                        if existing_by_name is not None:
                            candidate = _with_node_id(node, node_type, canonical_id)
                            if _node_richness(candidate) > _node_richness(existing_by_name):
                                primary, secondary = candidate, existing_by_name
                            else:
                                primary, secondary = existing_by_name, candidate
                            index = merged_nodes[node_type].index(existing_by_name)
                            merged_nodes[node_type][index] = _fill_missing_fields(primary, secondary)
                    continue

                merged_nodes[node_type].append(node)
                if node_name and not typed_diagnostic:
                    name_to_id[node_type][node_name] = node_id

    # Duplicate relations across chunks corroborate each other: union their
    # evidence instead of keeping only the first occurrence, so the confidence
    # corroboration signal sees every cited page.
    merged_relations_by_key: dict[tuple, OntologyRelationInstance] = {}
    for result in results:
        for relation in result.ontology.relations:
            from_id = id_remap.get(
                (relation.from_type, relation.from_id), relation.from_id,
            )
            to_id = id_remap.get(
                (relation.to_type, relation.to_id), relation.to_id,
            )
            key = (
                relation.name,
                from_id,
                to_id,
                str(getattr(relation, "branch_lineage_id", "") or ""),
            )
            existing = merged_relations_by_key.get(key)
            if existing is None:
                merged_relations_by_key[key] = OntologyRelationInstance(
                    name=relation.name,
                    from_type=relation.from_type,
                    from_id=from_id,
                    to_type=relation.to_type,
                    to_id=to_id,
                    evidence=list(relation.evidence or []),
                    branch_lineage_id=str(
                        getattr(relation, "branch_lineage_id", "") or ""
                    ),
                )
                continue
            seen_evidence = {
                (ev.source_page, ev.quote, ev.source_anchor) for ev in existing.evidence or []
            }
            for evidence_item in relation.evidence or []:
                signature = (
                    evidence_item.source_page,
                    evidence_item.quote,
                    evidence_item.source_anchor,
                )
                if signature in seen_evidence:
                    continue
                existing.evidence.append(evidence_item)
                seen_evidence.add(signature)
    merged_relations = list(merged_relations_by_key.values())

    merged_ontology = deepcopy(results[0].ontology)
    merged_ontology.nodes = merged_nodes
    merged_ontology.relations = merged_relations
    merged_schema = load_ontology_schema()
    merged_ontology = _normalize_ontology_instance(
        ontology=merged_ontology,
        schema=merged_schema,
        source_type=merged_ontology.source_type,
        source_title=merged_ontology.source_title,
        asset_identity=asset_identity,
    )

    def _dedup_issues(issues):
        seen = set()
        deduped = []
        for issue in issues:
            key = (getattr(issue, "message", str(issue)), getattr(issue, "severity", ""))
            if key in seen:
                continue
            deduped.append(issue)
            seen.add(key)
        return deduped

    all_semantic = _dedup_issues([issue for result in results for issue in result.semantic_issues])
    typed_accounted_evidence: set[str] = set()
    for result in results:
        report = dict(result.diagnostic_contract_report or {})
        window_anchors = {
            str(window.get("window_id") or ""): {
                str(anchor)
                for anchor in (window.get("allowed_source_anchors") or [])
                if str(anchor)
            }
            for window in (report.get("record_window_inventory") or [])
            if isinstance(window, dict) and str(window.get("window_id") or "")
        }
        for record in report.get("records", []) or []:
            if not isinstance(record, dict):
                continue
            if str(record.get("disposition") or "") not in {
                "publish", "gap", "review", "exclude",
            }:
                continue
            typed_accounted_evidence.update(
                str(evidence_id)
                for evidence_id in (record.get("evidence_ids") or [])
                if str(evidence_id)
            )
            typed_accounted_evidence.update(
                window_anchors.get(str(record.get("record_window_id") or ""), set())
            )

    def keep_schema_issue(result: OntologyPipelineResponse, issue) -> bool:
        if issue.code != "empty_draft_content":
            return True
        report = dict(result.diagnostic_contract_report or {})
        if not report.get("schema_version"):
            return False
        candidate_anchors = {
            str(anchor)
            for anchor in (report.get("candidate_input_anchors") or [])
            if str(anchor)
        }
        # An overlapped chunk may be partial or empty while a sibling chunk
        # sees and publishes the full record. Keep the blocking issue only for
        # candidate evidence that remains unaccounted across the entire run.
        return bool(candidate_anchors - typed_accounted_evidence)

    # empty_draft_content is a per-chunk diagnostic; when merging multiple chunks it is
    # expected that some chunks (e.g. a cover-page-only chunk) produce no diagnostic nodes.
    # Filter it out here so the final merge status reflects the consolidated ontology.
    all_schema = _dedup_issues([
        issue
        for result in results
        for issue in result.schema_issues
        if keep_schema_issue(result, issue)
    ])
    all_graph = [issue for result in results for issue in result.graph_issues]
    all_suggested = [item for result in results for item in result.suggested_relations]

    human_required_fields = {}
    for result in results:
        for field in result.human_required_fields:
            human_required_fields[field.field_key] = field

    # Derive merged status from the filtered schema/semantic issues, not the per-chunk statuses.
    # Per-chunk statuses can include "blocked" due to empty_draft_content (now filtered) which
    # would otherwise propagate to the merged result even though the combined ontology is valid.
    merged_human_required = list(human_required_fields.values())
    blocking_schema = [
        issue for issue in all_schema
        if str(getattr(issue, "severity", "")).strip().lower() != "warning"
    ]
    if blocking_schema:
        worst_status = "blocked"
    elif any(result.status == "needs_human_review" for result in results):
        worst_status = "needs_human_review"
    elif merged_human_required:
        worst_status = "needs_human"
    else:
        worst_status = "ready"
    retry_total = sum(result.retry_count for result in results)

    # Re-score confidence on the merged ontology so the report reflects the final
    # deduped structure and carries chain_participation signals that depend on
    # relations merged across chunks. Falls back to None when scoring is disabled.
    merged_confidence_report = None
    try:
        from backend.app_config import get_confidence_config
        from backend.services.confidence import score_ontology

        confidence_cfg = get_confidence_config()
        if confidence_cfg.get("enabled", True):
            merged_confidence_report = score_ontology(
                ontology=merged_ontology,
                schema=merged_schema,
                semantic_issues=all_semantic,
                schema_issues=all_schema,
                human_required_fields=merged_human_required,
                retry_count=retry_total,
                config=confidence_cfg,
            )
    except Exception:
        logger.exception("[ontology] Confidence re-scoring after merge failed; leaving report unset")

    diagnostic_reports = [
        dict(result.diagnostic_contract_report)
        for result in results
        if result.diagnostic_contract_report
    ]
    diagnostic_records: dict[str, dict] = {}
    diagnostic_candidate_input_anchors: set[str] = set()
    diagnostic_input_pages: set[int] = set()
    # Chunk reports can overlap. Count reasons attached to the final selected
    # record disposition once, while retaining provider/compiler reasons that
    # are not attributable to any record.
    unattributed_drop_reasons: dict[str, int] = {}
    for report in diagnostic_reports:
        diagnostic_candidate_input_anchors.update(
            str(anchor)
            for anchor in (report.get("candidate_input_anchors") or [])
            if str(anchor)
        )
        diagnostic_input_pages.update(
            int(page)
            for page in (report.get("input_pages") or [])
            if int(page) > 0
        )
        report_records = report.get("records", []) or report.get("dispositions", [])
        attributed_counts: dict[str, int] = {}
        for record in report_records:
            if not isinstance(record, dict):
                continue
            for reason in record.get("drop_reasons", []) or []:
                if not isinstance(reason, dict):
                    continue
                code = str(reason.get("code") or "").strip()
                if code:
                    attributed_counts[code] = attributed_counts.get(code, 0) + 1
        for code, count in (report.get("drop_reasons") or {}).items():
            normalized_code = str(code)
            residual = max(0, int(count or 0) - attributed_counts.get(normalized_code, 0))
            if residual:
                unattributed_drop_reasons[normalized_code] = (
                    unattributed_drop_reasons.get(normalized_code, 0) + residual
                )
        for record in report_records:
            if not isinstance(record, dict):
                continue
            key = str(
                record.get("branch_lineage_id")
                or record.get("record_lineage_id")
                or record.get("candidate_id")
                or _canonical_report_key(record)
            )
            current = diagnostic_records.get(key)
            disposition_rank = {"publish": 4, "exclude": 3, "gap": 2, "review": 1}
            if current is None or disposition_rank.get(
                str(record.get("disposition") or ""), 0
            ) > disposition_rank.get(str(current.get("disposition") or ""), 0):
                diagnostic_records[key] = record
    merged_diagnostic_report = {}
    if diagnostic_reports:
        merged_drop_reasons = dict(unattributed_drop_reasons)
        for record in diagnostic_records.values():
            for reason in record.get("drop_reasons", []) or []:
                if not isinstance(reason, dict):
                    continue
                code = str(reason.get("code") or "").strip()
                if code:
                    merged_drop_reasons[code] = merged_drop_reasons.get(code, 0) + 1
        contract_failure_count = sum(
            not bool(report.get("parsed", True))
            or bool(report.get("refusal", False))
            or str(report.get("finish_reason") or "stop").strip().lower()
            not in {"", "stop"}
            for report in diagnostic_reports
        )
        unaccounted_input_anchors = sorted(
            diagnostic_candidate_input_anchors - typed_accounted_evidence
        )
        unresolved_record_count = sum(
            str(record.get("disposition")) in {"gap", "review"}
            for record in diagnostic_records.values()
        )
        merged_diagnostic_report = {
            "schema_version": next(
                (
                    str(report.get("schema_version"))
                    for report in diagnostic_reports
                    if report.get("schema_version")
                ),
                "diagnostic-bundle-v1",
            ),
            "chunks": diagnostic_reports,
            "input_pages": sorted(diagnostic_input_pages),
            "candidate_input_anchors": sorted(diagnostic_candidate_input_anchors),
            "unaccounted_input_anchors": unaccounted_input_anchors,
            "records": [diagnostic_records[key] for key in sorted(diagnostic_records)],
            "candidate_count": len(diagnostic_records),
            "publish_count": sum(
                str(record.get("disposition")) == "publish"
                for record in diagnostic_records.values()
            ),
            "unresolved_count": unresolved_record_count,
            "contract_failure_count": contract_failure_count,
            # A provider refusal, parse failure or truncated chunk cannot be
            # erased merely because another (possibly overlapping) chunk
            # accounted for the anchors it happened to expose.
            "parsed": not unaccounted_input_anchors and not contract_failure_count,
            "refusal": any(bool(report.get("refusal")) for report in diagnostic_reports),
            "finish_reason": (
                "stop"
                if not unaccounted_input_anchors and not contract_failure_count
                else "incomplete"
            ),
            "drop_reasons": dict(sorted(merged_drop_reasons.items())),
            "escalation_recommended": bool(
                unaccounted_input_anchors
                or contract_failure_count
                or any(
                    bool(report.get("escalation_recommended"))
                    for report in diagnostic_reports
                )
            ),
        }

    contract_blocked = bool(
        merged_diagnostic_report
        and (
            not merged_diagnostic_report.get("parsed", True)
            or merged_diagnostic_report.get("refusal", False)
            or str(merged_diagnostic_report.get("finish_reason") or "stop")
            not in {"", "stop"}
        )
    )
    if contract_blocked:
        worst_status = "blocked"
    elif (
        merged_diagnostic_report
        and int(merged_diagnostic_report.get("unresolved_count", 0) or 0) > 0
        and _STATUS_RANK.get(worst_status, 0) < _STATUS_RANK["needs_human_review"]
    ):
        worst_status = "needs_human_review"

    return OntologyPipelineResponse(
        status=worst_status,
        ontology=merged_ontology,
        semantic_issues=all_semantic,
        schema_issues=all_schema,
        human_required_fields=merged_human_required,
        is_schema_compliant=(
            not all_schema and not merged_human_required and not contract_blocked
        ),
        is_ready_for_human_review=not blocking_schema and not contract_blocked,
        retry_count=retry_total,
        graph_issues=all_graph,
        suggested_relations=all_suggested,
        confidence_report=merged_confidence_report,
        diagnostic_contract_report=merged_diagnostic_report,
    )


def _split_pages_by_section(
    pages: list[dict],
    sections: list[dict],
    max_chars: int,
    max_pages: int = 30,
    overlap_pages: int = 0,
) -> list[tuple[list[dict], list[dict]]]:
    """Pack selected pages and optionally overlap contiguous chunk boundaries.

    A change in nested section signature is context, not a chunk boundary.  The
    former behaviour fragmented 30 pages into 19 calls; packing only on page or
    character limits preserves every page while making cost independent of ToC
    granularity.
    """
    if not pages:
        return []
    max_pages = max(1, int(max_pages or 1))
    max_chars = max(1, int(max_chars or 1))
    overlap_pages = max(0, int(overlap_pages or 0))
    page_map = {int(page["page_number"]): page for page in pages}
    ordered_pages = [page_map[number] for number in sorted(page_map)]

    chunks: list[tuple[list[dict], list[dict]]] = []
    chunk_pages: list[dict] = []
    chunk_chars = 0

    def context_for(items: list[dict]) -> list[dict]:
        page_numbers = {int(page["page_number"]) for page in items}
        context = []
        seen = set()
        for section in sections or []:
            start = int(section.get("start", 0) or 0)
            end = int(section.get("end", 0) or 0)
            if not any(start <= page_number <= end for page_number in page_numbers):
                continue
            signature = (
                str(section.get("name") or ""), start, end, str(section.get("source") or ""),
            )
            if signature in seen:
                continue
            seen.add(signature)
            context.append({
                "name": signature[0], "start": start, "end": end, "source": signature[3],
            })
        return sorted(context, key=lambda value: (value["start"], value["end"], value["name"]))

    def flush() -> None:
        nonlocal chunk_pages, chunk_chars
        if not chunk_pages:
            return
        chunks.append((chunk_pages, context_for(chunk_pages)))
        chunk_pages = []
        chunk_chars = 0

    for page in ordered_pages:
        page_chars = len(f"--- PAGE {page['page_number']} ---\n{page['text']}\n\n")
        contiguous = (
            not chunk_pages
            or int(page["page_number"]) == int(chunk_pages[-1]["page_number"]) + 1
        )
        if chunk_pages and (
            not contiguous
            or len(chunk_pages) >= max_pages
            or chunk_chars + page_chars > max_chars
        ):
            flush()
        chunk_pages.append(page)
        chunk_chars += page_chars
    flush()

    # Diagnostic records frequently put the symptom/cause at the bottom of a
    # page and the remedy on the next one.  A small physical-page overlap lets
    # one typed extraction call see both halves.  It is applied only across a
    # contiguous boundary; gaps created by scoping never get bridged.
    if overlap_pages and len(chunks) > 1:
        overlapped = [chunks[0]]
        for current_pages, _current_context in chunks[1:]:
            previous_pages = overlapped[-1][0]
            if (
                previous_pages
                and current_pages
                and int(previous_pages[-1]["page_number"]) + 1
                == int(current_pages[0]["page_number"])
            ):
                carry = previous_pages[-overlap_pages:]
                existing = {int(page["page_number"]) for page in current_pages}
                current_pages = [
                    *[page for page in carry if int(page["page_number"]) not in existing],
                    *current_pages,
                ]
            overlapped.append((current_pages, context_for(current_pages)))
        chunks = overlapped

    return chunks


def _build_section_header(sections: list[dict]) -> str:
    """Build a section context header from stored cut-plan sections."""
    if not sections:
        return ""
    lines = [
        "## DOCUMENT CONTEXT",
        "These pages come from the following manual sections:",
    ]
    for section in sections:
        lines.append(
            f"- {section['name']} (pp. {section['start']}-{section['end']}, "
            f"source: {section.get('source', '?')})",
        )
    lines.append("")
    lines.append(
        "Use this context to better interpret the content. Extract all "
        "ontology-relevant information from these sections, including components, "
        "error codes, symptoms, failure modes, and corrective actions.",
    )
    return "\n".join(lines)


def _is_transient_chunk_error(exc: Exception) -> bool:
    """Recognize transport/capacity failures that are safe to retry per chunk."""
    message = str(exc).casefold()
    transient_markers = (
        "connection error",
        "api connection",
        "timed out",
        "timeout",
        "rate limit",
        "temporarily unavailable",
        "server error",
        "status code: 429",
        "status code: 500",
        "status code: 502",
        "status code: 503",
        "status code: 504",
    )
    return any(marker in message for marker in transient_markers)


async def _run_chunk_with_retry(
    operation,
    *,
    attempts: int,
    base_delay_seconds: float,
):
    """Retry only the failed chunk; completed sibling chunks stay in memory."""
    total_attempts = max(1, int(attempts))
    for attempt in range(1, total_attempts + 1):
        try:
            return await asyncio.to_thread(operation)
        except Exception as exc:
            if attempt >= total_attempts or not _is_transient_chunk_error(exc):
                raise
            delay = max(0.0, float(base_delay_seconds)) * (2 ** (attempt - 1))
            logger.warning(
                "[ontology] Transient chunk failure; retrying attempt %d/%d in %.1fs: %s",
                attempt + 1,
                total_attempts,
                delay,
                exc,
            )
            if delay:
                await asyncio.sleep(delay)


def _finalize_run_level_quality(
    result: OntologyPipelineResponse,
    pages: list[dict],
    model_name: str | None,
    asset_identity: dict[str, str] | None,
    all_pages: list[dict] | None = None,
    *,
    reasoning_effort: str | None = None,
    relation_first: bool = False,
) -> tuple[OntologyPipelineResponse, list[dict], dict, dict]:
    """Run-level quality passes executed once on the merged ontology.

    1. Resolution completion: targeted retrieval for FailureModes without a
       CorrectiveAction and ErrorCodes without INDICATES, over the FULL scoped
       text (per-chunk runs could not see solutions living in other chunks).
    2. Graph closure: auto-apply grounded association relations (MAY_INDICATE,
       AFFECTS) the graph reasoner only suggested, so connected gaps the system
       can verify don't reach the operator.
    3. Evidence grounding: verify every relation evidence quote against the
       cited page; ungrounded relations push their nodes into the human-review
       confidence band.

    Returns (updated_result, llm_usage_entries, resolution_report, quality_stats).
    """
    from backend.app_config import get_confidence_config
    from backend.config import settings
    from backend.services.confidence import score_ontology
    from backend.services.evidence_grounding_service import ground_relation_evidence
    from backend.services.graph_closure_service import close_grounded_gaps
    from backend.services.graph_reasoning import run_graph_analysis
    from backend.services.ontology_canonicalization_service import canonicalize_ontology_instance
    from backend.services.ontology_pipeline import _extract_json_object, _validate_schema
    from backend.services.resolution_completion_service import complete_resolution_gaps

    schema = load_ontology_schema()
    ontology = result.ontology
    usage_entries: list[dict] = []

    text_with_pages = format_text_with_pages(pages)
    # Full-manual corpus for resolution completion's retrieval: a remedy often
    # lives on a maintenance/reference page the cut plan dropped. Falls back to
    # the kept pages when the caller has no wider set.
    search_text_with_pages = (
        format_text_with_pages(all_pages) if all_pages else text_with_pages
    )

    # Coverage completion FIRST: second harvest of diagnostic branches the draft
    # missed (branch coverage is nondeterministic run-to-run). Best-effort,
    # strictly additive. It runs before resolution completion so that chains it
    # adds without a corrective action become resolution targets in the same
    # run instead of surviving as unresolved gaps.
    from backend.services.coverage_completion_service import complete_coverage_gaps

    if relation_first:
        coverage_report = {
            "returned": 0,
            "applied": 0,
            "skipped": "typed_diagnostic_contract_owns_coverage",
        }
    else:
        try:
            ontology, coverage_usage, coverage_report = complete_coverage_gaps(
                ontology=ontology,
                text_with_pages=text_with_pages,
                model_name=model_name or settings.MODEL_NAME,
                parse_json=_extract_json_object,
                reasoning_effort=reasoning_effort,
            )
            usage_entries = [*usage_entries, *coverage_usage]
        except Exception:
            logger.exception("[ontology] Coverage completion failed; keeping ontology unchanged")
            coverage_report = {"returned": 0, "applied": 0, "error": "coverage_completion_failed"}
    if coverage_report.get("applied"):
        ontology = _normalize_ontology_instance(
            ontology=ontology,
            schema=schema,
            source_type=ontology.source_type,
            source_title=ontology.source_title,
            asset_identity=asset_identity,
        )

    if relation_first:
        resolution_report = {
            "attempted": 0,
            "completed": 0,
            "skipped": "typed_diagnostic_contract_requires_per_edge_evidence",
        }
    else:
        try:
            ontology, resolution_usage, resolution_report = complete_resolution_gaps(
                ontology=ontology,
                text_with_pages=text_with_pages,
                model_name=model_name or settings.MODEL_NAME,
                parse_json=_extract_json_object,
                search_text_with_pages=search_text_with_pages,
                reasoning_effort=reasoning_effort,
                require_observed_indicator=False,
            )
            usage_entries = [*usage_entries, *resolution_usage]
        except Exception:
            # Resolution completion is best-effort: never abort the draft for it.
            logger.exception("[ontology] Run-level resolution completion failed; keeping ontology unchanged")
            resolution_report = {"attempted": 0, "completed": 0, "error": "resolution_completion_failed"}
    resolution_changed = bool(resolution_report.get("completed", 0))
    if resolution_changed:
        ontology = _normalize_ontology_instance(
            ontology=ontology,
            schema=schema,
            source_type=ontology.source_type,
            source_title=ontology.source_title,
            asset_identity=asset_identity,
        )
        logger.info(
            "[ontology] Run-level resolution completion: %d/%d target(s) completed",
            int(resolution_report.get("completed", 0) or 0),
            int(resolution_report.get("attempted", 0) or 0),
        )

    # One global pass after every additive completion step handles duplicates
    # across chunk boundaries.  Only deterministic identity equivalents merge;
    # uncertain semantic neighbours remain distinct and enter the review report.
    ontology, canonicalization_report = canonicalize_ontology_instance(ontology)

    page_text_by_page = {
        int(page["page_number"]): str(page.get("text", "") or "")
        for page in pages
    }

    # Graph closure: auto-apply grounded association relations that the reasoner
    # only suggested. Anything not grounded stays in suggested_relations for the
    # operator.
    _, pre_suggestions = run_graph_analysis(ontology, schema)
    closure_stats: dict = {"considered": 0, "applied": 0}
    if relation_first:
        # Similarity suggestions are useful as diagnostics but not as claims and
        # would recreate the oversized legacy review queue.
        remaining_suggestions = []
        closure_stats = {
            "considered": len(pre_suggestions),
            "applied": 0,
            "skipped": "relation_first_requires_direct_evidence",
        }
    else:
        try:
            ontology, remaining_suggestions, closure_stats = close_grounded_gaps(
                ontology,
                pre_suggestions,
                page_text_by_page,
            )
        except Exception:
            logger.exception("[ontology] Graph closure pass failed; keeping ontology unchanged")
            remaining_suggestions = pre_suggestions
    if closure_stats.get("applied"):
        ontology = _normalize_ontology_instance(
            ontology=ontology,
            schema=schema,
            source_type=ontology.source_type,
            source_title=ontology.source_title,
            asset_identity=asset_identity,
        )

    grounding_issues, ungrounded_node_keys, grounding_stats = ground_relation_evidence(
        ontology,
        page_text_by_page,
    )

    semantic_issues = [*result.semantic_issues, *grounding_issues]
    schema_issues, human_fields = _validate_schema(ontology, schema)
    graph_issues, _ = run_graph_analysis(ontology, schema)
    # Surface only the suggestions we did NOT auto-apply.
    suggested_relations = remaining_suggestions

    confidence_report = result.confidence_report
    confidence_cfg = get_confidence_config()
    if confidence_cfg.get("enabled", True):
        try:
            confidence_report = score_ontology(
                ontology=ontology,
                schema=schema,
                semantic_issues=semantic_issues,
                schema_issues=schema_issues,
                human_required_fields=human_fields,
                retry_count=result.retry_count,
                config=confidence_cfg,
                ungrounded_node_keys=ungrounded_node_keys,
            )
        except Exception:
            logger.exception("[ontology] Confidence re-scoring after run-level passes failed")

    blocking_schema = [
        issue for issue in schema_issues
        if str(getattr(issue, "severity", "")).strip().lower() != "warning"
    ]
    contract_report = dict(result.diagnostic_contract_report or {})
    contract_blocked = bool(
        contract_report.get("schema_version")
        and (
            not contract_report.get("parsed", True)
            or contract_report.get("refusal", False)
            or str(contract_report.get("finish_reason") or "stop").strip().lower()
            not in {"", "stop"}
        )
    )
    if result.status == "blocked" or contract_blocked:
        status = "blocked"
    elif result.status == "needs_human_review":
        status = "needs_human_review"
    elif blocking_schema:
        status = "blocked"
    elif human_fields:
        status = "needs_human"
    else:
        status = "ready"

    # Build the unified review queue (the operator's "red zone").
    from backend.services.review_queue_service import build_review_queue, summarize_queue

    review_queue = build_review_queue(
        ontology.model_dump(),
        confidence_report=confidence_report,
        schema_issues=schema_issues,
        suggested_relations=suggested_relations,
    )
    review_summary = summarize_queue(review_queue)
    logger.info(
        "[ontology] Review queue: %d item(s) for the operator (%s)",
        review_summary["total"],
        review_summary.get("by_severity", {}),
    )

    updated = OntologyPipelineResponse(
        status=status,
        ontology=ontology,
        semantic_issues=semantic_issues,
        schema_issues=schema_issues,
        human_required_fields=human_fields,
        is_schema_compliant=(
            not schema_issues and not human_fields and not contract_blocked
        ),
        is_ready_for_human_review=not blocking_schema and not contract_blocked,
        retry_count=result.retry_count,
        graph_issues=graph_issues,
        suggested_relations=suggested_relations,
        confidence_report=confidence_report,
        diagnostic_contract_report=result.diagnostic_contract_report,
        resolution_completion_report=resolution_report,
        canonicalization_report=canonicalization_report,
        review_queue=review_queue,
        review_summary=review_summary,
    )
    quality_stats = {
        "grounding": grounding_stats,
        "closure": closure_stats,
        "coverage_completion": coverage_report,
        "canonicalization": canonicalization_report,
    }
    return updated, usage_entries, resolution_report, quality_stats


def _resolve_draft_pages(
    all_pages: list[dict],
    pages_to_keep: list[int] | None,
    *,
    always_include_first_pages: int,
    asset_identity: dict[str, str] | None,
) -> list[dict]:
    """Return the pages to use for ontology drafting.

    Keep the approved scoping selection stable. Front-matter pages are only
    force-added when we still lack a reliable asset identity.
    """
    if not pages_to_keep:
        return all_pages

    keep_set = set(int(page) for page in pages_to_keep)
    include_front_matter = (
        always_include_first_pages > 0
        and not str((asset_identity or {}).get("name") or "").strip()
    )
    if include_front_matter:
        keep_set |= {
            page["page_number"]
            for page in all_pages
            if page["page_number"] <= always_include_first_pages
        }
    return [page for page in all_pages if page["page_number"] in keep_set]


async def draft_ontology_workflow(store: dict, req: OntologyDraftRequest, on_event=None) -> OntologyPipelineResponse:
    """Run the existing ontology drafting flow against a store entry."""
    t0 = time.perf_counter()
    all_pages = store["pages"]
    ontology_cfg = get_ontology_config()
    asset_identity = _canonical_asset_identity(store)
    pages_to_keep = req.pages_to_keep or (store.get("cut_plan") or {}).get("pages_to_keep")
    filtered_pages = _resolve_draft_pages(
        all_pages,
        pages_to_keep,
        always_include_first_pages=int(ontology_cfg.get("always_include_first_pages", 0)),
        asset_identity=asset_identity,
    )

    sections = (store.get("cut_plan") or {}).get("sections", [])
    max_chars = int(ontology_cfg.get("max_input_chars", 600000))
    max_pages_per_chunk = int(ontology_cfg.get("max_pages_per_chunk", 30))
    role_config = store.get("pdf_extraction_roles") or {}
    diagnostic_page_numbers = {
        int(value) for value in role_config.get("diagnostic_pages", [])
    }
    structural_page_numbers = {
        int(value) for value in role_config.get("structural_pages", [])
    }
    has_role_partition = bool(diagnostic_page_numbers or structural_page_numbers)
    if has_role_partition:
        diagnostic_pages = [
            page for page in filtered_pages
            if int(page["page_number"]) in diagnostic_page_numbers
        ]
        structural_pages = [
            page for page in filtered_pages
            if int(page["page_number"]) in structural_page_numbers
        ]
    else:
        diagnostic_pages = filtered_pages
        structural_pages = []

    advisory_record_windows = _diagnostic_record_windows(store)
    # The semantic scope is authoritative.  Deterministic row/prose recognizers
    # are necessarily vocabulary- and layout-sensitive, so using their output
    # as an admission gate can silently erase entire troubleshooting sections.
    # Every scoped diagnostic page therefore reaches the typed extractor in a
    # bounded section chunk.  Record windows remain audit telemetry only; the
    # deterministic compiler still validates every returned evidence span.
    diagnostic_chunks = [
        (pages, context, [])
        for pages, context in _split_pages_by_section(
            diagnostic_pages,
            sections,
            max_chars,
            int(
                ontology_cfg.get(
                    "diagnostic_max_pages_per_chunk",
                    max_pages_per_chunk,
                )
            ),
            int(ontology_cfg.get("diagnostic_chunk_overlap_pages", 1)),
        )
    ]
    structural_chunks = _split_pages_by_section(
        structural_pages,
        sections,
        max_chars,
        int(ontology_cfg.get("structural_max_pages_per_chunk", max_pages_per_chunk)),
    )
    diagnostic_role = "diagnostic" if has_role_partition else "legacy"
    page_chunks = [
        (diagnostic_role, pages, context, windows)
        for pages, context, windows in diagnostic_chunks
    ] + [
        ("structural", pages, context, []) for pages, context in structural_chunks
    ]
    cost_preflight: dict = {}
    cost_guard_cfg = get_pdf_generation_cost_guard_config()
    relation_first_run = bool(ontology_cfg.get("relation_first", False)) and has_role_partition
    escalation_cfg = get_diagnostic_escalation_config()
    escalation_cap = max(0, int(escalation_cfg.get("max_chunks_per_run", 0) or 0))
    escalation_active = bool(
        relation_first_run
        and diagnostic_chunks
        and escalation_cfg.get("enabled", False)
        and escalation_cap > 0
    )
    escalation_max_calls = min(escalation_cap, len(diagnostic_chunks)) if escalation_active else 0
    if escalation_active:
        primary_model = str(escalation_cfg.get("primary_model") or "gpt-5.6-luna")
        escalation_model = str(escalation_cfg.get("model") or "")
        if not _model_matches_family(req.model_name, primary_model):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Diagnostic escalation requires the configured Luna primary model "
                    f"({primary_model}); received {req.model_name}."
                ),
            )
        if not _model_matches_family(escalation_model, "gpt-5.6-terra"):
            raise HTTPException(
                status_code=409,
                detail="Diagnostic escalation model must be a GPT-5.6 Terra model.",
            )
        if not cost_guard_cfg.get("enabled", True):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Diagnostic escalation requires the PDF cost guard so the Terra "
                    "envelope can be reserved before generation."
                ),
            )
    if relation_first_run and cost_guard_cfg.get("enabled", True):
        from backend.services.pdf_cost_guard import estimate_pdf_generation_envelope

        coverage_cfg = get_coverage_completion_config()
        resolution_cfg = get_resolution_completion_config()
        scoping_metrics = (
            ((store.get("run_metrics") or {}).get("stages") or {}).get("scoping") or {}
        )
        chunk_characters = []
        chunk_output_tokens = []
        for _role, chunk_pages, chunk_sections, chunk_windows in page_chunks:
            header = _build_section_header(chunk_sections)
            text = (
                _render_diagnostic_windows(chunk_windows)
                if chunk_windows
                else format_text_with_pages(chunk_pages)
            )
            chunk_characters.append(len(text) + len(header))
            chunk_output_tokens.append(
                _diagnostic_output_token_limit(chunk_windows, ontology_cfg)
                if _role == "diagnostic"
                else int(ontology_cfg.get("extraction_max_output_tokens", 16000))
            )
        cost_preflight = estimate_pdf_generation_envelope(
            model_name=req.model_name,
            chunk_input_characters=chunk_characters,
            extraction_max_output_tokens=int(ontology_cfg.get("extraction_max_output_tokens", 16000)),
            chunk_max_output_tokens=chunk_output_tokens,
            coverage_enabled=(
                not relation_first_run
                and bool(coverage_cfg.get("enabled", True))
                and bool(diagnostic_pages)
            ),
            coverage_max_input_tokens=int(coverage_cfg.get("estimated_max_input_tokens", 30000)),
            coverage_max_output_tokens=int(coverage_cfg.get("max_output_tokens", 4500)),
            resolution_enabled=(
                not relation_first_run
                and bool(resolution_cfg.get("enabled", True))
                and bool(diagnostic_pages)
            ),
            resolution_max_targets=int(resolution_cfg.get("max_targets", 0)),
            resolution_max_input_tokens=int(resolution_cfg.get("estimated_max_input_tokens", 12500)),
            resolution_max_output_tokens=int(resolution_cfg.get("max_output_tokens", 2500)),
            scoping_actual_cost_usd=float(scoping_metrics.get("estimated_cost_usd", 0) or 0),
            scoping_actual_call_count=int(scoping_metrics.get("llm_calls", 0) or 0),
            fixed_prompt_overhead_characters=int(
                cost_guard_cfg.get("fixed_prompt_overhead_characters", 30000)
            ),
            diagnostic_escalation_enabled=escalation_active,
            diagnostic_escalation_model_name=str(escalation_cfg.get("model") or ""),
            diagnostic_escalation_max_calls=escalation_max_calls,
            diagnostic_escalation_max_input_characters=int(
                escalation_cfg.get("max_input_chars", 0) or 0
            ),
            diagnostic_escalation_fixed_prompt_overhead_characters=int(
                escalation_cfg.get("schema_overhead_characters", 10000) or 0
            ),
            diagnostic_escalation_max_output_tokens=int(
                escalation_cfg.get("max_output_tokens", 0) or 0
            ),
        )
        hard_ceiling = float(cost_guard_cfg.get("hard_ceiling_usd", 0.49))
        cost_preflight["preferred_cost_usd"] = float(
            cost_guard_cfg.get("preferred_cost_usd", 0.35)
        )
        cost_preflight["hard_ceiling_usd"] = hard_ceiling
        cost_preflight["passed"] = cost_preflight["conservative_max_cost_usd"] <= hard_ceiling
        store["pdf_generation_cost_preflight"] = cost_preflight
        if not cost_preflight["passed"]:
            raise HTTPException(
                status_code=409,
                detail=(
                    "PDF generation cost preflight failed: conservative maximum "
                    f"${cost_preflight['conservative_max_cost_usd']:.6f} exceeds "
                    f"the ${hard_ceiling:.2f} ceiling."
                ),
            )
    logger.info(
        "[ontology] Drafting from %d pages (%d diagnostic, %d structural), %d sections → %d chunk(s)",
        len(filtered_pages),
        len(diagnostic_pages),
        len(structural_pages),
        len(sections),
        len(page_chunks),
    )

    chunk_concurrency = max(1, int(ontology_cfg.get("chunk_concurrency", 3)))
    chunk_retry_attempts = max(1, int(ontology_cfg.get("chunk_retry_attempts", 3)))
    chunk_retry_base_seconds = max(0.0, float(ontology_cfg.get("chunk_retry_base_seconds", 2)))
    chunk_semaphore = asyncio.Semaphore(chunk_concurrency)

    def _render_chunk_text(chunk_pages, chunk_sections, chunk_windows) -> str:
        if chunk_windows:
            return _render_diagnostic_windows(chunk_windows)
        chunk_header = _build_section_header(chunk_sections)
        chunk_text = format_text_with_pages(chunk_pages)
        if chunk_header:
            chunk_text = chunk_header + "\n\n" + chunk_text
        return chunk_text

    async def _process_chunk(
        index, extraction_role, chunk_pages, chunk_sections, chunk_windows,
    ):
        # Only describe the sections these pages actually belong to: listing the
        # whole manual's sections on an uncovered-pages chunk is prompt noise
        # that invites wrong section attributions.
        chunk_text = _render_chunk_text(chunk_pages, chunk_sections, chunk_windows)

        page_numbers = [page["page_number"] for page in chunk_pages]
        logger.info(
            "[ontology] Chunk %d/%d [%s] — %d sections, pages %d-%d (%d chars)",
            index,
            len(page_chunks),
            extraction_role,
            len(chunk_sections),
            min(page_numbers),
            max(page_numbers),
            len(chunk_text),
        )
        async with chunk_semaphore:
            result, metrics = await _run_chunk_with_retry(
                lambda: build_initial_ontology(
                    text_with_pages=chunk_text,
                    source_type=req.source_type,
                    source_title=req.source_title,
                    target_language=req.target_language,
                    model_name=req.model_name,
                    reasoning_effort=req.reasoning_effort,
                    asset_identity=asset_identity,
                    extraction_role=extraction_role,
                    relation_first=(
                        bool(ontology_cfg.get("relation_first", False))
                        and extraction_role != "legacy"
                    ),
                    diagnostic_call_options=(
                        {
                            "record_windows": chunk_windows,
                            "max_output_tokens": _diagnostic_output_token_limit(
                                chunk_windows, ontology_cfg
                            ),
                        }
                        if extraction_role == "diagnostic" and chunk_windows
                        else None
                    ),
                    diagnostic_evidence_units=(
                        _diagnostic_evidence_for_pages(
                            list(store.get("diagnostic_evidence_units") or []),
                            chunk_pages,
                        )
                        if extraction_role == "diagnostic"
                        else None
                    ),
                    on_event=on_event,
                ),
                attempts=chunk_retry_attempts,
                base_delay_seconds=chunk_retry_base_seconds,
            )
        metrics["chunk_index"] = index
        metrics["chunk_pages"] = len(chunk_pages)
        metrics["section_count"] = len(chunk_sections)
        metrics["extraction_role"] = extraction_role
        return result, metrics

    tasks = [
        _process_chunk(index, extraction_role, chunk_pages, chunk_sections, chunk_windows)
        for index, (
            extraction_role, chunk_pages, chunk_sections, chunk_windows,
        ) in enumerate(page_chunks, start=1)
    ]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    chunk_results: list[OntologyPipelineResponse] = []
    chunk_metrics: list[dict] = []
    for item in gathered:
        if isinstance(item, Exception):
            detail = str(item)
            status_code = 408 if "stopped after" in detail else 400
            raise HTTPException(status_code=status_code, detail=detail) from item
        result, metrics = item
        chunk_results.append(result)
        chunk_metrics.append(metrics)

    escalation_stats = {
        "enabled": escalation_active,
        "reserved_calls": escalation_max_calls,
        "eligible_chunks": 0,
        "attempted_chunks": 0,
        "selected_chunks": 0,
        "composed_chunks": 0,
        "skipped_chunks": 0,
        "model": str(escalation_cfg.get("model") or "") if escalation_active else "",
        "reasoning_effort": (
            str(escalation_cfg.get("reasoning_effort") or "medium")
            if escalation_active
            else ""
        ),
    }
    if escalation_active:
        escalation_candidates: list[tuple[int, int, int, int, str]] = []
        for offset, (
            extraction_role, _chunk_pages, _chunk_sections, _chunk_windows,
        ) in enumerate(page_chunks):
            if extraction_role != "diagnostic":
                continue
            primary_report = dict(chunk_results[offset].diagnostic_contract_report or {})
            reason = _diagnostic_escalation_reason(primary_report)
            if reason:
                escalation_candidates.append(
                    (
                        _diagnostic_escalation_priority(primary_report),
                        int(primary_report.get("unresolved_count", 0) or 0),
                        int(primary_report.get("candidate_count", 0) or 0),
                        offset,
                        reason,
                    )
                )
        escalation_candidates.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))

        for _priority, _unresolved, _candidates, offset, reason in escalation_candidates:
            extraction_role, chunk_pages, chunk_sections, chunk_windows = page_chunks[offset]
            primary_result = chunk_results[offset]
            primary_report = dict(primary_result.diagnostic_contract_report or {})
            escalation_stats["eligible_chunks"] += 1
            if escalation_stats["attempted_chunks"] >= escalation_max_calls:
                escalation_stats["skipped_chunks"] += 1
                chunk_results[offset] = _with_diagnostic_escalation_metadata(
                    primary_result,
                    reason=reason,
                    attempted=False,
                    selected="primary",
                    primary_report=primary_report,
                    skip_reason="run_cap_exhausted",
                )
                continue

            escalation_stats["attempted_chunks"] += 1
            chunk_text = _render_chunk_text(
                chunk_pages, chunk_sections, chunk_windows,
            )
            try:
                escalated_result, escalated_metrics = await asyncio.to_thread(
                    build_initial_ontology,
                    text_with_pages=chunk_text,
                    source_type=req.source_type,
                    source_title=req.source_title,
                    target_language=req.target_language,
                    model_name=str(escalation_cfg.get("model") or "gpt-5.6-terra"),
                    reasoning_effort=str(
                        escalation_cfg.get("reasoning_effort") or "medium"
                    ),
                    asset_identity=asset_identity,
                    extraction_role="diagnostic",
                    relation_first=True,
                    diagnostic_call_options={
                        "operation": "diagnostic_bundle_escalation",
                        "escalation_reason": reason,
                        "timeout_seconds": int(
                            escalation_cfg.get("timeout_seconds", 180) or 180
                        ),
                        "max_input_chars": int(
                            escalation_cfg.get("max_input_chars", 60000) or 60000
                        ),
                        "estimated_max_input_tokens": int(
                            escalation_cfg.get("estimated_max_input_tokens", 15000) or 15000
                        ),
                        "max_output_tokens": int(
                            escalation_cfg.get("max_output_tokens", 4000) or 4000
                        ),
                        "record_windows": chunk_windows,
                    },
                    diagnostic_evidence_units=_diagnostic_evidence_for_pages(
                        list(store.get("diagnostic_evidence_units") or []),
                        chunk_pages,
                    ),
                )
            except Exception as exc:
                logger.warning(
                    "[ontology] Terra diagnostic escalation skipped for chunk %d: %s",
                    offset + 1,
                    exc,
                )
                escalation_stats["skipped_chunks"] += 1
                chunk_results[offset] = _with_diagnostic_escalation_metadata(
                    primary_result,
                    reason=reason,
                    attempted=True,
                    selected="primary",
                    primary_report=primary_report,
                    skip_reason=f"{type(exc).__name__}",
                )
                continue

            escalated_metrics.update({
                "chunk_index": offset + 1,
                "chunk_pages": len(chunk_pages),
                "section_count": len(chunk_sections),
                "extraction_role": "diagnostic",
            })
            escalated_report = dict(escalated_result.diagnostic_contract_report or {})
            primary_published = _published_branch_ids(primary_report)
            escalated_published = _published_branch_ids(escalated_report)
            published_union = primary_published | escalated_published
            complementary_publication = (
                len(published_union) > max(
                    len(primary_published), len(escalated_published)
                )
            )
            if complementary_publication:
                # Both attempts have already passed the same typed compiler and
                # literal-evidence gate.  Preserve complementary branches as a
                # verified union instead of replacing the entire Luna result.
                selected_result = _merge_pipeline_results(
                    [primary_result, escalated_result],
                    asset_identity=asset_identity,
                )
                selected_label = "composed_union"
                escalation_stats["composed_chunks"] += 1
            else:
                use_escalated = _prefer_escalated_diagnostic_report(
                    primary_report,
                    escalated_report,
                )
                selected_result = escalated_result if use_escalated else primary_result
                selected_label = "escalated" if use_escalated else "primary"
            if selected_label != "primary":
                escalation_stats["selected_chunks"] += 1
            chunk_results[offset] = _with_diagnostic_escalation_metadata(
                selected_result,
                reason=reason,
                attempted=True,
                selected=selected_label,
                primary_report=primary_report,
                escalated_report=escalated_report,
            )
            chunk_metrics[offset] = _merge_escalated_chunk_metrics(
                chunk_metrics[offset],
                escalated_metrics,
            )

    # Keep exact call accounting: an eligible diagnostic chunk may contain one
    # Luna primary call and one preflight-reserved Terra escalation call.
    ontology_call_ledger: list[dict] = []
    for metrics in chunk_metrics:
        ontology_call_ledger.extend(
            _chunk_call_ledger_entries(metrics, req.reasoning_effort or "default")
        )

    result = _merge_pipeline_results(chunk_results, asset_identity=asset_identity)
    if result.diagnostic_contract_report:
        expected_diagnostic_pages = sorted({
            int(page["page_number"]) for page in diagnostic_pages
        })
        processed_diagnostic_pages = sorted({
            int(page)
            for page in (
                result.diagnostic_contract_report.get("input_pages") or []
            )
            if int(page) > 0
        })
        unprocessed_diagnostic_pages = sorted(
            set(expected_diagnostic_pages) - set(processed_diagnostic_pages)
        )
        coverage_complete = not unprocessed_diagnostic_pages
        coverage_report = {
            **dict(result.diagnostic_contract_report),
            "diagnostic_input_policy": "semantic_scope_full_page_v1",
            "expected_diagnostic_pages": expected_diagnostic_pages,
            "processed_diagnostic_pages": processed_diagnostic_pages,
            "unprocessed_diagnostic_pages": unprocessed_diagnostic_pages,
            "diagnostic_page_coverage_complete": coverage_complete,
        }
        if not coverage_complete:
            coverage_report.update({
                "parsed": False,
                "finish_reason": "incomplete",
                "escalation_recommended": True,
            })
        result = result.model_copy(update={
            "diagnostic_contract_report": coverage_report,
        })
    result, finalize_usage_entries, run_resolution_report, quality_stats = await asyncio.to_thread(
        _finalize_run_level_quality,
        result,
        diagnostic_pages,
        req.model_name,
        asset_identity,
        all_pages,
        reasoning_effort=req.reasoning_effort,
        relation_first=(
            bool(ontology_cfg.get("relation_first", False)) and has_role_partition
        ),
    )
    grounding_stats = quality_stats.get("grounding", {})
    closure_stats = quality_stats.get("closure", {})
    if finalize_usage_entries:
        from backend.services.run_metrics import aggregate_usage

        finalize_usage = aggregate_usage(finalize_usage_entries)
        chunk_metrics.append({
            **finalize_usage,
            "chunk_index": 0,
            "chunk_pages": 0,
            "section_count": 0,
        })
        ontology_call_ledger.extend({
            **entry,
            "reasoning_effort": req.reasoning_effort or "default",
            "extraction_role": "finalization",
            "chunk_index": 0,
            "aggregate_call_count": 1,
        } for entry in finalize_usage_entries)
    ontology_call_ledger = [
        {**entry, "call_index": index}
        for index, entry in enumerate(ontology_call_ledger, start=1)
    ]
    usage_summary = merge_usage_summaries(chunk_metrics)
    total_prompt_tokens = int(usage_summary["prompt_tokens"])
    total_cached_prompt_tokens = int(usage_summary["cached_prompt_tokens"])
    total_cache_write_prompt_tokens = int(
        usage_summary["cache_write_prompt_tokens"]
    )
    total_non_cached_prompt_tokens = int(usage_summary["non_cached_prompt_tokens"])
    total_completion_tokens = int(usage_summary["completion_tokens"])
    total_tokens = int(usage_summary["total_tokens"])
    total_llm_calls = int(usage_summary["llm_calls"])
    total_retries = sum(int(item.get("retry_count", 0) or 0) for item in chunk_metrics)
    total_cost_usd = float(usage_summary["estimated_cost_usd"])
    models = list(usage_summary["models"])
    operations = list(usage_summary["operations"])
    parse_repair_events: list[dict] = [
        event
        for item in chunk_metrics
        for event in (item.get("parse_repair_events") or [])
    ]
    resolution_attempts = int(run_resolution_report.get("attempted", 0) or 0)
    resolution_completed = int(run_resolution_report.get("completed", 0) or 0)
    resolution_target_count = int(run_resolution_report.get("target_count", 0) or 0)

    record_stage_metrics(
        store,
        "ontology",
        {
            "stage": "ontology",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            "llm_calls": total_llm_calls,
            "prompt_tokens": total_prompt_tokens,
            "cached_prompt_tokens": total_cached_prompt_tokens,
            "cache_write_prompt_tokens": total_cache_write_prompt_tokens,
            "non_cached_prompt_tokens": total_non_cached_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": total_cost_usd,
            "models": models,
            "operations": operations,
            "by_model": usage_summary["by_model"],
            "details": {
                "selected_pages": len(filtered_pages),
                "selected_sections": len(sections),
                "chunk_count": len(page_chunks),
                "diagnostic_pages": len(diagnostic_pages),
                "structural_pages": len(structural_pages),
                "diagnostic_chunks": len(diagnostic_chunks),
                "structural_chunks": len(structural_chunks),
                "diagnostic_input_policy": "semantic_scope_full_page_v1",
                "advisory_record_window_count": len(advisory_record_windows),
                "reasoning_effort": req.reasoning_effort or "default",
                "retry_count": total_retries,
                "status": result.status,
                "schema_issue_count": len(result.schema_issues),
                "semantic_issue_count": len(result.semantic_issues),
                "graph_issue_count": len(result.graph_issues),
                "suggested_relation_count": len(result.suggested_relations),
                "parse_repair_count": len(parse_repair_events),
                "parse_repair_events": parse_repair_events,
                "resolution_completion": {
                    "target_count": resolution_target_count,
                    "attempted": resolution_attempts,
                    "completed": resolution_completed,
                    "reports": [run_resolution_report] if run_resolution_report else [],
                },
                "evidence_grounding": grounding_stats,
                "graph_closure": closure_stats,
                "coverage_completion": quality_stats.get("coverage_completion", {}),
                "cost_preflight": cost_preflight,
                "diagnostic_escalation": escalation_stats,
                "call_ledger": ontology_call_ledger,
            },
        },
    )
    store["source_type"] = req.source_type
    store["source_title"] = req.source_title
    store["ontology_pipeline"] = result.model_dump()
    return result
