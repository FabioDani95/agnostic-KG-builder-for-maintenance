from __future__ import annotations

import copy
import json
import logging
import re
from pathlib import Path
from typing import Any

from httpx import Timeout
from openai import OpenAI

from backend.app_config import get_graph_cocreator_config
from backend.config import settings
from backend.services.graph_editor_validation import (
    _node_id_key_from_schema,
    _node_index,
    validate_node_create,
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

logger = logging.getLogger(__name__)
_editor_sessions: dict[str, dict[str, Any]] = {}
_openai_client_cache: dict[tuple[str, float], OpenAI] = {}


def _get_openai_client(api_key: str, timeout_seconds: float) -> OpenAI:
    key = (api_key or "", float(timeout_seconds))
    client = _openai_client_cache.get(key)
    if client is None:
        client = OpenAI(api_key=api_key, timeout=Timeout(timeout_seconds, connect=5.0))
        _openai_client_cache[key] = client
    return client


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


def _vis_node(node_id: str, node_type: str, node: dict[str, Any]) -> dict[str, str]:
    label = _node_label(node, node_id)
    return {
        "id": node_id,
        "label": label,
        "group": node_type,
        "title": f"{node_type}: {label}<br><code>{node_id}</code>",
    }


def create_node(
    path: Path,
    node_type: str,
    attrs: dict[str, Any],
    relationships: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ont = current_ontology(path)
    schema = load_schema(ont)
    node_type = str(node_type or "").strip()
    node_id, new_node = validate_node_create(ont, schema, node_type, attrs)

    proposed = copy.deepcopy(ont)
    proposed.setdefault("nodes", {}).setdefault(node_type, []).append(copy.deepcopy(new_node))

    normalized_relationships: list[dict[str, Any]] = []
    for rel in relationships or []:
        if not isinstance(rel, dict):
            continue
        relation_type = str(rel.get("type") or rel.get("name") or "").strip()
        from_id = str(rel.get("from_id") or "").strip()
        to_id = str(rel.get("to_id") or "").strip()
        if not relation_type and not from_id and not to_id:
            continue
        from_type, to_type = validate_relationship_add(proposed, schema, relation_type, from_id, to_id)
        normalized_relationships.append({
            "name": relation_type,
            "from_id": from_id,
            "to_id": to_id,
            "from_type": from_type,
            "to_type": to_type,
            "evidence": rel.get("evidence") if isinstance(rel.get("evidence"), list) else [],
        })
        relation_items(proposed).append(copy.deepcopy(normalized_relationships[-1]))

    ont.setdefault("nodes", {}).setdefault(node_type, []).append(new_node)
    rel_items = relation_items(ont)
    first_edge_idx = len(rel_items)
    rel_items.extend(normalized_relationships)
    _mark_dirty(path)

    edges = []
    for offset, rel in enumerate(normalized_relationships):
        rel_type = str(rel.get("name", rel.get("type", "REL")))
        edges.append({
            "id": f"e{first_edge_idx + offset}",
            "from": str(rel.get("from_id", "")),
            "to": str(rel.get("to_id", "")),
            "label": rel_type,
            "title": rel_type,
            "arrows": "to",
        })

    return {
        "ok": True,
        "node_id": node_id,
        "node": new_node,
        "vis_node": _vis_node(node_id, node_type, new_node),
        "all_node": {
            "id": node_id,
            "label": _node_label(new_node, node_id),
            "type": node_type,
        },
        "edges": edges,
    }


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


_TYPE_KEYWORDS = {
    "Asset": ("asset", "machine", "system", "robot", "printer", "controller", "model", "brand"),
    "Component": ("component", "pump", "motor", "sensor", "valve", "filter", "axis", "unit", "circuit", "module"),
    "Symptom": ("symptom", "alarm", "error", "warning", "issue", "problem", "low", "high", "leak", "noise", "overheat", "unstable"),
    "FailureMode": ("cause", "failure", "fault", "wear", "blocked", "broken", "damaged", "contamination", "misalignment", "loss"),
    "CorrectiveAction": ("replace", "clean", "inspect", "adjust", "reset", "tighten", "check", "verify", "calibrate", "procedure"),
    "ErrorCode": ("error code", "fault code", "alarm code", "code", "e-", "err", "alarm"),
}

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "if", "in", "into",
    "is", "it", "of", "on", "or", "the", "this", "to", "with", "without", "when", "while",
    "il", "lo", "la", "gli", "le", "un", "una", "uno", "e", "o", "di", "del", "della",
    "dei", "delle", "che", "con", "per", "nel", "nella", "quando", "se", "su", "da",
}


def _text_tokens(*values: Any) -> set[str]:
    text = " ".join(str(value or "") for value in values)
    tokens = {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}", text)
    }
    return {token for token in tokens if token not in _STOPWORDS}


def _first_sentence(text: str) -> str:
    clean = _SPACE_RE.sub(" ", str(text or "")).strip()
    if not clean:
        return ""
    parts = re.split(r"(?<=[.!?])\s+|[\n;]+", clean, maxsplit=1)
    return parts[0].strip(" .;:-")


def _title_from_text(text: str, max_words: int = 7) -> str:
    sentence = _first_sentence(text)
    if not sentence:
        return ""
    words = sentence.split()
    title = " ".join(words[:max_words]).strip(" .,:;")
    return title[:1].upper() + title[1:] if title else ""


def _infer_severity(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ("critical", "severe", "high", "blocking", "danger", "grave", "alto")):
        return "High"
    if any(term in lowered for term in ("low", "minor", "warning", "basso", "lieve")):
        return "Low"
    return "Medium"


def _infer_category(text: str) -> str:
    lowered = text.lower()
    categories = (
        ("Hydraulics", ("hydraulic", "pressure", "pump", "valve", "oil", "idraulic")),
        ("Electrical", ("electrical", "voltage", "current", "cable", "power", "motor", "elettric")),
        ("Pneumatics", ("air", "pneumatic", "compressed", "pressure", "pneumatic")),
        ("Control", ("controller", "plc", "cnc", "software", "parameter", "axis")),
        ("Mechanical", ("bearing", "belt", "shaft", "gear", "wear", "mechanic")),
        ("Safety", ("safety", "guard", "interlock", "emergency")),
    )
    for label, keywords in categories:
        if any(keyword in lowered for keyword in keywords):
            return label
    return "General"


def _relation_description(schema: dict[str, Any], relation_type: str) -> str:
    constraint = schema.get("relation_constraints", {}).get(relation_type, {})
    domain = ", ".join(constraint.get("domain") or [])
    range_ = ", ".join(constraint.get("range") or [])
    if domain or range_:
        return f"{domain or 'Any'} -> {range_ or 'Any'}"
    return "Schema-compatible relationship"


def _suggest_next_node_id(ontology: dict[str, Any], schema: dict[str, Any], node_type: str) -> str:
    id_key = _node_id_key_from_schema(node_type, schema)
    prefix_map = {
        "asset_id": "ASSET",
        "component_id": "CMP",
        "symptom_id": "SYM",
        "failure_mode_id": "FM",
        "action_id": "CA",
        "error_code_id": "ERR",
    }
    prefix = prefix_map.get(id_key)
    if not prefix:
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", node_type)
        prefix = ("".join(word[0] for word in words) or node_type[:3]).upper()
    existing = {_node_id(item) for items in ontology.get("nodes", {}).values() for item in items}
    existing.discard(None)
    max_seen = 0
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$", re.IGNORECASE)
    for node_id in existing:
        match = pattern.match(str(node_id))
        if match:
            max_seen = max(max_seen, int(match.group(1)))
    candidate_index = max_seen + 1
    while True:
        candidate = f"{prefix}-{candidate_index:03d}"
        if candidate not in existing:
            return candidate
        candidate_index += 1


def _score_node_type(text: str, node_type: str) -> float:
    lowered = text.lower()
    score = 0.0
    for keyword in _TYPE_KEYWORDS.get(node_type, ()):
        if keyword in lowered:
            score += 2.0 if " " in keyword else 1.0
    if node_type.lower() in lowered:
        score += 2.0
    if node_type == "Symptom" and any(term in lowered for term in ("may indicate", "appears", "observed", "detected", "si vede", "appare")):
        score += 2.0
    if node_type == "FailureMode" and any(term in lowered for term in ("caused by", "due to", "root cause", "failure mode")):
        score += 2.0
    if node_type == "CorrectiveAction" and re.search(r"\b(replace|clean|inspect|adjust|reset|verify|check|calibrate)\b", lowered):
        score += 1.5
    if node_type == "ErrorCode" and re.search(r"\b(?:error|alarm|code)\s*[A-Z0-9_-]{2,}\b", text, re.IGNORECASE):
        score += 2.5
    return score


def _infer_node_type(schema: dict[str, Any], text: str, preferred_type: str | None = None) -> str:
    node_types = list(schema.get("node_types", {}).keys())
    if preferred_type in node_types:
        return str(preferred_type)
    ranked = sorted(
        node_types,
        key=lambda item: (-_score_node_type(text, item), node_types.index(item)),
    )
    return ranked[0] if ranked else "Node"


def _draft_attrs_for_type(
    ontology: dict[str, Any],
    schema: dict[str, Any],
    node_type: str,
    text: str,
) -> dict[str, Any]:
    props = schema.get("node_types", {}).get(node_type, [])
    id_key = _node_id_key_from_schema(node_type, schema)
    name = _title_from_text(text)
    description = _polish_text_value("description", text)
    attrs: dict[str, Any] = {}

    for prop in props:
        key = prop.get("name")
        if not key:
            continue
        if key == id_key:
            attrs[key] = _suggest_next_node_id(ontology, schema, node_type)
        elif key == "name":
            attrs[key] = name
        elif key == "description":
            attrs[key] = description
        elif key == "severity":
            attrs[key] = _infer_severity(text)
        elif key in {"category", "material_context"}:
            attrs[key] = _infer_category(text)
        elif key == "instruction_text":
            attrs[key] = description
        elif key == "source_type":
            attrs[key] = "operator_note"
        elif key == "source_title":
            attrs[key] = str(ontology.get("source_title") or ontology.get("metadata", {}).get("source_title") or "Co-created graph edit")
        elif key == "source_reference":
            attrs[key] = "Co-created in graph editor"
        elif key == "code":
            match = re.search(r"\b(?:error|alarm|code)?\s*([A-Z]{1,4}[-_]?\d{2,5}|\d{3,5})\b", text, re.IGNORECASE)
            attrs[key] = match.group(1).upper() if match else ""
        elif prop.get("type") == "array":
            attrs[key] = []
        else:
            attrs[key] = ""

    if not attrs and node_type:
        attrs = {
            id_key: _suggest_next_node_id(ontology, schema, node_type),
            "name": name,
            "description": description,
        }
    return attrs


def _required_missing(schema: dict[str, Any], node_type: str, attrs: dict[str, Any]) -> list[str]:
    missing = []
    for prop in schema.get("node_types", {}).get(node_type, []):
        if not prop.get("required"):
            continue
        key = prop["name"]
        value = attrs.get(key)
        if prop.get("type") == "array":
            if not isinstance(value, list) or not value:
                missing.append(key)
            continue
        if not str(value or "").strip():
            missing.append(key)
    return missing


def _node_attr_text(node: dict[str, Any]) -> str:
    parts = []
    for key in ("name", "description", "category", "material_context", "code", "instruction_text"):
        value = node.get(key)
        if value:
            parts.append(" ".join(str(item) for item in value) if isinstance(value, list) else str(value))
    return " ".join(parts)


def _duplicate_candidates(ontology: dict[str, Any], node_type: str, attrs: dict[str, Any]) -> list[dict[str, Any]]:
    draft_tokens = _text_tokens(attrs.get("name"), attrs.get("description"), attrs.get("code"))
    if not draft_tokens:
        return []
    candidates = []
    for item in ontology.get("nodes", {}).get(node_type, []):
        item_tokens = _text_tokens(_node_label(item, ""), _node_attr_text(item))
        if not item_tokens:
            continue
        overlap = draft_tokens & item_tokens
        score = len(overlap) / max(1, len(draft_tokens | item_tokens))
        if score >= 0.2:
            node_id = _node_id(item)
            candidates.append({
                "node_id": node_id,
                "label": _node_label(item, str(node_id or "")),
                "score": round(score, 2),
                "reason": "similar wording in name or description",
            })
    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:5]


def _json_schema_context(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_types": schema.get("node_types", {}),
        "relation_constraints": schema.get("relation_constraints", {}),
    }


def _compact_existing_nodes(ontology: dict[str, Any], limit_per_type: int = 30) -> dict[str, list[dict[str, str]]]:
    compact: dict[str, list[dict[str, str]]] = {}
    for node_type, items in (ontology.get("nodes") or {}).items():
        compact[node_type] = [
            {
                "id": str(_node_id(item) or ""),
                "label": _node_label(item, ""),
                "text": _node_attr_text(item)[:240],
            }
            for item in list(items or [])[:limit_per_type]
            if _node_id(item)
        ]
    return compact


def _extract_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        raise ValueError("empty model response")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("model response must be a JSON object")
    return parsed


def _call_cocreator_json(
    system_prompt: str,
    user_payload: dict[str, Any],
    *,
    cfg: dict[str, Any],
    client: Any | None = None,
) -> dict[str, Any]:
    llm_client = client or _get_openai_client(
        settings.OPENAI_API_KEY,
        float(cfg.get("timeout_seconds", 12)),
    )
    response = llm_client.chat.completions.create(
        model=cfg.get("model") or settings.MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        temperature=float(cfg.get("temperature", 0.1)),
        max_completion_tokens=int(cfg.get("max_output_tokens", 1200)),
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    return _extract_json_payload(content or "")


def _llm_draft_payload(
    ontology: dict[str, Any],
    schema: dict[str, Any],
    text: str,
    preferred_type: str | None,
    *,
    cfg: dict[str, Any],
    client: Any | None = None,
) -> dict[str, Any] | None:
    system_prompt = (
        "You are Graph Co-Creator, a neuro-symbolic assistant for a maintenance knowledge graph. "
        "Return only JSON. Choose node_type only from schema.node_types. Fill attributes only with schema properties. "
        "Use concise maintenance terminology. Leave uncertain required fields as empty strings instead of inventing facts. "
        "Do not create relationships in this step."
    )
    payload = {
        "task": "draft_node",
        "operator_note": text,
        "preferred_type": preferred_type,
        "schema": _json_schema_context(schema),
        "existing_nodes_preview": _compact_existing_nodes(ontology, limit_per_type=12),
        "required_response_shape": {
            "node_type": "one schema node type",
            "attributes": {"schema_property": "value"},
            "rationale": "short reason",
        },
    }
    try:
        return _call_cocreator_json(system_prompt, payload, cfg=cfg, client=client)
    except Exception as exc:
        logger.info("Graph co-creator draft LLM fallback: %s", exc)
        return None


def _normalize_llm_draft(
    ontology: dict[str, Any],
    schema: dict[str, Any],
    text: str,
    preferred_type: str | None,
    llm_payload: dict[str, Any] | None,
) -> tuple[str, dict[str, Any], str, str]:
    schema_node_types = schema.get("node_types", {})
    fallback_type = _infer_node_type(schema, text, preferred_type)
    node_type = str((llm_payload or {}).get("node_type") or "").strip()
    if node_type not in schema_node_types:
        node_type = fallback_type

    base_attrs = _draft_attrs_for_type(ontology, schema, node_type, text)
    llm_attrs = (llm_payload or {}).get("attributes") or {}
    if not isinstance(llm_attrs, dict):
        llm_attrs = {}

    allowed = {
        str(prop.get("name"))
        for prop in schema_node_types.get(node_type, [])
        if prop.get("name")
    }
    for key, value in llm_attrs.items():
        if key in allowed:
            base_attrs[key] = value

    id_key = _node_id_key_from_schema(node_type, schema)
    if not str(base_attrs.get(id_key) or "").strip() or str(base_attrs.get(id_key)) in set(_node_index(ontology)):
        base_attrs[id_key] = _suggest_next_node_id(ontology, schema, node_type)

    rationale = str((llm_payload or {}).get("rationale") or "").strip()
    mode = "llm_symbolic" if llm_payload else "deterministic_symbolic"
    if not rationale:
        rationale = (
            f"Classified as {node_type} by the {'LLM co-creator' if llm_payload else 'symbolic fallback'} "
            "and normalized against the ontology schema."
        )
    return node_type, base_attrs, rationale, mode


def draft_node_from_text(
    path: Path,
    text: str,
    preferred_type: str | None = None,
    *,
    use_llm: bool = True,
    llm_client: Any | None = None,
) -> dict[str, Any]:
    clean_text = _SPACE_RE.sub(" ", str(text or "")).strip()
    if not clean_text:
        raise ValueError("text is required.")
    ont = current_ontology(path)
    schema = load_schema(ont)
    cfg = get_graph_cocreator_config()
    llm_payload = None
    if use_llm and cfg.get("llm_enabled", True):
        llm_payload = _llm_draft_payload(
            ont,
            schema,
            clean_text,
            preferred_type,
            cfg=cfg,
            client=llm_client,
        )
    node_type, attrs, rationale, mode = _normalize_llm_draft(
        ont,
        schema,
        clean_text,
        preferred_type,
        llm_payload,
    )
    missing = _required_missing(schema, node_type, attrs)
    duplicates = _duplicate_candidates(ont, node_type, attrs)
    return {
        "ok": True,
        "agent_mode": mode,
        "node_type": node_type,
        "attributes": attrs,
        "missing_fields": missing,
        "duplicate_candidates": duplicates,
        "rationale": rationale,
    }


def _compatible_relation_specs(schema: dict[str, Any], node_type: str) -> list[dict[str, str]]:
    specs = []
    for relation_type, constraint in (schema.get("relation_constraints") or {}).items():
        domains = constraint.get("domain") or []
        ranges = constraint.get("range") or []
        if not domains or node_type in domains:
            specs.append({"relation_type": relation_type, "direction": "out", "target_types": ranges})
        if not ranges or node_type in ranges:
            specs.append({"relation_type": relation_type, "direction": "in", "target_types": domains})
    return specs


def _relationship_reason(relation_type: str, target: dict[str, Any], overlap: set[str], schema: dict[str, Any]) -> str:
    label = _node_label(target, str(_node_id(target) or ""))
    if overlap:
        terms = ", ".join(sorted(overlap)[:4])
        return f"Shares context with '{label}' ({terms})."
    return f"Schema-compatible: {_relation_description(schema, relation_type)}."


def _symbolic_relationship_candidates(
    ontology: dict[str, Any],
    schema: dict[str, Any],
    node_type: str,
    attrs: dict[str, Any],
) -> list[dict[str, Any]]:
    draft_text = _node_attr_text(attrs or {})
    draft_tokens = _text_tokens(draft_text, attrs.get("name") if isinstance(attrs, dict) else "")
    specs = _compatible_relation_specs(schema, node_type)
    candidates: list[dict[str, Any]] = []

    for spec in specs:
        relation_type = spec["relation_type"]
        direction = spec["direction"]
        target_types = spec["target_types"] or list(ontology.get("nodes", {}).keys())
        for target_type in target_types:
            for target in ontology.get("nodes", {}).get(target_type, []):
                target_id = _node_id(target)
                if not target_id:
                    continue
                target_tokens = _text_tokens(_node_label(target, ""), _node_attr_text(target), target_type)
                overlap = draft_tokens & target_tokens
                base = 0.28 if overlap else 0.12
                schema_boost = 0.12
                relation_boost = 0.0
                if relation_type in {"MAY_INDICATE", "INDICATES"} and node_type in {"Symptom", "ErrorCode", "FailureMode"}:
                    relation_boost += 0.08
                if relation_type in {"AFFECTS", "HAS_COMPONENT"} and target_type == "Component":
                    relation_boost += 0.08
                if relation_type == "RESOLVED_BY" and (node_type == "CorrectiveAction" or target_type == "CorrectiveAction"):
                    relation_boost += 0.08
                overlap_boost = min(0.35, len(overlap) * 0.08)
                confidence = min(0.95, base + schema_boost + relation_boost + overlap_boost)
                from_id = "__NEW_NODE__" if direction == "out" else target_id
                to_id = target_id if direction == "out" else "__NEW_NODE__"
                candidates.append({
                    "candidate_id": f"c{len(candidates)}",
                    "relation_type": relation_type,
                    "direction": direction,
                    "from_id": from_id,
                    "to_id": to_id,
                    "target_id": target_id,
                    "target_label": _node_label(target, str(target_id)),
                    "target_type": target_type,
                    "confidence": round(confidence, 2),
                    "reason": _relationship_reason(relation_type, target, overlap, schema),
                    "symbolic_score": round(confidence, 2),
                })
    return candidates


def _rank_relationship_candidates_deterministic(
    candidates: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    ranked = sorted(
        candidates,
        key=lambda item: (-float(item["confidence"]), item["target_type"], item["target_label"]),
    )
    return ranked[: max(1, min(int(limit or 6), 20))]


def _llm_rank_relationship_candidates(
    schema: dict[str, Any],
    node_type: str,
    attrs: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    cfg: dict[str, Any],
    client: Any | None = None,
) -> list[dict[str, Any]] | None:
    system_prompt = (
        "You are Graph Co-Creator, ranking schema-valid relationship candidates for a maintenance KG. "
        "Return only JSON. Select only candidate_id values from the provided candidates. "
        "Do not invent relation types or target nodes. Confidence must be 0..1."
    )
    llm_top_k = max(1, int(cfg.get("relationship_llm_top_k", 12) or 12))
    llm_candidates = candidates[:llm_top_k]
    payload = {
        "task": "rank_relationship_candidates",
        "new_node": {
            "node_type": node_type,
            "attributes": attrs,
        },
        "schema_relation_constraints": schema.get("relation_constraints", {}),
        "candidates": [
            {
                "candidate_id": item["candidate_id"],
                "relation_type": item["relation_type"],
                "direction": item["direction"],
                "target_id": item["target_id"],
                "target_label": item["target_label"],
                "target_type": item["target_type"],
                "symbolic_score": item["symbolic_score"],
                "symbolic_reason": item["reason"],
            }
            for item in llm_candidates
        ],
        "required_response_shape": {
            "suggestions": [
                {
                    "candidate_id": "candidate id from candidates",
                    "confidence": 0.0,
                    "reason": "short maintenance-grounded reason",
                }
            ]
        },
    }
    try:
        parsed = _call_cocreator_json(system_prompt, payload, cfg=cfg, client=client)
    except Exception as exc:
        logger.info("Graph co-creator link LLM fallback: %s", exc)
        return None

    raw_suggestions = parsed.get("suggestions")
    if not isinstance(raw_suggestions, list):
        return None
    by_id = {item["candidate_id"]: item for item in candidates}
    ranked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_suggestions:
        if not isinstance(raw, dict):
            continue
        candidate_id = str(raw.get("candidate_id") or "")
        if candidate_id in seen or candidate_id not in by_id:
            continue
        item = copy.deepcopy(by_id[candidate_id])
        try:
            confidence = max(0.0, min(1.0, float(raw.get("confidence", item["confidence"]))))
        except (TypeError, ValueError):
            confidence = float(item["confidence"])
        reason = str(raw.get("reason") or "").strip()
        item["confidence"] = round(confidence, 2)
        if reason:
            item["reason"] = reason
        item["agent_mode"] = "llm_symbolic"
        ranked.append(item)
        seen.add(candidate_id)
    return ranked or None


def suggest_relationships(
    path: Path,
    node_type: str,
    attrs: dict[str, Any],
    limit: int = 6,
    *,
    use_llm: bool = True,
    llm_client: Any | None = None,
) -> dict[str, Any]:
    ont = current_ontology(path)
    schema = load_schema(ont)
    if node_type not in schema.get("node_types", {}):
        raise ValueError(f"Node type '{node_type}' is not defined in ontology_schema.JSON.")
    cfg = get_graph_cocreator_config()
    candidate_limit = int(cfg.get("relationship_candidate_limit", 30) or 30)
    candidates = _rank_relationship_candidates_deterministic(
        _symbolic_relationship_candidates(ont, schema, node_type, attrs if isinstance(attrs, dict) else {}),
        candidate_limit,
    )
    ranked = None
    if use_llm and cfg.get("llm_enabled", True) and candidates:
        ranked = _llm_rank_relationship_candidates(
            schema,
            node_type,
            attrs if isinstance(attrs, dict) else {},
            candidates,
            cfg=cfg,
            client=llm_client,
        )
    mode = "llm_symbolic" if ranked else "deterministic_symbolic"
    if not ranked:
        ranked = _rank_relationship_candidates_deterministic(candidates, limit)
    else:
        ranked = ranked[: max(1, min(int(limit or 6), 20))]
    for item in ranked:
        item.setdefault("agent_mode", mode)
    return {"ok": True, "agent_mode": mode, "suggestions": ranked}


_SPACE_RE = re.compile(r"\s+")
_SENTENCE_FIELD_TOKENS = ("description", "instruction", "context", "reference")


def _polish_text_value(key: str, value: Any) -> Any:
    if isinstance(value, list):
        return [_polish_text_value(key, item) for item in value]
    if not isinstance(value, str):
        return value
    polished = _SPACE_RE.sub(" ", value).strip()
    if not polished:
        return polished
    if key.endswith("_id") or key in {"code", "severity", "source_type"}:
        return polished
    if key == "name":
        return polished[:1].upper() + polished[1:]
    if any(token in key for token in _SENTENCE_FIELD_TOKENS):
        polished = polished[:1].upper() + polished[1:]
        if polished[-1] not in ".!?":
            polished += "."
    return polished


def polish_node_attributes(
    path: Path,
    node_type: str,
    attrs: dict[str, Any],
    fields: list[str] | None = None,
) -> dict[str, Any]:
    # The polishing step is intentionally deterministic here so the editor stays
    # usable without an LLM key. It trims, normalizes spacing, and lightly formats
    # human-readable text fields before validation/save.
    schema = load_schema(current_ontology(path))
    allowed_fields = {
        str(prop.get("name"))
        for prop in schema.get("node_types", {}).get(str(node_type or ""), [])
        if prop.get("name")
    }
    selected_fields = {str(field) for field in fields or [] if field}
    polished: dict[str, Any] = {}
    for key, value in (attrs or {}).items():
        if allowed_fields and key not in allowed_fields:
            polished[key] = value
            continue
        if selected_fields and key not in selected_fields:
            polished[key] = value
            continue
        polished[key] = _polish_text_value(key, value)
    return {"ok": True, "attributes": polished}
