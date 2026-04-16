"""Wrapper around the existing extraction workflow."""

from __future__ import annotations

from backend.graph.store import ensure_graph_state, update_extraction_state
from backend.services.extraction_workflow import extract_triplets_workflow


def _resolved_pages_to_keep(store: dict, req) -> list[int]:
    pages_to_keep = req.pages_to_keep or (store.get("cut_plan") or {}).get("pages_to_keep") or []
    if pages_to_keep:
        return list(pages_to_keep)
    return [page["page_number"] for page in store.get("pages", [])]


def run_extraction_agent(store: dict, req) -> object:
    ensure_graph_state(store, pdf_id=req.pdf_id)
    result, chunk_metadata = extract_triplets_workflow(store, req)
    update_extraction_state(
        store,
        result,
        model_name=req.model_name,
        chunk_metadata=chunk_metadata,
        pages_to_keep=_resolved_pages_to_keep(store, req),
    )
    return result
