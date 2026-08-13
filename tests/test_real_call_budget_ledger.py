from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.services import llm_gateway
from backend.services.real_call_budget_ledger import (
    ActualTokenUsage,
    BudgetConfigurationError,
    BudgetExceededError,
    LedgerCorruptionError,
    RealCallBudgetLedger,
    TokenEnvelope,
)


def _fixed_cost(
    envelope: TokenEnvelope,
    pricing: dict,
) -> Decimal:
    del envelope, pricing
    return Decimal("0.25")


def _ledger(path: Path, budget: str = "1.00") -> RealCallBudgetLedger:
    return RealCallBudgetLedger(
        path,
        absolute_budget_usd=budget,
        envelope_cost_estimator=_fixed_cost,
    )


def _reserve(
    ledger: RealCallBudgetLedger,
    call_id: str,
    *,
    worst_case: str | None = None,
):
    kwargs = {
        "call_id": call_id,
        "stage": "diagnostic_bundle_primary",
        "run_id": "run-001",
        "pdf_id": "manual-sha256:abc",
        "model": "gpt-5.6-luna",
        "reasoning_effort": "medium",
        "token_envelope": TokenEnvelope(
            max_prompt_tokens=12_000,
            max_completion_tokens=4_000,
        ),
    }
    if worst_case is not None:
        kwargs["worst_case_cost_usd"] = worst_case
    return ledger.reserve(**kwargs)


def test_reservation_is_fsynced_with_complete_audit_metadata(tmp_path: Path) -> None:
    path = tmp_path / "real_calls.jsonl"
    ledger = _ledger(path)

    reservation = _reserve(ledger, "call-1")

    assert reservation.worst_case_cost_usd == Decimal("0.250000000000")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    header, event = map(json.loads, lines)
    assert header["event"] == "ledger_initialized"
    assert header["absolute_budget_usd"] == 1.0
    assert event["event"] == "call_reserved"
    assert event["call_id"] == "call-1"
    assert event["stage"] == "diagnostic_bundle_primary"
    assert event["run_id"] == "run-001"
    assert event["pdf_id"] == "manual-sha256:abc"
    assert event["model"] == "gpt-5.6-luna"
    assert event["reasoning_effort"] == "medium"
    assert event["token_envelope"]["max_prompt_tokens"] == 12_000
    assert event["token_envelope"]["max_completion_tokens"] == 4_000
    assert event["pricing_snapshot"]["model_key"] == "gpt-5.6-luna"
    assert "prompt" not in event
    assert "api_key" not in json.dumps(event).lower()


def test_sequential_reservations_charge_actual_and_active_worst_case(tmp_path: Path) -> None:
    path = tmp_path / "real_calls.jsonl"
    ledger = _ledger(path)

    _reserve(ledger, "call-1")
    _reserve(ledger, "call-2")
    ledger.finalize("call-1", status="succeeded", actual_cost_usd="0.10")

    snapshot = ledger.snapshot()
    assert snapshot.committed_usd == Decimal("0.100000000000")
    assert snapshot.active_reserved_usd == Decimal("0.250000000000")
    assert snapshot.remaining_usd == Decimal("0.650000000000")
    assert snapshot.reservation_count == 2
    assert snapshot.finalized_count == 1


def test_over_budget_is_rejected_without_writing_reservation(tmp_path: Path) -> None:
    path = tmp_path / "real_calls.jsonl"
    ledger = _ledger(path, budget="0.40")
    _reserve(ledger, "call-1")

    with pytest.raises(BudgetExceededError) as exc_info:
        _reserve(ledger, "call-2")

    assert exc_info.value.requested_usd == Decimal("0.250000000000")
    assert [event["event"] for event in ledger.events()] == [
        "ledger_initialized",
        "call_reserved",
    ]


def test_unfinished_crash_reservation_survives_reopen_and_blocks_call(tmp_path: Path) -> None:
    path = tmp_path / "real_calls.jsonl"
    first_process = _ledger(path, budget="0.40")
    _reserve(first_process, "crashed-call")
    del first_process

    recovered = _ledger(path, budget="0.40")
    assert recovered.snapshot().active_reserved_usd == Decimal("0.250000000000")
    with pytest.raises(BudgetExceededError):
        _reserve(recovered, "post-crash-call")


def test_finalize_from_usage_releases_unused_reservation(tmp_path: Path) -> None:
    path = tmp_path / "real_calls.jsonl"
    ledger = RealCallBudgetLedger(path, absolute_budget_usd="1.00")
    reservation = _reserve(ledger, "call-1")

    finalized = ledger.finalize(
        reservation.call_id,
        status="succeeded",
        usage=ActualTokenUsage(
            prompt_tokens=1_000,
            completion_tokens=500,
            cached_prompt_tokens=200,
            cache_write_prompt_tokens=300,
        ),
    )

    # Luna: 500 ordinary @ .20/M, 200 cached @ .02/M,
    # 300 cache writes @ .25/M, and 500 output @ 1.20/M.
    assert finalized.actual_cost_usd == Decimal("0.000779000000")
    assert finalized.charged_cost_usd == Decimal("0.000779000000")
    assert not finalized.envelope_breached
    snapshot = ledger.snapshot()
    assert snapshot.active_reserved_usd == Decimal("0E-12")
    assert snapshot.committed_usd == Decimal("0.000779000000")


def test_unknown_usage_failure_keeps_worst_case(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path / "real_calls.jsonl")
    _reserve(ledger, "call-1")

    finalized = ledger.finalize("call-1", status="network_error_unknown_usage")

    assert finalized.actual_cost_usd is None
    assert finalized.charged_cost_usd == Decimal("0.250000000000")
    assert ledger.snapshot().committed_usd == Decimal("0.250000000000")


def test_context_manager_keeps_worst_case_when_caller_forgets_finalize(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path / "real_calls.jsonl")

    with ledger.call(
        call_id="call-1",
        stage="scoping",
        run_id="run-001",
        pdf_id="manual-sha256:abc",
        model="gpt-5.6-luna",
        reasoning_effort="medium",
        token_envelope=TokenEnvelope(5_000, 2_000),
    ):
        pass

    event = ledger.events()[-1]
    assert event["status"] == "completed_unknown_cost"
    assert event["charged_cost_usd"] == 0.25


def test_cancelled_before_call_releases_entire_reservation(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path / "real_calls.jsonl")
    reserved = ledger.call(
        call_id="call-1",
        stage="scoping",
        run_id="run-001",
        pdf_id="manual-sha256:abc",
        model="gpt-5.6-luna",
        reasoning_effort="medium",
        token_envelope=TokenEnvelope(5_000, 2_000),
    )

    finalized = reserved.mark_not_called()

    assert finalized.charged_cost_usd == Decimal("0E-12")
    assert ledger.snapshot().remaining_usd == Decimal("1.000000000000")


def test_concurrent_reservations_are_atomic_and_never_oversubscribe(tmp_path: Path) -> None:
    path = tmp_path / "real_calls.jsonl"
    ledger = _ledger(path, budget="1.00")

    def attempt(index: int) -> str:
        try:
            _reserve(ledger, f"call-{index}")
        except BudgetExceededError:
            return "rejected"
        return "reserved"

    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(attempt, range(20)))

    assert results.count("reserved") == 4
    assert results.count("rejected") == 16
    snapshot = ledger.snapshot()
    assert snapshot.active_reserved_usd == Decimal("1.000000000000")
    assert snapshot.remaining_usd == Decimal("0E-12")
    assert snapshot.reservation_count == 4


def test_existing_ledger_rejects_different_absolute_budget(tmp_path: Path) -> None:
    path = tmp_path / "real_calls.jsonl"
    _ledger(path, budget="1.00")

    with pytest.raises(BudgetConfigurationError):
        _ledger(path, budget="0.99")


def test_budget_can_only_be_increased_with_append_only_authorization(
    tmp_path: Path,
) -> None:
    path = tmp_path / "real_calls.jsonl"
    ledger = _ledger(path, budget="1.00")
    _reserve(ledger, "call-1")
    ledger.finalize("call-1", status="succeeded", actual_cost_usd="0.10")

    increased = ledger.increase_budget(
        "3.00",
        authorization_note="Operator raised the cumulative absolute cap.",
    )

    snapshot = increased.snapshot()
    assert snapshot.absolute_budget_usd == Decimal("3.000000000000")
    assert snapshot.committed_usd == Decimal("0.100000000000")
    assert snapshot.remaining_usd == Decimal("2.900000000000")
    assert increased.events()[-1] == {
        "schema_version": 1,
        "event": "budget_increased",
        "timestamp": increased.events()[-1]["timestamp"],
        "previous_absolute_budget_usd": 1.0,
        "absolute_budget_usd": 3.0,
        "authorization_note": "Operator raised the cumulative absolute cap.",
    }
    with pytest.raises(BudgetConfigurationError):
        _ledger(path, budget="1.00")


def test_torn_jsonl_fails_closed_instead_of_ignoring_reservation(tmp_path: Path) -> None:
    path = tmp_path / "real_calls.jsonl"
    _ledger(path)
    with path.open("ab") as stream:
        stream.write(b'{"event":"call_reserved"')

    with pytest.raises(LedgerCorruptionError):
        _ledger(path)


def test_llm_gateway_persists_reservation_before_real_client_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "gateway_calls.jsonl"
    observed_events: list[str] = []

    class FakeCompletions:
        def create(self, **kwargs):
            del kwargs
            observed_events.extend(
                event["event"]
                for event in RealCallBudgetLedger(
                    path, absolute_budget_usd="1.00"
                ).events()
            )
            return SimpleNamespace(
                usage=SimpleNamespace(
                    prompt_tokens=100,
                    completion_tokens=20,
                    prompt_tokens_details=SimpleNamespace(
                        cached_tokens=0, cache_write_tokens=0,
                    ),
                )
            )

    class FakeClient:
        def __init__(self, **kwargs):
            del kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("KG_LLM_MODE", "real")
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_LEDGER", str(path))
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_USD", "1.00")
    monkeypatch.setenv("KG_REAL_CALL_RUN_ID", "run-gateway")
    monkeypatch.setenv("KG_REAL_CALL_PDF_ID", "pdf-gateway")
    llm_gateway._BUDGET_LEDGERS.clear()

    client = llm_gateway.get_client(client_factory=FakeClient, api_key="not-secret")
    client.chat.completions.create(
        model="gpt-5.6-luna",
        reasoning_effort="medium",
        max_completion_tokens=100,
        messages=[{"role": "user", "content": "bounded request"}],
    )

    assert observed_events[-1] == "call_reserved"
    events = RealCallBudgetLedger(path, absolute_budget_usd="1.00").events()
    assert events[-1]["event"] == "call_finalized"
    assert events[-1]["status"] == "succeeded"
    assert events[-1]["actual_usage"]["prompt_tokens"] == 100


def test_llm_gateway_blocks_over_budget_before_client_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "blocked_gateway_calls.jsonl"
    called = False

    class FakeCompletions:
        def create(self, **kwargs):
            del kwargs
            nonlocal called
            called = True

    class FakeClient:
        def __init__(self, **kwargs):
            del kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("KG_LLM_MODE", "real")
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_LEDGER", str(path))
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_USD", "0.000001")
    monkeypatch.setenv("KG_REAL_CALL_RUN_ID", "run-blocked")
    monkeypatch.setenv("KG_REAL_CALL_PDF_ID", "pdf-blocked")
    llm_gateway._BUDGET_LEDGERS.clear()
    client = llm_gateway.get_client(client_factory=FakeClient, api_key="not-secret")

    with pytest.raises(BudgetExceededError):
        client.chat.completions.create(
            model="gpt-5.6-terra",
            max_completion_tokens=4000,
            messages=[{"role": "user", "content": "must not run"}],
        )
    assert called is False


def test_budgeted_gateway_disables_sdk_internal_retries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}

    class FakeClient:
        def __init__(self, **kwargs):
            observed.update(kwargs)
            self.chat = SimpleNamespace(completions=SimpleNamespace())

    monkeypatch.setenv("KG_LLM_MODE", "real")
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_LEDGER", str(tmp_path / "calls.jsonl"))
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_USD", "1.00")
    monkeypatch.setenv("KG_REAL_CALL_RUN_ID", "run-no-sdk-retry")
    monkeypatch.setenv("KG_REAL_CALL_PDF_ID", "pdf-no-sdk-retry")
    llm_gateway._BUDGET_LEDGERS.clear()

    llm_gateway.get_client(
        client_factory=FakeClient,
        api_key="not-secret",
        max_retries=7,
    )

    assert observed["max_retries"] == 0


def test_gateway_attaches_fail_closed_accounting_to_parse_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ProviderParseError(ValueError):
        pass

    class FakeCompletions:
        def parse(self, **kwargs):
            del kwargs
            raise ProviderParseError("typed payload invalid")

    class FakeClient:
        def __init__(self, **kwargs):
            del kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("KG_LLM_MODE", "real")
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_LEDGER", str(tmp_path / "calls.jsonl"))
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_USD", "1.00")
    monkeypatch.setenv("KG_REAL_CALL_RUN_ID", "run-parse-failure")
    monkeypatch.setenv("KG_REAL_CALL_PDF_ID", "pdf-parse-failure")
    llm_gateway._BUDGET_LEDGERS.clear()
    client = llm_gateway.get_client(client_factory=FakeClient, api_key="not-secret")

    with pytest.raises(ProviderParseError) as captured:
        client.chat.completions.parse(
            model="gpt-5.6-terra",
            max_completion_tokens=100,
            messages=[{"role": "user", "content": "typed call"}],
        )

    accounting = captured.value._kg_call_accounting
    assert accounting["status"] == "failed_unknown_cost"
    assert accounting["model"] == "gpt-5.6-terra"
    assert accounting["charged_cost_usd"] > 0
    assert accounting["actual_cost_usd"] is None


def test_real_call_stage_prefers_ontology_over_embedded_toc_context() -> None:
    stage = llm_gateway._real_call_stage(
        "create",
        {
            "messages": [{
                "role": "system",
                "content": (
                    "You are an ontology extraction agent. "
                    "The retained context includes a table of contents."
                ),
            }],
        },
    )

    assert stage == "chat.create:ontology"
