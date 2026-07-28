# Test Suite Map

How the tests are organized, what each layer answers, and how to run it.
The **quality/performance evaluation** (golden fixtures, KPIs, real-model
runs) is a separate layer governed by
[docs/EVALUATION_PROTOCOL.md](../docs/EVALUATION_PROTOCOL.md) — this file
covers the code-correctness suites.

## How to run

```bash
# Full python suite (fast, deterministic, no API key)
KG_LLM_MODE=mock .venv/bin/python -m pytest tests/ -q

# Frontend / E2E (the browser download is needed once)
npm ci
npx playwright install chromium
npm run test:e2e

# Quality gate on golden fixtures (deterministic, mock LLM)
.venv/bin/python scripts/eval_golden.py --mode mock --fail-on-regression
```

## Layers

### 1. Unit — services & algorithms
One service or algorithm, mocked collaborators.

| File | Covers |
|---|---|
| `test_confidence.py` | schema-aware confidence scoring |
| `test_cutplan_service.py` | cut-plan building |
| `test_page_offset_service.py` | PDF↔printed page offset detection |
| `test_pdf_service.py` | physical-page preservation + selective OCR fallback |
| `test_ontology_coverage.py` | internal/export relation formats + diagnostic-root KPIs |
| `test_coverage_completion_service.py` | coverage completion (id reuse, dangling relations) |
| `test_style_cleanup_service.py` | guarded LLM style rewrites |
| `test_ontology_merge_service.py`, `test_ontology_patch_service.py` | graph merge/patch |
| `test_ontology_semantics.py`, `test_llm_service_semantics.py` | semantic validation rules |
| `test_ontology_pipeline_coercion.py`, `test_ontology_pipeline_validation.py` | pipeline payload coercion/validation |
| `test_graph_editor_validation.py` | manual graph-edit validation |
| `test_extraction_quality_fixes.py` | regression tests for the Fase 0/1 extraction-quality bug fixes |
| `test_improvement_sprints.py` | resolution/completion improvement passes |
| `test_trace_recorder.py` | structured trace recording |

### 2. Contract — schemas & wire formats
Frozen shapes: if these fail, a consumer (frontend, stored runs) breaks.

| File | Covers |
|---|---|
| `test_schemas_contract.py` | Pydantic request/response schemas |
| `test_ontology_contract.py` | ontology JSON shape |
| `test_widget_contract.py` | chat-widget payload schema (persisted chat-event contract) |
| `test_run_state_schema.py` | persisted RunState schema |
| `test_chat_event_characterization.py` (+ `chat_event_fixtures.py`) | characterization of the chat event stream |

### 3. Integration — in-process flows (mock LLM)
Several services composed, real filesystem/run-store, `KG_LLM_MODE=mock`.

| File | Covers |
|---|---|
| `test_scoping_workflow.py` | scoping → cut-plan approval workflow |
| `test_ontology_workflow_pages.py` | ontology draft over kept pages |
| `test_multi_agent_mode_flow.py`, `test_multi_agent_state.py` | multi-agent orchestration & state |
| `test_graph_cocreator_agent.py` | graph co-creator agent |
| `test_chat_actions_service.py`, `test_chat_tools_state.py`, `test_chat_graph_modify_tools.py`, `test_chat_orchestrator_status.py` | chat orchestration & graph-modify tools |
| `test_run_store.py`, `test_replay_run.py` | run persistence & replay |
| `test_runs_router.py`, `test_modify_routes.py`, `test_generate_export_route.py` | FastAPI routes (HITL console, modify, export) |
| `test_ontology_export_store.py` | export store round-trip |
| `test_llm_gateway.py` | gateway mode switching (mock/economy/full) |
| `test_manual_loader.py` | markdown golden-manual loader |

### 4. Evaluation-harness tests
Meta-tests: they test the *evaluator*, not the pipeline. Guard the matching
rules the KPIs depend on (token-exact error codes, atomic-chain explosion,
grounding), so a metric change is always a deliberate one.

| File | Covers |
|---|---|
| `test_eval_golden.py` | `scripts/eval_golden.py` matching/gating logic + mock smoke run |

### 5. E2E — Playwright (`*.spec.js`)
Browser-level flows against the dev server.

| File | Covers |
|---|---|
| `console.spec.js` | HITL console (the only frontend, served at `/`) |

(The legacy chat/wizard frontend and its five specs were removed on
2026-07-06; the console is the sole UI.)

### Manual runners (not pass/fail tests)
Kept for telemetry and ad-hoc exploration; they emit reports, not verdicts.
Do **not** quote their output as performance results — use the golden eval.

| File | Notes |
|---|---|
| `scripts/live_chat_benchmark.py` | live chatbot probe → `benchmark_runs/live_chat_benchmark_*.json` |
| `scripts/run_manual_benchmark.py` | phased pipeline runner on PDFs → `benchmark_runs/` |
| `scripts/run_batch_export.py` | interactive batch export → `batch_runs/` |

## Known failures (verified 2026-07-28)

None — the suite is green under `KG_LLM_MODE=mock`.

(The 4 failures previously listed here were tests patching the stale
`<service>.OpenAI` seam after the mockable LLM gateway landed; under mock mode
`get_client()` ignores the client factory, so the scripted fake clients were
never used. Fixed by patching `get_client` in the service module instead —
tests that script LLM responses must mock `get_client`, not `OpenAI`.)

## Conventions

- New pytest files: `test_<area>_<aspect>.py`, placed in the layer above that
  matches what a failure would mean.
- Anything touching an LLM must run under `KG_LLM_MODE=mock` in tests.
- Golden fixtures and their annotations are governed by the evaluation
  protocol — never edit `tests/golden/expected/*.json` casually (frozen
  annotations, see protocol §6 step 8).
