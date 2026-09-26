"""Durable provider exchanges, written before any local response validation."""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _json_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _json_value(value.model_dump(mode="json"))
    if isinstance(value, type) and hasattr(value, "model_json_schema"):
        return value.model_json_schema()
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items() if str(k).lower() not in {"api_key", "authorization"}}
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if hasattr(value, "__dict__"):
        return _json_value(vars(value))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class ResponseArchive:
    def __init__(self, request: dict[str, Any], *, method: str, call_id: str = ""):
        directory = Path(os.environ.get("KG_LLM_TRACE_DIR") or "data/provider_responses")
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / f"{uuid.uuid4().hex}.json"
        self.started = time.perf_counter()
        self.payload = {
            "schema_version": 1, "method": method, "call_id": call_id,
            "run_id": os.environ.get("KG_REAL_CALL_RUN_ID", ""),
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "status": "prepared", "request": _json_value(request),
        }
        self._write()

    def _write(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(self.payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(self.path)

    def finish(self, *, response: Any = None, error: Exception | None = None) -> str:
        from backend.config import settings
        details = None
        if error is not None:
            message = str(error)
            if settings.OPENAI_API_KEY:
                message = message.replace(settings.OPENAI_API_KEY, "[REDACTED]")
            details = {"type": type(error).__name__, "status_code": getattr(error, "status_code", None), "message": message}
            body = getattr(error, "body", None)
            if body is not None:
                serialized = json.dumps(_json_value(body), ensure_ascii=False)
                if settings.OPENAI_API_KEY:
                    serialized = serialized.replace(settings.OPENAI_API_KEY, "[REDACTED]")
                details["provider_body"] = json.loads(serialized)
        self.payload.update({
            "status": "provider_error" if error else "received",
            "elapsed_seconds": time.perf_counter() - self.started,
            "response": _json_value(response),
            "provider_request_id": getattr(response, "_request_id", None) or getattr(error, "request_id", None),
            "error": details,
        })
        self._write()
        return hashlib.sha256(self.path.read_bytes()).hexdigest()


def response_format_for(model: type) -> dict[str, Any]:
    """Use the SDK's strict schema conversion without its all-or-nothing parser."""
    from openai.lib._pydantic import to_strict_json_schema

    return {"type": "json_schema", "json_schema": {
        "name": model.__name__, "strict": True, "schema": to_strict_json_schema(model),
    }}
