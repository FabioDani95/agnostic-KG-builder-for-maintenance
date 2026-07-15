"""Render the graph-editor HTML page.

The actual markup lives in frontend/editor/ (editor.html + editor.css +
editor.js, served statically by the backend); this module only injects the
per-request values (ontology name, API base path) into the HTML shell.
"""

from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path

_EDITOR_HTML_PATH = Path(__file__).resolve().parent.parent / "frontend" / "editor" / "editor.html"


@lru_cache(maxsize=1)
def _load_template() -> str:
    return _EDITOR_HTML_PATH.read_text(encoding="utf-8")


def render_html(ontology_name: str, api_base: str) -> str:
    return (
        _load_template()
        .replace("__ONTOLOGY_NAME__", html.escape(ontology_name))
        .replace("__API_BASE_JSON__", json.dumps(api_base))
    )
