from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from backend.services.ontology_export_store import LATEST_ONTOLOGY_PATH, ontology_path_for_pdf
from backend.services.graph_editor_validation import validate_node_update, validate_relationship_add
from backend.routers.upload import pdf_store
from modify.graph import _build_id_to_info, _find_node_id_key, _node_id, _node_label, build_graph
from modify.schema import load_schema
from modify.state import load_ontology, ontology_version, relation_items, save_ontology_to_path
from modify.template import render_html

router = APIRouter(prefix="/graph-editor", tags=["graph-editor"])

_editor_sessions: dict[str, dict[str, Any]] = {}


def _resolve_ontology_path(pdf_id: str | None) -> Path:
    if not pdf_id or pdf_id == "latest":
        path = LATEST_ONTOLOGY_PATH
    elif pdf_id in pdf_store and pdf_store[pdf_id].get("ontology_path"):
        path = Path(pdf_store[pdf_id]["ontology_path"])
    else:
        path = ontology_path_for_pdf(pdf_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Ontology export not found for '{pdf_id or 'latest'}'.")
    return path


def _get_session(path: Path) -> dict[str, Any]:
    key = str(path)
    mtime = path.stat().st_mtime
    session = _editor_sessions.get(key)
    if session is None or session["mtime"] != mtime:
        session = {
            "ontology": load_ontology(path),
            "dirty": False,
            "mtime": mtime,
        }
        _editor_sessions[key] = session
    return session


def _mark_dirty(path: Path) -> None:
    _editor_sessions[str(path)]["dirty"] = True


def _current_ontology(path: Path) -> dict[str, Any]:
    return _get_session(path)["ontology"]


def _save_session(pdf_id: str, path: Path) -> dict[str, Any]:
    session = _get_session(path)
    result = save_ontology_to_path(session["ontology"], path)
    new_path = Path(result["target_path"])
    session["dirty"] = False
    session["mtime"] = new_path.stat().st_mtime
    _editor_sessions.pop(str(path), None)
    _editor_sessions[str(new_path)] = session
    if pdf_id in pdf_store:
        pdf_store[pdf_id]["ontology_path"] = str(new_path)
    return result


def _safe_ontology_name(path: Path) -> str:
    try:
        return str(_current_ontology(path).get("ontology_name", "Ontology graph"))
    except Exception:
        return "Ontology graph"


@router.get("", response_class=HTMLResponse)
async def latest_graph_editor() -> HTMLResponse:
    path = _resolve_ontology_path("latest")
    return HTMLResponse(render_html(_safe_ontology_name(path), api_base="/graph-editor/latest/api"))


@router.get("/{pdf_id}", response_class=HTMLResponse)
async def graph_editor_page(pdf_id: str) -> HTMLResponse:
    path = _resolve_ontology_path(pdf_id)
    return HTMLResponse(render_html(_safe_ontology_name(path), api_base=f"/graph-editor/{pdf_id}/api"))


@router.get("/{pdf_id}/api/data")
async def data_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    return build_graph(_current_ontology(path))


@router.get("/{pdf_id}/api/schema")
async def schema_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    return load_schema(_current_ontology(path))


@router.get("/{pdf_id}/api/node/{node_id}")
async def node_detail(pdf_id: str, node_id: str):
    path = _resolve_ontology_path(pdf_id)
    ont = _current_ontology(path)
    id_info = _build_id_to_info(ont)

    found_obj = None
    found_type = None
    for ntype, items in ont.get("nodes", {}).items():
        for obj in items:
            if _node_id(obj) == node_id:
                found_obj = obj
                found_type = ntype
                break
        if found_obj:
            break

    if not found_obj:
        raise HTTPException(status_code=404, detail="Node not found.")

    schema = load_schema(ont)
    schema_props = schema.get("node_types", {}).get(found_type, [])
    merged_attrs = {}
    for prop in schema_props:
        merged_attrs[prop["name"]] = found_obj.get(prop["name"], "")
    for key, value in found_obj.items():
        merged_attrs.setdefault(key, value)
    for key, value in merged_attrs.items():
        found_obj.setdefault(key, value)

    rels_out = []
    rels_in = []
    for idx, rel in enumerate(relation_items(ont)):
        if str(rel.get("from_id", "")) == node_id:
            to_id = str(rel.get("to_id", ""))
            info = id_info.get(to_id, {"type": "?", "label": to_id})
            rels_out.append({
                "index": idx,
                "type": rel.get("name", rel.get("type", "")),
                "to_id": to_id,
                "to_label": info["label"],
                "to_type": info["type"],
            })
        elif str(rel.get("to_id", "")) == node_id:
            from_id = str(rel.get("from_id", ""))
            info = id_info.get(from_id, {"type": "?", "label": from_id})
            rels_in.append({
                "index": idx,
                "type": rel.get("name", rel.get("type", "")),
                "from_id": from_id,
                "from_label": info["label"],
                "from_type": info["type"],
            })

    return {
        "id": node_id,
        "type": found_type,
        "attributes": merged_attrs,
        "relationships_out": rels_out,
        "relationships_in": rels_in,
    }


@router.post("/{pdf_id}/api/node/{node_id}/update")
async def node_update(pdf_id: str, node_id: str, body: dict[str, Any]):
    path = _resolve_ontology_path(pdf_id)
    ont = _current_ontology(path)
    new_attrs = body.get("attributes", {})
    schema = load_schema(ont)

    try:
        ntype, updated = validate_node_update(ont, schema, node_id, new_attrs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    for current_type, items in ont.get("nodes", {}).items():
        for obj in items:
            if _node_id(obj) == node_id:
                id_key = _find_node_id_key(obj)
                obj.clear()
                obj.update(updated)
                if id_key and id_key not in obj:
                    obj[id_key] = node_id
                _mark_dirty(path)
                label = _node_label(obj, node_id)
                return {
                    "ok": True,
                    "vis_node": {
                        "id": node_id,
                        "label": label,
                        "group": current_type,
                        "title": f"{current_type}: {label}<br><code>{node_id}</code>",
                    },
                }

    raise HTTPException(status_code=404, detail="Node not found.")


@router.post("/{pdf_id}/api/node/{node_id}/delete")
async def node_delete(pdf_id: str, node_id: str):
    path = _resolve_ontology_path(pdf_id)
    ont = _current_ontology(path)

    removed = False
    for _, items in ont.get("nodes", {}).items():
        for index, obj in enumerate(items):
            if _node_id(obj) == node_id:
                items.pop(index)
                removed = True
                break
        if removed:
            break

    if not removed:
        raise HTTPException(status_code=404, detail="Node not found.")

    rels = relation_items(ont)
    ont["relations"] = [
        rel for rel in rels
        if str(rel.get("from_id", "")) != node_id and str(rel.get("to_id", "")) != node_id
    ]
    removed_rels = len(rels) - len(ont["relations"])
    _mark_dirty(path)
    return {"ok": True, "removed_relationships": removed_rels}


@router.post("/{pdf_id}/api/relationship/add")
async def relationship_add(pdf_id: str, body: dict[str, Any]):
    path = _resolve_ontology_path(pdf_id)
    ont = _current_ontology(path)
    rtype = body.get("type", "")
    from_id = body.get("from_id", "")
    to_id = body.get("to_id", "")
    schema = load_schema(ont)

    try:
        from_type, to_type = validate_relationship_add(ont, schema, rtype, from_id, to_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    relation_items(ont).append({
        "name": rtype,
        "from_id": from_id,
        "to_id": to_id,
        "from_type": from_type,
        "to_type": to_type,
        "evidence": [],
    })
    _mark_dirty(path)
    idx = len(relation_items(ont)) - 1
    return {
        "ok": True,
        "edge": {
            "id": f"e{idx}",
            "from": from_id,
            "to": to_id,
            "label": rtype,
            "title": rtype,
            "arrows": "to",
        },
    }


@router.post("/{pdf_id}/api/relationship/{index}/delete")
async def relationship_delete(pdf_id: str, index: int):
    path = _resolve_ontology_path(pdf_id)
    ont = _current_ontology(path)
    rels = relation_items(ont)
    if index < 0 or index >= len(rels):
        raise HTTPException(status_code=400, detail="Invalid index")
    removed = rels.pop(index)
    _mark_dirty(path)
    return {"ok": True, "removed": removed}


@router.post("/{pdf_id}/api/save")
async def save_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    try:
        return _save_session(pdf_id, path)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{pdf_id}/api/status")
async def status_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    session = _get_session(path)
    return {
        "has_unsaved_changes": session["dirty"],
        "version": ontology_version(session["ontology"]),
    }


@router.get("/{pdf_id}/api/all_nodes")
async def all_nodes_endpoint(pdf_id: str):
    path = _resolve_ontology_path(pdf_id)
    ont = _current_ontology(path)
    result = []
    for ntype, items in ont.get("nodes", {}).items():
        for obj in items:
            node_id = _node_id(obj)
            if node_id:
                result.append({"id": node_id, "label": _node_label(obj, node_id), "type": ntype})
    return result
