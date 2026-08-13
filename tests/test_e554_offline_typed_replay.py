from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

from backend.adapters.pdf import ADAPTER_VERSION, PdfAdapter
from backend.domain.diagnostic_bundles import DiagnosticChunkOutput
from backend.domain.sources import Source
from backend.domain.workspace import Workspace
from backend.services.diagnostic_bundle_compiler import compile_diagnostic_bundles
from backend.services.ontology_pipeline import validate_ontology_instance

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REMOVAL_COMMIT = "d0d91ebbee3345f7663f10e1694b75bf94758d37"
HISTORICAL_PDF_PATH = (
    "manuals/batch_manuals/eagle_s3l_laser_cutting_system_service_manual.pdf"
)
PDF_BLOB = "a9671a82beba279a423db0f1ed9b1d9d678da204"
PDF_SHA256 = "a7467316234f2d84550e7c267bf709fda55e1023055d9569dc27348f192641d0"
TARGET_PAGES = {37, 38, 39}
FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "tests/fixtures/e554_offline_replay/diagnostic_chunk_output.json"
)
GOLD_PATH = REPOSITORY_ROOT / "artifacts/acceptance/g3/e554/gold.json"
RESULT_PATH = (
    REPOSITORY_ROOT
    / "artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554"
    / "offline_typed_replay_real_pdf_result.json"
)


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", value).strip()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _historical_pdf_bytes() -> bytes:
    try:
        resolved_blob = subprocess.run(
            ["git", "rev-parse", f"{REMOVAL_COMMIT}^:{HISTORICAL_PDF_PATH}"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        ).stdout.decode("ascii").strip()
        payload = subprocess.run(
            ["git", "cat-file", "blob", PDF_BLOB],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"Historical E-554 Git object is unavailable in this checkout: {exc}")
    assert resolved_blob == PDF_BLOB
    assert hashlib.sha256(payload).hexdigest() == PDF_SHA256
    return payload


def _workspace_and_source(pdf_size: int) -> tuple[Workspace, Source]:
    timestamp = "2026-08-12T00:00:00Z"
    workspace = Workspace.model_validate(
        {
            "workspace_id": "ws_e554offline0001",
            "status": "ready",
            "asset": {
                "asset_id": "asset_e554offline0001",
                "name": "Eastman Eagle S3L",
                "description": "Automated laser cutting system",
                "brand": "Eastman",
                "model": "Eagle S3L",
                "asset_type": "automated laser cutting system",
            },
            "asset_identity_version": 1,
            "ontology_version": "1.0",
            "ontology_sha256": "0" * 64,
            "confirmed_at": timestamp,
            "created_at": timestamp,
            "updated_at": timestamp,
            "identifiers": [],
        }
    )
    source = Source.model_validate(
        {
            "source_id": "src_e554offline0001",
            "workspace_id": workspace.workspace_id,
            "source_kind": "pdf",
            "authority": "normative",
            "file_name": "E-554.pdf",
            "media_type": "application/pdf",
            "size_bytes": pdf_size,
            "sha256": PDF_SHA256,
            "language_hints": ["en"],
            "status": "accepted",
            "asset_assessment_id": None,
            "raw_relpath": None,
            "created_at": timestamp,
            "active_assessment": None,
        }
    )
    return workspace, source


@pytest.fixture(scope="module")
def real_pdf_adapter_result(tmp_path_factory):
    payload = _historical_pdf_bytes()
    pdf_path = tmp_path_factory.mktemp("e554-real-pdf") / "E-554.pdf"
    pdf_path.write_bytes(payload)
    workspace, source = _workspace_and_source(len(payload))
    result = PdfAdapter().inspect(
        path=pdf_path,
        workspace=workspace,
        source=source,
        included_pages=TARGET_PAGES,
        scope_version=1,
    )
    return result


def _materialize_current_anchors(
    payload: dict[str, Any],
    evidence_units,
) -> DiagnosticChunkOutput:
    """Resolve test-template anchors only from exact current adapter spans.

    Evidence IDs intentionally include locator identity. Keeping semantic
    quotes in the fixture and materializing IDs from the real adapter output
    makes this replay survive legitimate locator-version changes without ever
    weakening the compiler's exact-anchor validation.
    """
    evidence_by_page: dict[int, list[Any]] = defaultdict(list)
    for evidence in evidence_units:
        evidence_by_page[evidence.locator.page].append(evidence)

    anchor_map: dict[str, str] = {}
    for record in payload["records"]:
        spans = [
            *(span for indicator in record["indicators"] for span in indicator["claim_evidence"]),
            *(
                span
                for indicator in record["indicators"]
                for span in indicator["failure_link_evidence"]
            ),
            *(record["failure"]["claim_evidence"] if record["failure"] else []),
            *(span for action in record["actions"] for span in action["claim_evidence"]),
            *(
                span
                for action in record["actions"]
                for span in action["resolution_link_evidence"]
            ),
        ]
        for span in spans:
            matches = [
                evidence
                for evidence in evidence_by_page[span["source_page"]]
                if _normalized(span["quote"]) in _normalized(evidence.locator.quote)
            ]
            assert len(matches) == 1, (
                span["source_page"],
                span["quote"],
                [item.evidence_id for item in matches],
            )
            resolved = matches[0].evidence_id
            previous = anchor_map.setdefault(span["source_anchor"], resolved)
            assert previous == resolved
            span["source_anchor"] = resolved

    for record in payload["records"]:
        record["record_anchor"] = anchor_map[record["record_anchor"]]
        record["branch_anchor"] = anchor_map[record["branch_anchor"]]
    return DiagnosticChunkOutput.model_validate(payload)


@pytest.fixture(scope="module")
def typed_output(real_pdf_adapter_result) -> DiagnosticChunkOutput:
    return _materialize_current_anchors(
        _load(FIXTURE_PATH),
        real_pdf_adapter_result.evidence_units,
    )


@pytest.fixture(scope="module")
def compiled_replay(real_pdf_adapter_result, typed_output):
    return compile_diagnostic_bundles(
        typed_output,
        source_type="technical PDF",
        source_title="E-554.pdf",
        evidence_units=real_pdf_adapter_result.evidence_units,
        language="en",
    )


def _nodes_by_id(ontology) -> dict[str, tuple[str, dict[str, Any]]]:
    result: dict[str, tuple[str, dict[str, Any]]] = {}
    for node_type, nodes in ontology.nodes.items():
        for node in nodes:
            id_field = next(key for key in node if key.endswith("_id"))
            assert node[id_field] not in result
            result[node[id_field]] = (node_type, node)
    return result


def _compiled_paths(ontology) -> set[tuple[str, str, str]]:
    nodes = _nodes_by_id(ontology)
    resolved_by: dict[str, set[str]] = defaultdict(set)
    for relation in ontology.relations:
        if relation.name == "RESOLVED_BY":
            resolved_by[relation.from_id].add(relation.to_id)
    return {
        (
            nodes[relation.from_id][1]["name"],
            nodes[relation.to_id][1]["name"],
            nodes[action_id][1]["name"],
        )
        for relation in ontology.relations
        if relation.name == "MAY_INDICATE"
        for action_id in resolved_by[relation.to_id]
    }


def test_real_e554_pdf_adapter_preserves_all_required_source_spans(
    real_pdf_adapter_result,
    typed_output,
) -> None:
    assert ADAPTER_VERSION == "pdf-v3"
    assert len(real_pdf_adapter_result.page_previews) == 54
    assert {
        preview["page"]
        for preview in real_pdf_adapter_result.page_previews
        if preview["included"]
    } == TARGET_PAGES
    # EvidenceUnit cardinality is an extractor implementation detail; the
    # literal diagnostic spans and page coverage asserted below are the frozen
    # contract. PyMuPDF 1.27 coalesces several blocks that 1.26 kept separate.
    assert real_pdf_adapter_result.evidence_units
    assert {
        evidence.locator.page for evidence in real_pdf_adapter_result.evidence_units
    } == TARGET_PAGES

    evidence_by_id = {
        evidence.evidence_id: evidence
        for evidence in real_pdf_adapter_result.evidence_units
    }
    rendered = "\n".join(
        evidence.locator.quote for evidence in real_pdf_adapter_result.evidence_units
    ).casefold()
    assert "select save and exit" in rendered
    assert "click and drag the tool to the spindle" in rendered
    assert "loss of laser cutting power" in rendered
    assert "non-cut edges" in rendered

    fixture_anchors = {
        span.source_anchor
        for record in typed_output.records
        for span in [
            *(span for indicator in record.indicators for span in indicator.claim_evidence),
            *(span for indicator in record.indicators for span in indicator.failure_link_evidence),
            *(record.failure.claim_evidence if record.failure else []),
            *(span for action in record.actions for span in action.claim_evidence),
            *(span for action in record.actions for span in action.resolution_link_evidence),
        ]
    }
    assert fixture_anchors <= evidence_by_id.keys()

    calibration = typed_output.records[1]
    calibration_pages = {
        span.source_page
        for action in calibration.actions
        for span in action.claim_evidence
    }
    assert calibration_pages == {37, 38}


def test_real_e554_typed_compiler_represents_all_eight_gold_chains(
    compiled_replay,
) -> None:
    gold = _load(GOLD_PATH)
    expected_paths = {
        (chain["symptom"], chain["failure_mode"], chain["corrective_action"])
        for chain in gold["minimum_expected_manual_chains"]
    }

    assert compiled_replay.report.input_candidates == 8
    assert compiled_replay.report.unique_candidates == 8
    assert compiled_replay.report.duplicate_candidates == 0
    assert compiled_replay.report.disposition_counts == {
        "publish": 8,
        "gap": 0,
        "review": 0,
        "exclude": 0,
    }
    assert compiled_replay.report.dropped_items_by_reason == {}
    assert _compiled_paths(compiled_replay.ontology) == expected_paths

    assert {
        node_type: len(nodes)
        for node_type, nodes in compiled_replay.ontology.nodes.items()
        if nodes
    } == {
        "Symptom": 6,
        "FailureMode": 8,
        "CorrectiveAction": 8,
    }
    assert Counter(relation.name for relation in compiled_replay.ontology.relations) == {
        "MAY_INDICATE": 8,
        "RESOLVED_BY": 8,
    }
    assert sum(
        len(relation.evidence)
        for relation in compiled_replay.ontology.relations
    ) == 24


def test_real_e554_replay_rejects_all_forbidden_cross_pairings(compiled_replay) -> None:
    gold = _load(GOLD_PATH)
    chains = gold["minimum_expected_manual_chains"]
    failure_aliases = {
        "dirty focusing lens": chains[5]["failure_mode"],
        "intermittent pause circuit": chains[0]["failure_mode"],
        "touch screen calibration is required": chains[1]["failure_mode"],
    }
    nodes = _nodes_by_id(compiled_replay.ontology)
    actual_pairs = {
        (
            nodes[relation.from_id][1]["name"].casefold(),
            nodes[relation.to_id][1]["name"].casefold(),
        )
        for relation in compiled_replay.ontology.relations
        if relation.name == "MAY_INDICATE"
    }

    for forbidden in gold["forbidden_cross_pairings"]:
        forbidden_pair = (
            forbidden["symptom"].casefold(),
            failure_aliases[forbidden["failure_mode"].casefold()].casefold(),
        )
        assert forbidden_pair not in actual_pairs


def test_real_e554_relation_evidence_is_exact_and_edge_specific(
    real_pdf_adapter_result,
    typed_output,
    compiled_replay,
) -> None:
    evidence_by_id = {
        evidence.evidence_id: evidence
        for evidence in real_pdf_adapter_result.evidence_units
    }
    nodes = _nodes_by_id(compiled_replay.ontology)
    relations_by_names = {
        (
            relation.name,
            nodes[relation.from_id][1]["name"],
            nodes[relation.to_id][1]["name"],
        ): relation
        for relation in compiled_replay.ontology.relations
    }

    for record in typed_output.records:
        assert record.failure is not None
        indicator = record.indicators[0]
        action = record.actions[0]
        expected_edges = [
            (
                "MAY_INDICATE",
                indicator.name,
                record.failure.name,
                indicator.failure_link_evidence,
            ),
            (
                "RESOLVED_BY",
                record.failure.name,
                action.name,
                action.resolution_link_evidence,
            ),
        ]
        for relation_name, from_name, to_name, expected_spans in expected_edges:
            relation = relations_by_names[(relation_name, from_name, to_name)]
            expected = {
                (span.source_page, span.source_anchor, _normalized(span.quote))
                for span in expected_spans
            }
            actual = {
                (item.source_page, item.source_anchor, item.quote)
                for item in relation.evidence
            }
            assert actual == expected
            for item in relation.evidence:
                canonical = evidence_by_id[item.source_reference]
                assert item.source_anchor == canonical.evidence_id
                assert item.source_page == canonical.locator.page
                assert _normalized(item.quote) in _normalized(canonical.locator.quote)


def test_real_e554_compiled_schema_and_local_topology_are_closed(compiled_replay) -> None:
    ontology = compiled_replay.ontology
    nodes = _nodes_by_id(ontology)
    schema_issues, human_fields = validate_ontology_instance(ontology)
    assert not [issue for issue in schema_issues if issue.severity == "error"]
    assert {
        (field.target_type, field.property_name)
        for field in human_fields
    } == {
        ("Asset", "brand"),
        ("Asset", "model"),
    }

    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    for relation in ontology.relations:
        assert relation.from_id in nodes
        assert relation.to_id in nodes
        outgoing[relation.from_id].append(relation.name)
        incoming[relation.to_id].append(relation.name)

    for node_id, (node_type, _) in nodes.items():
        if node_type == "Symptom":
            assert outgoing[node_id].count("MAY_INDICATE") >= 1
        elif node_type == "FailureMode":
            assert incoming[node_id].count("MAY_INDICATE") == 1
            assert outgoing[node_id].count("RESOLVED_BY") == 1
        elif node_type == "CorrectiveAction":
            assert incoming[node_id].count("RESOLVED_BY") == 1
        else:
            raise AssertionError(f"Unexpected compiled node type: {node_type}")

    # The typed compiler owns diagnostic branches, not the canonical Asset
    # injection/HAS_COMPONENT merge. Its direct output is therefore a complete
    # diagnostic forest, not yet one globally Asset-connected source graph.
    assert ontology.nodes["Asset"] == []

    undirected: dict[str, set[str]] = defaultdict(set)
    for relation in ontology.relations:
        undirected[relation.from_id].add(relation.to_id)
        undirected[relation.to_id].add(relation.from_id)
    remaining = set(nodes)
    components = 0
    while remaining:
        components += 1
        pending = [remaining.pop()]
        while pending:
            current = pending.pop()
            unseen = undirected[current] & remaining
            remaining -= unseen
            pending.extend(unseen)
    assert components == 6


def test_real_e554_replay_result_artifact_matches_executable_gate() -> None:
    result = _load(RESULT_PATH)
    fixture_sha256 = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()

    assert result["kind"] == "offline_e554_real_pdf_typed_replay_result"
    assert result["status"] == "passed_with_asset_boundary_limit"
    assert result["execution"]["api_calls"] == 0
    assert result["execution"]["llm_calls"] == 0
    assert result["execution"]["production_rules_changed"] is False
    assert result["source_pdf"]["git_blob"] == PDF_BLOB
    assert result["source_pdf"]["sha256"] == PDF_SHA256
    assert result["typed_fixture"]["sha256"] == fixture_sha256
    assert result["acceptance"] == {
        "gold_chains_present": 8,
        "gold_chains_total": 8,
        "forbidden_cross_pairings_found": 0,
        "forbidden_cross_pairings_total": 3,
        "schema_error_count": 0,
        "diagnostic_nodes_without_complete_indicator_failure_action_path": 0,
        "isolated_diagnostic_nodes": 0,
    }
    assert result["compiler"]["relation_evidence_exact_grounding"] == {
        "passed": 24,
        "total": 24,
        "rule": (
            "normalized relation quote is contained in the canonical EvidenceUnit "
            "locator quote with identical evidence ID and page"
        ),
    }
    assert result["topology_boundary"]["standalone_weakly_connected_components"] == 6
    assert result["semantic_review"]["recommended_gold_chains"] == [4, 6, 7, 8]
