# Test suite map

The repository has two implementation tracks under test:

- the current multi-source MVP workspace flow;
- the retained one-PDF pipeline, which remains a regression floor.

Quality evaluation is a separate concern governed by
[docs/EVALUATION_PROTOCOL.md](../docs/EVALUATION_PROTOCOL.md).

## Run all gates

~~~bash
.venv/bin/python -m ruff check .
KG_LLM_MODE=mock .venv/bin/python -m pytest
.venv/bin/python scripts/check_docs_links.py
.venv/bin/python scripts/check_spec_consistency.py --format json --require-status READY_FOR_PLANNING
.venv/bin/python scripts/eval_golden.py --mode mock --fail-on-regression
npm ci
npx playwright install chromium
npm run test:e2e
~~~

pytest discovers both tests/test_*.py and tests/planned/test_*.py. The planned
directory name is historical: its current files are executable acceptance and
contract tests referenced by the normative specification package.

## Python layers

### Unit and service tests

Top-level test modules cover deterministic algorithms and isolated services:
confidence, scoping, PDF extraction/OCR, ontology contracts, graph reasoning,
grounding, merging, completion, structured preparation, source-subgraph
generation and repository behavior.

### Contract tests

Schema and characterization tests freeze:

- API/Pydantic payloads;
- ontology and widget shapes;
- persisted run state and chat events;
- absence of the removed graph editor and mutation API;
- structured evidence, graph revision and strict validation behavior.

### Integration tests

Integration tests compose real repositories, temporary filesystems and the
FastAPI app under KG_LLM_MODE=mock. They cover workspace/source persistence,
preparation, run replay, retained multi-agent orchestration, routes, export and
LLM-gateway mode selection without paid calls.

### MVP acceptance tests

tests/planned contains the executable scenarios linked to requirement IDs:

- workspace identity, source inventory and security boundaries;
- PDF preservation and structured-source accounting;
- CSV/XLSX/JSON/JSONL mapping, joins and language cases;
- HITL decisions and invalidation;
- source-scoped graph generation and strict ontology validation;
- regression and specification traceability.

The suite name does not imply that every product checkpoint is accepted.
Automated coverage and Product Owner acceptance are separate artifacts.

## Browser tests

| File | Surface |
|---|---|
| tests/console.spec.js | retained one-PDF HITL console |
| tests/planned/spec_acceptance.spec.js | workspace home, upload, structure phase, graph explorer, accessibility and blocker behavior |

Playwright starts the real FastAPI server with isolated SQLite/raw/output paths
and deterministic mock LLM behavior.

## Golden evaluation

scripts/eval_golden.py evaluates the frozen fixtures under tests/golden. Unit
tests for the evaluator protect its matching and gating logic; the evaluator
run itself produces a separate report under ignored eval_runs.

Mock success proves reproducibility and regression safety, not live-model
quality. Real-model reports must follow the evaluation protocol.

## Manual runners

These scripts emit telemetry and are not pass/fail tests:

| Script | Output |
|---|---|
| scripts/live_chat_benchmark.py | benchmark_runs |
| scripts/run_manual_benchmark.py | benchmark_runs |
| scripts/run_batch_export.py | batch_runs |
| scripts/replay_run.py | inspection of retained persisted runs |

Do not quote manual-run output as a quality result.

## Conventions

- Use test_<area>_<aspect>.py for new Python tests.
- Isolate filesystem and database state with temporary paths.
- Any LLM-touching correctness test must use deterministic mock mode.
- Do not casually edit tests/golden/expected; those files are frozen
  evaluator annotations.
- A passing test may support an acceptance criterion but cannot replace the
  Product Owner decision recorded under artifacts/user-gates.
