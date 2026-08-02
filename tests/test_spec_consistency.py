from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts import check_spec_consistency as checker

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = Path("docs/specs/SPEC_INDEX.json")
SCHEMA_PATH = Path("docs/specs/SPEC_INDEX.schema.json")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_index(root: Path, index: dict) -> None:
    _write(root / INDEX_PATH, json.dumps(index, ensure_ascii=False, indent=2) + "\n")


def _reseal(
    root: Path,
    index: dict,
    *,
    declared_status: str = "READY_FOR_PLANNING",
    semantic_status: str = "APPROVED",
    owner_status: str = "APPROVED",
) -> None:
    package = index["package"]
    package.pop("snapshot_sha256", None)
    digest = checker.compute_package_digest(root, index)
    package["snapshot_sha256"] = f"sha256:{digest}"

    semantic_review = {"status": semantic_status}
    if semantic_status == "APPROVED":
        semantic_review.update(
            {
                "reviewer": "spec-owner",
                "approved_at": "2026-07-29T10:00:00Z",
                "package_digest": f"sha256:{digest}",
            }
        )
    owner_approval = {"status": owner_status}
    if owner_status == "APPROVED":
        owner_approval.update(
            {
                "approver": "product-owner",
                "approved_at": "2026-07-29T10:01:00Z",
                "package_digest": f"sha256:{digest}",
            }
        )
    index["readiness"] = {
        "declared_status": declared_status,
        "semantic_review": semantic_review,
        "owner_approval": owner_approval,
    }
    _write_index(root, index)


@pytest.fixture
def spec_package(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "repo"
    _write(
        root / "SPECIFICHE_MVP.md",
        "# Test specification\n\n"
        "### FR-TEST-001 — Test requirement\n\n"
        "The implementation must preserve the test behavior.\n",
    )
    _write(
        root / "docs/specs/DATA_CONTRACTS.md",
        "# Test contracts\n\n"
        "### DC-TEST-001 — Test contract\n\n"
        "The artifact must expose a stable value.\n",
    )
    _write(
        root / "docs/specs/ACCEPTANCE_CRITERIA.md",
        "# Test acceptance\n\n"
        "### DS-CHAT-001 — Test dataset\n\n"
        "A deterministic fixture.\n\n"
        "### AC-TEST-001 — Test acceptance\n\n"
        "The observable report contains the stable value.\n",
    )
    ontology_bytes = b'{"title":"test ontology"}\n'
    ontology_path = root / "ontology_schema.JSON"
    ontology_path.parent.mkdir(parents=True, exist_ok=True)
    ontology_path.write_bytes(ontology_bytes)
    schema_source = REPO_ROOT / SCHEMA_PATH
    schema_target = root / SCHEMA_PATH
    schema_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(schema_source, schema_target)

    index = {
        "$schema": "./SPEC_INDEX.schema.json",
        "schema_version": "1.0",
        "package": {
            "id": "test-package",
            "spec_version": "1.0",
            "normative_documents": [
                {"path": "SPECIFICHE_MVP.md", "defines": ["requirement"]},
                {
                    "path": "docs/specs/DATA_CONTRACTS.md",
                    "defines": ["contract"],
                },
                {
                    "path": "docs/specs/ACCEPTANCE_CRITERIA.md",
                    "defines": ["acceptance", "dataset"],
                },
            ],
            "ontology": {
                "path": "ontology_schema.JSON",
                "sha256": hashlib.sha256(ontology_bytes).hexdigest(),
            },
        },
        "items": [
            {
                "id": "FR-TEST-001",
                "kind": "requirement",
                "status": "active",
                "defined_at": {
                    "path": "SPECIFICHE_MVP.md",
                    "heading": "FR-TEST-001",
                },
            },
            {
                "id": "DC-TEST-001",
                "kind": "contract",
                "status": "active",
                "defined_at": {
                    "path": "docs/specs/DATA_CONTRACTS.md",
                    "heading": "DC-TEST-001",
                },
            },
            {
                "id": "AC-TEST-001",
                "kind": "acceptance",
                "status": "active",
                "defined_at": {
                    "path": "docs/specs/ACCEPTANCE_CRITERIA.md",
                    "heading": "AC-TEST-001",
                },
            },
            {
                "id": "DS-CHAT-001",
                "kind": "dataset",
                "status": "active",
                "defined_at": {
                    "path": "docs/specs/ACCEPTANCE_CRITERIA.md",
                    "heading": "DS-CHAT-001",
                },
            },
        ],
        "obligations": [
            {
                "id": "OBL-FR-TEST-001",
                "source_id": "FR-TEST-001",
                "verified_behavior": "The requirement preserves the stable test behavior.",
                "acceptance_ids": ["AC-TEST-001"],
                "verification_ids": ["TST-TEST-001"],
                "artifact_ids": ["ART-TEST-001"],
            },
            {
                "id": "OBL-DC-TEST-001",
                "source_id": "DC-TEST-001",
                "verified_behavior": "The contract exposes the stable value.",
                "acceptance_ids": ["AC-TEST-001"],
                "verification_ids": ["TST-TEST-001"],
                "artifact_ids": ["ART-TEST-001"],
            },
        ],
        "verifications": [
            {
                "id": "TST-TEST-001",
                "kind": "automated",
                "lifecycle": "specified",
                "runner": "pytest",
                "target": "tests/test_future_contract.py::test_stable_value",
                "assertion": "The emitted value equals the annotated fixture value.",
                "dataset_ids": ["DS-CHAT-001"],
            }
        ],
        "artifacts": [
            {
                "id": "ART-TEST-001",
                "kind": "json_report",
                "lifecycle": "specified",
                "path_pattern": "artifacts/test-report-*.json",
                "observables": ["$.stable_value"],
            }
        ],
        "decisions": [
            {
                "id": "DEC-001",
                "status": "ACCEPTED",
                "scope": "product",
                "planning_blocker": False,
                "statement": "The fixture represents the selected product behavior.",
                "related_ids": ["FR-TEST-001"],
            }
        ],
        "findings": [
            {
                "id": "AUD-001",
                "status": "RESOLVED",
                "planning_blocker": True,
                "planning_disposition": "must_resolve_pre_plan",
                "summary": "The original test behavior was ambiguous.",
                "related_ids": ["FR-TEST-001"],
                "resolution_refs": ["DEC-001", "FR-TEST-001", "AC-TEST-001"],
            }
        ],
        "readiness": {
            "declared_status": "NOT_READY",
            "semantic_review": {"status": "PENDING"},
            "owner_approval": {"status": "PENDING"},
        },
    }
    _reseal(root, index)
    result = checker.evaluate(root)
    assert result.issues == (), result.messages()
    return root, index


def _codes(result: checker.Evaluation) -> set[str]:
    return {issue.code for issue in result.issues}


def test_complete_machine_index_is_ready(spec_package: tuple[Path, dict]):
    root, _ = spec_package

    result = checker.evaluate(root)

    assert result.issues == ()
    assert result.inventory.counts() == {
        "requirement": 1,
        "contract": 1,
        "acceptance": 1,
        "dataset": 1,
    }
    assert result.readiness.derived_status == "READY_FOR_PLANNING"
    assert checker.validate(root) == []


def test_strict_json_rejects_duplicate_keys(spec_package: tuple[Path, dict]):
    root, _ = spec_package
    path = root / INDEX_PATH
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        '"schema_version": "1.0",',
        '"schema_version": "1.0",\n  "schema_version": "1.0",',
        1,
    )
    path.write_text(text, encoding="utf-8")

    result = checker.evaluate(root)

    assert "IDX002" in _codes(result)
    assert "duplicate key" in result.messages()[0]


def test_fallback_validation_works_without_jsonschema(
    spec_package: tuple[Path, dict],
    monkeypatch: pytest.MonkeyPatch,
):
    root, _ = spec_package
    monkeypatch.setattr(checker, "_jsonschema", None)

    result = checker.evaluate(root)

    assert result.issues == ()


def test_duplicate_normative_heading_is_rejected(spec_package: tuple[Path, dict]):
    root, index = spec_package
    path = root / "SPECIFICHE_MVP.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n### FR-TEST-001 — Duplicate\n",
        encoding="utf-8",
    )
    _reseal(root, index)

    result = checker.evaluate(root)

    assert "ID004" in _codes(result)


def test_indexed_item_without_heading_is_rejected(spec_package: tuple[Path, dict]):
    root, index = spec_package
    index["items"].append(
        {
            "id": "FR-UNKNOWN-999",
            "kind": "requirement",
            "status": "active",
            "defined_at": {
                "path": "SPECIFICHE_MVP.md",
                "heading": "FR-UNKNOWN-999",
            },
        }
    )
    _reseal(root, index)

    result = checker.evaluate(root)

    assert "ID008" in _codes(result)


def test_contract_without_obligation_is_rejected(spec_package: tuple[Path, dict]):
    root, index = spec_package
    index["obligations"] = [
        obligation
        for obligation in index["obligations"]
        if obligation["source_id"] != "DC-TEST-001"
    ]
    _reseal(root, index)

    result = checker.evaluate(root)

    assert "TRC007" in _codes(result)
    assert any("DC-TEST-001" in message for message in result.messages())


def test_dataset_cannot_substitute_for_acceptance(spec_package: tuple[Path, dict]):
    root, index = spec_package
    index["obligations"][0]["acceptance_ids"] = ["DS-CHAT-001"]
    _reseal(root, index)

    result = checker.evaluate(root)

    assert "TRC003" in _codes(result)


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("acceptance_ids", "TRC003"),
        ("verification_ids", "TRC004"),
        ("artifact_ids", "TRC005"),
    ],
)
def test_obligation_requires_each_evidence_link(
    spec_package: tuple[Path, dict],
    field: str,
    expected_code: str,
):
    root, index = spec_package
    index["obligations"][0][field] = []
    _reseal(root, index)

    result = checker.evaluate(root)

    assert expected_code in _codes(result)


def test_implemented_verification_target_must_exist(spec_package: tuple[Path, dict]):
    root, index = spec_package
    index["verifications"][0]["lifecycle"] = "implemented"
    _reseal(root, index)

    result = checker.evaluate(root)

    assert "VER007" in _codes(result)


def test_open_product_decision_blocks_planning(spec_package: tuple[Path, dict]):
    root, index = spec_package
    decision = index["decisions"][0]
    decision["status"] = "OPEN"
    decision["planning_blocker"] = True
    _reseal(root, index, declared_status="NOT_READY")

    result = checker.evaluate(root)

    assert "DEC004" in _codes(result)
    assert result.readiness.derived_status == "NOT_READY"
    assert any("DEC-001" in blocker for blocker in result.readiness.blockers)


def test_deferred_implementation_choice_is_not_a_blocker(
    spec_package: tuple[Path, dict],
):
    root, index = spec_package
    decision = index["decisions"][0]
    decision["status"] = "DEFERRED"
    decision["scope"] = "implementation"
    decision["planning_blocker"] = False
    _reseal(root, index)

    result = checker.evaluate(root)

    assert "DEC004" not in _codes(result)
    assert result.readiness.derived_status == "READY_FOR_PLANNING"


def test_resolved_finding_requires_resolution_references(
    spec_package: tuple[Path, dict],
):
    root, index = spec_package
    index["findings"][0]["resolution_refs"] = []
    _reseal(root, index, declared_status="NOT_READY")

    result = checker.evaluate(root)

    assert "AUD004" in _codes(result)
    assert result.readiness.derived_status == "NOT_READY"


def test_false_ready_declaration_is_rejected(spec_package: tuple[Path, dict]):
    root, index = spec_package
    finding = index["findings"][0]
    finding["status"] = "OPEN"
    finding["resolution_refs"] = []
    _reseal(root, index, declared_status="READY_FOR_PLANNING")

    result = checker.evaluate(root)

    assert "AUD003" in _codes(result)
    assert "RDY008" in _codes(result)
    assert result.readiness.derived_status == "NOT_READY"


def test_approval_digest_becomes_stale_after_normative_change(
    spec_package: tuple[Path, dict],
):
    root, _ = spec_package
    path = root / "SPECIFICHE_MVP.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nA new normative statement.\n",
        encoding="utf-8",
    )

    result = checker.evaluate(root)

    assert "RDY005" in _codes(result)
    assert "RDY007" in _codes(result)
    assert result.readiness.derived_status == "NOT_READY"


def test_pending_owner_approval_derives_intermediate_state(
    spec_package: tuple[Path, dict],
):
    root, index = spec_package
    _reseal(
        root,
        index,
        declared_status="AWAITING_OWNER_APPROVAL",
        owner_status="PENDING",
    )

    result = checker.evaluate(root)

    assert result.readiness.derived_status == "AWAITING_OWNER_APPROVAL"
    assert "RDY009" in _codes(result)


def test_cli_can_require_planning_ready(
    spec_package: tuple[Path, dict],
    capsys: pytest.CaptureFixture[str],
):
    root, _ = spec_package

    exit_code = checker.main(
        [
            "--root",
            str(root),
            "--format",
            "json",
            "--require-status",
            "READY_FOR_PLANNING",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["readiness"]["derived_status"] == "READY_FOR_PLANNING"
    assert payload["required_status_satisfied"] is True


def test_real_normative_specification_package_is_consistent_when_index_exists():
    if not (REPO_ROOT / INDEX_PATH).exists():
        pytest.skip("SPEC_INDEX.json will be populated by the specification-remediation task.")

    result = checker.evaluate(REPO_ROOT)
    if result.readiness.derived_status == "READY_FOR_PLANNING":
        assert result.issues == ()
    else:
        assert result.readiness.derived_status == "AWAITING_OWNER_APPROVAL"
        assert {issue.code for issue in result.issues} == {"RDY009"}
