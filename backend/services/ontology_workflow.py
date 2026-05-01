"""Reusable ontology-drafting workflow shared by classic and multi-agent modes."""

from __future__ import annotations

import asyncio
import logging
import re as _re
import time
from copy import deepcopy

from fastapi import HTTPException

from backend.app_config import get_ontology_config
from backend.models import OntologyDraftRequest, OntologyPipelineResponse, OntologyRelationInstance
from backend.services.ontology_pipeline import _normalize_ontology_instance, build_initial_ontology
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.cutplan_service import extract_asset_identity
from backend.services.pdf_service import format_text_with_pages
from backend.services.run_metrics import record_stage_metrics
from backend.services.ontology_semantics import normalize_asset_node

logger = logging.getLogger(__name__)

_STATUS_RANK = {"blocked": 3, "needs_human_review": 2, "needs_human": 1, "ready": 0}


def _normalize_node_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse spaces for fuzzy dedup."""
    value = str(name or "").lower().strip()
    value = _re.sub(r"[^\w\s]", " ", value)
    return _re.sub(r"\s+", " ", value).strip()


def _canonical_asset_identity(store: dict) -> dict[str, str]:
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
                return identity

    if source_title or filename:
        return extract_asset_identity(
            {},
            fallback_name=source_title,
            source_type=source_type,
            filename=filename,
        )
    return {}


def _merge_pipeline_results(
    results: list[OntologyPipelineResponse],
    *,
    asset_identity: dict[str, str] | None = None,
) -> OntologyPipelineResponse:
    """Merge chunk-level ontology results into one normalized run-level payload."""
    if len(results) == 1:
        return results[0]

    id_remap: dict[str, str] = {}
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

    def _node_name(node: dict) -> str:
        return str(node.get("name", node.get("title", ""))).strip()

    def _node_richness(node: dict) -> int:
        return sum(1 for value in node.values() if value not in ("", [], {}, None))

    for result in results:
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
                    id_remap[original_node_id] = node_id

                existing_by_id = next(
                    (
                        existing for existing in merged_nodes[node_type]
                        if _node_id(existing, node_type) == node_id
                    ),
                    None,
                )
                if existing_by_id is not None:
                    if _node_richness(node) > _node_richness(existing_by_id):
                        merged_nodes[node_type].remove(existing_by_id)
                        merged_nodes[node_type].append(node)
                    continue

                if node_name and node_name in name_to_id[node_type]:
                    canonical_id = name_to_id[node_type][node_name]
                    if node_id != canonical_id:
                        id_remap[node_id] = canonical_id
                        existing_by_name = next(
                            (
                                existing for existing in merged_nodes[node_type]
                                if _node_id(existing, node_type) == canonical_id
                            ),
                            None,
                        )
                        if (
                            existing_by_name is not None
                            and _node_richness(node) > _node_richness(existing_by_name)
                        ):
                            merged_nodes[node_type].remove(existing_by_name)
                            merged_nodes[node_type].append(node)
                    continue

                merged_nodes[node_type].append(node)
                if node_name:
                    name_to_id[node_type][node_name] = node_id

    merged_relations: list[OntologyRelationInstance] = []
    seen_relations: set[tuple] = set()

    for result in results:
        for relation in result.ontology.relations:
            from_id = id_remap.get(relation.from_id, relation.from_id)
            to_id = id_remap.get(relation.to_id, relation.to_id)
            key = (relation.name, from_id, to_id)
            if key in seen_relations:
                continue
            merged_relations.append(OntologyRelationInstance(
                name=relation.name,
                from_type=relation.from_type,
                from_id=from_id,
                to_type=relation.to_type,
                to_id=to_id,
                evidence=relation.evidence,
            ))
            seen_relations.add(key)

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
    # empty_draft_content is a per-chunk diagnostic; when merging multiple chunks it is
    # expected that some chunks (e.g. a cover-page-only chunk) produce no diagnostic nodes.
    # Filter it out here so the final merge status reflects the consolidated ontology.
    all_schema = _dedup_issues([
        issue for result in results for issue in result.schema_issues
        if issue.code != "empty_draft_content"
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
    if all_schema:
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

    return OntologyPipelineResponse(
        status=worst_status,
        ontology=merged_ontology,
        semantic_issues=all_semantic,
        schema_issues=all_schema,
        human_required_fields=merged_human_required,
        is_schema_compliant=not all_schema and not merged_human_required,
        is_ready_for_human_review=not all_schema,
        retry_count=retry_total,
        graph_issues=all_graph,
        suggested_relations=all_suggested,
        confidence_report=merged_confidence_report,
    )


def _split_pages_by_section(
    pages: list[dict],
    sections: list[dict],
    max_chars: int,
    max_pages: int = 30,
) -> list[tuple[list[dict], list[dict]]]:
    """Split selected pages into chunk-sized groups while preserving section context."""
    if not sections or not pages:
        sorted_pages = sorted(pages, key=lambda page: page["page_number"])
        return [
            (sorted_pages[index:index + max_pages], [])
            for index in range(0, len(sorted_pages), max_pages)
        ] or [(pages, [])]

    page_map = {page["page_number"]: page for page in pages}
    covered_page_numbers: set[int] = set()
    ordered_groups: list[tuple[int, list[dict], list[dict]]] = []
    for section in sections:
        section_pages = [
            page_map[page_number]
            for page_number in range(section["start"], section["end"] + 1)
            if page_number in page_map
        ]
        if section_pages:
            covered_page_numbers.update(page["page_number"] for page in section_pages)
            ordered_groups.append((section_pages[0]["page_number"], section_pages, [section]))

    uncovered_pages = [
        page for page in sorted(pages, key=lambda page: page["page_number"])
        if page["page_number"] not in covered_page_numbers
    ]
    current_uncovered_run: list[dict] = []
    for page in uncovered_pages:
        if (
            current_uncovered_run
            and page["page_number"] != current_uncovered_run[-1]["page_number"] + 1
        ):
            ordered_groups.append(
                (current_uncovered_run[0]["page_number"], current_uncovered_run, []),
            )
            current_uncovered_run = []
        current_uncovered_run.append(page)
    if current_uncovered_run:
        ordered_groups.append(
            (current_uncovered_run[0]["page_number"], current_uncovered_run, []),
        )

    if not ordered_groups:
        sorted_pages = sorted(pages, key=lambda page: page["page_number"])
        return [
            (sorted_pages[index:index + max_pages], [])
            for index in range(0, len(sorted_pages), max_pages)
        ] or [(pages, [])]

    def _flush(current_pages, current_sections, target):
        if not current_pages:
            return
        for index in range(0, len(current_pages), max_pages):
            target.append((current_pages[index:index + max_pages], current_sections))

    chunks: list[tuple[list[dict], list[dict]]] = []
    current_pages: list[dict] = []
    current_sections: list[dict] = []
    current_chars = 0

    def _append_chunk_group(group_pages: list[dict], group_sections: list[dict]) -> None:
        if not group_pages:
            return
        group_chars = sum(
            len(f"--- PAGE {page['page_number']} ---\n{page['text']}\n\n")
            for page in group_pages
        )
        if group_chars > max_chars or len(group_pages) > max_pages:
            subset: list[dict] = []
            subset_chars = 0
            for page in group_pages:
                page_chars = len(f"--- PAGE {page['page_number']} ---\n{page['text']}\n\n")
                if subset and (subset_chars + page_chars > max_chars or len(subset) >= max_pages):
                    chunks.append((subset, group_sections))
                    subset = []
                    subset_chars = 0
                subset.append(page)
                subset_chars += page_chars
            if subset:
                chunks.append((subset, group_sections))
            return

        chunks.append((group_pages, group_sections))

    for _, group_pages, group_sections in sorted(ordered_groups, key=lambda item: item[0]):
        if not group_sections:
            _flush(current_pages, current_sections, chunks)
            current_pages = []
            current_sections = []
            current_chars = 0
            _append_chunk_group(group_pages, [])
            continue

        section_chars = sum(
            len(f"--- PAGE {page['page_number']} ---\n{page['text']}\n\n")
            for page in group_pages
        )
        would_exceed_chars = current_pages and (current_chars + section_chars > max_chars)
        would_exceed_pages = current_pages and (len(current_pages) + len(group_pages) > max_pages)
        if would_exceed_chars or would_exceed_pages:
            _flush(current_pages, current_sections, chunks)
            current_pages = []
            current_sections = []
            current_chars = 0

        if section_chars > max_chars or len(group_pages) > max_pages:
            _flush(current_pages, current_sections, chunks)
            current_pages = []
            current_sections = []
            current_chars = 0
            _append_chunk_group(group_pages, group_sections)
            continue

        current_pages.extend(group_pages)
        current_sections.extend(group_sections)
        current_chars += section_chars

    _flush(current_pages, current_sections, chunks)
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

    page_chunks = _split_pages_by_section(
        filtered_pages,
        sections,
        max_chars,
        max_pages_per_chunk,
    )
    logger.info(
        "[ontology] Drafting from %d pages, %d sections → %d chunk(s)",
        len(filtered_pages),
        len(sections),
        len(page_chunks),
    )

    chunk_semaphore = asyncio.Semaphore(5)

    async def _process_chunk(index, chunk_pages, chunk_sections):
        chunk_header = _build_section_header(chunk_sections) if chunk_sections else _build_section_header(sections)
        chunk_text = format_text_with_pages(chunk_pages)
        if chunk_header:
            chunk_text = chunk_header + "\n\n" + chunk_text

        page_numbers = [page["page_number"] for page in chunk_pages]
        logger.info(
            "[ontology] Chunk %d/%d — %d sections, pages %d-%d (%d chars)",
            index,
            len(page_chunks),
            len(chunk_sections),
            min(page_numbers),
            max(page_numbers),
            len(chunk_text),
        )
        async with chunk_semaphore:
            result, metrics = await asyncio.to_thread(
                build_initial_ontology,
                text_with_pages=chunk_text,
                source_type=req.source_type,
                source_title=req.source_title,
                target_language=req.target_language,
                model_name=req.model_name,
                asset_identity=asset_identity,
                on_event=on_event,
            )
        metrics["chunk_index"] = index
        metrics["chunk_pages"] = len(chunk_pages)
        metrics["section_count"] = len(chunk_sections)
        return result, metrics

    tasks = [
        _process_chunk(index, chunk_pages, chunk_sections)
        for index, (chunk_pages, chunk_sections) in enumerate(page_chunks, start=1)
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

    result = _merge_pipeline_results(chunk_results, asset_identity=asset_identity)
    total_prompt_tokens = sum(int(item.get("prompt_tokens", 0) or 0) for item in chunk_metrics)
    total_cached_prompt_tokens = sum(int(item.get("cached_prompt_tokens", 0) or 0) for item in chunk_metrics)
    total_non_cached_prompt_tokens = sum(int(item.get("non_cached_prompt_tokens", 0) or 0) for item in chunk_metrics)
    total_completion_tokens = sum(int(item.get("completion_tokens", 0) or 0) for item in chunk_metrics)
    total_tokens = sum(int(item.get("total_tokens", 0) or 0) for item in chunk_metrics)
    total_llm_calls = sum(int(item.get("llm_calls", 0) or 0) for item in chunk_metrics)
    total_retries = sum(int(item.get("retry_count", 0) or 0) for item in chunk_metrics)
    total_cost_usd = round(
        sum(float(item.get("estimated_cost_usd", 0) or 0) for item in chunk_metrics),
        6,
    )
    models = sorted({
        model
        for item in chunk_metrics
        for model in item.get("models", [])
        if model
    })
    operations = sorted({
        operation
        for item in chunk_metrics
        for operation in item.get("operations", [])
        if operation
    })
    parse_repair_events: list[dict] = [
        event
        for item in chunk_metrics
        for event in (item.get("parse_repair_events") or [])
    ]
    resolution_reports: list[dict] = [
        report
        for item in chunk_metrics
        for report in [item.get("resolution_completion")]
        if isinstance(report, dict) and report
    ]
    resolution_attempts = sum(int(report.get("attempted", 0) or 0) for report in resolution_reports)
    resolution_completed = sum(int(report.get("completed", 0) or 0) for report in resolution_reports)
    resolution_target_count = sum(int(report.get("target_count", 0) or 0) for report in resolution_reports)

    record_stage_metrics(
        store,
        "ontology",
        {
            "stage": "ontology",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            "llm_calls": total_llm_calls,
            "prompt_tokens": total_prompt_tokens,
            "cached_prompt_tokens": total_cached_prompt_tokens,
            "non_cached_prompt_tokens": total_non_cached_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": total_cost_usd,
            "models": models,
            "operations": operations,
            "details": {
                "selected_pages": len(filtered_pages),
                "selected_sections": len(sections),
                "chunk_count": len(page_chunks),
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
                    "reports": resolution_reports,
                },
            },
        },
    )
    store["source_type"] = req.source_type
    store["source_title"] = req.source_title
    store["ontology_pipeline"] = result.model_dump()
    return result
