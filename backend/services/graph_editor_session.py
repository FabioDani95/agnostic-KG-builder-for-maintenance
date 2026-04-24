from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.services.graph_editor_validation import (
    validate_node_update,
    validate_relationship_add,
)
from backend.services.ontology_export_store import (
    LATEST_ONTOLOGY_PATH,
    ontology_path_for_pdf,
)
from modify.graph import (
    _build_id_to_info,
    _find_node_id_key,
    _node_id,
    _node_label,
    build_graph,
)
from modify.schema import load_schema
from modify.state import (
    load_ontology,
    ontology_version,
    relation_items,
    save_ontology_to_path,
)

_editor_sessions: dict[str, dict[str, Any]] = {}


def resolve_ontology_path(pdf_id: str | None, store: dict[str, Any] | None = None) -> Path:
    if not pdf_id or pdf_id == "latest":
        path = LATEST_ONTOLOGY_PATH
    elif store and store.get("ontology_path"):
        path = Path(store["ontology_path"])
    else:
        path = ontology_path_for_pdf(pdf_id)

    if not path.exists():
        raise FileNotFoundError(f"Ontology export not found for '{pdf_id or 'latest'}'.")
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
    _get_session(path)["dirty"] = True


def current_ontology(path: Path) -> dict[str, Any]:
    return _get_session(path)["ontology"]


def safe_ontology_name(path: Path) -> str:
    try:
        return str(current_ontology(path).get("ontology_name", "Ontology graph"))
    except Exception:
        return "Ontology graph"


def graph_payload(path: Path) -> dict[str, Any]:
    return build_graph(current_ontology(path))


def schema_payload(path: Path) -> dict[str, Any]:
    return load_schema(current_ontology(path))


def node_detail_payload(path: Path, node_id: str) -> dict[str, Any]:
    ont = current_ontology(path)
    id_info = _build_id_to_info(ont)

    found_obj = None
    found_type = None
    for node_type, items in ont.get("nodes", {}).items():
        for obj in items:
            if _node_id(obj) == node_id:
                found_obj = obj
                found_type = node_type
                break
        if found_obj:
            break

    if not found_obj:
        raise KeyError("Node not found.")

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


def update_node(path: Path, node_id: str, new_attrs: dict[str, Any]) -> dict[str, Any]:
    ont = current_ontology(path)
    schema = load_schema(ont)
    _, updated = validate_node_update(ont, schema, node_id, new_attrs)

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

    raise KeyError("Node not found.")


def delete_node(path: Path, node_id: str) -> dict[str, Any]:
    ont = current_ontology(path)

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
        raise KeyError("Node not found.")

    rels = relation_items(ont)
    ont["relations"] = [
        rel for rel in rels
        if str(rel.get("from_id", "")) != node_id and str(rel.get("to_id", "")) != node_id
    ]
    removed_rels = len(rels) - len(ont["relations"])
    _mark_dirty(path)
    return {"ok": True, "removed_relationships": removed_rels}


def add_relationship(path: Path, relation_type: str, from_id: str, to_id: str) -> dict[str, Any]:
    ont = current_ontology(path)
    schema = load_schema(ont)
    from_type, to_type = validate_relationship_add(ont, schema, relation_type, from_id, to_id)

    relation_items(ont).append({
        "name": relation_type,
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
            "label": relation_type,
            "title": relation_type,
            "arrows": "to",
        },
    }


def delete_relationship(path: Path, index: int) -> dict[str, Any]:
    ont = current_ontology(path)
    rels = relation_items(ont)
    if index < 0 or index >= len(rels):
        raise IndexError("Invalid index")
    removed = rels.pop(index)
    _mark_dirty(path)
    return {"ok": True, "removed": removed}


def save_session(path: Path, store: dict[str, Any] | None = None) -> dict[str, Any]:
    session = _get_session(path)
    result = save_ontology_to_path(session["ontology"], path)
    new_path = Path(result["target_path"])
    session["ontology"] = load_ontology(new_path)
    session["dirty"] = False
    session["mtime"] = new_path.stat().st_mtime
    _editor_sessions.pop(str(path), None)
    _editor_sessions[str(new_path)] = session
    if store is not None:
        store["ontology_path"] = str(new_path)
    return result


def status_payload(path: Path) -> dict[str, Any]:
    session = _get_session(path)
    return {
        "has_unsaved_changes": session["dirty"],
        "version": ontology_version(session["ontology"]),
    }


def all_nodes_payload(path: Path) -> list[dict[str, Any]]:
    ont = current_ontology(path)
    result = []
    for node_type, items in ont.get("nodes", {}).items():
        for obj in items:
            node_id = _node_id(obj)
            if node_id:
                result.append({
                    "id": node_id,
                    "label": _node_label(obj, node_id),
                    "type": node_type,
                })
    return result
