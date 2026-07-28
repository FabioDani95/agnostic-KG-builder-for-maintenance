# Architecture

## Purpose and scope

The application turns one local maintenance PDF at a time into a reviewed,
diagnostic knowledge graph. It is an operator-assisted FastAPI application,
not a multi-tenant service or an installable Python library.

The ontology contract is defined by `ontology_schema.JSON`. The browser console
at `/` is the only primary UI; `/modify/latest` opens the standalone editor for
the latest exported graph.

## Runtime flow

```text
manuals/*.pdf
    |
    v
POST /api/load-manual
    |-- extracts native text and selective OCR
    |-- seeds live graph state
    `-- creates data/runs/<run_id>/
    |
    v
scoping -> operator approval -> ontology draft -> extraction/projection
    -> validation and HITL review -> best-effort export
    |
    v
output/<manual_slug>/{ontology,metrics,conversation}.json
```

`run.sh` delegates to `scripts/dev_server.mjs`, which creates `.venv` when
needed and runs `uvicorn backend.main:app`.

## Module boundaries

| Area | Responsibility |
|---|---|
| `backend/main.py` | Application factory, router registration, health/config endpoints, static UI |
| `backend/routers/` | HTTP and SSE adapters; no new domain logic should originate here |
| `backend/services/` | Scoping, ontology, extraction, validation, review, export, and editor behavior |
| `backend/services/conversation/` | Action dispatch, gating, event emission, heuristics, and tool adapters |
| `backend/agents/` | Phase-specific wrappers used by the multi-agent supervisor |
| `backend/graph/` | Live graph state, state transitions, supervisor routing, and API projections |
| `backend/runstore/` | Append-only events/trace, state snapshots, manifests, and archived-run loading |
| `backend/schemas/` and `backend/models.py` | Wire, state, widget, and ontology contracts |
| `backend/prompts/` | Model prompts only |
| `frontend/` | HITL console plus static graph-editor assets |
| `modify/` | Graph-editor rendering, state, schema, and graph helpers |
| `scripts/` | Offline evaluation, replay, page-offset diagnostics, and batch/manual runners |

The codebase currently has no internal Python import cycles. Compatibility
facades such as `backend/services/llm_service.py` and
`backend/services/ontology_pipeline.py` remain widely imported and should not
be deleted solely because some implementation has moved into smaller modules.

## State and persistence

Live runs are held in the process-local `pdf_store`. `RunStore` mirrors the
important state to `data/runs/<run_id>/`:

```text
manifest.json
pages.json
events.jsonl
trace.jsonl
input/manual.pdf
state_snapshots/<phase>.json
export/{ontology,metrics,conversation}.json
```

Persisted runs can be listed and inspected after a restart, but they are
read-only for pipeline actions. A server restart therefore does not resume
in-flight model work.

## Active routes

The UI uses the manual, chat/action, run, multi-agent status, export, and modify
routes. The unused step-wise `cutplan`, `extract`, and `ontology` compatibility
routers were removed during the cleanup on 2026-07-28.

## Configuration

- `.env` contains local secrets and the default model override.
- `config.yaml` contains pipeline, model, timeout, validation, OCR, confidence,
  and completion settings.
- `backend/app_config.py` owns configuration loading, defaults, and in-memory
  runtime overrides.
- `KG_LLM_MODE=mock` selects deterministic fixture-backed model behavior.
- `KG_RUNS_DIR`, `KG_OUTPUT_DIR`, and `KG_MANUALS_DIR` isolate test/runtime
  artifacts.

## Verification layers

Python unit, contract, and integration tests run without paid model calls.
Playwright exercises the console against the real FastAPI app in mock mode.
The golden harness measures extraction quality separately from code
correctness. See [Test Suite Map](../tests/README.md) and
[Evaluation Protocol](EVALUATION_PROTOCOL.md).

## Known structural hotspots

The architecture is modular, but several implementation units remain large:

- `frontend/console.js` and `frontend/editor/editor.js`;
- `backend/services/graph_editor_session.py`;
- `backend/services/scoping_workflow.py::create_cut_plan_workflow`;
- `backend/services/ontology_workflow.py`;
- `backend/routers/generate.py::generate_json`.

Refactor these only behind existing contract and E2E tests. The preferred
direction is extraction of cohesive helpers, not a new framework or a second
pipeline.
