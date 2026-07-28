# Agnostic KG Builder for Maintenance

A FastAPI application with a browser UI for building diagnostic knowledge graphs from maintenance manuals, one manual at a time.

Start with the [documentation index](docs/README.md) for the current
architecture, evaluation protocol, and repository-cleanup status.

## What It Does

- Loads PDF manuals placed in `manuals/`
- Scopes the pages that are relevant for diagnostics, maintenance, and component coverage
- Drafts an ontology aligned with `ontology_schema.JSON`
- Lets the operator review missing fields, graph issues, and suggested relations
- Extracts diagnostic triplets from the approved scope
- Supports human validation before export
- Exports a best-effort ontology JSON bundle to `output/`, surfacing contract gaps as warnings instead of blocking the final file

## Current System Specification

### Product Scope

The current system is designed for manual, operator-assisted processing of one technical maintenance manual at a time. It is not documented here as a batch-processing tool.

The extracted knowledge graph is ontology-first and targets these node families:

- `Asset`
- `Component`
- `Symptom`
- `FailureMode`
- `CorrectiveAction`
- `ErrorCode`

The allowed schema and required properties are defined in `ontology_schema.JSON`.

Scoping is recall-oriented for component coverage:

- troubleshooting, diagnostics, alarms, maintenance, repair, calibration, and inspection sections remain in scope
- assembly drawings, exploded views, drawings and parts lists, spare-parts sections, and component reference diagrams are also in scope when they help identify physical components or subsystems
- pages selected from component-rich sections are preserved even when the language filter would otherwise drop low-text drawing pages

### Runtime Model

- Backend: FastAPI
- Frontend: the HITL console, a static browser UI served by the backend at `/` (also reachable as `/console.html`). The legacy chat/wizard UI was removed on 2026-07-06.
- Input source: PDFs placed locally in `manuals/`
- Runtime workspace: `data/`
- Export destination: `output/latest/` and `output/<manual_slug>/`

The current default execution mode is `multi_agent`, configured in `config.yaml`. In practice, the operator still follows the same staged UI flow while backend execution is routed through the current agent wrappers and state tracking.

### HITL Console

The console (served at `/`) is the operator-facing UI. It lists every persisted run (from `data/runs/`, exposed via `/api/runs`), reopens archived sessions with their review decisions intact, and drives a live run end to end: start a new session (manual + models + language + operator initials), approve the scoping page selection, start extraction, inspect the extracted graph and diagnostic chains, work through the review queue (confidence signals, evidence quotes, suggested relations, multi-cause ambiguities), fill the fields the extraction could not complete, and export once the pipeline reaches the export phase. Review verdicts are appended to each run's `events.jsonl` audit trail via `/api/runs/{id}/review-decisions`, so a session can be closed and resumed later. Export stays locked until extraction and validation are complete; open gaps are declared in the exported file rather than hidden.

The pipeline pauses at explicit operator handoffs (cut-plan approval, extraction start): the backend marks them in the run status (`run_status = awaiting_operator` plus the pending `next_step`) and the console dashboard announces them with a "your turn" banner and a direct call-to-action. While a phase is running, the banner shows a live "last recorded progress N s ago" ticker; a session whose backend process died mid-flow is labelled as interrupted rather than complete. Note: reopening a persisted run is read-only for pipeline actions — a run interrupted mid-flow (e.g. by a server restart) currently requires a new session to complete the extraction.

### Quality Evaluation

Extraction quality is measured with golden fixtures under `tests/golden/` via `scripts/eval_golden.py`. The normative procedure — metric definitions (sample recall, unsupported-chain rate, grounded precision), fixture anatomy, the two-phase authoring/calibration process, and the protocol for model/config comparisons — is in `docs/EVALUATION_PROTOCOL.md`. Per-fixture calibration reports live in `docs/*_GOLDEN_EVAL.md`; the deterministic mock gate is `python3 scripts/eval_golden.py --mode mock --fail-on-regression`.

### Operator Workflow

The current shipped workflow is:

1. Select a manual from the local `manuals/` directory.
2. Provide the page offset when printed manual numbering does not start at PDF page 1.
3. Run document scoping to produce a cut plan.
4. Review and approve the selected sections.
5. Generate an ontology draft from the approved pages.
6. Review required ontology fields, graph issues, and suggested relations.
7. Continue to triplet extraction.
8. Validate or skip extracted triplets.
9. Export the final ontology JSON bundle. The export path is best-effort: the file is still produced even when advisory or blocking ontology issues remain, and those issues are carried forward as export warnings.

### Current Review Surfaces

Before extraction, the ontology review stage can expose:

- schema issues
- required human input fields
- suggested relations
- graph reasoning diagnostics
- confidence and supervisor diagnostics when enabled

The operator-facing path is still centered on required input and final triplet validation. Ontology issues remain visible to the operator, but they do not hard-block the final JSON export.

### Outputs

Each successful export writes:

- `output/latest/ontology.json`
- `output/latest/metrics.json`
- `output/<manual_slug>/ontology.json`
- `output/<manual_slug>/metrics.json`
- `output/<manual_slug>/conversation.json` for exports initiated from the HITL console

The exported ontology is normalized and validated against the current contract before being written. Export is best-effort:

- contract-compliant payloads are written with `metadata.export_status = "ok"`
- incomplete payloads are still written with `metadata.export_status = "warning"`
- export warnings are stored in `metadata.export_warnings` and counted in `metadata.export_warning_count`
- the HTTP export response also returns `X-Export-Warnings-Count`

### Graph Editor

After an export is available, the latest ontology can be inspected in the browser at:

```text
http://127.0.0.1:8000/modify/latest
```

### Current Repository Policy

- Sample manuals are not included in the repository.
- Runtime outputs, local manuals, benchmarks, and installed dependencies are intentionally excluded from version control.
- The root `README.md` is the canonical high-level description of the current repository state.
- Generated state for local AI tools (`.claude/`, `.codex/`) is not part of the project.

### Repository Layout

```text
backend/          FastAPI routes, pipeline services, agents, schemas, and run persistence
frontend/         HITL console and standalone graph editor
modify/           Graph-editor domain and rendering helpers
scripts/          Evaluation, replay, benchmark, and batch utilities
tests/            Python, contract, golden-evaluation, and browser tests
docs/             Current technical docs plus clearly labelled historical records
manuals/          Local PDF inputs (ignored except for directory placeholders)
data/             Runtime run state and copied inputs (ignored)
output/           Exported ontology bundles (ignored)
```

See [Architecture](docs/ARCHITECTURE.md) for module boundaries and the runtime
flow. Follow the test and evaluation protocols before changing contracts or
golden fixtures.

## Requirements

- Python 3.12+
- Node.js 18+ for browser tests
- An OpenAI API key for real-model runs (not required for deterministic mock tests)
- Local PDF manuals to process
- Optional: Tesseract OCR with the `eng` language data. Without it, native PDF
  extraction continues normally and low-text pages are reported as OCR-unavailable.

### Selective OCR

PDF ingestion preserves every physical page, including image-only pages. OCR is
selective rather than document-wide: it is attempted on low-text front-matter
pages needed for ToC discovery and on low-text pages inside the sections chosen
by scoping. Limits, language, DPI, and the native-text threshold are configured
under `pdf_ingestion.ocr` in `config.yaml`. Each page records `text_source` and
`ocr_status`, and the run metrics list unreadable pages explicitly.

On macOS, Tesseract can be installed with `brew install tesseract`; on Debian or
Ubuntu, install the `tesseract-ocr` and `tesseract-ocr-eng` packages.

## Setup

1. Create the environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set `OPENAI_API_KEY`.

3. Place one or more PDF manuals in `manuals/`.

4. Start the application:

   ```bash
   ./run.sh
   ```

The script creates `.venv` if needed, installs Python dependencies when missing, and starts the server on `http://127.0.0.1:8000`.

## Deployment Boundary

The current application is designed for a trusted local operator. It has no
authentication, accepts runtime configuration changes, uses permissive CORS,
and reads/writes the local filesystem. Do not expose it directly to an
untrusted network without adding authentication, authorization, restrictive
CORS, request limits, and a hardened storage boundary.

## Tests

Run the backend test suite with:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/eval_golden.py --mode mock --fail-on-regression
```

Frontend end-to-end tests use Playwright:

```bash
npm ci
npx playwright install chromium  # one-time browser download
npm run test:e2e
```

See [Test Suite Map](tests/README.md) for the unit, contract, integration,
evaluation-harness, and E2E layers. The normative quality procedure is in
[Evaluation Protocol](docs/EVALUATION_PROTOCOL.md).
