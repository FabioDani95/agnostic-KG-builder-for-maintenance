"""Reusable extraction workflow shared by classic and multi-agent modes."""

from __future__ import annotations

import time
from typing import Any

from backend.app_config import get_extraction_config
from backend.models import ExtractRequest, ExtractionResult
from backend.services.llm_service import _split_page_chunks, extract_triplets_chunked
from backend.services.run_metrics import record_stage_metrics


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
) -> tuple[ExtractionResult, list[dict[str, Any]]]:
    """Run the existing extraction flow against a store entry."""
    t0 = time.perf_counter()
    pages = store["pages"]

    pages_to_keep = req.pages_to_keep or (store.get("cut_plan") or {}).get("pages_to_keep")
    if pages_to_keep:
        keep_set = set(pages_to_keep)
        pages = [page for page in pages if page["page_number"] in keep_set]

    sections = (store.get("cut_plan") or {}).get("sections", [])
    chunk_metadata = _build_chunk_metadata(pages)

    try:
        result, usage_summary = extract_triplets_chunked(
            pages=pages,
            source_type=req.source_type,
            source_title=req.source_title,
            target_language=req.target_language,
            model_name=req.model_name,
            sections=sections,
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
            },
        },
    )
    store["source_type"] = req.source_type
    store["source_title"] = req.source_title
    return result, chunk_metadata
