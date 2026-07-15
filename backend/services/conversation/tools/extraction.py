"""Extraction tools: run extraction and re-extract page ranges.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

import asyncio

from backend.services.conversation.tools.common import (
    _build_review_graph_payload,
)


async def _run_extraction(args, store, on_event):
    from backend.graph.store import set_run_progress, update_extraction_state
    from backend.models import ExtractRequest
    from backend.services.extraction_workflow import extract_triplets_workflow

    # Flip the status immediately so the console stops showing "your turn"
    # while the (long) extraction is running.
    set_run_progress(store, run_status="in_progress", next_step="extraction")

    req = ExtractRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type", ""),
        source_title=store.get("source_title", ""),
        model_name=(store.get("selected_models") or {}).get("extraction") or None,
        pages_to_keep=(store.get("cut_plan") or {}).get("pages_to_keep"),
        target_language=store.get("target_language", "en"),
    )
    result, chunk_metadata = await asyncio.to_thread(
        extract_triplets_workflow, store, req, on_event
    )
    pages_to_keep = req.pages_to_keep or [p["page_number"] for p in store.get("pages", [])]
    update_extraction_state(
        store,
        result,
        model_name=str(req.model_name or ""),
        chunk_metadata=chunk_metadata,
        pages_to_keep=pages_to_keep,
    )
    triplets = [triplet.model_dump() for triplet in result.triplets]
    from backend.graph.store import set_run_progress
    # Triplets are extracted; the ball is in the operator's court (review).
    set_run_progress(store, run_status="awaiting_operator", next_step="review")
    return {
        "status": "ok",
        "triplet_count": len(result.triplets),
        "message": f"Extraction complete — {len(result.triplets)} triplet(s) ready for review.",
        "graph": _build_review_graph_payload(store, focus_index=0 if triplets else None),
        "widget": "extraction_graph",
    }


async def _re_extract_pages(args, store, on_event):
    from backend.models import ExtractRequest
    from backend.services.extraction_workflow import extract_triplets_workflow

    start = args["start_page"]
    end = args["end_page"]
    hint = str(args.get("hint", "") or "").strip()

    pages = store.get("pages") or []
    target_pages = [p for p in pages if start <= p["page_number"] <= end]
    if not target_pages:
        return {"status": "error", "message": f"No pages found in range {start}–{end}."}

    # Temporarily override pages_to_keep for this sub-extraction
    fake_store = dict(store)
    fake_store["pages"] = target_pages
    fake_store["cut_plan"] = {**(store.get("cut_plan") or {}), "pages_to_keep": [p["page_number"] for p in target_pages]}

    req_kwargs = {
        "pdf_id": store["pdf_id"],
        "source_type": store.get("source_type", ""),
        "source_title": store.get("source_title", ""),
        "target_language": store.get("target_language", "en"),
        "hint": hint,
        "force_llm": True,
    }
    selected_model = (store.get("selected_models") or {}).get("extraction")
    if selected_model:
        req_kwargs["model_name"] = selected_model
    req = ExtractRequest(**req_kwargs)
    new_result, _ = await asyncio.to_thread(extract_triplets_workflow, fake_store, req, on_event)

    # Merge new triplets with existing ones
    gs = store.get("graph_state") or {}
    existing_triplets = gs.get("cleaned_triplets") or []

    # Filter out triplets from the re-extracted page range in the existing set
    kept = [
        t for t in existing_triplets
        if not (start <= int((t.get("symptom") or {}).get("evidence_page", 0) or 0) <= end)
    ]
    added = [t.model_dump() for t in new_result.triplets]
    merged_triplets = kept + added

    gs["cleaned_triplets"] = merged_triplets
    store["graph_state"] = gs

    return {
        "status": "ok",
        "new_triplets": len(added),
        "total_triplets": len(merged_triplets),
        "message": f"Re-extracted pages {start}–{end}: found {len(added)} triplet(s).",
    }
