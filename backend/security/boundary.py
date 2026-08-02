"""Request limits, safe inventory names and canonical containment."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from starlette.types import ASGIApp, Message, Receive, Scope, Send


def _positive_int(environment_key: str, fallback: int) -> int:
    raw = str(os.environ.get(environment_key, "") or "").strip()
    if not raw:
        return fallback
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{environment_key} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{environment_key} must be positive")
    return value


@dataclass(frozen=True)
class SecurityLimits:
    max_upload_bytes: int
    max_body_bytes: int
    max_request_bytes: int


def security_limits() -> SecurityLimits:
    return SecurityLimits(
        max_upload_bytes=_positive_int("KG_MAX_UPLOAD_BYTES", 50 * 1024 * 1024),
        max_body_bytes=_positive_int("KG_MAX_BODY_BYTES", 1024 * 1024),
        max_request_bytes=_positive_int("KG_MAX_REQUEST_BYTES", 52 * 1024 * 1024),
    )


def allowed_origins() -> list[str]:
    configured = str(os.environ.get("KG_ALLOWED_ORIGINS", "") or "").strip()
    if configured:
        values = [item.strip().rstrip("/") for item in configured.split(",") if item.strip()]
    else:
        port = str(os.environ.get("PORT", "8000") or "8000").strip()
        values = [f"http://127.0.0.1:{port}", f"http://localhost:{port}"]
    if any(value == "*" for value in values):
        raise RuntimeError("Wildcard Origin is forbidden")
    return list(dict.fromkeys(values))


def allowed_hosts() -> list[str]:
    configured = str(os.environ.get("KG_ALLOWED_HOSTS", "") or "").strip()
    values = (
        [item.strip().casefold() for item in configured.split(",") if item.strip()]
        if configured
        else ["127.0.0.1", "localhost", "testserver", "[::1]"]
    )
    if any(value == "*" for value in values):
        raise RuntimeError("Wildcard Host is forbidden")
    return list(dict.fromkeys(values))


def actionable_error(
    *,
    title: str,
    object_ref: str,
    cause: str,
    preserved: str,
    action: str,
    technical_detail: str,
    retryability: str,
) -> dict[str, str]:
    return {
        "title": title,
        "object": object_ref,
        "cause": cause,
        "preserved": preserved,
        "action": action,
        "technical_detail": technical_detail,
        "retryability": retryability,
    }


def validate_inventory_name(value: str) -> str:
    """Reject encoded traversal and require one plain inventory basename."""
    raw = str(value or "").strip()
    decoded = raw
    for _ in range(3):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    if (
        not raw
        or "\x00" in decoded
        or "/" in decoded
        or "\\" in decoded
        or decoded in {".", ".."}
        or Path(decoded).name != decoded
    ):
        raise ValueError("File name is not a valid inventory entry")
    return decoded


def contained_file(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file() or resolved.is_symlink():
        raise FileNotFoundError("File is outside the authorized inventory root")
    return resolved


class _RequestTooLarge(RuntimeError):
    pass


class RequestLimitMiddleware:
    """Enforce Content-Length and streamed-body limits before route handling."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limits = security_limits()
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_type = headers.get(b"content-type", b"").decode("latin-1").casefold()
        effective_limit = (
            limits.max_request_bytes
            if content_type.startswith("multipart/form-data")
            else min(limits.max_body_bytes, limits.max_request_bytes)
        )
        try:
            content_length = int(headers.get(b"content-length", b"0") or b"0")
        except ValueError:
            content_length = 0
        if content_length > effective_limit:
            await self._reject(send, effective_limit, content_length)
            return

        consumed = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > effective_limit:
                    raise _RequestTooLarge
            return message

        async def tracked_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _RequestTooLarge:
            if response_started:
                raise
            await self._reject(send, effective_limit, consumed)

    @staticmethod
    async def _reject(send: Send, limit: int, observed: int) -> None:
        payload = json.dumps(
            {
                "detail": actionable_error(
                    title="Richiesta troppo grande",
                    object_ref="HTTP request",
                    cause=f"La richiesta supera il limite configurato di {limit} byte.",
                    preserved="Workspace e fonti già inventariate non sono stati modificati.",
                    action="Ridurre il file o la richiesta e riprovare.",
                    technical_detail=f"REQUEST_LIMIT_EXCEEDED observed={observed} limit={limit}",
                    retryability="riprendibile",
                )
            },
            ensure_ascii=False,
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(payload)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": payload})


class LocalRequestBoundaryMiddleware:
    """Fail closed for Host or Origin values outside the trusted-local inventory."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        host_header = headers.get(b"host", b"").decode("latin-1").strip().casefold()
        host = self._host_without_port(host_header)
        if not host or host not in allowed_hosts():
            await self._reject(send, 400, "HOST_NOT_ALLOWED", host_header or "[missing]")
            return
        origin = headers.get(b"origin")
        if origin is not None:
            decoded_origin = origin.decode("latin-1").strip().rstrip("/")
            if decoded_origin not in allowed_origins():
                await self._reject(send, 403, "ORIGIN_NOT_ALLOWED", decoded_origin)
                return
        await self.app(scope, receive, send)

    @staticmethod
    def _host_without_port(value: str) -> str:
        if value.startswith("["):
            closing = value.find("]")
            return value[: closing + 1] if closing >= 0 else value
        return value.split(":", 1)[0]

    @staticmethod
    async def _reject(send: Send, status: int, code: str, observed: str) -> None:
        payload = json.dumps(
            {
                "detail": actionable_error(
                    title="Origine locale non ammessa",
                    object_ref="HTTP boundary",
                    cause="Host o Origin non appartiene alla configurazione trusted-local.",
                    preserved="Nessuna route applicativa è stata eseguita.",
                    action="Aprire la console dall'indirizzo loopback configurato.",
                    technical_detail=f"{code} observed={observed}",
                    retryability="riprendibile",
                )
            },
            ensure_ascii=False,
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(payload)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": payload})
