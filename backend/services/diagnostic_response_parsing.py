"""Decode complete JSON and validate independent records without schema repair."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from backend.domain.diagnostic_bundles import DiagnosticBundleCandidate, DiagnosticChunkOutput


@dataclass(frozen=True)
class RecordParseResult:
    output: DiagnosticChunkOutput | None
    rejected: list[dict[str, Any]]
    envelope_error: str = ""


def parse_diagnostic_records(raw: str, *, anchor_aliases: dict[str, str] | None = None) -> RecordParseResult:
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError) as exc:
        return RecordParseResult(None, [], type(exc).__name__)
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        return RecordParseResult(None, [], "invalid_envelope")
    try:
        # Validate envelope fields/extra keys independently with the same model.
        DiagnosticChunkOutput.model_validate({**payload, "records": []})
    except ValidationError:
        return RecordParseResult(None, [], "invalid_envelope")
    records, rejected = [], []
    def expand(value, key=""):
        if isinstance(value, dict):
            return {k: expand(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [expand(v, key) for v in value]
        if isinstance(value, str) and key in {"source_anchor", "record_anchor", "branch_anchor", "allowed_source_anchors"}:
            return (anchor_aliases or {}).get(value, value)
        return value
    for index, value in enumerate(payload["records"]):
        value = expand(value)
        try:
            records.append(DiagnosticBundleCandidate.model_validate(value))
        except ValidationError as exc:
            rejected.append({"index": index, "payload": value, "errors": exc.errors(include_context=False, include_url=False)})
    return RecordParseResult(
        DiagnosticChunkOutput.model_validate({**payload, "records": records}), rejected,
    )
