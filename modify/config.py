from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = BASE_DIR / "data" / "generated"
LEGACY_ONTOLOGY_PATH = BASE_DIR / "ontology.json"
ONTOLOGY_PATH = GENERATED_DIR / "latest_ontology.json"
SCHEMA_PATH = BASE_DIR / "ontology_schema.JSON"
