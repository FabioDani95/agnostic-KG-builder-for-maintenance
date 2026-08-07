# Maintenance Knowledge Graph Builder

Operator-assisted application for turning maintenance PDFs and structured
records into evidence-backed, source-scoped knowledge graphs.

## Current status

The repository is in active MVP development against
[SPECIFICHE_MVP.md](SPECIFICHE_MVP.md) and the
[normative specification package](docs/specs/README.md).

| Checkpoint | Status | Delivered scope |
|---|---|---|
| G1 | Product Owner accepted | machine workspaces, multi-file inventory, secure local ingestion and automatic PDF preparation |
| G2 | Product Owner accepted | deterministic CSV/XLSX/JSON/JSONL profiling, mapping, evidence creation and exception handling |
| G3 | Human review open | source-scoped graph generation, strict validation, evidence drill-down and the graph explorer are implemented; no subgraph is approved, merged or published automatically |

The automated G3 hardening suite is green, but it is not a Product Owner
acceptance. PDF sources now use the retained scoping and ontology workflow to
produce the same immutable, source-scoped review contract as structured
sources; the UI also shows the exact semantic page selection. Multilingual
canonicalization, broader real-data coverage and the qualitative PDF campaign
remain open. See
[G3 Engine Hardening Handoff](docs/G3_ENGINE_HARDENING_HANDOFF.md) and
[CSV Hardening Campaign](docs/CSV_HARDENING_CAMPAIGN.md).

## Product flow

The primary application works on one machine per workspace:

1. **Macchina** — record and confirm machine identity.
2. **Documenti** — upload PDF, CSV, XLSX, JSON or JSONL sources.
3. **Struttura** — prepare structured sources automatically and present only
   unresolved mapping or join decisions, one at a time.
4. **Grafo** — build one immutable revision per source, inspect nodes,
   relations and originating evidence, then make an explicit human decision.

Important invariants:

- a populated mapped cell is one claim; punctuation never creates hidden claims;
- one semantic role belongs to one source column at a time;
- changing a mapping invalidates downstream evidence and graph revisions;
- PDF semantic extraction preserves the all-pages G1 inventory and records its
  derived selected/unselected page partition on the graph revision;
- knowledge gaps and malformed graph payloads are different blocker classes;
- cross-source merge and publication stay closed until their later checkpoints.

## Runtime surfaces

- **/** redirects to the machine-workspace home at **/home.html**.
- **/console.html?foundation=1** is the current workspace application.
- **/console.html** is the retained one-PDF HITL baseline used as a regression
  surface while the MVP migration is incomplete.
- **/docs** is FastAPI's generated API documentation.

The two browser applications share the FastAPI process but have separate
state models and styling boundaries. The current module and persistence map is
documented in [Architecture](docs/ARCHITECTURE.md).

## Technology

- Python 3.12+, FastAPI and Pydantic
- SQLite for MVP operational state
- content-addressed local raw storage
- vanilla HTML, CSS and JavaScript
- pytest, Ruff, Playwright and a deterministic golden-evaluation harness

The application is a local operator tool, not an installable Python library.

## Quick start

1. Create the local environment file:

   ~~~bash
   cp .env.example .env
   ~~~

2. Add OPENAI_API_KEY to .env for real-model PDF runs. Deterministic mock tests
   do not require a key.

3. Put local PDF manuals under manuals/ if you want to use the retained PDF
   workflow.

4. Start the application:

   ~~~bash
   ./run.sh
   ~~~

The launcher creates .venv when absent, installs missing runtime dependencies
from requirements.txt, frees the configured local port, and starts Uvicorn at
http://127.0.0.1:8000. Set PORT, HOST, KG_RELOAD or PYTHON_BIN to override its
development defaults.

## Development setup

Install runtime and development dependencies:

~~~bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm ci
npx playwright install chromium
~~~

Run the same gates used by CI:

~~~bash
.venv/bin/python -m ruff check .
KG_LLM_MODE=mock .venv/bin/python -m pytest
.venv/bin/python scripts/check_docs_links.py
.venv/bin/python scripts/check_spec_consistency.py --format json --require-status READY_FOR_PLANNING
.venv/bin/python scripts/eval_golden.py --mode mock --fail-on-regression
npm run test:e2e
~~~

See [Test Suite Map](tests/README.md) for suite ownership and
[Evaluation Protocol](docs/EVALUATION_PROTOCOL.md) for golden and live-model
quality evaluation.

## Repository layout

| Path | Responsibility |
|---|---|
| backend/ | FastAPI adapters, domain models, services, repositories and migrations |
| frontend/ | workspace UI plus the retained PDF console |
| tests/ | unit, contract, integration, acceptance, golden and browser tests |
| scripts/ | launch, consistency, evaluation, replay and benchmark utilities |
| docs/ | current documentation, normative specifications and labelled archives |
| artifacts/ | versioned checkpoint evidence referenced by acceptance records |
| data/ | ignored local operational database, raw inputs and run state |
| manuals/ | ignored local source manuals |
| output/ | ignored legacy export bundles |
| eval_runs/, benchmark_runs/, batch_runs/ | ignored local evaluation output |

Generated previews and ad-hoc demo bundles belong outside version control.
Committed datasets live under tests/fixtures or tests/golden; committed
checkpoint evidence lives under artifacts.

## Deployment boundary

The current application is designed for a trusted local operator. It binds to
loopback by default and enforces local Host/Origin checks, canonical path
containment and request-size limits. It has no user authentication or
authorization and must not be exposed directly to an untrusted network.

Production deployment requires an explicit security architecture,
authentication, authorization, secret management, audited dependency locking
and deployment-specific storage controls.

## Documentation

Start from [docs/README.md](docs/README.md). Historical plans are kept under
docs/archive and are non-normative; they should not be used to infer current
routes, UI behavior or implementation status.
