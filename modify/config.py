from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = BASE_DIR / "data" / "generated"
ONTOLOGY_PATH = BASE_DIR / "output" / "latest" / "ontology.json"
SCHEMA_PATH = BASE_DIR / "ontology_schema.JSON"
