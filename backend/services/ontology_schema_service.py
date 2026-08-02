from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from backend.models import OntologySchemaDefinition

_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "ontology_schema.JSON"
APPROVED_ONTOLOGY_SHA256 = "81f2d894e8b4c3c0ba3bb2e7149941ae91b704ebd8a8b8dedef91b79bd1508db"


@dataclass(frozen=True)
class OntologyContract:
    version: str
    sha256: str
    path: Path


def ontology_contract(path: Path | None = None) -> OntologyContract:
    """Load and checksum the ontology at runtime, failing closed on drift."""
    resolved = (path or _SCHEMA_PATH).resolve()
    raw = resolved.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if checksum != APPROVED_ONTOLOGY_SHA256:
        raise RuntimeError(
            "ontology_schema.JSON checksum mismatch: "
            f"expected {APPROVED_ONTOLOGY_SHA256}, got {checksum}"
        )
    payload = json.loads(raw)
    return OntologyContract(
        version=str(payload.get("version") or ""),
        sha256=checksum,
        path=resolved,
    )


@lru_cache(maxsize=1)
def load_ontology_schema() -> OntologySchemaDefinition:
    ontology_contract()
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return OntologySchemaDefinition.model_validate(data)


def dump_ontology_schema_json() -> str:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return f.read()
