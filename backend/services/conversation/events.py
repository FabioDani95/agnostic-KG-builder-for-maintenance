"""Per-run event bus for streaming pipeline progress to the chat UI.

Usage pattern:
    # In a workflow:
    on_event({"type": "progress", "phase": "extraction", "message": "Chunk 2/5 done"})

    # In the SSE router:
    async for event in stream_events(pdf_id, timeout=300):
        yield f"data: {json.dumps(event)}\\n\\n"
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Event type literals (keeps callers honest without a full enum)
EVT_PROGRESS = "progress"
EVT_CHAT_DELTA = "chat_delta"
EVT_WIDGET = "widget"
EVT_CRITIQUE = "critique"
EVT_NEEDS_INPUT = "needs_input"
EVT_DONE = "done"
EVT_ERROR = "error"
EVT_THINKING = "thinking"

_queues: dict[str, asyncio.Queue] = {}
_locks: dict[str, asyncio.Lock] = {}


def get_lock(pdf_id: str) -> asyncio.Lock:
    """Return (creating if needed) the per-run mutex."""
    if pdf_id not in _locks:
        _locks[pdf_id] = asyncio.Lock()
    return _locks[pdf_id]


def register(pdf_id: str) -> None:
    """Ensure a queue and lock exist for this run.  Idempotent — safe to call
    from both /chat/stream and /chat/start regardless of ordering."""
    if pdf_id not in _queues:
        _queues[pdf_id] = asyncio.Queue()
    if pdf_id not in _locks:
        _locks[pdf_id] = asyncio.Lock()


def unregister(pdf_id: str) -> None:
    """Tear down queue and lock after a run is fully consumed."""
    _queues.pop(pdf_id, None)
    _locks.pop(pdf_id, None)


def make_on_event(pdf_id: str):
    """Return a sync callback that enqueues an event for `pdf_id`.

    MUST be called from an async context so the running event loop is captured
    at creation time.  The returned callback is then safe to invoke from any
    thread (including asyncio.to_thread workers) via call_soon_threadsafe.
    """
    queue = _queues.get(pdf_id)
    if queue is None:
        return lambda evt: None  # no-op if not registered

    try:
        loop = asyncio.get_running_loop()   # capture NOW, in async context
    except RuntimeError:
        loop = None

    def _emit(event: dict[str, Any]) -> None:
        try:
            if loop is not None and not loop.is_closed():
                loop.call_soon_threadsafe(queue.put_nowait, event)
            else:
                queue.put_nowait(event)
        except Exception:
            pass  # never crash a workflow because of event dispatch

    return _emit


def emit(pdf_id: str, event: dict[str, Any]) -> None:
    """Emit an event synchronously (must be called from async context or threadpool)."""
    on_event = make_on_event(pdf_id)
    on_event(event)


async def put(pdf_id: str, event: dict[str, Any]) -> None:
    """Enqueue an event from async context."""
    queue = _queues.get(pdf_id)
    if queue is not None:
        await queue.put(event)


async def stream_events(pdf_id: str, timeout: float = 600.0):
    """Async generator yielding events for the duration of a session.

    Stays open until `timeout` seconds of inactivity.  EVT_DONE is a
    per-action marker forwarded to the client — it does NOT close the stream.
    """
    queue = _queues.get(pdf_id)
    if queue is None:
        return
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                yield {"type": EVT_ERROR, "message": "Stream timed out."}
                return
            yield event
    except GeneratorExit:
        pass


def progress_event(phase: str, message: str, **extra) -> dict[str, Any]:
    return {"type": EVT_PROGRESS, "phase": phase, "message": message, **extra}


def widget_event(widget_type: str, payload: dict[str, Any], **extra) -> dict[str, Any]:
    return {"type": EVT_WIDGET, "widget": widget_type, "payload": payload, **extra}


def critique_event(message: str, entity_id: str | None, suggestion: str | None, **extra) -> dict[str, Any]:
    return {
        "type": EVT_CRITIQUE,
        "message": message,
        "entity_id": entity_id,
        "suggestion": suggestion,
        **extra,
    }


def chat_delta_event(text: str) -> dict[str, Any]:
    return {"type": EVT_CHAT_DELTA, "text": text}


def done_event(summary: str = "") -> dict[str, Any]:
    return {"type": EVT_DONE, "summary": summary}


def error_event(message: str) -> dict[str, Any]:
    return {"type": EVT_ERROR, "message": message}
