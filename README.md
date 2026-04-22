# Agnostic KG Builder for Maintenance

A FastAPI application with a browser UI for building diagnostic knowledge graphs from maintenance manuals, one manual at a time.

## What It Does

- Loads PDF manuals placed in `manuals/`
- Scopes the pages that are relevant for diagnostics and maintenance
- Drafts an ontology aligned with `ontology_schema.JSON`
- Lets the operator review missing fields, graph issues, and suggested relations
- Extracts diagnostic triplets from the approved scope
- Supports human validation before export
- Exports a schema-compliant ontology JSON bundle to `output/`

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

### Runtime Model

- Backend: FastAPI
- Frontend: static browser UI served by the backend
- Input source: PDFs placed locally in `manuals/`
- Runtime workspace: `data/`
- Export destination: `output/latest/` and `output/<manual_slug>/`

The current default execution mode is `multi_agent`, configured in `config.yaml`. In practice, the operator still follows the same staged UI flow while backend execution is routed through the current agent wrappers and state tracking.

### Operator Workflow

The current shipped workflow is:

1. Select a manual from the local `manuals/` directory.
2. Provide the page offset when printed manual numbering does not start at PDF page 1.
3. Run document scoping to produce a cut plan.
4. Review and approve or edit the selected sections.
5. Generate an ontology draft from the approved pages.
6. Review required ontology fields, graph issues, and suggested relations.
7. Continue to triplet extraction.
8. Validate or skip extracted triplets.
9. Export the final ontology JSON bundle.

### Current Review Surfaces

Before extraction, the ontology review stage can expose:

- blocking schema issues
- required human input fields
- suggested relations
- graph reasoning diagnostics
- confidence and supervisor diagnostics when enabled

The operator-facing path is still centered on required input and final triplet validation.

### Outputs

Each successful export writes:

- `output/latest/ontology.json`
- `output/latest/metrics.json`
- `output/<manual_slug>/ontology.json`
- `output/<manual_slug>/metrics.json`

The exported ontology is normalized and validated against the current contract before being written.

### Graph Editor

After an export is available, the latest ontology can be inspected in the browser at:

```text
http://127.0.0.1:8000/graph-editor/latest
```

### Current Repository Policy

- Sample manuals are not included in the repository.
- Runtime outputs, local manuals, benchmarks, and installed dependencies are intentionally excluded from version control.
- The root `README.md` is the canonical high-level description of the current repository state.

## Requirements

- Python 3.11+
- An OpenAI API key
- Local PDF manuals to process

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

## Tests

Run the backend test suite with:

```bash
python3 -m pytest
```

Frontend end-to-end tests use Playwright:

```bash
npm install
npx playwright test
```
