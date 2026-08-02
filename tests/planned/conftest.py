from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def foundation_client(tmp_path, monkeypatch):
    monkeypatch.setenv("KG_OPERATIONAL_DB", str(tmp_path / "operational.db"))
    monkeypatch.setenv("KG_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("KG_INCOMING_DIR", str(tmp_path / "incoming"))
    from backend.main import create_app

    return TestClient(create_app())


@pytest.fixture()
def machine_payload():
    return {
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

