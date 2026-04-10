"""Wrapper around the existing extraction workflow."""

from __future__ import annotations

from backend.graph.store import ensure_graph_state, update_extraction_state
from backend.services.extraction_workflow import extract_triplets_workflow


def run_extraction_agent(store: dict, req) -> object:
    ensure_graph_state(store, pdf_id=req.pdf_id)
    result, chunk_metadata = extract_triplets_workflow(store, req)
    pages_to_keep = req.pages_to_keep or (store.get("cut_plan") or {}).get("pages_to_keep") or []
    if not pages_to_keep:
        pages_to_keep = [page["page_number"] for page in store.get("pages", [])]
    update_extraction_state(
        store,
        result,
        model_name=req.model_name,
        chunk_metadata=chunk_metadata,
        pages_to_keep=pages_to_keep,
    )
    return result
