"""Isolated smoke check for the G1 CSV upload/assessment boundary."""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
temp_root = Path(tempfile.mkdtemp(prefix="log-kg-csv-smoke-"))
os.environ.update(
    KG_OPERATIONAL_DB=str(temp_root / "operational.db"),
    KG_RAW_DIR=str(temp_root / "raw"),
    KG_INCOMING_DIR=str(temp_root / "incoming"),
)

create_app = importlib.import_module("backend.main").create_app
client = TestClient(create_app())
machine = {
    "asset": {
        "name": "Hydraulic Press 7",
        "description": "Hydraulic forming press in maintenance bay seven.",
        "brand": "ExampleWorks",
        "model": "HP-700",
        "asset_type": "hydraulic_press",
    },
    "identifiers": [
        {
            "namespace": "manufacturer_serial",
            "value": "HP7-000042",
            "kind": "serial",
        }
    ],
    "assertion": {
        "reason": "Identity read directly from the machine nameplate.",
        "observation_basis": "nameplate",
        "operator": "FD",
    },
}
workspace = client.post("/api/workspace", json=machine).json()["workspace"]
csv_path = Path(__file__).with_name("hydraulic_press_7_maintenance_log.csv")
upload = client.post(
    f"/api/workspaces/{workspace['workspace_id']}/sources",
    data={"authority": "observational"},
    files={"file": (csv_path.name, csv_path.read_bytes(), "text/csv")},
)
assert upload.status_code == 200, upload.text
source = upload.json()["source"]
assert source["source_kind"] == "csv"
assert source["status"] == "quarantined"
assert source["active_assessment"]["outcome"] == "uncertain"
assert source["active_assessment"]["reason_codes"] == ["NO_STRONG_IDENTIFIER"]

confirmation = client.post(
    f"/api/sources/{source['source_id']}/assessment/resolve",
    json={
        "action": "confirm",
        "reason": "Serial HP7-000042 verified in the uploaded CSV.",
        "observation_basis": "operator_record",
        "operator": "FD",
        "evidence_seen": [source["asset_assessment_id"]],
    },
)
assert confirmation.status_code == 200, confirmation.text
assert confirmation.json()["status"] == "accepted"

print(
    json.dumps(
        {
            "records": 12,
            "upload_status": source["status"],
            "assessment": source["active_assessment"]["outcome"],
            "reason_codes": source["active_assessment"]["reason_codes"],
            "after_confirmation": confirmation.json()["status"],
        },
        indent=2,
    )
)
