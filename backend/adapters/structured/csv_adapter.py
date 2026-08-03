from __future__ import annotations

import codecs
import csv
import io
import re
from pathlib import Path

from backend.domain.evidence import QualityFlag, RawUnitDraft
from backend.domain.locators import TableRowLocator
from backend.domain.sources import Source

from .common import (
    ADAPTER_VERSION,
    ParsedRecord,
    StructuredInspection,
    ambiguous_mapping_exceptions,
    build_structure_profile,
    normalize_header,
    raw_hash,
    stable_raw_id,
)


def inspect_csv(path: Path, source: Source) -> StructuredInspection:
    payload = path.read_bytes()
    detected_encoding = ""
    try:
        if payload.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
            detected_encoding = "utf-32"
            text = payload.decode("utf-32")
        elif payload.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
            detected_encoding = "utf-16"
            text = payload.decode("utf-16")
        else:
            try:
                detected_encoding = "utf-8-sig"
                text = payload.decode("utf-8-sig", errors="strict")
            except UnicodeDecodeError:
                detected_encoding = "cp1252"
                text = payload.decode("cp1252", errors="strict")
    except UnicodeDecodeError:
        detected_encoding = ""
        text = ""
    nul_ratio = payload.count(b"\x00") / len(payload) if payload else 0
    bom_allows_nuls = detected_encoding in {"utf-16", "utf-32"}
    if not detected_encoding or "\x00" in text or (nul_ratio > 0.05 and not bom_allows_nuls):
        structure = build_structure_profile(
            structure_id="csv:main", name=source.file_name or "CSV", kind="table", rows=[]
        )
        return StructuredInspection(
            structures=[structure],
            records=[],
            exceptions=[
                {
                    "exception_kind": "csv_decode_blocked",
                    "severity": "blocking",
                    "title": "Il CSV non è leggibile come testo",
                    "explanation": (
                        "Il file sembra binario o usa una codifica non riconoscibile. "
                        "Il contenuto originale è rimasto invariato: sostituisci il file con un CSV testuale."
                    ),
                    "payload": {"structure_id": "csv:main", "encoding": detected_encoding or None},
                }
            ],
        )
    sample = text[:65536]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    # ``Sniffer`` can incorrectly set ``doublequote=False`` even for a valid
    # RFC 4180-style file containing escaped quotes (``""``).  Keep its
    # delimiter detection, but honor standard CSV escaping when the sample
    # contains it; otherwise a quoted semicolon becomes a phantom column.
    reader_options: dict[str, object] = {"dialect": dialect, "strict": True}
    if dialect.quotechar and f"{dialect.quotechar}{dialect.quotechar}" in sample:
        reader_options["doublequote"] = True
    reader = csv.reader(io.StringIO(text, newline=""), **reader_options)
    try:
        header_row = next(reader)
    except StopIteration:
        structure = build_structure_profile(
            structure_id="csv:main", name=source.file_name or "CSV", kind="table", rows=[]
        )
        return StructuredInspection(structures=[structure], records=[])
    except csv.Error as exc:
        structure = build_structure_profile(
            structure_id="csv:main", name=source.file_name or "CSV", kind="table", rows=[]
        )
        return StructuredInspection(
            structures=[structure],
            records=[],
            exceptions=[
                {
                    "exception_kind": "csv_parse_blocked",
                    "severity": "blocking",
                    "title": "Il CSV non contiene un'intestazione leggibile",
                    "explanation": (
                        f"Il parser non riesce a leggere l'intestazione: {exc}. "
                        "Il file originale è rimasto invariato; correggi o sostituisci il CSV."
                    ),
                    "payload": {"structure_id": "csv:main", "line": reader.line_num},
                }
            ],
        )
    seen: dict[str, int] = {}
    headers = [normalize_header(value, index + 1, seen) for index, value in enumerate(header_row)]
    duplicate_headers = [name for name in headers if re.search(r"#\d+$", name)]
    records: list[ParsedRecord] = []
    rows: list[dict] = []
    row_shape_mismatches: list[dict] = []
    parse_error: dict | None = None
    previous_line = reader.line_num
    record_number = 0
    while True:
        try:
            values = next(reader)
        except StopIteration:
            break
        except csv.Error as exc:
            parse_error = {
                "exception_kind": "csv_parse_blocked",
                "severity": "blocking",
                "title": "Il CSV contiene una riga non leggibile",
                "explanation": (
                    f"Il parser si è fermato vicino alla linea {reader.line_num}: {exc}. "
                    "Le righe già lette e il file originale sono rimasti invariati; correggi o sostituisci il CSV."
                ),
                "payload": {"structure_id": "csv:main", "line": reader.line_num},
            }
            break
        record_number += 1
        line_end = reader.line_num
        line_start = previous_line + 1
        previous_line = line_end
        if not any(str(value).strip() for value in values):
            continue
        actual_columns = len(values)
        expected_columns = len(headers)
        shape_mismatch = actual_columns != expected_columns
        normalized_values = list(values)
        if len(normalized_values) < len(headers):
            normalized_values.extend([None] * (len(headers) - len(normalized_values)))
        row_headers = list(headers)
        if len(normalized_values) > len(headers):
            row_headers.extend(
                f"extra_column_{index}"
                for index in range(1, len(normalized_values) - len(headers) + 1)
            )
        row = dict(zip(row_headers, normalized_values, strict=True))
        if shape_mismatch:
            row_shape_mismatches.append(
                {
                    "record": record_number,
                    "line_start": line_start,
                    "line_end": line_end,
                    "expected_columns": expected_columns,
                    "actual_columns": actual_columns,
                }
            )
        rows.append(row)
        locator = TableRowLocator(
            table_id="csv:main",
            table_name=source.file_name or "CSV",
            record=record_number,
            line_start=line_start,
            line_end=line_end,
            columns=row_headers,
        )
        locator_payload = locator.model_dump(mode="json")
        records.append(
            ParsedRecord(
                raw_unit=RawUnitDraft(
                    raw_unit_id=stable_raw_id(source.source_id, "csv:main", locator_payload),
                    parent_raw_unit_id=None,
                    unit_kind="csv_record",
                    source_id=source.source_id,
                    structure_id="csv:main",
                    locator=locator,
                    raw_hash=raw_hash(row),
                    adapter_version=ADAPTER_VERSION,
                    quality_flags=(
                        [QualityFlag.POSSIBLE_COLUMN_SHIFT] if shape_mismatch else []
                    ),
                ),
                values=row,
                included=not shape_mismatch,
                disposition="failed" if shape_mismatch else "processed",
                reason_code=(
                    "CSV_COLUMN_COUNT_MISMATCH"
                    if shape_mismatch
                    else "STRUCTURED_RECORD_PREPARED"
                ),
            )
        )
    structure = build_structure_profile(
        structure_id="csv:main",
        name=source.file_name or "CSV",
        kind="table",
        rows=rows,
    )
    exceptions = ambiguous_mapping_exceptions(structure)
    if parse_error is not None:
        exceptions.insert(0, parse_error)
    if row_shape_mismatches:
        exceptions.insert(
            0,
            {
                "exception_kind": "csv_row_shape_mismatch",
                "severity": "warning",
                "title": "Alcune righe hanno un numero errato di colonne",
                "explanation": (
                    f"{len(row_shape_mismatches)} righe sono state isolate senza fermare le altre. "
                    "I valori originali sono conservati e non alimenteranno il grafo."
                ),
                "payload": {
                    "structure_id": "csv:main",
                    "rows": row_shape_mismatches[:20],
                    "total": len(row_shape_mismatches),
                },
            },
        )
    if duplicate_headers:
        exceptions.insert(
            0,
            {
                "exception_kind": "duplicate_headers",
                "severity": "warning",
                "title": "Sono presenti intestazioni duplicate",
                "explanation": "Le colonne sono state conservate senza perdita e distinte con un numero progressivo.",
                "payload": {"structure_id": "csv:main", "columns": duplicate_headers},
            },
        )
    return StructuredInspection(structures=[structure], records=records, exceptions=exceptions)
