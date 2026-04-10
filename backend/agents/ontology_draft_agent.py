"""Wrapper around the existing ontology-draft workflow."""

from __future__ import annotations

from backend.graph.store import ensure_graph_state, update_ontology_state
from backend.services.ontology_workflow import draft_ontology_workflow


async def run_ontology_draft_agent(store: dict, req) -> object:
    ensure_graph_state(store, pdf_id=req.pdf_id)
    result = await draft_ontology_workflow(store, req)
    update_ontology_state(store, result, model_name=req.model_name)
    return result
