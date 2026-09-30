# Maintenance knowledge graphs from PDF manuals

This repository turns a technical maintenance manual (PDF) into a knowledge graph of
troubleshooting branches: symptom or error code, cause, corrective action and affected
component, following the fixed ontology in [ontology_schema.JSON](ontology_schema.JSON).
Every relation carries the manual segments it comes from and a certificate that says why
it is trusted.

The pipeline is **V3 "Cite, Check, Ask"** ([plan](docs/PIANO_V3.md)):

```text
PDF → 1 read (segments with short IDs) → 2 map (which pages are diagnostic)
    → 3 extract (two independent model reads, IDs instead of copied text)
    → 4 check (witnesses: page structure, agreement, verifier → green/yellow/red)
    → 5 merge (one node per thing, disagreements asked, not fused)
    → 6 ask (grouped questions: an agent first, a person only for what it cannot settle)
    → graph.json + report.json + questions_for_people.txt
```

## Run

```bash
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env   # set OPENAI_API_KEY
.venv/bin/python scripts/kg_v3.py --pdf manual.pdf --out runs/my_manual --gates agent
```

Every model call goes through an archived gateway with a hard cost ceiling
(`backend/services/real_call_budget_ledger.py`); tests run offline:

```bash
.venv/bin/ruff check . && .venv/bin/python -m pytest
```

## Interface (prototype)

A local web interface over the same pipeline: the library of graphs and their versions,
a guided start (a new PDF or a new version of a manual already there), the run followed live
as a growing 3D graph, what waits for a person (questions, approvals), the finished graph with
the evidence of every edge, the log of all runs with the time and cost of each, and the fixed ontology.
One command (Node.js is needed):

```bash
.venv/bin/python scripts/ui.py   # http://127.0.0.1:8765
```

Campaign runs are only read and can be replayed at no cost; runs started from the interface,
and copies made to answer questions, live in `workspace/` (not versioned). Real runs go
through the same ledger with a spend ceiling. Design rules: [docs/DESIGN.md](docs/DESIGN.md);
plan and API: [docs/PIANO_FRONTEND.md](docs/PIANO_FRONTEND.md).

## Evaluation

The evaluation campaign lives in [campaign/](campaign/README.md): one folder per manual with
the hand-annotated gold, the runs and the KPIs, driven by `scripts/campaign.py`. Current
results, negative ones included: [campaign/results/REPORT.md](campaign/results/REPORT.md).
Scientific status and paper workspace: [paper/STATUS.md](paper/STATUS.md).

## Layout

| Path | Content |
| --- | --- |
| `backend/kg_v3/` | the six stations, contracts, reviewers, run with saved state, export |
| `backend/adapters/pdf.py`, `backend/services/pdf_service.py` | PDF text, tables and OCR |
| `backend/services/llm_gateway.py`, `llm_response_archive.py`, `real_call_budget_ledger.py`, `model_pricing.py` | model calls, archive, budget, prices |
| `scripts/kg_v3.py` | one manual from the command line |
| `backend/ui/`, `frontend/`, `scripts/ui.py` | local interface: API, events and replay, React app |
| `scripts/campaign.py`, `kg_v3_kpi.py`, `kg_v3_evaluate.py`, `kg_v3_precision_sheet.py` | evaluation campaign |
| `campaign/` | manuals, gold, runs and results |
| `paper/` | manuscript workspace and frozen experiment evidence |

The previous v22 pipeline, the web application and its frontend were removed; the last
commit containing them is tagged `legacy-v22`.
