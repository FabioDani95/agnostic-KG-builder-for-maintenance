# Development

Read [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution and data boundaries.
The [architecture guide](architecture.md) maps features to their source files.

## Run locally

After the [initial installation](getting-started.md#install), start both development
servers from the repository root:

```bash
.venv/bin/python scripts/ui.py --dev
```

The frontend is at `http://127.0.0.1:5173`, with `/api` forwarded to port 8765.
Vite reloads frontend changes. Restart the launcher after backend changes; it
does not enable Uvicorn's reload mode. Keep the default API port unless you also
change the Vite proxy.

For a production frontend build served by the local API:

```bash
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python scripts/ui.py
```

This is a local deployment configuration. Authentication, multi-user isolation
and public hosting are outside the current application's implementation.

## Checks

Run the repository checks without making provider calls:

```bash
.venv/bin/ruff check backend scripts tests
.venv/bin/python scripts/test_offline.py -q
.venv/bin/python scripts/check_repository.py
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build
git diff --check
```

`test_offline.py` invokes pytest with external Python socket connections blocked,
while retaining loopback for local tests. Model fixtures supply responses without
an API key. The wrapper is a test guard, not an operating-system network sandbox.
The frontend build includes TypeScript checking. CI runs the corresponding backend
and frontend checks; see [the workflow directory](../.github/workflows/).

Do not turn a passing test suite into an extraction-quality claim. Tests exercise
contracts, software decisions, persistence and known regressions. Accuracy and
completeness require version-matched source evidence and judged outputs.

## Where to add checks

| Change | Relevant checks |
| --- | --- |
| PDF extraction / source layout | `tests/test_pdf_service.py`, `test_pdf_adapter_layout.py`, `test_kg_v3_reader.py` |
| Mapping, extraction, verification and merging | `tests/test_kg_v3_mapper.py`, `test_kg_v3_pipeline.py`, `test_kg_v3_checker.py`, `test_kg_v3_merger.py` |
| Quality evidence and evaluation | `tests/test_kg_v3_quality_*.py` |
| UI catalogue, questions and job lifecycle | `tests/test_ui_catalog.py`, `test_ui_answers.py`, `test_ui_jobs.py`, `test_ui_api.py` |
| Editor operations and accepted revisions | `tests/test_ui_graph_document.py`, `test_ui_revisions.py`, `test_ui_editor_regressions.py` |
| Frontend behaviour | `frontend/tests/` |

For a targeted check, pass its path to the offline runner, for example:

```bash
.venv/bin/python scripts/test_offline.py tests/test_ui_revisions.py -q
```

## Browser fixture without API spending

The editor fixture creates synthetic manuals and a separate workspace. It disables
extraction, answer application and pipeline approval, while allowing editor revisions.
Choose an empty scratch directory rather than a directory containing real work:

```bash
npm --prefix frontend run build
.venv/bin/python -m tests.graph_editor_browser_fixture --root /tmp/kg-editor-qa
```

Open [http://127.0.0.1:8017](http://127.0.0.1:8017). To complete its synthetic live
run from another terminal:

```bash
.venv/bin/python -m tests.graph_editor_browser_fixture --root /tmp/kg-editor-qa --finish-live
```

Exercise edit, check, summary, back navigation, discard, acceptance and reopening.
An accepted version should preserve its base and provenance. This fixture
validates interaction with artificial data, not extraction on a real manual.

## Maintain the documentation

Keep each topic in one canonical guide under `docs/` and link to it from the index.
Update the relevant guide when commands, defaults, output contracts or user-visible
workflow change. Preserve the bilingual in-app Guide's chapter slugs and section
identifiers; check English/Italian parity when editing its content.

Keep gold and frozen experiments separate from implementation work. Do not replace
a failed historical result with output from newer code or carry its metrics forward
without rerunning. Manuscript materials are private and excluded from this repository;
the application and its tests do not require that workspace. If you also work on
the author's local `paper/` copy, read its writing guidelines, status and instructions
there. Never add manuscript files to a shared commit.
