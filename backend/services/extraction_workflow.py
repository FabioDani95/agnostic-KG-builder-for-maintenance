"""Reusable extraction workflow used by the multi-agent pipeline."""

from __future__ import annotations

import time
from typing import Any

from backend.app_config import get_extraction_config
from backend.models import ExtractionResult, ExtractRequest
from backend.services.llm_service import _split_page_chunks, extract_triplets_chunked
from backend.services.run_metrics import aggregate_usage, record_stage_metrics


def _build_chunk_metadata(pages: list[dict]) -> list[dict[str, Any]]:
    cfg = get_extraction_config()
    chunks = _split_page_chunks(
        pages=pages,
        max_pages=int(cfg.get("chunk_max_pages", 4)),
        overlap=int(cfg.get("chunk_page_overlap", 1)),
        max_chars=int(cfg.get("chunk_max_chars", 12000)),
    )
    return [
        {
            "chunk_index": index,
            "page_numbers": [page["page_number"] for page in chunk],
            "page_start": chunk[0]["page_number"],
            "page_end": chunk[-1]["page_number"],
            "page_count": len(chunk),
        }
        for index, chunk in enumerate(chunks, start=1)
        if chunk
    ]


def extract_triplets_workflow(
    store: dict,
    req: ExtractRequest,
    on_event=None,
) -> tuple[ExtractionResult, list[dict[str, Any]]]:
    """Run triplet extraction against one in-memory store entry."""
    t0 = time.perf_counter()
    pages = store["pages"]

    pages_to_keep = req.pages_to_keep or (store.get("cut_plan") or {}).get("pages_to_keep")
    if pages_to_keep:
        keep_set = set(pages_to_keep)
        pages = [page for page in pages if page["page_number"] in keep_set]

    sections = (store.get("cut_plan") or {}).get("sections", [])
    chunk_metadata = _build_chunk_metadata(pages)
    ontology_draft = (store.get("ontology_pipeline") or {}).get("ontology")

    # Fase A3 — unified extractor: when the draft graph already contains
    # diagnostic chains, derive the triplets to validate from the graph itself
    # instead of running a second, independent LLM extraction. The triplets keep
    # the graph's own ids, so export becomes an identity merge (no fuzzy id
    # reconciliation) and the operator validates exactly what was extracted.
    from backend.services.graph_projection_service import (
        graph_has_validatable_chains,
        project_graph_to_triplets,
    )

    if not req.force_llm and graph_has_validatable_chains(ontology_draft or {}):
        result = project_graph_to_triplets(
            ontology_draft,
            source_type=req.source_type,
            source_title=req.source_title,
        )
        usage_summary = {"chunk_count": 0, "projected_from_graph": True, **aggregate_usage([])}
    else:
        try:
            result, usage_summary = extract_triplets_chunked(
                pages=pages,
                source_type=req.source_type,
                source_title=req.source_title,
                target_language=req.target_language,
                model_name=req.model_name,
                sections=sections,
                ontology_draft=ontology_draft,
                on_event=on_event,
                hint=req.hint,
            )
        except RuntimeError as exc:
            detail = str(exc)
            raise RuntimeError(detail) from exc

    record_stage_metrics(
        store,
        "extraction",
        {
            "stage": "extraction",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            **usage_summary,
            "details": {
                "selected_pages": len(pages),
                "triplet_count": len(result.triplets),
                "source_type": req.source_type,
                "source_title": req.source_title,
                "chunk_count": len(chunk_metadata),
                "extraction_mode": (
                    "graph_projection" if usage_summary.get("projected_from_graph") else "llm_extraction"
                ),
            },
        },
    )
    store["source_type"] = req.source_type
    store["source_title"] = req.source_title
    return result, chunk_metadata
