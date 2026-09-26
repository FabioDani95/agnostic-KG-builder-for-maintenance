from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.services.diagnostic_response_parsing import parse_diagnostic_records
from backend.services.llm_gateway import get_client
from backend.services.ontology_workflow import _run_chunk_with_retry, _split_pages_by_section


def _fixture():
    return json.loads(Path("tests/fixtures/typed_diagnostic_integration/diagnostic_bundles.json").read_text())


def test_invalid_record_preserves_valid_sibling_without_schema_repair():
    payload = _fixture()
    good = copy.deepcopy(payload["records"][0])
    bad = copy.deepcopy(good)
    bad["indicators"] = []
    payload["records"] = [good, bad]
    parsed = parse_diagnostic_records(json.dumps(payload))
    assert len(parsed.output.records) == 1
    assert parsed.output.records[0].record_anchor == good["record_anchor"]
    assert parsed.rejected[0]["index"] == 1
    assert parsed.rejected[0]["payload"] == bad
    assert parsed.rejected[0]["errors"]


@pytest.mark.parametrize("raw", ['{"records":[', '{"schema_version":"wrong","source_language":"en","records":[]}', '{"schema_version":"1.0","source_language":"en","records":[],"extra":1}'])
def test_incomplete_or_invalid_envelope_is_not_repaired(raw):
    assert parse_diagnostic_records(raw).output is None


def test_provider_usage_and_raw_body_are_archived_before_local_validation(monkeypatch, tmp_path):
    monkeypatch.setenv("KG_LLM_MODE", "real")
    monkeypatch.setenv("KG_LLM_TRACE_DIR", str(tmp_path / "responses"))
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_LEDGER", str(tmp_path / "budget.jsonl"))
    monkeypatch.setenv("KG_REAL_CALL_BUDGET_USD", "0.10")
    monkeypatch.setenv("KG_REAL_CALL_RUN_ID", "offline-fake")
    monkeypatch.setenv("KG_REAL_CALL_PDF_ID", "synthetic")
    response = SimpleNamespace(
        id="fake-paid-response", model="gpt-6-luna",
        choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content='{"records":42}', refusal=None))],
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=30, total_tokens=130),
    )
    class FakeProvider:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))

    received = get_client(client_factory=FakeProvider, api_key="must-not-be-saved").chat.completions.create(
        model="gpt-6-luna", messages=[{"role": "user", "content": "synthetic input"}], max_completion_tokens=100,
    )
    assert parse_diagnostic_records(received.choices[0].message.content).output is None
    archive = Path(received._kg_response_archive)
    payload = json.loads(archive.read_text())
    assert payload["response"]["usage"]["completion_tokens"] == 30
    assert payload["response"]["choices"][0]["message"]["content"] == '{"records":42}'
    assert "must-not-be-saved" not in archive.read_text()
    events = [json.loads(x) for x in (tmp_path / "budget.jsonl").read_text().splitlines()]
    assert events[-1]["status"] == "succeeded"


def test_returned_transport_failure_retries_and_keeps_all_usage():
    calls = []
    def operation():
        calls.append(1)
        report = {"parsed": len(calls) > 1, "error_status_code": 503 if len(calls) == 1 else None}
        return SimpleNamespace(diagnostic_contract_report=report), {"llm_calls": 1, "prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30, "estimated_cost_usd": 0.01, "llm_call_entries": [{"attempt": len(calls)}]}
    result, metrics = asyncio.run(_run_chunk_with_retry(operation, attempts=3, base_delay_seconds=0))
    assert len(calls) == 2
    assert result.diagnostic_contract_report["parsed"]
    assert len(result.diagnostic_contract_report["transport_attempts"]) == 2
    assert metrics["llm_calls"] == 2
    assert metrics["total_tokens"] == 60
    assert metrics["estimated_cost_usd"] == 0.02
    assert len(metrics["llm_call_entries"]) == 2


def test_refusal_and_record_schema_failure_are_not_transport_retried():
    for report in ({"parsed": False, "refusal": True}, {"parsed": True, "invalid_record_count": 2}):
        calls = []
        def operation():
            calls.append(1)
            return {"diagnostic_contract_report": report}
        asyncio.run(_run_chunk_with_retry(operation, attempts=3, base_delay_seconds=0))
        assert len(calls) == 1


def test_overlap_respects_limits_preserves_pages_and_never_bridges_scope_gaps():
    pages = [{"page_number": i, "text": "x" * 40} for i in [1, 2, 3, 4, 5, 6, 9, 10]]
    chunks = _split_pages_by_section(pages, [], max_chars=190, max_pages=3, overlap_pages=1)
    assert {p["page_number"] for chunk, _ in chunks for p in chunk} == {p["page_number"] for p in pages}
    for chunk, _ in chunks:
        assert len(chunk) <= 3
        assert sum(len(f"--- PAGE {p['page_number']} ---\n{p['text']}\n\n") for p in chunk) <= 190
        assert all(b["page_number"] == a["page_number"] + 1 for a, b in zip(chunk, chunk[1:]))
    assert any(chunk[0]["page_number"] == 3 for chunk, _ in chunks)


def test_recovery_is_bounded_and_preserves_continuation_context():
    from backend.services.diagnostic_recovery import recovery_packets
    pages = [{"page_number": n, "text": str(n)} for n in range(10, 14)]
    packets = recovery_packets({"finish_reason": "length"}, pages, [], limit=2)
    assert len(packets) == 2
    assert {p["page_number"] for packet, _ in packets for p in packet} == {10, 11, 12, 13}
    assert set(p["page_number"] for p in packets[0][0]) & set(p["page_number"] for p in packets[1][0]) == {12}
    assert not recovery_packets({"finish_reason": "length", "refusal": True}, pages, [], limit=2)


def test_record_recovery_targets_only_failed_record_pages():
    from backend.services.diagnostic_recovery import recovery_packets
    report = {"records": [{"accounting_state": "record_schema_invalid", "invalid_payload": {"claim_evidence": [{"source_page": 12}]}}]}
    pages = [{"page_number": n, "text": str(n)} for n in range(10, 14)]
    assert recovery_packets(report, pages, [], limit=2) == [([pages[2]], [])]


def test_aliases_expand_only_anchor_fields_without_changing_literal_quotes():
    payload = _fixture()
    good = payload["records"][0]
    anchor = good["record_anchor"]
    raw = json.dumps(payload).replace(anchor, "a0001")
    parsed = parse_diagnostic_records(raw, anchor_aliases={"a0001": anchor})
    assert parsed.output.records[0].record_anchor == anchor
    assert parsed.output.records[0].indicators[0].name == good["indicators"][0]["name"]


def test_unknown_model_is_rejected_before_budget_reservation(tmp_path):
    from backend.services.real_call_budget_ledger import BudgetConfigurationError, RealCallBudgetLedger, TokenEnvelope
    ledger = RealCallBudgetLedger(tmp_path / "budget.jsonl", absolute_budget_usd="20")
    with pytest.raises(BudgetConfigurationError):
        ledger.reserve(stage="test", run_id="test", pdf_id="pdf", model="unpriced-model", reasoning_effort="low", token_envelope=TokenEnvelope(100, 100))
    assert ledger.snapshot().reservation_count == 0


def test_long_corrupt_native_text_is_eligible_for_ocr_but_numeric_tables_are_not():
    from backend.services.pdf_service import native_text_is_corrupt
    assert native_text_is_corrupt("a" * 900 + "\x01" * 40)
    assert not native_text_is_corrupt("230 V 24 V 50 Hz 3.3 5.0 2.2 ±10% " * 40)


def test_generic_sdk_parse_archives_raw_usage_even_if_local_schema_fails(monkeypatch, tmp_path):
    from openai.types.chat import ChatCompletion
    from pydantic import BaseModel, ValidationError
    class RequiredValue(BaseModel):
        value: int
    response = ChatCompletion.model_validate({"id": "offline-response", "object": "chat.completion", "created": 0, "model": "gpt-6-luna", "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": '{"value":"bad"}'}}], "usage": {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}})
    class Provider:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))
    monkeypatch.setenv("KG_LLM_MODE", "real")
    monkeypatch.setenv("KG_LLM_TRACE_DIR", str(tmp_path))
    monkeypatch.delenv("KG_REAL_CALL_BUDGET_LEDGER", raising=False)
    monkeypatch.delenv("KG_REAL_CALL_BUDGET_USD", raising=False)
    with pytest.raises(ValidationError) as failed:
        get_client(client_factory=Provider, api_key="not-used").chat.completions.parse(model="gpt-6-luna", messages=[], response_format=RequiredValue, max_completion_tokens=100)
    assert failed.value.completion.usage.total_tokens == 16
    saved = json.loads(Path(failed.value._kg_response_archive).read_text())
    assert saved["response"]["choices"][0]["message"]["content"] == '{"value":"bad"}'
    assert saved["local_validation"]["status"] == "failed"


def test_plain_parameter_rows_do_not_become_missing_diagnostic_records():
    from backend.services.ontology_pipeline import _diagnostic_input_inventory
    text = "--- PAGE 1 ---\n[[EVIDENCE_ID: ev_parameters01]]\nVoltage | Frequency | Width\n[[EVIDENCE_ID: ev_parameters02]]\n230 V | 50 Hz | 20 cm"
    assert not _diagnostic_input_inventory(text)["candidate_input_anchors"]
    text = "--- PAGE 1 ---\n[[EVIDENCE_ID: ev_headers0001]]\nProblem | Cause | Remedy\n[[EVIDENCE_ID: ev_datarow0001]]\nLow pressure | Stuck valve | Open valve"
    assert "ev_datarow0001" in _diagnostic_input_inventory(text)["candidate_input_anchors"]
