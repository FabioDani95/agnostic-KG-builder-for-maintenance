"""Incremental full-pipeline rerun: exact archived requests plus bounded new API calls.

This is NOT an offline replay or an independent extraction. Only requests whose
source-page packet is explicitly allowed may reach the API. Every actual call
uses the existing campaign ledger; cached usage is not billed a second time.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from replay_extraction_experiment import ReadOnlyStore, key, read, write

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-root", type=Path, required=True)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--new-pages", default="")
    parser.add_argument("--max-new-calls", type=int, default=4)
    args = parser.parse_args()
    original, output, code_root = args.run.resolve(), args.output.resolve(), args.code_root.resolve()
    output.mkdir(parents=True, exist_ok=False)
    profile, graph = read(original / "runtime_profile.json"), read(original / "graph.json")
    cap = read(args.campaign / "manifest.json")["budget_cap_usd"]
    assert 0 < float(cap) <= 20
    os.environ.update(
        KG_LLM_MODE="real",
        KG_LLM_TRACE_DIR=str(output / "new_provider_responses"),
        KG_REAL_CALL_BUDGET_LEDGER=str((args.campaign / "real_call_budget.jsonl").resolve()),
        KG_REAL_CALL_BUDGET_USD=str(cap),
        KG_REAL_CALL_RUN_ID=output.name,
        KG_REAL_CALL_PDF_ID="sha256:" + profile["pdf_sha256"],
    )
    sys.path.insert(0, str(code_root))
    import httpx
    from openai import APIConnectionError, APIStatusError, APITimeoutError
    from openai.types.chat import ChatCompletion

    from backend.app_config import load_config
    from backend.config import settings
    from backend.domain.evidence import EvidenceUnit
    from backend.services import llm_gateway
    from backend.services.llm_response_archive import _json_value
    from backend.services.pdf_source_subgraph_generation import PdfSourceSubgraphBuilder, pdf_input_config_hash
    from backend.services.real_call_budget_ledger import RealCallBudgetLedger
    from backend.storage.repositories.sources import SourceRepository
    from backend.storage.repositories.workspaces import WorkspaceRepository

    cfg = load_config()
    cfg.clear()
    cfg.update(profile["config"])
    settings.MODEL_NAME = profile["arguments"]["model"]
    ledger = RealCallBudgetLedger(args.campaign / "real_call_budget.jsonl", absolute_budget_usd=cap)
    allowed = {int(x) for x in args.new_pages.split(",") if x}
    exchanges = defaultdict(deque)
    for value in sorted(
        (read(p) for p in (original / "provider_responses").glob("*.json")), key=lambda x: x["started_utc"]
    ):
        exchanges[key(value["request"])].append(value)
    used, new, blocked = [], [], []
    lock = threading.Lock()
    real_get_client = llm_gateway.get_client

    def factory(**options):
        def create(**kwargs):
            # Match the actual wire request archived by the gateway, including
            # its deterministic service-tier/schema normalization.
            _, kwargs, _ = llm_gateway._transport_request(None, "create", kwargs)
            request = _json_value(kwargs)
            fingerprint = key(request)
            with lock:
                exchange = exchanges[fingerprint].popleft() if exchanges[fingerprint] else None
                if exchange is not None:
                    used.append({"fingerprint": fingerprint, "source_call_id": exchange.get("call_id")})
                else:
                    source_text = next((m["content"] for m in request["messages"] if m["role"] == "user"), "")
                    pages = {int(n) for n in re.findall(r"--- PAGE (\d+) ---", source_text)}
                    if not allowed or pages != allowed or len(new) >= args.max_new_calls:
                        blocked.append({"fingerprint": fingerprint, "pages": sorted(pages)})
                        raise RuntimeError("New request outside frozen incremental protocol")
                    new.append({"fingerprint": fingerprint, "pages": sorted(pages)})
            if exchange is None:
                return real_get_client(**options).chat.completions.create(**kwargs)
            error = exchange.get("error")
            if error and not exchange.get("response"):
                req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
                if error["type"] == "APITimeoutError":
                    raise APITimeoutError(request=req)
                if error.get("status_code"):
                    raise APIStatusError(
                        error["message"],
                        response=httpx.Response(error["status_code"], request=req),
                        body=error.get("provider_body"),
                    )
                raise APIConnectionError(message=error["message"], request=req)
            if not exchange.get("response"):
                raise RuntimeError("Archived exchange has no response")
            return ChatCompletion.model_validate(exchange["response"])

        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    db = ReadOnlyStore(original / "operational.db")
    workspace = WorkspaceRepository(db).get_by_id(graph["workspace_id"])
    source = SourceRepository(db).get(graph["source_id"])
    with db.read() as conn:
        evidence = [
            EvidenceUnit.model_validate_json(row[0]) for row in conn.execute("SELECT payload_json FROM evidence_units")
        ]
    hashes = {
        str(p.relative_to(code_root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(code_root.glob("backend/**/*.py"))
    }
    write(
        output / "runtime_profile.json",
        {
            "mode": "incremental_exact_cache_plus_new_requests",
            "source_run": str(original),
            "source_profile_sha256": hashlib.sha256((original / "runtime_profile.json").read_bytes()).hexdigest(),
            "code_files": hashes,
            "code_sha256": key(hashes),
            "config": cfg,
            "allowed_new_pages": sorted(allowed),
            "max_new_calls": args.max_new_calls,
            "gold_used_in_generation": False,
        },
    )
    started = time.perf_counter()
    state = {"status": "running", "budget_before": ledger.snapshot().as_dict()}
    write(output / "continuation.json", state)
    try:
        with (
            patch("backend.services.ontology_pipeline.get_client", factory),
            patch("backend.services.llm_service.get_client", factory),
        ):
            revision = asyncio.run(
                PdfSourceSubgraphBuilder().build_revision(
                    workspace=workspace,
                    source=source,
                    scope={"included_pages": list(range(1, graph["pdf_extraction_scope"]["total_pages"] + 1))},
                    evidence=[e for e in evidence if e.source_id == source.source_id and e.locator.kind == "pdf"],
                    operator_evidence=[e for e in evidence if e.locator.kind == "operator_input"],
                    fingerprint=graph["preparation_fingerprint"],
                    config_hash=pdf_input_config_hash(),
                    supersedes=graph["source_subgraph_revision_id"],
                )
            )
        if blocked:
            raise RuntimeError("Incremental request matching failed")
        write(output / "graph.json", revision.model_dump(mode="json"))
        state["status"] = "completed"
    except Exception as exc:
        state.update(status="failed", error_type=type(exc).__name__, error=str(exc))
    state.update(
        elapsed_seconds=round(time.perf_counter() - started, 3),
        cached_exchanges=used,
        new_requests=new,
        blocked_requests=blocked,
        unused_exchanges=sum(len(x) for x in exchanges.values()),
        budget_after=ledger.snapshot().as_dict(),
        usage_note="Graph metrics include archived usage. New cost is only the campaign ledger delta for this run ID.",
    )
    write(output / "continuation.json", state)
    print(
        json.dumps(
            {k: v for k, v in state.items() if k not in {"cached_exchanges", "new_requests", "blocked_requests"}}
        )
    )
    return 0 if state["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
