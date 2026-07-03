"""Chat endpoints.

POST /chat/message   — user sends a text message; returns an SSE stream
POST /chat/action    — widget callback (user clicks a button in a chat widget)
GET  /chat/stream/{pdf_id} — subscribe to the SSE stream for a run
POST /chat/start/{pdf_id}  — kick off the conversation after manual load
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend.graph.store import seed_conversation_state
from backend.routers.upload import pdf_store
from backend.services.conversation import events as evt_bus
from backend.services.conversation.orchestrator import handle_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatStartRequest(BaseModel):
    selected_scoping_model: str | None = None
    selected_extraction_model: str | None = None
    target_language: str = "en"
    page_offset: int = 0


class ChatMessageRequest(BaseModel):
    pdf_id: str
    message: str


class ChatActionRequest(BaseModel):
    pdf_id: str
    action: str          # e.g. "approve_triplet", "approve_cut_plan"
    payload: dict = {}   # action-specific data
    client_action_id: str | None = None


# ── Start (auto-kick) ──────────────────────────────────────────────────

@router.post("/start/{pdf_id}")
async def start_chat(pdf_id: str, req: ChatStartRequest = None):
    """Begin the chat session for a loaded manual.

    Registers the event queue, seeds conversation state, applies model
    selections from the startup form, and fires the auto-start scoping.
    """
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")

    store = pdf_store[pdf_id]

    # Apply model selections and language from the startup form to the store
    if req:
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
        # Mirror back into store-level selected_models for tools that read it directly
        store["selected_models"] = dict(sm)

    seed_conversation_state(store)
    evt_bus.register(pdf_id)

    # Fire auto-start in background so the SSE stream can be opened immediately
    asyncio.create_task(
        handle_message(pdf_id, store, user_message=None, auto_start=True)
    )
    return {"status": "ok", "pdf_id": pdf_id}


# ── SSE stream ─────────────────────────────────────────────────────────

@router.get("/stream/{pdf_id}")
async def stream_chat(pdf_id: str):
    """SSE stream for the chat session of a given run."""
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")

    # Ensure queue exists (may have been registered by /start already)
    if pdf_id not in evt_bus._queues:
        evt_bus.register(pdf_id)

    async def event_generator():
        async for event in evt_bus.stream_events(pdf_id, timeout=3600.0):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: {\"type\": \"stream_closed\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── User message ───────────────────────────────────────────────────────

@router.post("/message")
async def post_message(req: ChatMessageRequest):
    """Handle a user text message. Fires the orchestrator in background;
    events are delivered via SSE."""
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")

    store = pdf_store[req.pdf_id]
    seed_conversation_state(store)

    if req.pdf_id not in evt_bus._queues:
        evt_bus.register(req.pdf_id)

    asyncio.create_task(
        handle_message(req.pdf_id, store, user_message=req.message)
    )
    return {"status": "ok"}


# ── Widget action ──────────────────────────────────────────────────────

@router.post("/action")
async def post_action(req: ChatActionRequest):
    """Handle a widget action (button click in the chat UI).

    Maps directly to a tool dispatch so the LLM is not needed for
    deterministic widget interactions.
    """
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")

    store = pdf_store[req.pdf_id]
    seed_conversation_state(store)

    if req.pdf_id not in evt_bus._queues:
        evt_bus.register(req.pdf_id)

    from backend.services.conversation.gate import check as gate_check

    on_event = evt_bus.make_on_event(req.pdf_id)
    tagged_on_event = _tag_client_action(on_event, req.client_action_id)
    ok, reason = gate_check(req.action, req.payload, store)
    if not ok:
        event = evt_bus.error_event(reason)
        if req.client_action_id:
            event["client_action_id"] = req.client_action_id
        await evt_bus.put(req.pdf_id, event)
        # Still send a natural-language explanation via the orchestrator
        asyncio.create_task(
            handle_message(
                req.pdf_id,
                store,
                user_message=f"[system: action '{req.action}' was blocked — {reason}]",
            )
        )
        return {"status": "refused", "reason": reason}

    asyncio.create_task(_run_action(req.pdf_id, store, req.action, req.payload, tagged_on_event))
    return {"status": "ok"}


# Actions that automatically chain to another tool on success
_CHAIN_ON_SUCCESS: dict[str, str] = {
    "approve_cut_plan": "draft_ontology",
    "run_extraction": "get_next_triplet",   # show first triplet immediately after extraction
    "approve_triplet": "get_next_triplet",
    "skip_triplet": "get_next_triplet",
}

_CHAIN_PREAMBLE: dict[str, str] = {
    "approve_cut_plan": "Section selection confirmed. Starting ontology draft now…",
    "run_extraction": "",
    "approve_triplet": "",
    "skip_triplet": "",
}


def _tag_client_action(on_event, client_action_id: str | None):
    if not client_action_id:
        return on_event

    def _emit(event: dict) -> None:
        tagged = dict(event)
        tagged["client_action_id"] = client_action_id
        on_event(tagged)

    return _emit


async def _run_action(pdf_id: str, store: dict, action: str, payload: dict, on_event) -> None:
    from backend.services.conversation.tools import dispatch

    on_event(evt_bus.progress_event(action, f"Running {action.replace('_', ' ')}…"))
    result = await dispatch(action, payload, store, on_event)
    if result.get("widget") and result["widget"] not in ("triplet_review_start",):
        on_event(evt_bus.widget_event(result["widget"], {k: v for k, v in result.items() if k != "widget"}))
    summary = result.get("message") or ""
    if summary:
        on_event(evt_bus.chat_delta_event(summary))

    # Auto-chain to next tool if applicable
    next_tool = _CHAIN_ON_SUCCESS.get(action)
    if next_tool and result.get("status") == "ok":
        preamble = _CHAIN_PREAMBLE.get(action, "")
        if preamble:
            on_event(evt_bus.chat_delta_event(preamble))
        next_result = await dispatch(next_tool, {}, store, on_event)
        if next_result.get("widget"):
            on_event(evt_bus.widget_event(next_result["widget"], {k: v for k, v in next_result.items() if k != "widget"}))
        next_msg = next_result.get("message") or ""
        if next_msg:
            on_event(evt_bus.chat_delta_event(next_msg))

    on_event(evt_bus.done_event())


# ── Conversation history ───────────────────────────────────────────────

@router.get("/history/{pdf_id}")
async def get_history(pdf_id: str):
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    store = pdf_store[pdf_id]
    conversation = store.get("conversation") or {}
    return {
        "pdf_id": pdf_id,
        "messages": [
            m for m in (conversation.get("messages") or [])
            if m.get("role") in ("user", "assistant")
        ],
    }


@router.get("/download/{pdf_id}")
async def download_export(pdf_id: str):
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    store = pdf_store[pdf_id]
    path_value = store.get("ontology_path")
    if not path_value:
        raise HTTPException(status_code=404, detail="No exported ontology is available yet.")
    path = Path(str(path_value))
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Exported ontology file was not found.")
    return FileResponse(
        path,
        media_type="application/json",
        filename=path.name,
    )
