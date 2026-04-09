from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.models import OntologySchemaDefinition

_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "ontology_schema.JSON"


@lru_cache(maxsize=1)
def load_ontology_schema() -> OntologySchemaDefinition:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return OntologySchemaDefinition.model_validate(data)


def dump_ontology_schema_json() -> str:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return f.read()
