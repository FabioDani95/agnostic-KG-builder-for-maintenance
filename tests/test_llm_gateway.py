from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys

from backend.services.conversation.orchestrator import handle_message
from backend.services.llm_gateway import get_client
from backend.services.llm_service import call_openai, call_openai_scoping, parse_extraction
from backend.services.ontology_pipeline import build_initial_ontology
from backend.services.style_cleanup_service import _rewrite_fields_with_llm


def test_gateway_defaults_to_real_mode_and_uses_real_factory(monkeypatch):
    monkeypatch.delenv("KG_LLM_MODE", raising=False)
    calls = []

    class FakeRealClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    client = get_client(timeout=3, api_key="key-real", client_factory=FakeRealClient)

    assert isinstance(client, FakeRealClient)
    assert calls == [{"api_key": "key-real", "timeout": 3}]


def test_mock_mode_works_without_openai_api_key_in_fresh_process():
    code = (
        "from backend.services.llm_service import call_openai_scoping; "
        "raw, usage = call_openai_scoping('table of contents toc_entries', model_name='mock'); "
        "print(raw); "
        "print(usage['total'])"
    )
    env = dict(os.environ)
    env["KG_LLM_MODE"] = "mock"
    env.pop("OPENAI_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=os.getcwd(),
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "toc_entries" in result.stdout
    assert result.stdout.strip().endswith("0")


def test_mock_scoping_and_extraction_call_sites(monkeypatch):
    monkeypatch.setenv("KG_LLM_MODE", "mock")

    raw_scope, scope_usage = call_openai_scoping("table of contents toc_entries", model_name="mock")
    raw_extract, extract_usage = call_openai(
        "--- PAGE 1 ---\nLow flow. --- PAGE 2 ---\nClean filter.",
        "maintenance manual",
        "Mock Manual",
        "en",
        model_name="mock",
    )
    parsed = parse_extraction(raw_extract, "maintenance manual", "Mock Manual")

    assert json.loads(raw_scope)["toc_entries"]
    assert scope_usage["total"] == 0
    assert extract_usage["total"] == 0
    assert len(parsed.triplets) == 1


def test_mock_async_chat_call_site(monkeypatch):
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    events = []
    store = {
        "pdf_id": "pdf-mock",
        "filename": "mock.pdf",
        "pages": [{"page_number": 1, "text": "Low flow troubleshooting."}],
        "page_count": 1,
        "graph_state": {
            "current_phase": "loaded",
            "run_id": "run_mock",
            "pdf_id": "pdf-mock",
            "filename": "mock.pdf",
            "started_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "phase_history": [],
            "config_snapshot": {"pipeline": {"mode": "multi_agent"}},
            "selected_models": {},
        },
        "conversation": {"messages": [], "tool_calls": [], "critiques": []},
    }

    async def run():
        from backend.services.conversation import events as evt_bus

        evt_bus.register("pdf-mock")
        original = evt_bus.make_on_event
        evt_bus.make_on_event = lambda pdf_id: events.append
        try:
            await handle_message("pdf-mock", store, "What is the status?")
        finally:
            evt_bus.make_on_event = original
            evt_bus.unregister("pdf-mock")

    asyncio.run(run())

    assert any(event.get("type") == "chat_delta" for event in events)


def test_mock_style_cleanup_call_site(monkeypatch):
    monkeypatch.setenv("KG_LLM_MODE", "mock")

    rewritten, usage = _rewrite_fields_with_llm(
        flat_fields={"nodes.Asset.0.description": "already clean"},
        target_language="en",
        model_name="mock",
        timeout_seconds=10,
        max_output_tokens=200,
    )

    assert rewritten == {"nodes.Asset.0.description": "already clean"}
    assert usage["total"] == 0


def test_mock_ontology_pipeline_call_site(monkeypatch):
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    monkeypatch.setattr(
        "backend.services.ontology_pipeline.get_reflective_loop_config",
        lambda: {"max_retries": 0},
    )

    result, metrics = build_initial_ontology(
        text_with_pages="--- PAGE 1 ---\nLow flow indicates a clogged filter.\n--- PAGE 2 ---\nClean the filter.",
        source_type="maintenance manual",
        source_title="Mock Manual",
        target_language="en",
        model_name="mock",
    )

    assert result.ontology.nodes["Asset"]
    assert result.ontology.nodes["Symptom"]
    assert metrics["llm_calls"] >= 1
    assert metrics["total_tokens"] == 0


def test_mock_fixture_response_overrides_generic_stage_reply(monkeypatch, tmp_path):
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    monkeypatch.setenv("KG_LLM_FIXTURE", "demo_fixture")
    monkeypatch.setenv("KG_LLM_MOCK_DIR", str(tmp_path))

    fixture_dir = tmp_path / "demo_fixture"
    fixture_dir.mkdir()
    (fixture_dir / "ontology.json").write_text(
        json.dumps({"ontology_name": "FixtureDrivenOntology", "nodes": {}}),
        encoding="utf-8",
    )
    (fixture_dir / "extraction.json").write_text(
        json.dumps({"content": "| fixture extraction tables |"}),
        encoding="utf-8",
    )

    client = get_client()

    ontology_reply = client.chat.completions.create(
        model="mock",
        messages=[{"role": "user", "content": "Extract the ontology nodes from this manual."}],
    ).choices[0].message.content
    assert json.loads(ontology_reply)["ontology_name"] == "FixtureDrivenOntology"

    # A "content"-only payload is returned as raw text, not JSON.
    extraction_reply = client.chat.completions.create(
        model="mock",
        messages=[{"role": "user", "content": "Return exactly three markdown tables."}],
    ).choices[0].message.content
    assert extraction_reply == "| fixture extraction tables |"

    # Stages without a fixture file keep the generic deterministic reply.
    validation_reply = client.chat.completions.create(
        model="mock",
        messages=[{"role": "user", "content": "List semantic validation issues."}],
    ).choices[0].message.content
    assert json.loads(validation_reply) == {"issues": []}


def test_mock_without_fixture_env_keeps_generic_replies(monkeypatch):
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    monkeypatch.delenv("KG_LLM_FIXTURE", raising=False)

    client = get_client()
    reply = client.chat.completions.create(
        model="mock",
        messages=[{"role": "user", "content": "Extract the ontology nodes from this manual."}],
    ).choices[0].message.content

    assert json.loads(reply)["ontology_name"] == "MockMaintenanceOntology"
