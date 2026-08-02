from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1] / "golden" / "workspaces"
DS003 = ROOT / "ds003"
DENYLIST = {
    "semantic_text",
    "event_signature_id",
    "linked_failure_mode_id",
    "linked_symptom_id",
    "quality_flags",
    "expected_claim",
    "gold_label",
    "split",
}


def test_i03_ds003_skeleton_is_versioned_valid_and_gold_blind():
    schema = json.loads((ROOT / "ds003_expected.schema.json").read_text(encoding="utf-8"))
    expected = json.loads((DS003 / "expected.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(expected)
    assert expected["claim_count"] == sum(
        len(expected["expected"][kind])
        for kind in ("nodes", "properties", "relationships")
    )
    assert sum(source["kind"] == "pdf" for source in expected["sources"]) == 2
    assert (DS003 / "SKELETON.json").exists()

    checksums = {}
    for line in (DS003 / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        checksums[relative] = digest
    declared_paths = set()
    for source in expected["sources"]:
        raw_path = source["raw_path"]
        view_path = source["ingestion_view"]["path"]
        declared_paths.update({raw_path, view_path})
        assert hashlib.sha256((DS003 / raw_path).read_bytes()).hexdigest() == source["sha256"]
        assert hashlib.sha256((DS003 / view_path).read_bytes()).hexdigest() == source["ingestion_view"]["sha256"]
        assert not DENYLIST.intersection(source["ingestion_view"].get("columns", []))
    assert declared_paths == set(checksums)
    assert all(hashlib.sha256((DS003 / path).read_bytes()).hexdigest() == digest for path, digest in checksums.items())

