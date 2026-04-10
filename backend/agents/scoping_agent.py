"""Wrapper around the existing scoping workflow."""

from __future__ import annotations

from backend.graph.store import ensure_graph_state, update_scoping_state
from backend.services.scoping_workflow import create_cut_plan_workflow


def run_scoping_agent(store: dict, req) -> object:
    ensure_graph_state(store, pdf_id=req.pdf_id)
    result = create_cut_plan_workflow(store, req)
    update_scoping_state(store, result, model_name=req.model_name)
    return result
