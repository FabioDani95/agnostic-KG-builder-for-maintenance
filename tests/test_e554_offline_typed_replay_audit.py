from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    REPOSITORY_ROOT
    / "artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554"
    / "offline_typed_replay_evidence_audit.json"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_e554_offline_replay_audit_is_pinned_to_persisted_v5_v6_inputs() -> None:
    audit = _load(AUDIT_PATH)

    assert audit["kind"] == "offline_e554_typed_replay_evidence_audit"
    assert audit["status"] == "blocked_missing_persisted_source_evidence"
    assert audit["scope"] == {
        "fixture_type": "test_artifact_only",
        "manual": "E-554.pdf",
        "pages": [37, 38, 39],
        "production_rules_changed": False,
        "api_calls": 0,
    }

    loaded_sources: dict[str, dict[str, Any]] = {}
    for source_name, source in audit["sources"].items():
        path = REPOSITORY_ROOT / source["path"]
        assert path.is_file(), source_name
        assert _sha256(path) == source["sha256"], source_name
        if path.suffix == ".json":
            loaded_sources[source_name] = _load(path)

    gold = loaded_sources["gold"]
    v5 = loaded_sources["v5_generation_response"]
    run_state = loaded_sources["v5_run_state"]
    v6 = loaded_sources["v6_microbenchmark"]

    assert len(gold["minimum_expected_manual_chains"]) == 8
    assert len(gold["forbidden_cross_pairings"]) == 3
    assert run_state["source_preparation"]["evidence_count"] == 895

    revision = v5["sources"][0]["subgraph"]
    evidence = revision["evidence"]
    assert len(evidence) == 358
    assert sum(
        isinstance(item["locator"].get("page"), int)
        and 37 <= item["locator"]["page"] <= 39
        for item in evidence
    ) == 39

    causal_relation_types = {"MAY_INDICATE", "INDICATES", "RESOLVED_BY"}
    diagnostic_relations_on_target_pages = [
        relation
        for relation in revision["relations"]
        if relation.get("relation_type") in causal_relation_types
        and any(
            isinstance(ref["locator"].get("page"), int)
            and 37 <= ref["locator"]["page"] <= 39
            for ref in relation.get("evidence_refs", [])
        )
    ]
    assert diagnostic_relations_on_target_pages == []

    assert v6["input_pages"] == [37, 38, 39]
    assert "evidence_units" not in v6
    assert "canonical_page_text" not in v6
    assert "text_with_pages" not in v6

    inventory = audit["persisted_inventory"]
    assert inventory["v5_prepared_evidence_count_reported"] == 895
    assert inventory["v5_published_revision_evidence_count"] == len(evidence)
    assert inventory["v5_published_revision_evidence_pages_37_39"] == 39
    assert inventory["v5_diagnostic_relations_with_evidence_on_pages_37_39"] == 0
    assert inventory["v6_raw_input_evidence_units_persisted"] is False
    assert inventory["v6_canonical_page_text_persisted"] is False


def test_e554_offline_replay_audit_accounts_for_all_gold_without_fake_fixture() -> None:
    audit = _load(AUDIT_PATH)
    gold = _load(REPOSITORY_ROOT / audit["sources"]["gold"]["path"])
    v5 = _load(REPOSITORY_ROOT / audit["sources"]["v5_generation_response"]["path"])
    evidence_by_id = {
        item["evidence_id"]: item
        for item in v5["sources"][0]["subgraph"]["evidence"]
    }

    chains = audit["chains"]
    assert [chain["gold_index"] for chain in chains] == list(range(1, 9))
    assert len(chains) == len(gold["minimum_expected_manual_chains"])

    for chain in chains:
        for reference in chain["available_evidence"]:
            persisted = evidence_by_id[reference["evidence_id"]]
            assert persisted["locator"]["page"] == reference["page"]
            assert persisted["locator"]["quote"].strip()
            assert reference["supports"]
        if chain["evidence_status"] == "blocked":
            assert chain["missing_requirements"]
        else:
            assert chain["evidence_status"] == "sufficient_for_source_grounded_candidate"
            assert chain["missing_requirements"] == []

    assert [
        chain["gold_index"]
        for chain in chains
        if chain["evidence_status"] == "sufficient_for_source_grounded_candidate"
    ] == [1, 5]
    assert [
        chain["gold_index"]
        for chain in chains
        if chain["evidence_status"] == "blocked"
    ] == [2, 3, 4, 6, 7, 8]

    decision = audit["decision"]
    assert decision["diagnostic_chunk_output_fixture_created"] is False
    assert decision["deterministic_compiler_replay_executed"] is False
    assert decision["gold_chains_total"] == 8
    assert decision["gold_chains_certified_replayable_from_persisted_v5_v6_source_evidence"] == 2
    assert decision["gold_chains_verified_by_compiler"] is None
    assert decision["forbidden_cross_pairings_total"] == 3
    assert decision["forbidden_cross_pairings_verified_by_compiler"] is None
    assert decision["schema_invariants_verified"] is False
    assert decision["topology_invariants_verified"] is False

    forbidden = audit["forbidden_cross_pairings"]
    assert forbidden == {
        "count": len(gold["forbidden_cross_pairings"]),
        "evaluation_status": "not_run_without_complete_compiled_replay",
        "found": None,
    }


def test_e554_missing_gold_text_is_not_misclassified_as_v6_source_evidence() -> None:
    audit = _load(AUDIT_PATH)
    v5 = _load(REPOSITORY_ROOT / audit["sources"]["v5_generation_response"]["path"])
    v6 = _load(REPOSITORY_ROOT / audit["sources"]["v6_microbenchmark"]["path"])

    target_quotes = "\n".join(
        item["locator"]["quote"]
        for item in v5["sources"][0]["subgraph"]["evidence"]
        if isinstance(item["locator"].get("page"), int)
        and 37 <= item["locator"]["page"] <= 39
    ).casefold()
    assert "select save and exit" not in target_quotes
    assert "click and drag the tool to the spindle" not in target_quotes
    assert "loss of laser cutting power" not in target_quotes
    assert "non-cut edges" not in target_quotes

    generated_v6_output = json.dumps(v6["ontology"], ensure_ascii=False).casefold()
    assert "select save and exit" in generated_v6_output
    assert "click and drag the tool to the spindle" in generated_v6_output
    assert "loss of laser cutting power" in generated_v6_output
    assert v6["relation_counts"] == {"HAS_COMPONENT": 34}

    excluded = {item["path"]: item["reason"] for item in audit["excluded_non_evidence"]}
    assert audit["sources"]["v6_microbenchmark"]["path"] in excluded
    assert "tests/golden/manuals/eagle_s3l_laser_cutter_manual.md" in excluded
