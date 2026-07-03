from __future__ import annotations

import json
import re
from pathlib import Path

from backend.schemas.widgets import WidgetType, validate_widget_payload

REGISTRY_PATH = Path("frontend/widgets/registry.js")
FIXTURE_DIR = Path("tests/fixtures/widgets")


def _registry_widget_types() -> set[str]:
    source = REGISTRY_PATH.read_text(encoding="utf-8")
    match = re.search(r"WIDGET_RENDERERS\s*=\s*Object\.freeze\(\{(?P<body>.*?)\}\);", source, re.DOTALL)
    assert match, "WIDGET_RENDERERS registry not found"
    return set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:", match.group("body"), flags=re.MULTILINE))


def test_backend_widget_types_are_registered_in_frontend_registry():
    assert {item.value for item in WidgetType}.issubset(_registry_widget_types())


def test_widget_payload_fixtures_validate_against_backend_schema():
    fixture_paths = sorted(FIXTURE_DIR.glob("*.json"))
    fixture_types = {path.stem for path in fixture_paths}
    assert fixture_types == {item.value for item in WidgetType}

    for path in fixture_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["widget"] == path.stem
        validate_widget_payload(payload)
