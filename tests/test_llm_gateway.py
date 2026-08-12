from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from types import SimpleNamespace

from pydantic import BaseModel

from backend.services.conversation.orchestrator import handle_message
from backend.services.llm_gateway import (
    chat_reasoning_kwargs,
    chat_temperature_kwargs,
    get_async_client,
    get_client,
)
from backend.services.llm_service import call_openai, call_openai_scoping, parse_extraction
from backend.services.ontology_pipeline import build_initial_ontology
from backend.services.run_metrics import (
    estimate_cost_usd,
    pricing_for_model,
    usage_from_response,
)
from backend.services.style_cleanup_service import _rewrite_fields_with_llm


class _FixtureDiagnosticBundle(BaseModel):
    record_anchor: str
    branch_anchor: str


class DiagnosticChunkOutput(BaseModel):
    schema_version: str
    bundles: list[_FixtureDiagnosticBundle]


def test_gateway_defaults_to_real_mode_and_uses_real_factory(monkeypatch):
    monkeypatch.delenv("KG_LLM_MODE", raising=False)
    calls = []

    class FakeRealClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    client = get_client(timeout=3, api_key="key-real", client_factory=FakeRealClient)

    assert isinstance(client, FakeRealClient)
    assert calls == [{"api_key": "key-real", "timeout": 3}]


def test_gpt_56_models_use_their_supported_default_temperature():
    assert chat_temperature_kwargs("gpt-5.6-terra", 0.0) == {}
    assert chat_temperature_kwargs("gpt-5.6-sol-2026-08-01", 0.0) == {}
    assert chat_temperature_kwargs("gpt-5.4", 0.0) == {"temperature": 0.0}


def test_reasoning_effort_is_explicit_only_for_supported_pipeline_models():
    assert chat_reasoning_kwargs("gpt-5.6-luna", " low ") == {"reasoning_effort": "low"}
    assert chat_reasoning_kwargs("gpt-5.6-terra", "medium") == {"reasoning_effort": "medium"}
    assert chat_reasoning_kwargs("gpt-4o-mini", "low") == {}
    assert chat_reasoning_kwargs("gpt-5.6-luna", None) == {}


def test_reasoning_effort_rejects_configuration_typos():
    import pytest

    with pytest.raises(ValueError, match="Unsupported reasoning_effort"):
        chat_reasoning_kwargs("gpt-5.6-luna", "cheap")

    with pytest.raises(ValueError, match="Unsupported reasoning_effort"):
        chat_reasoning_kwargs("gpt-5.6-luna", "minimal")


def test_gpt_56_terra_usage_keeps_its_model_identity_and_current_rates():
    pricing = pricing_for_model("gpt-5.6-terra")

    assert pricing["model_key"] == "gpt-5.6-terra"
    assert pricing["label"] == "GPT-5.6 Terra"
    assert estimate_cost_usd(100_000, 100_000, model_name="gpt-5.6-terra") == 1.4


def test_gpt_56_cost_estimator_prices_cache_writes_and_long_context() -> None:
    assert estimate_cost_usd(
        1_000_000,
        1_000_000,
        model_name="gpt-5.6-terra",
    ) == 22.0
    assert estimate_cost_usd(
        100_000,
        0,
        model_name="gpt-5.6-terra",
        cache_write_prompt_tokens=100_000,
    ) == 0.25


def test_usage_ledger_preserves_provider_cache_write_tokens() -> None:
    response = SimpleNamespace(
        model="gpt-5.6-terra",
        usage=SimpleNamespace(
            prompt_tokens=1000,
            completion_tokens=100,
            total_tokens=1100,
            prompt_tokens_details=SimpleNamespace(
                cached_tokens=100,
                cache_write_tokens=400,
            ),
        ),
    )

    usage = usage_from_response(response, "diagnostic_bundle_escalation")

    assert usage["cached_prompt"] == 100
    assert usage["cache_write_prompt"] == 400
    assert usage["non_cached_prompt"] == 900
    assert usage["estimated_cost_usd"] == 0.00322


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


def test_mock_structured_parse_uses_response_format_stage_and_exposes_parsed_message(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    monkeypatch.setenv("KG_LLM_FIXTURE", "structured_fixture")
    monkeypatch.setenv("KG_LLM_MOCK_DIR", str(tmp_path))

    payload = {
        "schema_version": "diagnostic_bundle_v1",
        "bundles": [{"record_anchor": "ev_record", "branch_anchor": "ev_branch"}],
    }
    fixture_dir = tmp_path / "structured_fixture"
    fixture_dir.mkdir()
    (fixture_dir / "diagnostic_bundles.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    # If prompt-based stage detection won, this incompatible ontology fixture
    # would be selected instead of the response-format-specific fixture.
    (fixture_dir / "ontology.json").write_text(
        json.dumps({"ontology_name": "WrongStage"}),
        encoding="utf-8",
    )

    response = get_client().chat.completions.parse(
        model="mock-structured",
        response_format=DiagnosticChunkOutput,
        messages=[{"role": "user", "content": "Extract diagnostic ontology nodes."}],
    )
    message = response.choices[0].message

    assert response.id == "chatcmpl-mock"
    assert response.model == "mock-structured"
    assert response.usage.total_tokens == 0
    assert response.choices[0].finish_reason == "stop"
    assert json.loads(message.content) == payload
    assert message.parsed == DiagnosticChunkOutput.model_validate(payload)
    assert message.refusal is None


def test_mock_async_structured_parse_matches_sync_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    monkeypatch.setenv("KG_LLM_FIXTURE", "async_structured_fixture")
    monkeypatch.setenv("KG_LLM_MOCK_DIR", str(tmp_path))

    payload = {
        "schema_version": "diagnostic_bundle_v1",
        "bundles": [{"record_anchor": "ev_async_record", "branch_anchor": "ev_async_branch"}],
    }
    fixture_dir = tmp_path / "async_structured_fixture"
    fixture_dir.mkdir()
    (fixture_dir / "diagnostic_bundles.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    async def run():
        return await get_async_client().chat.completions.parse(
            model="mock-structured-async",
            response_format=DiagnosticChunkOutput,
            messages=[{"role": "user", "content": "Extract diagnostic bundles."}],
        )

    response = asyncio.run(run())
    message = response.choices[0].message

    assert response.id == "chatcmpl-mock"
    assert response.model == "mock-structured-async"
    assert response.usage.total_tokens == 0
    assert response.choices[0].finish_reason == "stop"
    assert json.loads(message.content) == payload
    assert message.parsed == DiagnosticChunkOutput.model_validate(payload)
    assert message.refusal is None


def test_mock_resolution_stage_wins_over_generic_ontology(monkeypatch):
    monkeypatch.setenv("KG_LLM_MODE", "mock")

    response = get_client().chat.completions.create(
        model="mock",
        messages=[{
            "role": "system",
            "content": (
                "You complete missing troubleshooting resolution links in an "
                "ontology-first extraction pipeline. CURRENT ONTOLOGY NODES"
            ),
        }],
    )

    assert json.loads(response.choices[0].message.content) == {
        "status": "not_found",
        "failure_mode": {},
        "corrective_actions": [],
    }


def test_mock_without_fixture_env_keeps_generic_replies(monkeypatch):
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    monkeypatch.delenv("KG_LLM_FIXTURE", raising=False)

    client = get_client()
    response = client.chat.completions.create(
        model="mock",
        messages=[{"role": "user", "content": "Extract the ontology nodes from this manual."}],
    )
    message = response.choices[0].message

    assert response.id == "chatcmpl-mock"
    assert response.choices[0].finish_reason == "stop"
    assert json.loads(message.content)["ontology_name"] == "MockMaintenanceOntology"
    assert message.parsed is None
    assert message.refusal is None
