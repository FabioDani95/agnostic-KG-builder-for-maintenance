"""Replay frozen provider exchanges through the current pipeline, without network.

Exact request fingerprints are mandatory. A missing exchange fails closed and
cannot fall back to an API call. Original source stores are opened read-only.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def key(request):
    return hashlib.sha256(json.dumps(request, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


class ReadOnlyStore:
    def __init__(self, path):
        self.path = path.resolve()

    @contextmanager
    def read(self):
        connection = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-root", type=Path, default=ROOT)
    parser.add_argument("--extra-response-dir", type=Path, action="append", default=[],
                        help="Additional frozen exchanges from an incremental run; exact matching and network denial still apply.")
    args = parser.parse_args()
    original, output = args.run.resolve(), args.output.resolve()
    code_root = args.code_root.resolve()
    sys.path.insert(0, str(code_root))
    output.mkdir(parents=True, exist_ok=False)
    os.environ.update(KG_LLM_MODE="real", KG_LLM_TRACE_DIR=str(output / "replayed_exchanges"))
    for name in ("KG_REAL_CALL_BUDGET_LEDGER", "KG_REAL_CALL_BUDGET_USD", "KG_REAL_CALL_RUN_ID", "KG_REAL_CALL_PDF_ID"):
        os.environ.pop(name, None)
    import httpx
    from openai import APIConnectionError, APIStatusError, APITimeoutError
    from openai.resources.chat.completions import AsyncCompletions, Completions
    from openai.types.chat import ChatCompletion

    from backend.app_config import load_config
    from backend.config import settings
    from backend.domain.evidence import EvidenceUnit
    from backend.services.llm_response_archive import _json_value
    from backend.services.pdf_source_subgraph_generation import PdfSourceSubgraphBuilder, pdf_input_config_hash
    from backend.storage.repositories.sources import SourceRepository
    from backend.storage.repositories.workspaces import WorkspaceRepository

    profile = read(original / "runtime_profile.json")
    graph = read(original / "graph.json")
    cfg = load_config()
    cfg.clear()
    cfg.update(profile["config"])
    settings.MODEL_NAME = profile["arguments"]["model"]
    settings.OPENAI_API_KEY = "offline-replay-no-real-credential"
    exchanges = defaultdict(deque)
    exchange_paths = sorted({p.resolve() for directory in [original / "provider_responses", *args.extra_response_dir]
                             for p in directory.glob("*.json")})
    for value in sorted((read(p) for p in exchange_paths), key=lambda x: x["started_utc"]):
        exchanges[key(value["request"])].append(value)
    used, missing = [], []
    lock = threading.Lock()
    network_attempts = []

    def deny_network(*args, **kwargs):
        network_attempts.append(True)
        raise RuntimeError("Network is forbidden during offline replay")

    def create(_client, **kwargs):
        request = _json_value(kwargs)
        fingerprint = key(request)
        with lock:
            if not exchanges[fingerprint]:
                missing.append({"fingerprint": fingerprint, "request": request})
                raise RuntimeError("No exact archived request for offline replay: " + fingerprint)
            exchange = exchanges[fingerprint].popleft()
            used.append(exchange.get("call_id"))
        error = exchange.get("error")
        if error and not exchange.get("response"):
            req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
            if error["type"] == "APITimeoutError":
                raise APITimeoutError(request=req)
            if error.get("status_code"):
                raise APIStatusError(error["message"], response=httpx.Response(error["status_code"], request=req), body=error.get("provider_body"))
            raise APIConnectionError(message=error["message"], request=req)
        if not exchange.get("response"):
            raise RuntimeError("Archived attempt has no replayable response")
        return ChatCompletion.model_validate(exchange["response"])

    async def async_create(client, **kwargs):
        return create(client, **kwargs)

    db = ReadOnlyStore(original / "operational.db")
    workspace = WorkspaceRepository(db).get_by_id(graph["workspace_id"])
    source = SourceRepository(db).get(graph["source_id"])
    with db.read() as connection:
        evidence = [EvidenceUnit.model_validate_json(row[0]) for row in connection.execute("SELECT payload_json FROM evidence_units")]
    pdf_evidence = [e for e in evidence if e.source_id == source.source_id and e.locator.kind == "pdf"]
    operators = [e for e in evidence if e.locator.kind == "operator_input"]
    hashes = {str(p.relative_to(code_root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(code_root.glob("backend/**/*.py"))}
    write(output / "runtime_profile.json", {"mode": "offline_exact_provider_replay", "source_run": str(original), "source_profile_sha256": hashlib.sha256((original / "runtime_profile.json").read_bytes()).hexdigest(), "code_files": hashes, "code_sha256": key(hashes), "config": cfg, "api_calls_made": 0, "gold_used_in_generation": False, "exchange_files": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in exchange_paths}})
    start = time.perf_counter()
    state = {"status": "running", "api_calls_made": 0}
    try:
        with patch.object(Completions, "create", create), patch.object(AsyncCompletions, "create", async_create), patch.object(httpx.Client, "send", deny_network), patch.object(httpx.AsyncClient, "send", deny_network):
            revision = asyncio.run(PdfSourceSubgraphBuilder().build_revision(
                workspace=workspace, source=source,
                scope={"included_pages": list(range(1, graph["pdf_extraction_scope"]["total_pages"] + 1))},
                evidence=pdf_evidence, operator_evidence=operators,
                fingerprint=graph["preparation_fingerprint"], config_hash=pdf_input_config_hash(), supersedes=graph["source_subgraph_revision_id"],
            ))
        if missing or network_attempts:
            raise RuntimeError("Replay attempted a request without an exact archived exchange")
        write(output / "graph.json", revision.model_dump(mode="json"))
        state["status"] = "completed"
    except Exception as exc:
        state.update(status="failed", error_type=type(exc).__name__, error=str(exc))
    state.update(elapsed_seconds=round(time.perf_counter() - start, 3), network_attempts=len(network_attempts), exchanges_used=used, missing_requests=missing, unused_exchanges=sum(len(v) for v in exchanges.values()))
    write(output / "replay.json", state)
    print(json.dumps({k: v for k, v in state.items() if k not in {"exchanges_used", "missing_requests"}}))
    return 0 if state["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
