from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.conversation.tools import dispatch
from backend.services.conversation.tools.dispatch import _DISPATCH_MAP
from backend.services.conversation.tools.schemas import TOOL_SCHEMAS
from backend.services.graph_view_service import build_graph

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_TOOLS = {
    "add_node_manual",
    "confirm_node_manual",
    "update_exported_node",
    "delete_exported_node",
    "add_exported_relationship",
    "delete_exported_relationship",
    "save_exported_graph",
}


def _published_graph() -> dict:
    return {
        "metadata": {"version": "V1", "status": "published"},
        "nodes": {
            "Asset": [
                {
                    "asset_id": "asset_1",
                    "name": "Machine A",
                    "description": "Test machine",
                    "brand": "Example",
                    "model": "M1",
                }
            ],
            "Component": [],
            "Symptom": [
                {
                    "symptom_id": "sym_1",
                    "name": "Unexpected noise",
                    "description": "The machine emits an unexpected noise.",
                }
            ],
            "FailureMode": [],
            "CorrectiveAction": [],
            "ErrorCode": [],
        },
        "relationships": [],
    }


def test_legacy_editor_sources_and_routes_are_absent():
    assert not (ROOT / "modify").exists()
    assert not (ROOT / "frontend" / "editor").exists()

    with TestClient(app) as client:
        assert client.get("/modify").status_code == 404
        assert client.get("/modify/latest").status_code == 404
        assert client.get("/modify/anything/api/data").status_code == 404
        assert all(not path.startswith("/modify") for path in client.get("/openapi.json").json()["paths"])


def test_chat_catalog_has_no_free_graph_mutation_tools():
    schema_names = {
        schema["function"]["name"]
        for schema in TOOL_SCHEMAS
        if schema.get("type") == "function"
    }
    assert FORBIDDEN_TOOLS.isdisjoint(schema_names)
    assert FORBIDDEN_TOOLS.isdisjoint(_DISPATCH_MAP)


def test_published_graph_inspection_is_read_only(tmp_path):
    graph_path = tmp_path / "knowledge_graph_v001.json"
    graph_path.write_text(json.dumps(_published_graph()), encoding="utf-8")
    before = hashlib.sha256(graph_path.read_bytes()).hexdigest()

    result = asyncio.run(
        dispatch(
            "inspect_exported_graph",
            {"node_id": "sym_1"},
            {"ontology_path": str(graph_path)},
            None,
        )
    )

    assert result["status"] == "ok"
    assert result["node"]["id"] == "sym_1"
    assert result["node"]["read_only"] is True
    assert result["read_only"] is True
    assert hashlib.sha256(graph_path.read_bytes()).hexdigest() == before

    refused = asyncio.run(
        dispatch(
            "update_exported_node",
            {"node_id": "sym_1", "attributes": {"name": "Changed"}},
            {"ontology_path": str(graph_path)},
            None,
        )
    )
    assert refused["status"] == "error"
    assert hashlib.sha256(graph_path.read_bytes()).hexdigest() == before


def test_read_only_visualization_payload_survives_editor_removal():
    payload = build_graph(_published_graph())

    assert {node["id"] for node in payload["nodes"]} == {"asset_1", "sym_1"}
    assert payload["edges"] == []
    assert payload["node_types"] == ["Asset", "Symptom"]
