"""Model gateway and price estimates used by every V3 model call."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.services.llm_gateway import (
    chat_reasoning_kwargs,
    chat_temperature_kwargs,
    get_client,
)
from backend.services.model_pricing import (
    estimate_cost_usd,
    pricing_for_model,
    usage_from_response,
)


def test_gateway_defaults_to_real_mode_and_uses_real_factory(monkeypatch):
    monkeypatch.delenv("KG_LLM_MODE", raising=False)
    calls = []

    class FakeRealClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)
            self.chat = SimpleNamespace(completions=SimpleNamespace())

    client = get_client(timeout=3, api_key="key-real", client_factory=FakeRealClient)

    assert isinstance(client._wrapped, FakeRealClient)
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


def test_gpt_6_luna_rates_used_by_the_campaign():
    pricing = pricing_for_model("gpt-6-luna")
    assert (pricing["input_per_million"], pricing["output_per_million"]) == (0.10, 0.50)




def test_an_image_is_reserved_by_a_bounded_allowance_not_by_its_base64_length():
    from backend.services.llm_gateway import _real_call_envelope

    text = {"model": "gpt-6-luna", "messages": [{"role": "user", "content": "Read the flowchart."}],
            "max_completion_tokens": 4000}
    image = "data:image/png;base64," + "A" * 400_000
    with_image = {**text, "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Read the flowchart."},
        {"type": "image_url", "image_url": {"url": image, "detail": "high"}}]}]}
    plain, pictured = _real_call_envelope(text), _real_call_envelope(with_image)
    assert 6000 <= pictured.max_prompt_tokens - plain.max_prompt_tokens < 6200
