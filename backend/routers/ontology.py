import asyncio
import json
import logging
import re as _re
import time
from copy import deepcopy

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
from fastapi.responses import Response

from backend.models import (
    ApplySuggestionsRequest,
    OntologyDraftRequest,
    OntologyExportRequest,
    OntologyPipelineResponse,
    OntologyRelationInstance,
    OntologyReviewRequest,
)
from backend.routers.upload import pdf_store
from backend.services.graph_reasoning import run_graph_analysis
from backend.services.ontology_pipeline import (
    apply_human_binding,
    build_initial_ontology,
    ontology_export_payload,
    validate_ontology_instance,
)
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.pdf_service import format_text_with_pages
from backend.app_config import get_ontology_config
from backend.services.run_metrics import record_stage_metrics

router = APIRouter(prefix="/ontology", tags=["ontology"])


def _load_filtered_text(req_pdf_id: str, pages_to_keep: list[int] | None) -> str:
    if req_pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found. Upload a PDF first.")
    store = pdf_store[req_pdf_id]
    pages = store["pages"]
    final_pages_to_keep = pages_to_keep or (store.get("cut_plan") or {}).get("pages_to_keep")
    if final_pages_to_keep:
        keep_set = set(final_pages_to_keep)
        pages = [p for p in pages if p["page_number"] in keep_set]
    return format_text_with_pages(pages)


_STATUS_RANK = {"blocked": 3, "needs_human_review": 2, "needs_human": 1, "ready": 0}


def _normalize_node_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse spaces for fuzzy dedup."""
    s = str(name or "").lower().strip()
    s = _re.sub(r"[^\w\s]", " ", s)
    return _re.sub(r"\s+", " ", s).strip()


def _merge_pipeline_results(results: list[OntologyPipelineResponse]) -> OntologyPipelineResponse:
    """
    Merge multiple chunk pipeline results into one consolidated ontology.

    Strategy:
    - Nodes: union with two-pass dedup (first by ID, then by normalized name).
      When a name collision is detected across chunks, keep the node with more
      populated fields and remap the duplicate ID to the kept ID.
    - Relations: union deduplicated by (name, from_id, to_id) after ID remapping.
    - Issues: aggregate all, dedup identical messages.
    - Status: worst across chunks.
    """
    if len(results) == 1:
        return results[0]

    # id_remap[old_id] = canonical_id  — built as we find duplicates
    id_remap: dict[str, str] = {}

    # Pass 1: collect all nodes, build id→node and name→id per type
    merged_nodes: dict[str, list[dict]] = {}
    # name_to_id[type][normalized_name] = canonical_id
    name_to_id: dict[str, dict[str, str]] = {}

    def _node_id(node: dict, node_type: str) -> str:
        id_field = {
            "Asset": "asset_id", "Component": "component_id",
            "Symptom": "symptom_id", "FailureMode": "failure_mode_id",
            "CorrectiveAction": "action_id", "ErrorCode": "error_code_id",
        }.get(node_type, "id")
        return str(node.get(id_field, node.get("id", ""))).strip()

    def _node_name(node: dict) -> str:
        return str(node.get("name", node.get("title", ""))).strip()

    def _node_richness(node: dict) -> int:
        """Count non-empty fields as a proxy for information density."""
        return sum(1 for v in node.values() if v and v != "" and v != [] and v != {})

    for result in results:
        for node_type, node_list in result.ontology.nodes.items():
            if node_type not in merged_nodes:
                merged_nodes[node_type] = []
                name_to_id[node_type] = {}

            for node in node_list:
                nid = _node_id(node, node_type)
                nname = _normalize_node_name(_node_name(node))
                if not nid:
                    continue

                # Check if same ID already present
                existing_by_id = next(
                    (n for n in merged_nodes[node_type] if _node_id(n, node_type) == nid),
                    None
                )
                if existing_by_id is not None:
                    # Same ID — keep richer version
                    if _node_richness(node) > _node_richness(existing_by_id):
                        merged_nodes[node_type].remove(existing_by_id)
                        merged_nodes[node_type].append(node)
                    continue

                # Check if same name already present under a different ID
                if nname and nname in name_to_id[node_type]:
                    canonical_id = name_to_id[node_type][nname]
                    if nid != canonical_id:
                        id_remap[nid] = canonical_id
                        # Keep richer version
                        existing_by_name = next(
                            (n for n in merged_nodes[node_type]
                             if _node_id(n, node_type) == canonical_id),
                            None
                        )
                        if existing_by_name and _node_richness(node) > _node_richness(existing_by_name):
                            merged_nodes[node_type].remove(existing_by_name)
                            merged_nodes[node_type].append(node)
                    continue

                # New node
                merged_nodes[node_type].append(node)
                if nname:
                    name_to_id[node_type][nname] = nid

    # Pass 2: collect relations, apply id_remap, dedup
    merged_relations: list[OntologyRelationInstance] = []
    seen_rels: set[tuple] = set()

    for result in results:
        for rel in result.ontology.relations:
            from_id = id_remap.get(rel.from_id, rel.from_id)
            to_id = id_remap.get(rel.to_id, rel.to_id)
            key = (rel.name, from_id, to_id)
            if key not in seen_rels:
                # Create updated relation with remapped IDs
                remapped = OntologyRelationInstance(
                    name=rel.name,
                    from_type=rel.from_type,
                    from_id=from_id,
                    to_type=rel.to_type,
                    to_id=to_id,
                    evidence=rel.evidence,
                )
                merged_relations.append(remapped)
                seen_rels.add(key)

    # Build merged ontology
    merged_ontology = deepcopy(results[0].ontology)
    merged_ontology.nodes = merged_nodes
    merged_ontology.relations = merged_relations

    # Aggregate issues — dedup identical messages
    def _dedup_issues(issues):
        seen = set()
        out = []
        for i in issues:
            key = (getattr(i, 'message', str(i)), getattr(i, 'severity', ''))
            if key not in seen:
                out.append(i)
                seen.add(key)
        return out

    all_semantic = _dedup_issues([i for r in results for i in r.semantic_issues])
    all_schema = _dedup_issues([i for r in results for i in r.schema_issues])
    all_graph = [i for r in results for i in r.graph_issues]
    all_suggested = [s for r in results for s in r.suggested_relations]

    # Human required fields: dedup by field_key
    hrf_map = {}
    for r in results:
        for f in r.human_required_fields:
            hrf_map[f.field_key] = f
    all_human = list(hrf_map.values())

    worst_status = max(results, key=lambda r: _STATUS_RANK.get(r.status, 0)).status
    retry_total = sum(r.retry_count for r in results)

    return OntologyPipelineResponse(
        status=worst_status,
        ontology=merged_ontology,
        semantic_issues=all_semantic,
        schema_issues=all_schema,
        human_required_fields=all_human,
        is_schema_compliant=all(r.is_schema_compliant for r in results),
        is_ready_for_human_review=any(r.is_ready_for_human_review for r in results),
        retry_count=retry_total,
        graph_issues=all_graph,
        suggested_relations=all_suggested,
    )


def _split_pages_by_section(
    pages: list[dict],
    sections: list[dict],
    max_chars: int,
    max_pages: int = 30,
) -> list[tuple[list[dict], list[dict]]]:
    """
    Split pages into chunks driven by cut-plan sections, bounded by both
    max_chars and max_pages per chunk.  Returns list of (pages, sections).
    Falls back to a single chunk when no sections are available.
    """
    if not sections or not pages:
        # No sections: split purely by page count
        sorted_pages = sorted(pages, key=lambda p: p["page_number"])
        return [
            (sorted_pages[i:i + max_pages], [])
            for i in range(0, len(sorted_pages), max_pages)
        ] or [(pages, [])]

    page_map = {p["page_number"]: p for p in pages}
    covered_page_numbers: set[int] = set()
    ordered_groups: list[tuple[int, list[dict], list[dict]]] = []
    for s in sections:
        sec_pages = [
            page_map[pn]
            for pn in range(s["start"], s["end"] + 1)
            if pn in page_map
        ]
        if sec_pages:
            covered_page_numbers.update(p["page_number"] for p in sec_pages)
            ordered_groups.append((sec_pages[0]["page_number"], sec_pages, [s]))

    uncovered_pages = [
        page for page in sorted(pages, key=lambda p: p["page_number"])
        if page["page_number"] not in covered_page_numbers
    ]
    current_uncovered_run: list[dict] = []
    for page in uncovered_pages:
        if (
            current_uncovered_run
            and page["page_number"] != current_uncovered_run[-1]["page_number"] + 1
        ):
            ordered_groups.append(
                (current_uncovered_run[0]["page_number"], current_uncovered_run, [])
            )
            current_uncovered_run = []
        current_uncovered_run.append(page)
    if current_uncovered_run:
        ordered_groups.append(
            (current_uncovered_run[0]["page_number"], current_uncovered_run, [])
        )

    if not ordered_groups:
        sorted_pages = sorted(pages, key=lambda p: p["page_number"])
        return [
            (sorted_pages[i:i + max_pages], [])
            for i in range(0, len(sorted_pages), max_pages)
        ] or [(pages, [])]

    def _flush(cur_pages, cur_sections, target):
        """Sub-divide current accumulation by max_pages if needed."""
        if not cur_pages:
            return
        for i in range(0, len(cur_pages), max_pages):
            target.append((cur_pages[i:i + max_pages], cur_sections))

    chunks: list[tuple[list[dict], list[dict]]] = []
    current_pages: list[dict] = []
    current_sections: list[dict] = []
    current_chars = 0

    def _append_chunk_group(group_pages: list[dict], group_sections: list[dict]) -> None:
        if not group_pages:
            return

        group_chars = sum(
            len(f"--- PAGE {p['page_number']} ---\n{p['text']}\n\n")
            for p in group_pages
        )
        # Group alone exceeds limits — sub-divide page by page.
        if group_chars > max_chars or len(group_pages) > max_pages:
            sub: list[dict] = []
            sub_chars = 0
            for p in group_pages:
                p_chars = len(f"--- PAGE {p['page_number']} ---\n{p['text']}\n\n")
                if sub and (sub_chars + p_chars > max_chars or len(sub) >= max_pages):
                    chunks.append((sub, group_sections))
                    sub = []
                    sub_chars = 0
                sub.append(p)
                sub_chars += p_chars
            if sub:
                chunks.append((sub, group_sections))
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

        sec_chars = sum(
            len(f"--- PAGE {p['page_number']} ---\n{p['text']}\n\n")
            for p in group_pages
        )
        would_exceed_chars = current_pages and (current_chars + sec_chars > max_chars)
        would_exceed_pages = current_pages and (len(current_pages) + len(group_pages) > max_pages)

        if would_exceed_chars or would_exceed_pages:
            _flush(current_pages, current_sections, chunks)
            current_pages = []
            current_sections = []
            current_chars = 0

        if sec_chars > max_chars or len(group_pages) > max_pages:
            _flush(current_pages, current_sections, chunks)
            current_pages = []
            current_sections = []
            current_chars = 0
            _append_chunk_group(group_pages, group_sections)
            continue

        current_pages.extend(group_pages)
        current_sections.extend(group_sections)
        current_chars += sec_chars

    _flush(current_pages, current_sections, chunks)
    return chunks


def _build_section_header(sections: list[dict]) -> str:
    """Build a section context header from stored cut-plan sections."""
    if not sections:
        return ""
    lines = ["## DOCUMENT CONTEXT",
             "These pages come from the following manual sections:"]
    for s in sections:
        lines.append(f"- {s['name']} (pp. {s['start']}-{s['end']}, source: {s.get('source', '?')})")
    lines.append("")
    lines.append("Use this context to better interpret the content. "
                 "Extract all ontology-relevant information from these sections, "
                 "including components, error codes, symptoms, failure modes, and corrective actions.")
    return "\n".join(lines)


@router.post("/draft", response_model=OntologyPipelineResponse)
async def draft_ontology(req: OntologyDraftRequest):
    t0 = time.perf_counter()
    store = pdf_store[req.pdf_id]
    all_pages = store["pages"]
    ontology_cfg = get_ontology_config()
    pages_to_keep = req.pages_to_keep or (store.get("cut_plan") or {}).get("pages_to_keep")
    if pages_to_keep:
        keep_set = set(pages_to_keep)
        # Always include the first N pages: they typically contain the component diagram/parts list
        # which the cut-plan may exclude (treats "Diagrams" as non-diagnostic)
        always_n = int(ontology_cfg.get("always_include_first_pages", 0))
        first_page_nums = {p["page_number"] for p in all_pages if always_n and p["page_number"] <= always_n}
        keep_set = keep_set | first_page_nums
        filtered_pages = [p for p in all_pages if p["page_number"] in keep_set]
    else:
        filtered_pages = all_pages

    sections = (store.get("cut_plan") or {}).get("sections", [])
    max_chars = int(ontology_cfg.get("max_input_chars", 600000))
    max_pages_per_chunk = int(ontology_cfg.get("max_pages_per_chunk", 30))

    page_chunks = _split_pages_by_section(filtered_pages, sections, max_chars, max_pages_per_chunk)
    logger.info(
        "[ontology] Drafting from %d pages, %d sections → %d chunk(s)",
        len(filtered_pages), len(sections), len(page_chunks),
    )

    _chunk_semaphore = asyncio.Semaphore(5)

    async def _process_chunk(idx, chunk_pages, chunk_sections):
        chunk_header = _build_section_header(chunk_sections) if chunk_sections else _build_section_header(sections)
        chunk_text = format_text_with_pages(chunk_pages)
        if chunk_header:
            chunk_text = chunk_header + "\n\n" + chunk_text

        page_nums = [p["page_number"] for p in chunk_pages]
        logger.info(
            "[ontology] Chunk %d/%d — %d sections, pages %d-%d (%d chars)",
            idx, len(page_chunks),
            len(chunk_sections),
            min(page_nums), max(page_nums),
            len(chunk_text),
        )
        async with _chunk_semaphore:
            result, metrics = await asyncio.to_thread(
                build_initial_ontology,
                text_with_pages=chunk_text,
                source_type=req.source_type,
                source_title=req.source_title,
                target_language=req.target_language,
                model_name=req.model_name,
            )
        metrics["chunk_index"] = idx
        metrics["chunk_pages"] = len(chunk_pages)
        metrics["section_count"] = len(chunk_sections)
        return result, metrics

    tasks = [
        _process_chunk(idx, chunk_pages, chunk_sections)
        for idx, (chunk_pages, chunk_sections) in enumerate(page_chunks, start=1)
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

    result = _merge_pipeline_results(chunk_results)
    total_prompt_tokens = sum(int(item.get("prompt_tokens", 0) or 0) for item in chunk_metrics)
    total_cached_prompt_tokens = sum(int(item.get("cached_prompt_tokens", 0) or 0) for item in chunk_metrics)
    total_non_cached_prompt_tokens = sum(int(item.get("non_cached_prompt_tokens", 0) or 0) for item in chunk_metrics)
    total_completion_tokens = sum(int(item.get("completion_tokens", 0) or 0) for item in chunk_metrics)
    total_tokens = sum(int(item.get("total_tokens", 0) or 0) for item in chunk_metrics)
    total_llm_calls = sum(int(item.get("llm_calls", 0) or 0) for item in chunk_metrics)
    total_retries = sum(int(item.get("retry_count", 0) or 0) for item in chunk_metrics)
    total_cost_usd = round(sum(float(item.get("estimated_cost_usd", 0) or 0) for item in chunk_metrics), 6)
    models = sorted({
        model
        for item in chunk_metrics
        for model in item.get("models", [])
        if model
    })
    operations = sorted({
        op
        for item in chunk_metrics
        for op in item.get("operations", [])
        if op
    })

    record_stage_metrics(
        pdf_store[req.pdf_id],
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
            },
        },
    )
    pdf_store[req.pdf_id]["source_type"] = req.source_type
    pdf_store[req.pdf_id]["source_title"] = req.source_title
    pdf_store[req.pdf_id]["ontology_pipeline"] = result.model_dump()
    return result


@router.get("/{pdf_id}", response_model=OntologyPipelineResponse)
async def get_ontology_state(pdf_id: str):
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    pipeline_state = pdf_store[pdf_id].get("ontology_pipeline")
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Ontology pipeline has not been run yet.")
    return OntologyPipelineResponse.model_validate(pipeline_state)


@router.post("/review", response_model=OntologyPipelineResponse)
async def review_ontology(req: OntologyReviewRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    pipeline_state = pdf_store[req.pdf_id].get("ontology_pipeline")
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Run /ontology/draft first.")
    existing = OntologyPipelineResponse.model_validate(pipeline_state)
    try:
        result = apply_human_binding(existing.ontology, req.answers)
    except RuntimeError as exc:
        detail = str(exc)
        status_code = 408 if "stopped after" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    if existing.semantic_issues:
        result.semantic_issues = existing.semantic_issues
    pdf_store[req.pdf_id]["ontology_pipeline"] = result.model_dump()
    return result


@router.post("/apply-suggestions", response_model=OntologyPipelineResponse)
async def apply_suggestions(req: ApplySuggestionsRequest):
    """Apply operator-accepted suggested relations to the ontology instance.

    The operator reviews the graph_reasoning suggestions in the frontend,
    accepts a subset, and this endpoint merges them into the stored ontology
    before re-running graph analysis and schema validation.
    """
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    pipeline_state = pdf_store[req.pdf_id].get("ontology_pipeline")
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Run /ontology/draft first.")

    existing = OntologyPipelineResponse.model_validate(pipeline_state)
    ontology_data = deepcopy(existing.ontology.model_dump())

    # Build existing edge set to avoid duplicates
    existing_edges: set[tuple[str, str, str]] = {
        (r["name"], r["from_id"], r["to_id"])
        for r in ontology_data.get("relations", [])
    }

    for suggestion in req.accepted_suggestions:
        edge_key = (suggestion.relation_name, suggestion.from_id, suggestion.to_id)
        if edge_key in existing_edges:
            continue
        ontology_data["relations"].append({
            "name": suggestion.relation_name,
            "from_type": suggestion.from_type,
            "from_id": suggestion.from_id,
            "to_type": suggestion.to_type,
            "to_id": suggestion.to_id,
            "evidence": [],
        })
        existing_edges.add(edge_key)

    from backend.models import OntologyInstance
    updated_ontology = OntologyInstance.model_validate(ontology_data)

    # Re-run validation and graph analysis on the updated ontology
    schema = load_ontology_schema()
    schema_issues, human_fields = validate_ontology_instance(updated_ontology)
    graph_issues, suggested_relations = run_graph_analysis(updated_ontology, schema)

    result = OntologyPipelineResponse(
        status="blocked" if schema_issues else ("needs_human" if human_fields else "ready"),
        ontology=updated_ontology,
        semantic_issues=existing.semantic_issues,
        schema_issues=schema_issues,
        human_required_fields=human_fields,
        is_schema_compliant=not schema_issues and not human_fields,
        is_ready_for_human_review=not schema_issues,
        retry_count=existing.retry_count,
        graph_issues=graph_issues,
        suggested_relations=suggested_relations,
    )
    pdf_store[req.pdf_id]["ontology_pipeline"] = result.model_dump()
    return result


@router.post("/export")
async def export_ontology(req: OntologyExportRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    pipeline_state = pdf_store[req.pdf_id].get("ontology_pipeline")
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Run /ontology/draft first.")
    result = OntologyPipelineResponse.model_validate(pipeline_state)
    if result.schema_issues or result.human_required_fields:
        detail = {
            "message": "Ontology is not exportable yet.",
            "schema_issues": [issue.model_dump() for issue in result.schema_issues],
            "human_required_fields": [field.model_dump() for field in result.human_required_fields],
        }
        raise HTTPException(status_code=409, detail=json.dumps(detail, ensure_ascii=False))
    try:
        json_str = ontology_export_payload(result.ontology)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=ontology_instance.json"},
    )
