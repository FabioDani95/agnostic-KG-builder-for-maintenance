"""Document regression tests, not independent semantic gold."""
import json
from pathlib import Path

from backend.domain.evidence import EvidenceUnit
from backend.services.diagnostic_bundle_compiler import compile_diagnostic_bundles
from backend.services.diagnostic_recovery import procedure_context_packets, recovery_packets
from backend.services.ontology_semantics import normalize_severity

FIXTURE = Path(__file__).parent / "fixtures/diagnostic_procedure_recovery"


def compile_profile(profile, units=None):
    units = units or [EvidenceUnit.model_validate(x) for x in json.loads((FIXTURE / "source.json").read_text())["evidence"]]
    return compile_diagnostic_bundles(json.loads((FIXTURE / f"{profile}_candidates.json").read_text()),
        source_type="technical PDF", source_title="hypertherm_powermax30_air_service_manual_rev4_808850.pdf", evidence_units=units)


def test_explicit_causal_list_recovers_links_but_not_unlisted_wire_failure():
    result = compile_profile("low")
    assert result.report.disposition_counts["publish"] == 4
    wire = next(e for e in result.report.entries if "wires" in e.candidate["failure"]["name"])
    assert wire.disposition == "review"
    for entry in result.report.entries:
        if entry.disposition == "publish":
            record = entry.validated_record
            assert record.procedure_context
            assert not record.procedure_path_verified
            assert any("disconnect the power cord" in s.quote for s in record.procedure_context)
            assert any("root cause may be" in s.quote for s in record.indicators[0].failure_link_evidence)


def test_causal_list_requires_explicit_intro_not_just_adjacent_bullets():
    units = [EvidenceUnit.model_validate(x) for x in json.loads((FIXTURE / "source.json").read_text())["evidence"]]
    changed = []
    for u in units:
        text = u.locator.quote.replace("the root cause may be:", "replacement parts:")
        changed.append(u.model_copy(update={"locator": u.locator.model_copy(update={"quote": text})}))
    assert compile_profile("low", changed).report.disposition_counts["publish"] == 0


def test_compound_negative_answer_is_not_two_negative_facts():
    result = compile_profile("medium")
    record = next(e for e in result.report.entries if (e.candidate.get("failure") or {}).get("name") == "Faulty internal compressor")
    assert record.disposition == "review"
    assert "compound_negative_condition_strengthened" in {r.code for r in record.drop_reasons}


def test_semantic_recovery_keeps_source_context_and_is_bounded():
    pages = [{"page_number": n, "text": "source"} for n in [8, 9]]
    report = {"records": [{"disposition": "review", "drop_reasons": [{"code": "relation_endpoint_support_unestablished"}]}]}
    assert recovery_packets(report, pages, [], limit=2) == [(pages, [])]
    assert recovery_packets(report, pages, [], limit=0) == []
    assert recovery_packets({**report, "refusal": True}, pages, [], limit=2) == []


def test_unknown_severity_is_not_an_invented_medium_risk():
    assert normalize_severity("Unknown") == "Unknown"


def test_named_procedure_recovers_continuations_across_role_partition():
    pages = [{"page_number": n, "text": f"Step on page {n}"} for n in range(1, 7)]
    pages[0]["text"] = "Test 12 – component checks"
    pages[5]["text"] = "Test 13 – next procedure"
    diagnostic = {1, 2, 5}
    assert procedure_context_packets([p for p in pages if p["page_number"] in diagnostic], max_chars=1000) == []
    assert procedure_context_packets(pages, max_chars=1000, diagnostic_page_numbers=diagnostic) == [pages[:5]]
    assert procedure_context_packets(pages, max_chars=10, diagnostic_page_numbers=diagnostic) == []
    assert procedure_context_packets(pages, max_chars=1000, diagnostic_page_numbers={5}) == []
