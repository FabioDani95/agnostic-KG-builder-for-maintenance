# Getting started

## Install

Use Python 3.12 or later. The run and revision locks use `fcntl`, so run on macOS,
Linux or WSL. Install Node.js 22.13+ or 24 LTS and npm if you want the interface.
Commands below assume a POSIX shell and the repository root as the working directory.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Keep an existing `.env` instead of overwriting it. Set `OPENAI_API_KEY` there for
real model calls. `requirements.txt` is sufficient for runtime use;
`requirements-dev.txt` adds test and lint tools. This is an application repository,
so use the scripts directly rather than `pip install -e .`.

Native PDF text is read with PyMuPDF. Scanned pages may need Tesseract OCR and its
language data. Missing OCR is recorded in reading diagnostics; installing the
Python requirements alone does not supply those language files. See
[OCR configuration](configuration.md#pdf-reading-and-ocr).

## Build a connected graph from the command line

`scripts/kg_build.py` runs the connected-graph pipeline: no questions, no gates.
Start with the plan and its cost estimate, which reads the PDF and calls nothing:

```bash
.venv/bin/python scripts/kg_build.py --pdf /absolute/path/manual.pdf --asset-name "Example machine" --estimate
```

The estimate is a range, because the pages to read are chosen by the first model
step. It is not a spending limit. `--preflight --out <dir>` additionally checks the
sections found in the PDF and writes the input manifest, still without a provider.

A real run needs three things said explicitly: that spending is allowed, the
cumulative cap, and a ledger file for this experiment. Without them the command
stops before any call. Ledgers of earlier campaigns are refused.

```bash
.venv/bin/python scripts/kg_build.py \
  --pdf /absolute/path/manual.pdf --asset-name "Example machine" \
  --out workspace/cli/example-kg4 \
  --authorize-spend --budget 1.00 --ledger workspace/cli/example-kg4-budget.jsonl
```

The run directory then holds `graph.json`, `report.json` (with the quality card
under `scorecard`), `input_manifest.json`, the state of every step and the archived
provider responses. Running the same command again resumes. `--replay <dir>`
rebuilds a run from archived responses without the network. Use a new directory
after changing the PDF, the model, the prompts or the ontology.

Options that change cost or content: `--gap-calls` and `--enrich-calls` (most calls
of the gap search and of node enrichment; `0` turns the stage off), `--no-verify`,
`--pages` (extra PDF pages to read), `--model` and `--reasoning`. See
[Architecture](architecture.md#connected-graph-pipeline) for what each stage does
and [Evaluation](evaluation.md) for how to measure the result.

## Extract a PDF with the V3 pipeline

First check the source and configuration without making model calls:

```bash
.venv/bin/python scripts/kg_v3.py \
  --pdf /absolute/path/manual.pdf \
  --asset-name "Example machine" \
  --out workspace/cli/example-run \
  --ledger workspace/cli/example-budget.jsonl \
  --budget 1.00 \
  --preflight
```

Preflight reads the PDF, prepares the input manifest and validates configuration.
It writes local preparation files; it does not measure extraction quality or
verify online model access. The example budget is a cumulative cap in USD, not an
estimate of what a manual will cost.

For a real extraction, run the same command with `--gates interactive` in place
of `--preflight`. Choose a budget you intend to spend. The current CLI defaults
to `gpt-6-luna`; use `--model` and `--agent-model` if a different supported model
is required. Names and prices configured in the repository do not establish
availability to your account.

`interactive` sends unresolved questions to a human question store and leaves
approval to a person. It does **not** open a terminal conversation: inspect
`questions_for_people.txt`. The UI-managed workflow below is the convenient way
to submit answers. `--human-store` additionally persists questions in `people.json`;
an arbitrary CLI output directory is not automatically added to the UI catalogue.

For an unattended workflow, `--gates agent` delegates questions to a model and
uses automatic workflow approval. That approval is not a human review. All gate
presets are explained in [Configuration](configuration.md#reviewer-gates).

Use a new output directory after changing the PDF, extraction code, ontology,
model or semantic configuration. Repeating a compatible command resumes saved
stages; an input mismatch is rejected. Historical state without a manifest is
read-only. Do not remove manifests to force a resume.

## Read the output

| File or directory | Contents |
| --- | --- |
| `graph.json` | Nodes, edges, occurrences, evidence, tiers, excluded relations and workflow status |
| `report.json` | Stage timing, usage, provenance, gate decisions and remaining problems |
| `questions_for_people.txt` | Pending questions for a person |
| `input_manifest.json`, `artifact_index.json` | Input identity and exported artifact hashes |
| `state/`, `state_envelopes/` | Saved stages and integrity metadata for resume |
| `provider_responses/` | Archived provider requests/responses for diagnosis and exact replay |
| `people.json`, `events.jsonl` | Human store and progress events when requested |

The optional quality profile writes additional files documented in
[Architecture](architecture.md#graph-formats-and-exports). Preserve the whole run
directory for reproducibility. Source text and images can be present in the
request archive and exported evidence.

## Use the interface

```bash
.venv/bin/python scripts/ui.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). The launcher runs `npm ci` when
dependencies are missing and rebuilds stale frontend output. Without npm it starts
only the API. API documentation is at `/api/docs`.

1. In the library, open a manual and choose a graph version. Explore nodes,
   relations, source excerpts and PDF pages when available.
2. To start a graph, upload a PDF or choose an existing manual. Confirm the
   machine identity and reviewer mode. Automatic machine identification is itself
   a paid model call; manual entry is available.
3. Follow the extraction in the live view. **Your turn** lists unresolved
   questions and approval tasks. Answer questions, then apply the answers to
   resume the pipeline. Submission alone does not change the graph.
4. Inspect the resulting graph and approve or reject when the workflow offers
   that decision. All interface presets leave final approval to a person.
5. Use **Edit graph** for direct corrections, checks and acceptance of a new
   revision. See the [editor guide](EDITOR_GRAFO.md).

The UI reads saved campaign runs and writes new work under `workspace/`. Answering
questions on a compatible campaign version first creates a workspace copy.
Historical versions can remain readable even when current code cannot resume them.
The catalogue reads its campaign/workspace layout, not arbitrary CLI directories.

**First-run limitation:** the UI refuses extraction when it has no campaign
history from which to estimate cost. It also retains development spending limits.
Use the CLI for a standalone first run; see
[UI storage and limits](configuration.md#interface-storage-and-limits) before
starting work in an established workspace.

## Replay and export

The UI's replay animates saved events or state and makes no provider calls. A
pipeline replay is different: `scripts/kg_v3.py --replay /path/to/archive` supplies
archived responses for exact matching requests. A cache miss never falls back to
a live provider, but it can leave the run failed or incomplete.

The pipeline always writes `graph.json` to its output directory. The API also
serves a version at `/api/manuals/{manual_id}/versions/{version_id}/graph`.
For accepted manual revisions, **Download version and provenance** provides a ZIP
with the graph, base, changes, validation, acceptance and available frozen source.
This ZIP endpoint is specific to manual revisions.

## Common problems

| Symptom | Check |
| --- | --- |
| Empty library | Local campaign/workspace assets may not be part of the clone |
| UI refuses a run with no cost estimate | Use the CLI; estimation needs campaign run history |
| Budget exhausted | Read the ledger and reservations; choose a new authorised run budget without resetting an existing ledger |
| Input or checkpoint mismatch | Use a fresh output directory with the intended inputs |
| Source page unavailable | The original PDF may be absent or no longer match saved evidence |
| Frontend unavailable | Install compatible Node.js/npm and rebuild from `frontend/` |
| API authentication/model error | Check key, model access and the recorded error; do not infer access from a configured name |
| OCR unavailable | Install/configure Tesseract language data or inspect native-text limitations |

The server binds to loopback and has no multi-user authentication layer. Use it
as a local application.
