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

The default PDF generator is **V3 "Cite, Check, Ask"** (`backend/kg_v3`,
[plan](docs/PIANO_V3.md)). The model cites short segment IDs instead of copying
text; each relation gets a certificate of independent witnesses and a
green/yellow/red tier; doubts become grouped questions that an agent reviewer
answers first, so a person sees only what it cannot settle. On the four
development manuals V3 recovers as many or more reference cases than v22
(by meaning: Eastman 7 vs 6 of 8, Danfoss 8 vs 5 of 8, Graco 18 vs 17 of 18),
leaves 0–2 questions per manual for a person instead of 26–157 review items, and
runs 2–13 times faster at lower API cost. These are development measurements on
the manuals used to build the system, with a reference not yet validated by
technicians; blind precision review and gold confirmation sheets are prepared.
See [V3 development results](docs/V3_RISULTATI_SVILUPPO.md) and
[scientific status](paper/STATUS.md).

The previous generator `pdf-g3-structured-recovery-v22` remains selectable with
`kg_v3.pdf_generator: legacy_v22` or `KG_PDF_GENERATOR=legacy_v22` until it is
removed; its C9–C12 evidence is in the [v22 PDF status](docs/PDF_DIAGNOSTIC_STATUS.md)
and the [C9–C12 report](paper/experiments/robustness_continuation_20260926/REPORT.md).

The v11 campaign remains a historical development result.
Its accounting and lexical scores must not be interpreted as validated semantic
recall or transferred to v22. The original report is retained in
[PDF G3 Second Hardening](docs/PDF_G3_SECOND_HARDENING.md). Structured-source
checkpoint evidence remains in [CSV Hardening Campaign](docs/CSV_HARDENING_CAMPAIGN.md).

## Product flow

The primary application works on one machine per workspace:

1. **Macchina** — record and confirm machine identity.
2. **Documenti** — upload PDF, CSV, XLSX, JSON or JSONL sources.
3. **Struttura** — prepare structured sources automatically and present only
   unresolved mapping or join decisions, one at a time.
4. **Grafo** — build one immutable revision per source, inspect nodes,
   relations and originating evidence, correct individual diagnostic records
   with source evidence and revision history,
   then make an explicit human decision.

Important invariants:

- a populated mapped cell is one claim; punctuation never creates hidden claims;
- one semantic role belongs to one source column at a time;
- changing a mapping invalidates downstream evidence and graph revisions;
- PDF semantic extraction preserves the all-pages G1 inventory and records its
  derived selected/unselected page partition on the graph revision;
- new PDF revisions persist wall time, API-reported token usage and an estimated
  USD list-price cost, displayed in the graph review UI;
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

2. Add OPENAI_API_KEY to .env for real-model PDF runs. Models are selected per
   role under `agents` in `config.yaml`; `KG_GENERATION_MODEL` is only the
   fallback. Deterministic mock tests do not require a key.

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
checkpoint evidence lives under artifacts and paper/experiments. Raw PDFs and
SQLite stores excluded by .gitignore remain local; see each campaign’s
reproduction instructions for required source data.

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
