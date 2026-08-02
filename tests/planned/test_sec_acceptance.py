from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.storage.raw_store import RawStore
from tests.planned.source_fixtures import pdf_bytes


@pytest.fixture()
def limited_client(tmp_path, monkeypatch):
    monkeypatch.setenv("KG_OPERATIONAL_DB", str(tmp_path / "operational.db"))
    monkeypatch.setenv("KG_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("KG_INCOMING_DIR", str(tmp_path / "incoming"))
    monkeypatch.setenv("KG_MAX_UPLOAD_BYTES", "1024")
    monkeypatch.setenv("KG_MAX_BODY_BYTES", "512")
    monkeypatch.setenv("KG_MAX_REQUEST_BYTES", "4096")
    from backend.main import create_app

    return TestClient(create_app())


def _create_workspace(client):
    payload = {
        "asset": {
            "name": "Hydraulic Press 7",
            "description": "Hydraulic forming press in maintenance bay seven.",
            "brand": "ExampleWorks",
            "model": "HP-700",
        },
        "identifiers": [
            {"namespace": "manufacturer_serial", "value": "HP7-000042", "kind": "serial"}
        ],
        "assertion": {
            "reason": "Identity read directly from the machine nameplate.",
            "observation_basis": "nameplate",
            "operator": "FD",
        },
    }
    return client.post("/api/workspace", json=payload).json()["workspace"]


@pytest.mark.parametrize("hostile_name", ["../escape.pdf", "%2e%2e%2fescape.pdf", "..%252fescape.pdf"])
def test_i04_upload_rejects_traversal_names(limited_client, hostile_name):
    workspace = _create_workspace(limited_client)
    response = limited_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/sources",
        data={"authority": "normative"},
        files={"file": (hostile_name, pdf_bytes("SERIAL: HP7-000042"), "application/pdf")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["preserved"]
    assert detail["action"]
    assert detail["retryability"] == "riprendibile"


def test_i04_upload_and_request_limits_are_effective(limited_client):
    workspace = _create_workspace(limited_client)
    oversized = b"%PDF-1.4\n" + (b"x" * 1500)
    response = limited_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/sources",
        data={"authority": "normative"},
        files={"file": ("large.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413
    assert response.json()["detail"]["technical_detail"].startswith(
        ("UPLOAD_LIMIT_EXCEEDED", "REQUEST_LIMIT_EXCEEDED")
    )

    body_response = limited_client.post(
        "/api/workspace",
        content=b"{" + (b" " * 700) + b"}",
        headers={"content-type": "application/json"},
    )
    assert body_response.status_code == 413
    assert "REQUEST_LIMIT_EXCEEDED" in body_response.json()["detail"]["technical_detail"]


def test_i04_raw_store_rejects_symlink_escape_and_prefix_collision(tmp_path):
    root = tmp_path / "raw"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.pdf"
    secret.write_bytes(b"secret")
    (root / "escape").symlink_to(secret)
    sibling = tmp_path / "raw-evil"
    sibling.mkdir()
    sibling_file = sibling / "other.pdf"
    sibling_file.write_bytes(b"other")
    store = RawStore(root=root, incoming=tmp_path / "incoming")
    with pytest.raises(FileNotFoundError):
        store.resolve("escape")
    with pytest.raises(FileNotFoundError):
        store.resolve("../raw-evil/other.pdf")
    with pytest.raises(FileNotFoundError):
        store.resolve(str(sibling_file))


def test_i04_legacy_manual_load_is_exact_inventory_only(tmp_path, monkeypatch):
    manuals = tmp_path / "manuals"
    manuals.mkdir()
    valid = manuals / "valid.pdf"
    valid.write_bytes(pdf_bytes("Inventory manual text that is long enough to avoid OCR bootstrap."))
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(pdf_bytes("Outside"))
    (manuals / "escape.pdf").symlink_to(outside)
    monkeypatch.setenv("KG_MANUALS_DIR", str(manuals))
    monkeypatch.setenv("KG_OPERATIONAL_DB", str(tmp_path / "operational.db"))
    from backend.main import create_app

    client = TestClient(create_app())
    inventory = client.get("/api/manuals").json()["manuals"]
    assert [item["filename"] for item in inventory] == ["valid.pdf"]
    assert inventory[0]["inventory_id"].startswith("manual_")
    assert client.post("/api/load-manual", json={"filename": "../outside.pdf"}).status_code == 400
    assert client.post("/api/load-manual", json={"filename": "%2e%2e%2foutside.pdf"}).status_code == 400
    assert client.post("/api/load-manual", json={"filename": "escape.pdf"}).status_code == 404


def test_ac_sec_003(tmp_path, monkeypatch):
    monkeypatch.setenv("KG_OPERATIONAL_DB", str(tmp_path / "operational.db"))
    monkeypatch.setenv("KG_ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000")
    monkeypatch.setenv("KG_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")
    from backend.main import create_app

    client = TestClient(create_app())
    allowed = client.get("/api/health", headers={"Origin": "http://127.0.0.1:8000"})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:8000"
    denied = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert denied.status_code == 403
    assert "ORIGIN_NOT_ALLOWED" in denied.json()["detail"]["technical_detail"]
    assert client.get("/api/health", headers={"Host": "evil.example"}).status_code == 400
    preflight = client.options(
        "/api/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code == 403

    source = (Path(__file__).resolve().parents[2] / "backend" / "main.py").read_text(encoding="utf-8")
    assert 'allow_origins=["*"]' not in source
    launcher = (Path(__file__).resolve().parents[2] / "scripts" / "dev_server.mjs").read_text(
        encoding="utf-8"
    )
    assert 'process.env.HOST || "127.0.0.1"' in launcher


def test_i05_started_server_enforces_origin_on_loopback(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    environment = {
        **os.environ,
        "PORT": str(port),
        "KG_OPERATIONAL_DB": str(tmp_path / "operational.db"),
        "KG_RAW_DIR": str(tmp_path / "raw"),
        "KG_INCOMING_DIR": str(tmp_path / "incoming"),
        "KG_RUNS_DIR": str(tmp_path / "runs"),
    }
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    health = f"http://127.0.0.1:{port}/api/health"
    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                with urllib.request.urlopen(health, timeout=0.5) as response:
                    assert response.status == 200
                break
            except (OSError, urllib.error.URLError):
                if time.monotonic() >= deadline:
                    raise AssertionError("Uvicorn did not become ready on loopback")
                time.sleep(0.05)
        request = urllib.request.Request(
            health,
            headers={"Origin": "https://evil.example"},
        )
        with pytest.raises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=1)
        assert caught.value.code == 403
    finally:
        process.terminate()
        process.wait(timeout=10)
