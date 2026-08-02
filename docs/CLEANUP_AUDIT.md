# Repository Cleanup Audit — Outcome

**Audit date:** 2026-07-28  
**Status:** cleanup applied; no unresolved source-code deletion candidate remains.

## Outcome

The repository now has one clear documentation entry point, one documented
runtime architecture, a smaller active API surface, and a clean separation
between automated tests and manual benchmarks.

Completed actions:

- Removed `CONTRIBUTING.md`; this is a privately maintained project.
- Added `docs/README.md` as the documentation index.
- Added `docs/ARCHITECTURE.md` as the current architecture specification.
- Moved the completed stabilization plan, frontend redesign plan, and pre-fix
  QA report to `docs/archive/`.
- Removed the unused step-wise `cutplan`, `extract`, and `ontology` routers,
  their environment flag, and their compatibility-only tests. The active
  `generate`, console, run, chat, multi-agent, upload, and, at the audit date,
  `modify` routes remained. The `modify` routes were intentionally removed on
  2026-07-29 by `DEC-022`.
- Moved the live report-producing probe from
  `tests/chatbot_e2e_test.py` to `scripts/live_chat_benchmark.py`.
- Removed the obsolete triplet-extraction phase from
  `scripts/run_manual_benchmark.py`; quality extraction is measured by the
  golden harness and the full live path by `live_chat_benchmark.py`.
- Corrected documentation drift: Python 3.12, all nine golden fixtures,
  calibrated Whirlpool gates, current output files, and local deployment
  boundaries.
- Replaced mutable Pydantic collection defaults with explicit factories.
- Added stable npm metadata and `npm run test:e2e`.
- Expanded CI from Ruff + pytest to also check documentation links, run the
  deterministic golden gate, and execute Playwright.
- Added `scripts/check_docs_links.py` so moved or deleted documentation cannot
  leave broken local links.
- Ignored local AI-tool state, Playwright reports, and secondary coverage
  artifacts.

## Local cleanup outcome

- Three clean `.claude/worktrees/` worktrees were removed.
- Their branch references were retained, so no commit was discarded.
- Two untracked evaluation reports from the removed `modest-brahmagupta`
  worktree were moved into the root ignored `eval_runs/` directory.
- One worktree was deliberately retained:
  `.claude/worktrees/distracted-kowalevski-7d4e1f`.

The retained worktree contains uncommitted changes in:

```text
backend/services/llm_gateway.py
tests/golden/README.md
tests/golden/manuals/eagle_s3l_laser_cutter_manual.md
tests/golden/manuals/haier_lma4120_washer_manual.md
tests/test_llm_gateway.py
```

Deleting it would lose work. It should be reviewed and either committed,
discarded explicitly, or merged before the worktree is removed.

Generated caches, browser-test output, project-local Codex visualizations,
macOS metadata, and obsolete `chatbot_e2e_*` telemetry were removed after the
final verification run.

## Deliberately retained

These paths are ignored but may contain valuable local or research data and
were not bulk-deleted:

| Path | Reason retained |
|---|---|
| `data/` | Run history, copied inputs, events, traces, and snapshots |
| `manuals/` | Real source manuals not present in Git |
| `output/` | Exported ontology bundles |
| `benchmark_runs/` | Manual benchmark evidence other than obsolete chatbot telemetry |
| `batch_runs/` | Batch-export reports |
| `eval_runs/` | Golden and real-model evaluation evidence |
| `.venv/`, `node_modules/` | Installed local development dependencies |
| `.claude/worktrees/distracted-kowalevski-7d4e1f` | Contains uncommitted work |

The five `docs/*_GOLDEN_EVAL.md` files were also retained. They are not
duplicated documentation: they record why frozen annotations and quality gates
exist.

## Verification

The cleanup is accepted only when all of these remain green:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/check_docs_links.py
.venv/bin/python scripts/eval_golden.py --mode mock --fail-on-regression
npm run test:e2e
```

Current result:

- Ruff: passed.
- Pytest: 313 passed; the count decreased by two because the removed tests
  covered only the deleted legacy-route flag.
- Documentation links: passed.
- Deterministic golden evaluation: 9/9 fixtures passed.
- Playwright: 1/1 console E2E passed.
- Internal Python import graph: no cycles found.
- Current tracked files: no obvious API-key or private-key pattern found.

## Remaining release work

These are not repository-cleanup tasks and were intentionally not mixed into
this change:

1. Produce a reviewed Python constraints or lock file for tagged releases;
   runtime dependencies are currently mostly unpinned.
2. Repeat the historical real-model QA scenario before calling a build
   production-ready; passing mock gates does not measure live-model variance.
3. Add authentication, authorization, restrictive CORS, request limits, and a
   hardened storage boundary before exposing the app outside a trusted local
   machine.
4. Review the one dirty Claude worktree and decide whether its changes belong
   on `main`.

## Maintainability backlog

The code is healthy, but these large units are the next sensible refactoring
targets:

1. `backend/services/scoping_workflow.py::create_cut_plan_workflow`
2. `backend/routers/generate.py::generate_json`
3. `frontend/console.js`
4. `frontend/editor/editor.js`
5. `backend/services/ontology_workflow.py`

Refactor them only behind the pytest, golden, and Playwright gates. They are
maintainability hotspots, not current correctness blockers.
