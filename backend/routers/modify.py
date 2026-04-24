from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from backend.routers.upload import pdf_store
from backend.services import graph_editor_session
from modify.template import render_html

router = APIRouter(prefix="/modify", tags=["modify"])


def _resolve_ontology_path(pdf_id: str | None):
    try:
        return graph_editor_session.resolve_ontology_path(
            pdf_id,
            store=pdf_store.get(pdf_id) if pdf_id else None,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_class=HTMLResponse)
async def latest_modify_page() -> HTMLResponse:
    path = _resolve_ontology_path("latest")
    return HTMLResponse(render_html(graph_editor_session.safe_ontology_name(path), api_base="/modify/latest/api"))


@router.get("/{pdf_id}", response_class=HTMLResponse)
async def modify_page(pdf_id: str) -> HTMLResponse:
    path = _resolve_ontology_path(pdf_id)
    return HTMLResponse(render_html(graph_editor_session.safe_ontology_name(path), api_base=f"/modify/{pdf_id}/api"))


@router.get("/{pdf_id}/api/data")
async def data_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    return graph_editor_session.graph_payload(path)


@router.get("/{pdf_id}/api/schema")
async def schema_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    return graph_editor_session.schema_payload(path)


@router.get("/{pdf_id}/api/node/{node_id}")
async def node_detail(pdf_id: str, node_id: str):
    path = _resolve_ontology_path(pdf_id)
    try:
        return graph_editor_session.node_detail_payload(path, node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{pdf_id}/api/node/{node_id}/update")
async def node_update(pdf_id: str, node_id: str, body: dict[str, Any]):
    path = _resolve_ontology_path(pdf_id)
    try:
        return graph_editor_session.update_node(path, node_id, body.get("attributes", {}))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{pdf_id}/api/node/{node_id}/delete")
async def node_delete(pdf_id: str, node_id: str):
    path = _resolve_ontology_path(pdf_id)
    try:
        return graph_editor_session.delete_node(path, node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{pdf_id}/api/relationship/add")
async def relationship_add(pdf_id: str, body: dict[str, Any]):
    path = _resolve_ontology_path(pdf_id)
    try:
        return graph_editor_session.add_relationship(
            path,
            body.get("type", ""),
            body.get("from_id", ""),
            body.get("to_id", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{pdf_id}/api/relationship/{index}/delete")
async def relationship_delete(pdf_id: str, index: int):
    path = _resolve_ontology_path(pdf_id)
    try:
        return graph_editor_session.delete_relationship(path, index)
    except IndexError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{pdf_id}/api/save")
async def save_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    try:
        return graph_editor_session.save_session(path, store=pdf_store.get(pdf_id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{pdf_id}/api/status")
async def status_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    return graph_editor_session.status_payload(path)


@router.get("/{pdf_id}/api/all_nodes")
async def all_nodes_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    return graph_editor_session.all_nodes_payload(path)
