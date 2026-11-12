# Architecture

## Two pipelines

The repository holds two extraction pipelines that share the PDF reader, the model
gateway, the budget ledger and the graph file format.

| Pipeline | Entry point | State |
| --- | --- | --- |
| Connected graph (`backend/kg_v4/`) | `scripts/kg_build.py` | Autonomous, built for connected and described graphs. Verified offline with a scripted model; not yet measured on real manuals |
| V3 (`backend/kg_v3/`) | `scripts/kg_v3.py`, and the interface | The pipeline of the saved campaigns; the baseline every new measurement is compared with |

The interface still starts V3. Graphs of both pipelines open in the interface and
in the editor, and the live view shows the steps of either on the same stations.

## Connected-graph pipeline

A run goes from the PDF to the graph without asking anyone anything:

```text
read → survey → extract → verify → resolve → gaps → enrich → export
```

| Stage | Work performed | Model calls | Implementation |
| --- | --- | --- | --- |
| Read | Segments, tables and OCR as in V3; heading trail, printed page numbers and printed pointers for every segment | none | `backend/adapters/pdf.py`, `kg_v3/reader.py`, `kg_v4/sections.py` |
| Survey | One reading of the whole text: which pages hold troubleshooting knowledge, one catalogue of components (with hierarchy) and codes, what the manual says the machine is | one per batch of pages | `survey.py` |
| Extract | One record per source entry (a table row, a flowchart, a procedure): problem, causes, actions, with the manual's descriptions, steps and expected values; parts are named from the catalogue | one per passage, plus one for unused table rows | `extract.py`, `images.py` |
| Verify | One meaning check of every fact against its passage | one per passage | `verify.py` |
| Resolve | One node per real thing, with aliases and all provenance | one per batch of close names | `resolve.py`, `names.py` |
| Gaps | The graph lists what a diagnosis would miss; the manual is searched for exactly that | bounded (default 24) | `gaps.py` |
| Enrich | Description and attributes of every node, from the passages where it is written | bounded (default 40) | `enrich.py` |
| Export | `graph.json`, report and quality card | none | `export.py`, `metrics.py`, `pipeline.py` |

Design rules, each tied to a defect measured on saved runs:

- **Global before local.** Each V3 passage was read with no knowledge of the rest of
  the manual, so the same part became several nodes and no relation joined sections.
  The survey gives every extraction call the same list of parts and codes.
- **A record is a source entry.** Causes and their actions are nested under their
  problem, so a cause cannot take the remedy of the row beside it.
- **Only meaning rejects.** A fact always carries a page and a section; segment IDs
  are added when the model cites them or the code finds the words. A missing or odd
  citation never removes a fact. The verifier can reject a fact only by naming what
  is wrong in its meaning (an opposite value, another entry, a prerequisite taken
  for the remedy, something the passage never names, another part). Everything else
  is a confidence level: `high` (supported), `medium` (not checked), `low` (unclear).
  Rejected facts are listed in `excluded_relations` with the reason.
- **Identity is global, branches stay on facts.** Names equal in canonical form
  (case, articles, plurals, number words) are one entity. Close names go to a model
  that sees how the manual describes and uses each. Names that differ by a number,
  an axis, a side, an opposite or a negation are never merged, whatever a score or a
  model says, and two names nobody compared are not merged through a third. Every
  occurrence keeps its source record, so a consumer can still walk one entry.
- **Absence is stated.** A remedy the manual gives without a cause is linked to the
  symptom or code directly; there are no placeholder causes. A cause without a
  remedy, a problem without an explanation and a cause no symptom leads to are
  searched for in the manual; when nothing is written, the node says so
  (`remedy_status`, `diagnosis_status`, `entry_status`).
- **Text is kept.** Descriptions, instruction steps and expected values are read
  with the facts and written again per node by the enrichment stage. A value the
  manual does not give is exported as a declared placeholder and counted.

Two repairs need no model: a printed pointer from one entry to another ("like
'Pump gets too hot'") is followed, and an item whose own name names a catalogued
part is linked to that part. Such links carry `origin: reference` and
`origin: name_mention`; the quality card reports connectivity with and without
the second kind. A word that names the machine itself is not a part.

### What was kept, cut and rewritten

| Area | Kept | Not used by the connected-graph pipeline | Rewritten |
| --- | --- | --- | --- |
| Reading | Segments, table rows with column names, merged cells, numbered steps, passage packing with title trail | Page labels from a 480-character outline, two map readings, the map gate | Sections per segment; drawn flowchart pages sent as images |
| Extraction | Segment citations, record labels, typed conditions, split on truncation, second read of unused table rows | Second full read, placeholder causes, the rule that renamed causes close to their problem | Record schema with descriptions, steps, expected values, components and pointers |
| Checking | One passage-level check | Witness counting, certificates, bindings, scopes, quarantines, the agent re-review, the cross-branch rule, action reduction | Verdicts about meaning with a named problem |
| Merging | Union with "different" constraints, aliases | Branch-scoped identity, the prompt bias towards "different entries, different entities" | Canonical names, false-friend guards, catalogue names for parts |
| Human gates | The editor and accepted revisions, as an optional layer | Map, doubt and approval gates during a run | none |

V3 code is unchanged and still runs. It is removed only when the new pipeline has
been measured against it on the same manuals.

## V3 pipeline, two entry points

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

[ontology_schema.JSON](../ontology_schema.JSON), version 3.0, defines `Asset`,
`Component`, `Symptom`, `FailureMode`, `CorrectiveAction` and `ErrorCode`.
Extraction and editor validation use this schema.

| Relation | From → to | Since | Why it exists |
| --- | --- | --- | --- |
| `HAS_COMPONENT`, `GENERATES_ERROR` | Asset → Component, ErrorCode | 2.0 | Added by the code, marked `derived` |
| `MAY_INDICATE`, `INDICATES` | Symptom, ErrorCode → FailureMode | 2.0 | What is observed and its possible causes |
| `RESOLVED_BY` | FailureMode → CorrectiveAction | 2.0 | The remedy or check for a cause |
| `AFFECTS` | FailureMode → Component | 2.0 | The part a fault concerns |
| `PART_OF` | Component → Component | 3.0 | The hierarchy from parts lists and assembly sections |
| `ACTS_ON` | CorrectiveAction → Component | 3.0 | The part an action or check works on; a component test needs no invented symptom |
| `OBSERVED_ON` | Symptom → Component | 3.0 | A diagnosis can start from the part where the problem shows |
| `ADDRESSED_BY` | Symptom → CorrectiveAction | 3.0 | A remedy given without a named cause; replaces placeholder causes |
| `CLEARED_BY` | ErrorCode → CorrectiveAction | 3.0 | The same, for codes |

Relations and properties marked `added_in` in the file belong to the
connected-graph pipeline. V3 keeps reading the 2.0 subset
(`load_ontology()`); the new pipeline and the editor read everything
(`load_ontology(full=True)`). The three relations that end on a component are what
joins the islands: in saved V3 graphs the only edge reaching a component was
`AFFECTS`.

In V3 graphs an edge can contain several occurrences, each with its own source
evidence, conditions and verification certificate. Page/segment identifiers let a
reviewer return to the evidence. The code adds asset links marked `derived: true`.
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
| `kg-v3-graph-2` in `graph.json` | Pipeline graph consumed by the UI; for V3 quality runs it is a compatibility projection. The connected-graph pipeline writes the same shape with `"pipeline": "kg-v4"` and optional fields |
| `kg-ingestion-quality-1` in `ingestion_quality.json` | Rich quality output with source scope, lineage, rejected candidates, coverage and validation |
| `kg-v3-graph-3` in a manual revision | Graph accepted through the editor, with per-occurrence human decisions and revision provenance |

Quality runs also write `source_index.json`, `coverage.json`,
`review_requests.json` and `quality_review.md`. Image-only facts may be present
in the rich output and absent from the text-based graph projection. Check the
projection status and `not_projected` records before treating `graph.json` as the
whole result. Its relationship to the quality output is protected by hashes;
editing it outside the pipeline can make that binding stale.

Fields the connected-graph pipeline adds; every consumer may ignore them:

| Where | Field | Meaning |
| --- | --- | --- |
| evidence item | `section`, `anchor` | Heading trail; `cited` (the model named the segment), `matched` (found by the code), `unit` or `page` (only the passage or page is known) |
| occurrence | `confidence`, `verdict`, `origin`, `note` | `high`/`medium`/`low`; where the fact comes from (`extract`, `reread`, `gap_repair`, `reference`, `name_mention`, `catalogue`) |
| node | `description_source` | `manual`, or `context` when the description is composed from the graph because the manual says nothing more |
| node | `inferred_properties`, `placeholder_properties`, `name_derived_properties` | Attributes deduced from the passages, left as declared placeholders, or repeating the name |
| excluded relation | `reason` | The problem of meaning the verifier named |

`tier` and `trusted` keep their meaning for consumers written for V3: `green` is a
supported fact, `yellow` an unchecked or unclear one. The historical branch scorer
reads these graphs through `backend/kg_v4/scoring.py`, which shows a remedy given
without a cause the way the scorer expects it, without adding anything to the graph.

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

The connected-graph pipeline keeps its state in `<run>/state/`: `manifest.json`
(PDF hash, segment hash, prompt hashes, ontology hash, model and the settings that
change facts), then one file per finished step and passage. The same command on the
same directory resumes; different inputs are refused. A failed read is not saved,
so running again reads that passage again. Worker counts and the call budgets of
the gap search and enrichment are not part of the manifest. A run ends as
`approved` (automatic, recorded as such in `report.approval`) or `incomplete`
(failed reads, failed survey batches or an empty graph); with `--approval person`
it ends as `awaiting_approval` and waits for the button in the interface.

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
| `backend/kg_v4/` | Connected-graph pipeline: sections, survey, records, verification, resolution, gaps, enrichment, export, metrics |
| `backend/kg_v3/` | V3 extraction, contracts, review and export; reader, model client and run state shared with `kg_v4` |
| `backend/domain/`, `backend/adapters/`, `backend/services/` | Evidence/source models, PDF reading, provider gateway and budget accounting |
| `backend/ui/`, `frontend/`, `scripts/ui.py` | Local application |
| `scripts/kg_build.py` | Connected-graph CLI: estimate, preflight, replay, authorised run |
| `scripts/kg_v3.py` | V3 single-PDF CLI |
| `scripts/kg_scorecard.py`, `kg_loss_analysis.py`, `kg_rebuild_from_v3.py` | Offline measures; see [Evaluation](evaluation.md) |
| `tests/`, `frontend/tests/` | Offline software checks |
| `docs/` | Operational and developer documentation |
| `campaign/` | Manual registry, gold and historical campaign workflows |
| `workspace/` | Local UI data, uploads, runs, revisions and preferences |

Some local experiment and review directories are deliberately outside version
control. Their presence in one workstation does not make them clone prerequisites.
The local `paper/` workspace is private and excluded from code sharing.
