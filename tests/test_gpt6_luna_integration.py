from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.services.llm_gateway import chat_reasoning_kwargs, chat_temperature_kwargs
from backend.services.llm_service import call_openai_scoping
from backend.services.run_metrics import estimate_cost_usd, pricing_for_model, usage_from_response


@pytest.mark.parametrize("model", ["gpt-6-luna", "gpt-6-luna-2026-09-22"])
def test_luna_reasoning_payload_and_pricing_identity(model):
    assert chat_temperature_kwargs(model, 0.0) == {}
    for effort in ("none", "low", "medium", "high", "xhigh", "max"):
        assert chat_reasoning_kwargs(model, effort) == {"reasoning_effort": effort}
    with pytest.raises(ValueError, match="Unsupported reasoning_effort"):
        chat_reasoning_kwargs(model, "minimal")
    assert pricing_for_model(model)["model_key"] == "gpt-6-luna"


def test_luna_standard_cost_includes_cache_and_long_context_boundary():
    assert estimate_cost_usd(100_000, 100_000, model_name="gpt-6-luna") == pytest.approx(0.06)
    assert estimate_cost_usd(
        100_000, 0, cached_prompt_tokens=20_000,
        cache_write_prompt_tokens=30_000, model_name="gpt-6-luna",
    ) == pytest.approx(0.00895)
    assert estimate_cost_usd(272_000, 1000, model_name="gpt-6-luna") == pytest.approx(0.0277)
    assert estimate_cost_usd(272_001, 1000, model_name="gpt-6-luna") == pytest.approx(0.0551502)


def test_luna_usage_keeps_returned_model_and_cache_write_accounting():
    response = SimpleNamespace(
        model="gpt-6-luna",
        usage=SimpleNamespace(
            prompt_tokens=1000, completion_tokens=100, total_tokens=1100,
            prompt_tokens_details=SimpleNamespace(cached_tokens=100, cache_write_tokens=400),
        ),
    )
    usage = usage_from_response(response, "diagnostic_extraction")
    assert usage["model"] == "gpt-6-luna"
    assert usage["cache_write_prompt"] == 400
    assert usage["estimated_cost_usd"] == pytest.approx(0.000151)


def test_scoping_passes_luna_reasoning_without_sampling_parameters(monkeypatch):
    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            model=kwargs["model"], usage=None,
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"toc_entries": []}'))],
        )

    monkeypatch.setattr(
        "backend.services.llm_service.get_client",
        lambda **kwargs: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
    )
    raw, _ = call_openai_scoping("Extract the table of contents", model_name="gpt-6-luna", reasoning_effort="low")
    assert raw == '{"toc_entries": []}'
    assert captured["model"] == "gpt-6-luna"
    assert captured["reasoning_effort"] == "low"
    assert "temperature" not in captured
    assert "tools" not in captured
