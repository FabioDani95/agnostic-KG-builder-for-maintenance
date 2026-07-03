from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from backend.graph.store import seed_conversation_state
from backend.services.conversation import events as evt_bus


def get_store(pdf_store: dict[str, dict], pdf_id: str) -> dict[str, Any]:
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    return pdf_store[pdf_id]


def prepare_chat_store(pdf_store: dict[str, dict], pdf_id: str) -> dict[str, Any]:
    store = get_store(pdf_store, pdf_id)
    seed_conversation_state(store)
    evt_bus.ensure_registered(pdf_id)
    return store


def apply_start_options(store: dict[str, Any], req: Any) -> None:
    if not req:
        return
    gs = store.setdefault("graph_state", {})
    sm = gs.setdefault("selected_models", {})
    if req.selected_scoping_model:
        sm["scoping"] = req.selected_scoping_model
    if req.selected_extraction_model:
        sm["extraction"] = req.selected_extraction_model
        sm["ontology_draft"] = req.selected_extraction_model
    if req.target_language:
        store["target_language"] = req.target_language
        gs["target_language"] = req.target_language
    if req.page_offset is not None:
        store["page_offset"] = req.page_offset
    store["selected_models"] = dict(sm)


def history_payload(pdf_id: str, store: dict[str, Any]) -> dict[str, Any]:
    conversation = store.get("conversation") or {}
    return {
        "pdf_id": pdf_id,
        "messages": [
            message
            for message in (conversation.get("messages") or [])
            if message.get("role") in ("user", "assistant")
        ],
    }


def exported_ontology_path(store: dict[str, Any]) -> Path:
    path_value = store.get("ontology_path")
    if not path_value:
        raise HTTPException(status_code=404, detail="No exported ontology is available yet.")
    path = Path(str(path_value))
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Exported ontology file was not found.")
    return path
