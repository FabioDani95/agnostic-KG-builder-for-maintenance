# Agnostic KG Builder for Maintenance

Neurosymbolic pipeline for extracting diagnostic knowledge graphs from technical maintenance manuals.

The system ingests PDF manuals, scopes the relevant pages, drafts an ontology, extracts diagnostic triplets, applies symbolic validation and graph reasoning, and supports operator review before final JSON export.

## Current Status

- Backend execution mode defaults to `multi_agent`.
- The current UI still follows the existing sequential operator flow.
- `GraphState`, supervisor audit logs, and confidence scoring are implemented on the backend.
- The main unstable area is the reflective re-extraction loop when retries are enabled aggressively.

## Core Pipeline

1. Load a manual from `manuals/`.
2. Run scoping and approve the cut plan.
3. Draft an ontology from the selected pages.
4. Review ontology issues, missing bindings, and suggested relations.
5. Extract diagnostic triplets.
6. Optionally run advisory validation/coverage/grounding/refinement agents.
7. Review triplets and export the final ontology JSON.

## Documentation Guide

- [paper_architecture.md](paper_architecture.md): primary technical reference for the current implemented architecture.
- [specification.md](specification.md): product and workflow specification, including UI flow and API behavior.
- [roadmap_agentic.md](roadmap_agentic.md): implementation roadmap, benchmark notes, and open research/engineering work.
- [multi_agent_architecture.md](multi_agent_architecture.md): historical design/specification notes from the original multi-agent architecture planning.

## Repository Layout

- `backend/`: FastAPI app, agents, workflows, graph-state management, ontology pipeline, services.
- `frontend/`: current browser UI.
- `tests/`: backend and frontend regression coverage.
- `manuals/`: local input manuals used during development and benchmarking.
- `benchmark_runs/`: saved benchmark outputs and inspection artifacts.

## Quick Start

Requirements:
- Python environment with project dependencies installed
- `OPENAI_API_KEY` in `.env`

Run the app:

```bash
./run.sh
```

The frontend is served on `http://127.0.0.1:8000`.

## Test Commands

Focused multi-agent regression tests:

```bash
python3 -m pytest tests/test_multi_agent_state.py tests/test_multi_agent_mode_flow.py
```

Broader backend checks can be run from the repo root with `pytest`.

## Publication Notes

For paper writing and public repo framing:
- use `paper_architecture.md` for implementation claims,
- use `roadmap_agentic.md` for future work and current limitations,
- avoid citing `multi_agent_architecture.md` as the source of truth for what is already implemented.
