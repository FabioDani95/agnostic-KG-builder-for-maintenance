from __future__ import annotations

import json
from pathlib import Path

from backend.schemas.widgets import WidgetType, validate_widget_payload

# The legacy chat frontend (and its widget renderer registry) was removed;
# widget payloads remain part of the persisted chat-event contract, so the
# backend schema and its fixtures stay under test.
FIXTURE_DIR = Path("tests/fixtures/widgets")


def test_widget_payload_fixtures_validate_against_backend_schema():
    fixture_paths = sorted(FIXTURE_DIR.glob("*.json"))
    fixture_types = {path.stem for path in fixture_paths}
    assert fixture_types == {item.value for item in WidgetType}

    for path in fixture_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["widget"] == path.stem
        validate_widget_payload(payload)


def test_triplet_widget_accepts_tool_logic_assessment_lines():
    payload = json.loads((FIXTURE_DIR / "triplet.json").read_text(encoding="utf-8"))
    payload["logic_assessment"] = [
        "Logic: the symptom forms a complete diagnostic chain.",
        "Sense check: the source pages are traceable.",
    ]

    validate_widget_payload(payload)
