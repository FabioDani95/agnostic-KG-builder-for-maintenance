#!/usr/bin/env python3
"""Prepare the Hypertherm holdout in an isolated, zero-LLM workspace."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from io import BytesIO
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PDF_PATH = (
    REPOSITORY_ROOT
    / "manuals"
    / "holdout_candidates_20260813"
    / "hypertherm_powermax30_air_service_manual_rev4_808850.pdf"
)
EXPECTED_SHA256 = "3c2b7cd62ae1b8b69f8b86fcbf9b36f4ee1fc8d35fed3f90d6271f8ef50d5c45"


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    os.environ.update(
        {
            "KG_LLM_MODE": "mock",
            "OPENAI_API_KEY": "",
            "KG_OPERATIONAL_DB": str((RUN_ROOT / "operational.db").resolve()),
            "KG_RAW_DIR": str((RUN_ROOT / "raw").resolve()),
            "KG_INCOMING_DIR": str((RUN_ROOT / "incoming").resolve()),
        }
    )
    if str(REPOSITORY_ROOT) not in sys.path:
        sys.path.insert(0, str(REPOSITORY_ROOT))

    from fastapi.testclient import TestClient

    from backend.main import create_app
    from backend.storage.repositories.evidence import EvidenceRepository
    from backend.storage.repositories.raw_units import RawUnitRepository

    pdf_bytes = PDF_PATH.read_bytes()
    actual_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    if actual_sha256 != EXPECTED_SHA256:
        raise RuntimeError(f"Hypertherm PDF hash mismatch: {actual_sha256}")
    if (RUN_ROOT / "preparation.json").exists():
        raise RuntimeError("Offline preparation already completed; refusing to overwrite it")

    client = TestClient(create_app())
    workspace_response = client.post(
        "/api/workspaces",
        json={
            "asset": {
                "name": "Powermax30 AIR plasma cutting system",
                "description": "Plasma arc cutting system with integrated air compressor",
                "brand": "Hypertherm",
                "model": "Powermax30 AIR",
                "asset_type": "plasma cutting system",
            },
            "identifiers": [],
            "assertion": {
                "reason": "Identity transcribed from the holdout manual cover before generation.",
                "observation_basis": "operator_record",
                "operator": "Codex Hypertherm holdout preparation",
            },
        },
    )
    workspace_response.raise_for_status()
    workspace = workspace_response.json()["workspace"]

    upload_response = client.post(
        f"/api/workspaces/{workspace['workspace_id']}/sources",
        data={"authority": "normative"},
        files={"file": (PDF_PATH.name, BytesIO(pdf_bytes), "application/pdf")},
    )
    upload_response.raise_for_status()
    registration = upload_response.json()
    source = registration["source"]

    evidence = EvidenceRepository().list_evidence(
        workspace_id=workspace["workspace_id"],
        source_id=source["source_id"],
    )
    raw_units = RawUnitRepository().list_inventory(source["source_id"])
    page_units = [item for item in raw_units if item.unit_kind == "pdf_page"]
    quality_counts: dict[str, int] = {}
    for item in evidence:
        for flag in item.quality_flags:
            key = str(flag.value if hasattr(flag, "value") else flag)
            quality_counts[key] = quality_counts.get(key, 0) + 1

    result = {
        "mode": "offline_preparation_only",
        "llm_mode": os.environ["KG_LLM_MODE"],
        "openai_api_key_present": bool(os.environ["OPENAI_API_KEY"]),
        "generation_started": False,
        "golden_loaded": False,
        "approval_decision_taken": False,
        "merge_started": False,
        "pdf": {
            "path": str(PDF_PATH),
            "sha256": actual_sha256,
            "size_bytes": len(pdf_bytes),
        },
        "workspace": workspace,
        "source": source,
        "preparation": registration.get("preparation"),
        "inventory": {
            "raw_units": len(raw_units),
            "page_units": len(page_units),
            "evidence_units": len(evidence),
            "quality_flag_counts": quality_counts,
        },
    }
    write_json(RUN_ROOT / "preparation.json", result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
