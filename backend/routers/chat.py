from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.routers.upload import pdf_store
from backend.schemas.actions import HumanAction
from backend.services.conversation import actions as action_service
from backend.services.conversation import events as evt_bus
from backend.services.conversation import session as chat_session
from backend.services.conversation.orchestrator import handle_message

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatStartRequest(BaseModel):
    selected_scoping_model: str | None = None
    selected_extraction_model: str | None = None
    target_language: str = "en"
    # The printed-page offset is autodetected by the scoping workflow; this
    # field remains only as an expert override for pathological documents.
    page_offset: int | None = None


class ChatMessageRequest(BaseModel):
    pdf_id: str
    message: str


class ChatActionRequest(BaseModel):
    pdf_id: str
    action: str
    payload: dict = Field(default_factory=dict)
    client_action_id: str | None = None


@router.post("/start/{pdf_id}")
async def start_chat(pdf_id: str, req: ChatStartRequest = None):
    store = chat_session.prepare_chat_store(pdf_store, pdf_id)
    chat_session.apply_start_options(store, req)
    asyncio.create_task(handle_message(pdf_id, store, user_message=None, auto_start=True))
    return {"status": "ok", "pdf_id": pdf_id}


@router.get("/stream/{pdf_id}")
async def stream_chat(pdf_id: str):
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    evt_bus.ensure_registered(pdf_id)

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


@router.post("/message")
async def post_message(req: ChatMessageRequest):
    store = chat_session.prepare_chat_store(pdf_store, req.pdf_id)
    asyncio.create_task(handle_message(req.pdf_id, store, user_message=req.message))
    return {"status": "ok"}


@router.post("/action")
async def post_action(req: ChatActionRequest):
    store = chat_session.prepare_chat_store(pdf_store, req.pdf_id)
    on_event = evt_bus.make_on_event(req.pdf_id)
    outcome = action_service.run_action(
        req.pdf_id,
        store,
        HumanAction.model_validate(req.model_dump()),
        on_event,
    )
    if outcome.status == "refused":
        asyncio.create_task(
            handle_message(
                req.pdf_id,
                store,
                user_message=f"[system: action '{req.action}' was blocked — {outcome.reason}]",
            )
        )
        return {"status": "refused", "reason": outcome.reason}
    return {"status": "ok"}


@router.get("/history/{pdf_id}")
async def get_history(pdf_id: str):
    return chat_session.history_payload(pdf_id, chat_session.get_store(pdf_store, pdf_id))


@router.get("/download/{pdf_id}")
async def download_export(pdf_id: str):
    path = chat_session.exported_ontology_path(chat_session.get_store(pdf_store, pdf_id))
    return FileResponse(
        path,
        media_type="application/json",
        filename=path.name,
    )
