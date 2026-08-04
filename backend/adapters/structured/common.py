from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from backend.domain.evidence import QualityFlag, RawUnitDraft
from backend.domain.sources import Source, SourceKind
from backend.domain.structured import ColumnProfile, MappingColumn, StructureProfile

# Identifies the byte-level parse: encoding, delimiter, rows and columns. It is
# stamped into every immutable RawUnit, so bumping it makes existing rows
# impossible to re-register. Change it only when the parse itself changes —
# never for a change in how meaning is derived from it (see
# EVIDENCE_DERIVATION_VERSION in services/structured_preparation.py).
ADAPTER_VERSION = "structured-v2"
_ROLE_CONFIG_PATH = Path(__file__).with_name("role_aliases.v2.json")


def _normalized_token(value: Any) -> str:
    """Return a locale-neutral, deterministic token for matching headers."""
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = re.sub(r"[^\w]+", "_", text, flags=re.UNICODE)
    return re.sub(r"_+", "_", text).strip("_")


def _load_role_config() -> dict[str, Any]:
    with _ROLE_CONFIG_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload.get("version"), str) or not isinstance(payload.get("roles"), dict):
        raise RuntimeError("Invalid structured role-alias configuration")
    return payload


_ROLE_CONFIG = _load_role_config()
ROLE_ALIAS_CONFIG_VERSION = _ROLE_CONFIG["version"]
_ROLE_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = tuple(
    (role, tuple(_normalized_token(alias) for alias in aliases))
    for role, aliases in _ROLE_CONFIG["roles"].items()
)
_ATTRIBUTE_HEADERS = {_normalized_token(value) for value in _ROLE_CONFIG["attribute_headers"]}
_DIAGNOSTIC_HEADER_TOKENS = {
    _normalized_token(value) for value in _ROLE_CONFIG["diagnostic_header_tokens"]
}


@dataclass(frozen=True)
class ParsedRecord:
    raw_unit: RawUnitDraft
    values: dict[str, Any]
    included: bool = True
    disposition: str = "processed"
    reason_code: str = "STRUCTURED_RECORD_PREPARED"


@dataclass
class StructuredInspection:
    structures: list[StructureProfile]
    records: list[ParsedRecord]
    exceptions: list[dict[str, Any]] = field(default_factory=list)
    fingerprint: str = ""
    mapping: dict[str, dict[str, MappingColumn]] = field(default_factory=dict)

    def finalize(self) -> "StructuredInspection":
        schema = [
            {
                "structure_id": structure.structure_id,
                "columns": [
                    {"name": column.name, "type": column.inferred_type}
                    for column in structure.columns
                ],
            }
            for structure in self.structures
        ]
        self.mapping = {
            structure.structure_id: {
                column.name: MappingColumn(
                    role=column.proposed_role,
                    included=structure.included,
                    inferred_type=column.inferred_type,
                )
                for column in structure.columns
            }
            for structure in self.structures
        }
        self.fingerprint = hashlib.sha256(canonical_bytes({
            "adapter_version": ADAPTER_VERSION,
            "role_alias_config_version": ROLE_ALIAS_CONFIG_VERSION,
            "schema": schema,
            "mapping": {
                structure_id: {
                    column: config.model_dump(mode="json")
                    for column, config in columns.items()
                }
                for structure_id, columns in self.mapping.items()
            },
        })).hexdigest()
        return self


def canonical_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, (list, tuple)):
        return [canonical_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): canonical_value(item) for key, item in value.items()}
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonical_value(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def stable_raw_id(source_id: str, structure_id: str, locator: dict[str, Any]) -> str:
    token = hashlib.sha256(
        canonical_bytes({"source_id": source_id, "structure_id": structure_id, "locator": locator})
    ).hexdigest()[:28]
    return f"raw_{token}"


def raw_hash(values: Any) -> str:
    return hashlib.sha256(canonical_bytes(values)).hexdigest()


def normalize_header(value: Any, position: int, seen: dict[str, int]) -> str:
    base = _normalized_token(value) or f"column_{position}"
    count = seen.get(base, 0) + 1
    seen[base] = count
    return base if count == 1 else f"{base}#{count}"


def infer_type(values: list[Any]) -> str:
    populated = [value for value in values if value not in (None, "")]
    if not populated:
        return "empty"
    if all(isinstance(value, bool) for value in populated):
        return "boolean"
    if all(isinstance(value, int) and not isinstance(value, bool) for value in populated):
        return "integer"
    if all(isinstance(value, (int, float, Decimal)) and not isinstance(value, bool) for value in populated):
        return "number"
    iso_dates = 0
    for value in populated:
        if isinstance(value, (date, datetime)):
            iso_dates += 1
            continue
        text = str(value).strip()
        try:
            datetime.fromisoformat(text.replace("Z", "+00:00"))
            iso_dates += 1
        except ValueError:
            pass
    if iso_dates == len(populated):
        return "datetime"
    if any(isinstance(value, (dict, list)) for value in populated):
        return "nested"
    return "text"


def proposed_role(name: str, values: list[Any] | None = None) -> tuple[str, bool]:
    canonical = _normalized_token(re.sub(r"#\d+$", "", name))
    for role, aliases in _ROLE_ALIASES:
        # Header names carry context.  A suffix match turns e.g.
        # ``origine_segnalazione`` into a Symptom and ``esito_intervento``
        # into a CorrectiveAction: both are semantic corruption.  Unknown
        # diagnostic headers must surface an explicit mapping decision.
        if canonical in aliases:
            return role, False
    if canonical in _ATTRIBUTE_HEADERS or canonical.endswith(("_id", "_code")):
        return "attribute", False
    if values:
        populated = [value for value in values if value not in (None, "")]
        if populated and all(_is_numeric_value(value) for value in populated):
            return "attribute", False
    header_tokens = set(canonical.split("_"))
    potentially_diagnostic = bool(header_tokens & _DIAGNOSTIC_HEADER_TOKENS)
    if potentially_diagnostic:
        return "attribute", True
    return "attribute", False


def _is_numeric_value(value: Any) -> bool:
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return True
    try:
        Decimal(str(value).strip().replace(",", "."))
    except Exception:
        return False
    return True


def build_structure_profile(
    *,
    structure_id: str,
    name: str,
    kind: str,
    rows: list[dict[str, Any]],
    included: bool = True,
    hidden: bool = False,
) -> StructureProfile:
    names: list[str] = []
    for row in rows:
        for key in row:
            if key not in names:
                names.append(key)
    columns: list[ColumnProfile] = []
    for name_value in names:
        values = [row.get(name_value) for row in rows]
        populated = [canonical_value(value) for value in values if value not in (None, "")]
        role, ambiguous = proposed_role(name_value, values)
        columns.append(
            ColumnProfile(
                name=name_value,
                inferred_type=infer_type(values),
                null_rate=(len(values) - len(populated)) / len(values) if values else 0,
                cardinality=len({json.dumps(value, sort_keys=True, default=str) for value in populated}),
                examples=[str(value)[:160] for value in populated[:3]],
                proposed_role=role,
                ambiguous=ambiguous,
            )
        )
    return StructureProfile(
        structure_id=structure_id,
        name=name,
        kind=kind,
        row_count=len(rows),
        included=included,
        hidden=hidden,
        columns=columns,
        preview=[canonical_value(row) for row in rows[:20]],
    )


def ambiguous_mapping_exceptions(structure: StructureProfile) -> list[dict[str, Any]]:
    return [
        {
            "exception_kind": "mapping_ambiguous",
            "severity": "blocking",
            "title": f"Dove va usata la colonna “{column.name}”?",
            "explanation": (
                "Il nome della colonna non basta per stabilirne il significato. "
                "Scegli il ruolo corretto; i valori originali resteranno invariati."
            ),
            "payload": {
                "structure_id": structure.structure_id,
                "column": column.name,
                "examples": column.examples,
                "suggested_role": column.proposed_role,
                "mapping_config_version": ROLE_ALIAS_CONFIG_VERSION,
                "choices": [
                    "observation", "cause", "action", "component", "error_code",
                    "occurred_at", "outcome", "measurement", "attribute", "excluded",
                ],
            },
        }
        for column in structure.columns
        if column.ambiguous and structure.included
    ]


def inspect_structured_source(path: Path, source: Source) -> StructuredInspection:
    if source.source_kind is SourceKind.CSV:
        from .csv_adapter import inspect_csv

        return inspect_csv(path, source).finalize()
    if source.source_kind is SourceKind.XLSX:
        from .xlsx_adapter import inspect_xlsx

        return inspect_xlsx(path, source).finalize()
    if source.source_kind in {SourceKind.JSON, SourceKind.JSONL}:
        from .json_adapter import inspect_json_source

        return inspect_json_source(path, source).finalize()
    raise ValueError(f"Unsupported structured source kind: {source.source_kind.value}")


def quality_flags(*flags: QualityFlag) -> list[QualityFlag]:
    return list(dict.fromkeys(flags))
