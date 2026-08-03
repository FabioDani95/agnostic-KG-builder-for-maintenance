from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from backend.domain.evidence import QualityFlag, RawUnitDraft
from backend.domain.locators import JsonPathLocator
from backend.domain.sources import Source, SourceKind

from .common import (
    ADAPTER_VERSION,
    ParsedRecord,
    StructuredInspection,
    ambiguous_mapping_exceptions,
    build_structure_profile,
    quality_flags,
    raw_hash,
    stable_raw_id,
)


class DuplicateJsonKey(ValueError):
    pass


def _object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey(str(key))
        result[key] = value
    return result


def _loads(text: str):
    return json.loads(
        text,
        object_pairs_hook=_object_no_duplicates,
        parse_float=Decimal,
        parse_int=Decimal,
    )


def _collections(value: Any, path: str = "$") -> list[tuple[str, list[dict[str, Any]]]]:
    found: list[tuple[str, list[dict[str, Any]]]] = []
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return [(path, value)]
    if isinstance(value, dict):
        for key, item in value.items():
            escaped = str(key).replace("'", "\\'")
            child_path = f"{path}['{escaped}']"
            if isinstance(item, list) and all(isinstance(entry, dict) for entry in item):
                found.append((child_path, item))
            elif isinstance(item, dict):
                found.extend(_collections(item, child_path))
    return found


def _record(
    *,
    source: Source,
    structure_id: str,
    values: dict[str, Any],
    json_path: str,
    line: int | None = None,
    included: bool = True,
    disposition: str = "processed",
    reason_code: str = "STRUCTURED_RECORD_PREPARED",
    flags: list[QualityFlag] | None = None,
) -> ParsedRecord:
    locator = JsonPathLocator(json_path=json_path, line=line)
    locator_payload = locator.model_dump(mode="json")
    return ParsedRecord(
        raw_unit=RawUnitDraft(
            raw_unit_id=stable_raw_id(source.source_id, structure_id, locator_payload),
            parent_raw_unit_id=None,
            unit_kind="jsonl_line" if line is not None else "json_item",
            source_id=source.source_id,
            structure_id=structure_id,
            locator=locator,
            raw_hash=raw_hash(values),
            adapter_version=ADAPTER_VERSION,
            quality_flags=flags or [],
        ),
        values=values,
        included=included,
        disposition=disposition,
        reason_code=reason_code,
    )


def inspect_json_source(path: Path, source: Source) -> StructuredInspection:
    if source.source_kind is SourceKind.JSONL:
        return _inspect_jsonl(path, source)
    return _inspect_json(path, source)


def _inspect_jsonl(path: Path, source: Source) -> StructuredInspection:
    rows: list[dict[str, Any]] = []
    records: list[ParsedRecord] = []
    exceptions: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            value = _loads(raw_line)
            if not isinstance(value, dict):
                raise ValueError("Each JSONL line must be an object")
        except (json.JSONDecodeError, DuplicateJsonKey, ValueError) as exc:
            values = {"raw_line": raw_line}
            records.append(
                _record(
                    source=source,
                    structure_id="jsonl:$",
                    values=values,
                    json_path=f"$[line={line_number}]",
                    line=line_number,
                    included=False,
                    disposition="failed",
                    reason_code="MALFORMED_JSONL_LINE",
                    flags=quality_flags(QualityFlag.MISSING_REQUIRED_SOURCE_FIELD),
                )
            )
            exceptions.append(
                {
                    "exception_kind": "malformed_jsonl_line",
                    "severity": "warning",
                    "title": f"La riga JSONL {line_number} non è leggibile",
                    "explanation": "È stata isolata; tutte le altre righe e fonti continuano. Il contenuto originale resta disponibile.",
                    "payload": {"structure_id": "jsonl:$", "line": line_number, "cause": str(exc)},
                }
            )
            continue
        rows.append(value)
        records.append(
            _record(
                source=source,
                structure_id="jsonl:$",
                values=value,
                json_path=f"$[line={line_number}]",
                line=line_number,
            )
        )
    structure = build_structure_profile(
        structure_id="jsonl:$", name=source.file_name or "JSONL", kind="jsonl", rows=rows
    )
    exceptions.extend(ambiguous_mapping_exceptions(structure))
    return StructuredInspection(structures=[structure], records=records, exceptions=exceptions)


def _inspect_json(path: Path, source: Source) -> StructuredInspection:
    text = path.read_text(encoding="utf-8-sig")
    try:
        value = _loads(text)
    except (json.JSONDecodeError, DuplicateJsonKey) as exc:
        record = _record(
            source=source,
            structure_id="json:$",
            values={"raw_document": text},
            json_path="$",
            included=False,
            disposition="quarantined",
            reason_code="JSON_STRUCTURE_BLOCKED",
        )
        structure = build_structure_profile(
            structure_id="json:$", name=source.file_name or "JSON", kind="array", rows=[]
        )
        return StructuredInspection(
            structures=[structure],
            records=[record],
            exceptions=[
                {
                    "exception_kind": "json_structure_blocked",
                    "severity": "blocking",
                    "title": "Il documento JSON contiene una struttura ambigua",
                    "explanation": "Il file è preservato, ma questa struttura non può essere preparata senza correggere il JSON.",
                    "payload": {"structure_id": "json:$", "cause": str(exc)},
                }
            ],
        )
    collections = _collections(value)
    if not collections and isinstance(value, dict):
        collections = [("$", [value])]
    structures = []
    records: list[ParsedRecord] = []
    exceptions: list[dict[str, Any]] = []
    for path_value, rows in collections:
        structure_id = f"json:{path_value}"
        structure = build_structure_profile(
            structure_id=structure_id,
            name=path_value,
            kind="array",
            rows=rows,
        )
        structures.append(structure)
        exceptions.extend(ambiguous_mapping_exceptions(structure))
        for index, row in enumerate(rows):
            records.append(
                _record(
                    source=source,
                    structure_id=structure_id,
                    values=row,
                    json_path=f"{path_value}[{index}]",
                )
            )
    return StructuredInspection(structures=structures, records=records, exceptions=exceptions)
