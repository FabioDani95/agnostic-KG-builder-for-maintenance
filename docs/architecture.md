# Architecture

## One pipeline, two entry points

The CLI (`scripts/kg_v3.py`) prepares a PDF, model clients, reviewers and a run
directory, then invokes `backend/kg_v3/run.py`. The local interface starts the
same CLI in a child process. It adds a catalogue, persisted human questions,
progress events and graph revisions; it does not implement a second extractor.

| Stage | Work performed | Main implementation |
| --- | --- | --- |
| Read | Preserve page evidence, text segments, table layout and OCR diagnostics | `backend/adapters/pdf.py`, `backend/services/pdf_service.py`, `backend/kg_v3/reader.py` |
| Map | Identify diagnostic pages and form reading units; scan content beyond the outline | `mapper.py` |
| Extract | Ask the model for structured diagnostic records with source identifiers; two reads by default | `extractor.py`, `prompts.py`, `references.py` |
| Check | Combine structural evidence, agreement and model verification into relation certificates | `checker.py`, `vision.py` |
| Merge | Consolidate compatible entities and relations while retaining assertions and disagreements | `merger.py`, `navigation.py` |
| Review | Route map, doubt and approval questions through configured reviewers | `questions.py`, `reviewers.py`, `run.py` |
| Export | Write a graph, report and integrity metadata | `export.py`, `run_state.py` |

Module names without a prefix in this table are under `backend/kg_v3/`.
These stages include recovery and verification passes, so two extraction reads
do not mean two provider calls for a whole manual. Independent requests to the
same model also do not establish statistical independence.

## Ontology and evidence

[ontology_schema.JSON](../ontology_schema.JSON) defines `Asset`, `Component`,
`Symptom`, `FailureMode`, `CorrectiveAction` and `ErrorCode`, with six relation types:
`HAS_COMPONENT`, `MAY_INDICATE`, `AFFECTS`, `RESOLVED_BY`, `GENERATES_ERROR` and
`INDICATES`. Extraction and editor validation use this schema.

An edge can contain several occurrences, each with its own source evidence,
conditions and verification certificate. Page/segment identifiers let a reviewer
return to the evidence. The code adds asset links marked `derived: true`.
Missing properties may be represented explicitly as `not_stated` or `Unknown`.
Do not interpret these placeholders as statements printed in the manual.

The standard export includes green and yellow edges. Yellow edges carry
`trusted: false`; red relations appear in `excluded_relations`. A green tier
records the software's verification outcome. Neither a source quotation nor a
green certificate proves operational safety, complete extraction or causal truth.

The optional `quality_v1` profile extends the same pipeline with immutable evidence
references, explicit branch/entry scopes, diagnostic instances, coverage items,
visual routing and bounded review requests. It is coordinated by `quality_run.py`
and implemented in `source_index.py`, `visual_catalog.py`, `coverage.py` and
`validation.py`. The default `base_safe` profile leaves these extensions off.
See the [quality guide](kg_quality/README.md) for its contracts and current limits.

## Graph formats and exports

| Format | Meaning |
| --- | --- |
| `kg-v3-graph-2` in `graph.json` | Pipeline graph consumed by the existing UI; for quality runs it is a compatibility projection |
| `kg-ingestion-quality-1` in `ingestion_quality.json` | Rich quality output with source scope, lineage, rejected candidates, coverage and validation |
| `kg-v3-graph-3` in a manual revision | Graph accepted through the editor, with per-occurrence human decisions and revision provenance |

Quality runs also write `source_index.json`, `coverage.json`,
`review_requests.json` and `quality_review.md`. Image-only facts may be present
in the rich output and absent from the text-based graph projection. Check the
projection status and `not_projected` records before treating `graph.json` as the
whole result. Its relationship to the quality output is protected by hashes;
editing it outside the pipeline can make that binding stale.

The quality loaders in `export.py` distinguish verified bundles from legacy or
stale data. Historical graphs without a sidecar are not retroactively certified.
Editor revisions are a separate human-review artifact; accepting one does not
rerun extraction or regenerate a quality sidecar.

## State, calls and spending

The input manifest binds a run to its PDF, parsed evidence, extraction sources,
ontology, model and semantic configuration. Checkpoint envelopes bind completed
stages to their dependencies. Compatible resumes reuse saved work; incompatible
or legacy checkpoints are rejected. A local writer lock prevents concurrent CLI
writes to one run directory, and files are published with atomic replacement.

`ModelClient` uses the OpenAI Chat Completions interface through
`backend/services/llm_gateway.py`. `llm_response_archive.py` stores provider
traces. `real_call_budget_ledger.py` reserves an estimated worst-case amount
before a provider attempt and records its final accounting. Repository pricing
is defined in `model_pricing.py`; usage estimates are not provider invoices.

A run can finish with unresolved questions, rejected approval or incomplete
extraction. `approved` describes workflow state, and can originate from the
CLI's automatic reviewer. It is not a quality score. Consult the report and
occurrence-level evidence together.

## Interface and revisions

`backend/ui/api.py` exposes REST endpoints and server-sent events.
`catalog.py` reads manuals and versions, `jobs.py` starts/resumes CLI jobs,
`store.py` persists human answers, and `evidence.py` retrieves verified source
segments and page images. `frontend/src/App.tsx` defines the UI routes;
`screens/`, `editor/`, `graph/` and `live/` implement browsing, editing,
3D rendering and event state.

Graph editing is local and makes no model calls. Preview validates proposed
operations without saving a draft. Acceptance creates an atomic revision under
`workspace/<manual_id>/revisions/`, preserving the parent graph and available
source evidence. Original campaign runs remain unchanged. See the
[editor guide](EDITOR_GRAFO.md) for the distinction between version acceptance,
automatic verification and human confirmation.

## Repository map

| Path | Responsibility |
| --- | --- |
| `backend/kg_v3/` | Extraction, contracts, review and export |
| `backend/domain/`, `backend/adapters/`, `backend/services/` | Evidence/source models, PDF reading, provider gateway and budget accounting |
| `backend/ui/`, `frontend/`, `scripts/ui.py` | Local application |
| `scripts/kg_v3.py` | Single-PDF CLI |
| `tests/`, `frontend/tests/` | Offline software checks |
| `docs/` | Operational and developer documentation |
| `campaign/` | Manual registry, gold and historical campaign workflows |
| `workspace/` | Local UI data, uploads, runs, revisions and preferences |

Some local experiment and review directories are deliberately outside version
control. Their presence in one workstation does not make them clone prerequisites.
The local `paper/` workspace is private and excluded from code sharing.
