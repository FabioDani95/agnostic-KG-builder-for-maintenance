"""Opaque identifiers and canonical UTC timestamps."""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator

_OPAQUE_ID = re.compile(r"^[a-z][a-z0-9_]*_[A-Za-z0-9_-]{10,}$")
_PREFIXES = {
    "workspace": "ws",
    "asset": "asset",
    "source": "src",
    "evidence": "ev",
    "batch": "batch",
    "run": "run",
    "candidate": "cand",
    "decision": "decision",
    "assertion": "assert",
    "assessment": "srcassess",
    "raw_unit": "raw",
    "disposition": "disp",
    "preparation": "prep",
}


def new_id(entity_type: str) -> str:
    """Return an opaque, collision-resistant identifier with a stable type prefix."""
    try:
        prefix = _PREFIXES[entity_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported entity type: {entity_type}") from exc
    return f"{prefix}_{secrets.token_urlsafe(16)}"


def validate_opaque_id(value: str) -> str:
    value = str(value or "").strip()
    if not _OPAQUE_ID.fullmatch(value):
        raise ValueError("Identifier must be a non-empty opaque prefixed string")
    return value


OpaqueId = Annotated[str, AfterValidator(validate_opaque_id)]


def utc_now() -> str:
    """Return an application timestamp in UTC ISO-8601 form with a literal Z."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def validate_utc_timestamp(value: str) -> str:
    value = str(value or "").strip()
    if not value.endswith("Z"):
        raise ValueError("Application timestamps must use UTC and end in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("Invalid ISO-8601 timestamp") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("Application timestamps must be UTC")
    return value


UtcTimestamp = Annotated[str, AfterValidator(validate_utc_timestamp)]

