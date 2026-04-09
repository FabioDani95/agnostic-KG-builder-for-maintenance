# Diagnostic Knowledge Graph Extraction Application

## Technical Specification

## 1. Purpose

The application processes technical manuals and extracts troubleshooting knowledge into a structured, ontology-first knowledge graph.

The current MVP focuses on:
- product metadata
- physical components
- symptoms
- failure modes
- corrective actions
- error codes

The system remains human-in-the-loop, but it now pushes more work into deterministic scoping, ontology drafting, semantic cleanup, graph reasoning, validation, and final KPI reporting before the operator intervenes.

The current implementation is designed around one practical constraint: an operator must be able to reach a final JSON export without losing already-paid LLM work whenever the automatic ontology draft is incomplete or structurally imperfect.

---

## 2. Real Workflow

The current application flow is:

1. Load a manual from the local `manuals/` directory.
2. Run document scoping to propose a cut plan.
3. Let the operator approve or edit the cut plan.
4. Build an automatic ontology draft from the selected pages.
5. Surface three separate ontology-review buckets:
   - automatic issues
   - required human input
   - optional suggested relations
6. Allow the operator to:
   - accept or reject suggested relations
   - fill missing required ontology fields
   - continue to triplet review even if schema issues still remain
7. Extract and clean triplets from the approved pages.
8. Let the operator validate the extracted triplets.
9. Export the final JSON instance.
10. Show end-of-run KPIs, token usage, model breakdown, and estimated cost.

The current browser UI is organized into these screens:
- upload/start screen
- cut plan screen
- ontology pre-review screen
- triplet validation screen (content shown in source document language)
- final summary / download screen (exported JSON translated to output language if != English)

The app is not a generic upload widget in the current UI. The frontend loads manuals from the local `manuals/` folder through the backend API, then copies the chosen PDF into `data/` for runtime processing.

---

## 3. Upload, Startup, And Runtime Controls

The startup screen collects:
- scoping model
- extraction model
- output language
- operator name
- extraction date
- page offset

The frontend also loads runtime-editable settings from `/api/config`, currently including:
- `small_doc_threshold`
- `reflective_loop.max_retries`
- `reflective_loop.retry_on_severity`

Those values can be overridden in memory through `POST /api/config`. The overrides are not persisted across server restarts.

The backend requires:
- `OPENAI_API_KEY` in `.env`

Optional:
- `MODEL_NAME`

`MODEL_NAME` remains the backend fallback if a request does not explicitly specify a model, but the UI selectors are populated from `config.yaml`.

### 3.1 Current Model Selectors

The current shared model shortlist exposed in the UI is:
- `gpt-5.4`
- `gpt-5.4-mini`
- `gpt-5.4-nano`
- `gpt-5.4-pro`

The UI dropdown shows only the model name, without pricing information. Pricing is used only internally by the KPI engine and is not surfaced in the model selector.

For KPI estimation, `gpt-5.4-pro` falls back to standard input pricing if cached prompt tokens are reported, because no separate cached-input tier is currently configured for that model.

At the time of writing, the backend default model remains `gpt-5.4`.

---

## 4. Cut Plan

The cut plan is generated for documents with more than `small_doc_threshold` pages.

The current scoping strategy combines:
- deterministic keyword scan
- Table of Contents detection
- rule-based ToC scoring
- LLM-based section selection
- page language filtering

### 4.1 Keyword Scan

Pages are scanned for troubleshooting keywords such as:
- maintenance
- diagnostic
- fault
- error
- alarm
- troubleshooting
- repair
- anomaly

Matching pages are grouped into sections. Keyword sections remain high-priority fallback evidence and are merged with rule-based and LLM selections.

### 4.2 Table Of Contents

The first pages of the PDF are scanned for a ToC. If found, the ToC text is passed to the LLM as context for section selection.

The current implementation does not rely on the LLM alone.

After ToC extraction, the backend also applies a deterministic title-scoring pass that:
- promotes troubleshooting, repair, calibration, replacement, reboot, and service-procedure sections
- suppresses safety legends, labels, introductions, copyright, revision history, and other front matter
- stabilizes the selected page set across repeated runs on the same manual

These rule-based sections are shown in the cut plan UI with source `rule`.

### 4.3 LLM Scoping

The scoping prompt receives:
- document metadata
- first pages of the manual
- ToC text if found
- keyword scan context

The LLM returns proposed page sections. Those sections are filtered and then merged with rule-based ToC sections and keyword sections using deterministic priority:
- rule-based ToC sections
- high-confidence LLM sections
- keyword fallback sections

Product metadata from scoping is normalized before storage, so downstream `source_title` remains more stable even when model wording varies slightly.

### 4.4 Cut Plan UI

The cut plan screen shows:
- a PDF preview
- selected sections
- ToC table if detected
- editable page offset
- manual range controls
- approve and skip actions

The operator can:
- keep or remove sections
- add manual ranges
- adjust offsets
- skip the cut plan and use all pages

If the document is small, the cut plan is skipped automatically and all pages are used.

The cut-plan stage now records run metrics including:
- total pages
- selected pages
- stage duration
- LLM token usage
- estimated cost

---

## 5. Ontology Draft Stage

After cut-plan approval, the system runs a separate ontology-drafting stage before human validation of triplets.

This stage is now a central part of the workflow and is no longer a fragile hard gate that forces the operator to restart extraction in order to continue.

### 5.1 What It Produces

The draft aligns with [ontology_schema.JSON](ontology_schema.JSON), which currently defines:
- `Asset`
- `Component`
- `Symptom`
- `FailureMode`
- `CorrectiveAction`
- `ErrorCode`

And these relations:
- `HAS_COMPONENT`
- `MAY_INDICATE`
- `AFFECTS`
- `RESOLVED_BY`
- `GENERATES_ERROR`
- `INDICATES`

### 5.2 Chunking Strategy

Large selected page sets are split into ontology chunks before LLM drafting.

The current ontology configuration includes:
- `max_pages_per_chunk: 30`

This means the ontology router drafts each chunk separately, then aggregates the chunk outputs, issues, suggested relations, and human-required fields into one review payload for the frontend.

This reduces prompt size per call and allows very large manuals to proceed without forcing the entire ontology draft into one oversized request.

### 5.3 Pipeline Behavior

The ontology pipeline performs:
- ontology extraction
- normalization
- semantic validation
- optional reflective re-extraction
- schema validation
- graph reasoning

At a high level, the execution pattern is:

```text
extract
→ normalize
→ semantic_validate
→ optional re_extract loop
→ schema_validate
→ graph_reasoning
→ aggregate review payload
```

The pipeline:
- extracts an ontology instance from the approved pages
- normalizes node and relation structure
- deduplicates entities
- preserves provenance where available
- runs semantic validation with the LLM
- optionally runs a reflective re-extraction loop using structured issue feedback
- validates required schema fields and relation integrity
- runs graph reasoning using NetworkX to surface structural issues and candidate missing relations

### 5.4 Reflective Loop Defaults

The reflective re-extraction loop still exists, but its defaults were hardened to prevent uncontrolled token burn.

Current defaults:
- `reflective_loop.max_retries: 0`
- `reflective_loop.retry_on_severity: "error"`

That means:
- the reflective loop is disabled by default
- no automatic re-extraction is attempted unless the operator explicitly raises retries at runtime
- even when re-enabled, the trigger threshold defaults to `error`, not `warning`

This is a deliberate cost-control change.

### 5.5 Ontology Draft Response

The draft response includes:
- `status`
- `retry_count`
- `ontology`
- `semantic_issues`
- `schema_issues`
- `graph_issues`
- `human_required_fields`
- `suggested_relations`
- `is_schema_compliant`
- `is_ready_for_human_review`

Current status semantics are:
- `ready`: no schema blockers and no required human fields remain
- `needs_human`: required human fields remain
- `needs_human_review`: the system escalated the draft for operator review
- `blocked`: the draft has structural issues

Important frontend rule change:
- `blocked` no longer prevents the operator from continuing to triplet review
- it is now an informational ontology status, not an unconditional workflow dead-end

### 5.6 Schema Issues

Schema issues are structural ontology problems such as:
- `empty_draft_content`
- `missing_id`
- `duplicate_id`
- `unknown_node_type`
- `unknown_relation`
- `relation_domain_range_mismatch`
- `relation_missing_source`
- `relation_missing_target`

The schema validator explicitly rejects empty ontology drafts that contain only the root `Asset` node and no substantive diagnostic content. This is reported as `empty_draft_content`.

Schema issues are shown to the operator in the ontology screen, but they no longer prevent the user from reaching triplet validation and final JSON export.

### 5.7 Human-Required Fields

If required ontology fields cannot be recovered reliably from the manual, the system does not invent them.

Instead, it creates `human_required_fields` entries that the operator can fill directly in the ontology review UI.

This behavior is now broader than the earlier MVP. It is no longer limited to a narrow `Asset` subset such as brand/model only.

Current rule:
- missing required non-ID node properties are surfaced as editable `human_required_fields`
- missing IDs remain structural schema issues
- fields are deduplicated by `(node_type, property_name)`: if multiple nodes of the same type share the same missing property, a single input field is shown and the entered value is applied to all affected nodes

This deduplication prevents the operator from being asked the same question twice when multiple nodes of the same type share a missing required property (e.g. two `Asset` nodes both lacking `brand`).

Human-required fields include:
- a stable `field_key`
- target node type
- target node ID (or `*` for grouped wildcard fields)
- property name
- prompt
- reason
- suggested value when available

The ontology review UI renders these fields as editable text inputs and applies them through `POST /ontology/review`.

### 5.8 Suggested Relations

Graph reasoning may propose `suggested_relations` with:
- relation name
- source node
- target node
- confidence
- rationale

These are optional.

The operator can:
- accept them
- reject them
- reject all
- apply accepted suggestions

Accepted suggestions are sent to `POST /ontology/apply-suggestions`, after which the backend re-runs schema and graph checks and returns an updated ontology review payload.

Important UI fix:
- suggestion cards now store decisions consistently as `accepted` or `rejected`
- the `Apply Accepted Suggestions` button now reads the same state values it writes

This fixes the earlier bug where accepted suggestions looked selected in the UI but were not recognized when applying.

### 5.9 Ontology Review Screen Behavior

The ontology screen now explicitly distinguishes three buckets:
- `Blocking schema issues`
- `Required human input`
- `Suggested relations`

Those labels are important because they represent different operator actions:
- schema issues are explanatory and non-editable in that screen
- required human input is editable and must be filled before applying that review step
- suggested relations are optional graph hints

The primary continue button now behaves as follows:
- if human-required fields exist, it acts as `Apply Missing Info & Continue`
- otherwise it acts as `Continue to Human Validation`
- if schema issues remain, it is explicitly labeled as continuing despite ontology issues

Most importantly, the operator can now continue to triplet extraction even when ontology schema issues remain, so the run is not lost.

### 5.10 Rerun Behavior

`Re-run Draft` still exists, but it is now optional recovery behavior rather than the only exit path from ontology review.

The operator does not need to rerun the ontology draft merely to preserve progress toward the final JSON export.

### 5.11 Ontology Stage Metrics

The ontology stage records:
- per-stage duration
- LLM calls
- prompt tokens
- cached prompt tokens
- non-cached prompt tokens
- completion tokens
- total tokens
- estimated cost
- models used
- by-model usage breakdown
- chunk-level operational detail

---

## 6. Triplet Extraction

After the ontology draft stage, the system extracts diagnostic triplets from the selected pages.

The extraction still uses the classic three-entity structure:
- `Symptom`
- `FailureMode`
- `CorrectiveAction`

The backend formats the selected pages with markers such as:
- `--- PAGE N ---`

The LLM is instructed to:
- extract only explicit information from the document
- keep the extracted meaning grounded in source text
- avoid speculation
- keep asset scope aligned with the scoping `source_title`
- avoid using verification/test outcomes as `FailureMode`
- avoid using inspection-only or verification-only steps as `CorrectiveAction`
- return exactly three Markdown tables

The response is parsed into Pydantic models:
- `Symptom`
- `FailureMode`
- `CorrectiveAction`
- `Triplet`

After parsing, the backend applies a deterministic semantic cleanup layer that:
- removes verification-only or incomplete triads
- deduplicates semantically equivalent entities across chunks
- upgrades severities conservatively
- prefers the most informative wording among duplicates
- verifies each `CorrectiveAction` against the cited `source_page`
- trims unsupported procedural steps from `instruction_text`
- drops corrective actions that are not sufficiently supported by the cited page text

Only complete, post-cleanup triplets are forwarded to the human validation screen and to export.

The extraction stage also records metrics and cost data, just like scoping and ontology.

### 6.1 Language Handling

Extraction and ontology drafting always operate in the source document language. The LLM is instructed to write all extracted values in the same language as the source text. This avoids the quality degradation that occurs when the model must simultaneously extract and translate.

The output language selected by the operator is applied as a separate post-extraction translation step at export time (`POST /generate-json`). When the target language differs from English, the `translation_service` sends a single batched LLM call that translates only the human-readable string fields of the validated nodes and triplets. IDs, codes, page references, and schema keys are never translated.

The operator validates triplets in the source document language during the human review phase. The translated JSON is produced only in the final exported artifact.

---

## 7. Validation UI

The triplet validation screen remains part of the workflow.

The operator reviews each extracted triplet one at a time:
- left side: PDF viewer
- right side: editable triplet tables

The operator can:
- save and move to the next triplet
- discard the triplet
- edit editable fields inline

The PDF viewer scrolls automatically to the `source_page` of the corrective action currently shown.

This validation screen is still the main human review layer for extracted triplets, but it now comes after ontology pre-review rather than immediately after cut-plan approval.

The workflow intent is:
- ontology review improves structure and metadata where possible
- triplet validation remains the durable recovery path
- final export should still remain reachable even if ontology drafting was partial

---

## 8. Export

The application now has one practical export objective: deliver a final canonical JSON without discarding already-reviewed triplets, even when the ontology draft was imperfect.

### 8.1 Canonical Export Contract

The exported JSON uses a canonical contract with exactly these top-level keys:
- `metadata`
- `nodes`
- `relationships`

The `metadata` object includes:
- `product_name`
- `product_short_name`
- `product_type`
- `domain_topics`

The `nodes` object always includes these arrays:
- `Asset`
- `Component`
- `Symptom`
- `FailureMode`
- `CorrectiveAction`
- `ErrorCode`

The `relationships` array uses the export shape:
- `type`
- `from_id`
- `to_id`

Internal runtime fields such as `ontology_name`, `source_type`, `source_title`, and internal `relations` remain runtime-only and are not part of the canonical exported payload.

### 8.2 Final Export Path

The current final export path is `POST /generate-json`.

If a `pdf_id` is present, the backend:
1. loads the current ontology pipeline state
2. prepares export base candidates in this order:
   - stored ontology draft
   - minimal fallback ontology
3. merges validated triplets into each candidate base
4. validates each merged candidate
5. exports the first candidate that passes validation

This means final export is no longer a naive append-only merge.

The backend now:
- semantically matches validated triplets against ontology nodes
- reuses existing ontology nodes when meaning matches
- keeps asset scope normalized
- tries the draft ontology first
- falls back to a clean minimal ontology if the draft remains structurally unusable

The selected export base is recorded in run metrics as:
- `ontology_draft`
- or `minimal_fallback`

### 8.3 Export Blocking Rules

Final export still returns `409 Conflict` if:
- validated triplets plus candidate export base still produce schema issues
- human-required fields still remain unresolved after merge validation

However, the key change is that unresolved ontology draft issues no longer automatically waste the run:
- the user can proceed to triplet review
- the export layer can fall back to `minimal_fallback`
- already validated triplets are preserved

### 8.4 Ontology Export Endpoint

`POST /ontology/export` still exists for schema-compliant ontology export.

Its use case is narrower:
- explicit ontology-centric export
- export of a schema-compliant reviewed ontology instance

The more practical operator-facing success path remains `POST /generate-json`.

---

## 9. Run Metrics, Costs, And Final KPI Summary

The application now records per-run operational metrics and exposes them through:
- `GET /run-metrics/{pdf_id}`

These metrics are built from all completed stages:
- scoping
- ontology
- extraction
- export

### 9.1 Per-Stage Metrics

Each stage records:
- `duration_seconds`
- `llm_calls`
- `prompt_tokens`
- `cached_prompt_tokens`
- `non_cached_prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `estimated_cost_usd`
- `models`
- `by_model`
- stage-specific `details`

### 9.2 Pricing Catalog

The KPI engine maintains an internal pricing catalog for:
- `gpt-5.4`
- `gpt-5.4-mini`
- `gpt-5.4-nano`
- `gpt-5.4-pro`

Versioned model names returned by the API are normalized before pricing. For example:
- `gpt-5.4-2026-03-05` is priced as `gpt-5.4`

### 9.3 Totals And Derived KPIs

The metrics payload includes:
- document filename
- total pages
- selected pages
- stage summaries
- total run usage
- pricing basis
- pricing catalog
- derived KPIs

Current derived KPIs include:
- pages-kept ratio
- seconds per selected page
- cost per selected page
- cost per extracted triplet

### 9.4 Final Summary Screen

After JSON generation, the frontend loads run metrics and renders a final summary block that shows:
- total automation time
- total token usage
- estimated total cost
- per-stage time and token breakdown
- per-model cost breakdown
- selected pages versus total pages
- cost per selected page
- cost per extracted triplet
- node count by type (e.g. Asset: 1, Symptom: 5, FailureMode: 8, …)

The node count table is derived from the ontology draft and gives the operator a quick structural overview of the extracted knowledge graph alongside the operational KPIs.

This summary is shown after final JSON generation, so the operator sees both:
- the output artifact
- the operational cost and structural output of obtaining it

---

## 10. Backend Architecture

The backend is a FastAPI application with shared in-memory storage.

### 10.1 Main Modules

- `backend/main.py`
- `backend/routers/upload.py`
- `backend/routers/cutplan.py`
- `backend/routers/ontology.py`
- `backend/routers/extract.py`
- `backend/routers/generate.py`
- `backend/services/pdf_service.py`
- `backend/services/cutplan_service.py`
- `backend/services/llm_service.py`
- `backend/services/ontology_pipeline.py`
- `backend/services/ontology_contract.py`
- `backend/services/ontology_merge_service.py`
- `backend/services/ontology_semantics.py`
- `backend/services/graph_reasoning.py`
- `backend/services/legacy_ontology_migration.py`
- `backend/services/graph_editor_validation.py`
- `backend/services/ontology_schema_service.py`
- `backend/services/llm_guardrails.py`
- `backend/services/run_metrics.py`

### 10.2 In-Memory Store

The runtime store is `pdf_store`.

It holds:
- filename
- PDF path
- extracted page text
- source metadata
- cut plan
- ontology pipeline state
- page count
- run metrics

No persistent database is used. Everything is lost on server restart.

### 10.3 Contract Boundaries

The application distinguishes three explicit layers:
- internal ontology runtime model used by drafting and review
- legacy migration layer used only when old JSON payloads are loaded
- canonical export contract used for final JSON

Legacy compatibility is isolated in `backend/services/legacy_ontology_migration.py`.

The graph editor and export code load old payloads through that migration layer before applying current validation rules.

### 10.4 PDF Handling

The backend uses PyMuPDF to extract text page by page from the stored PDF.

The PDF itself is copied into `data/` and served back through `/pdf/{pdf_id}` for client-side rendering with PDF.js.

---

## 11. Frontend Behavior And Hardening

The frontend has been hardened specifically around long-running ontology and extraction steps.

### 11.1 Status Feedback

Long-running stages now use a heartbeat-style status indicator with:
- live timer updates
- animated progress styling
- stage-specific loading messages
- explicit success/error status transitions

This was introduced to avoid the earlier behavior where the UI appeared frozen while the backend was still working correctly.

### 11.2 Ontology Draft Fetch Reliability

The ontology-draft frontend flow was corrected to avoid a strict-mode JavaScript failure during `fetch` response handling.

This previously caused:
- backend `200 OK`
- no UI update
- no transition to the next stage

The current implementation correctly stores and processes the `fetch` response before rendering ontology review.

### 11.3 Suggestions UI Reliability

The suggested-relations UI was corrected so that:
- `Accept` marks a card as `accepted`
- `Reject` marks a card as `rejected`
- `Apply Accepted Suggestions` reads the same `accepted` state

This removes the earlier mismatch where the operator had visibly selected suggestions but the apply action still reported that nothing was selected.

### 11.4 Ontology Guidance

The ontology screen now explains:
- what is blocking
- what is editable here
- what is optional
- which action will let the user proceed

This is critical because the ontology review stage now serves both as:
- a quality-improvement screen
- and a non-destructive pass-through to triplet validation

---

## 12. LLM Guardrails

All LLM calls have explicit guardrails in `config.yaml`.

Configured limits include:
- timeout
- maximum input characters
- estimated maximum input tokens
- maximum output tokens

The system estimates prompt size before calling the model. If the estimated prompt is too large, the request is rejected early instead of spending tokens.

If the LLM does not complete within the timeout, the backend stops the request and returns a clear error.

Current guardrail settings are applied separately for:
- scoping
- extraction
- ontology drafting
- ontology validation
- ontology re-extraction

---

## 13. Configuration

### 13.1 `.env`

Required:
- `OPENAI_API_KEY`

Optional:
- `MODEL_NAME`

### 13.2 `config.yaml`

Current top-level sections:
- `shared_models`
- `scoping`
- `extraction`
- `ontology`
- `reflective_loop`

Current runtime-significant defaults:
- ontology chunk size: `max_pages_per_chunk: 30`
- reflective retries: `max_retries: 0`
- reflective retry severity: `error`

Each functional section can define:
- timeout
- token/character guardrails
- model list for the UI

The `reflective_loop` section controls the self-correction behavior:
- `max_retries`: maximum re-extraction attempts before escalating to operator review
- `retry_on_severity`: minimum issue severity that triggers a retry
- `re_extract_max_output_tokens`: output budget for re-extraction calls

The current defaults are intentionally cost-conservative.

---

## 14. API Endpoints

### 14.1 `GET /api/config`

Returns frontend model lists and runtime-editable settings.

### 14.2 `POST /api/config`

Applies in-memory overrides for runtime-editable settings such as:
- `small_doc_threshold`
- `max_retries`
- `retry_on_severity`

### 14.3 `GET /api/manuals`

Lists manuals found in the local `manuals/` directory.

### 14.4 `POST /api/load-manual`

Copies a selected manual into `data/`, extracts page text, and creates a `pdf_id`.

### 14.5 `POST /cut-plan`

Generates the cut plan.

The response reflects a deterministic merge of:
- rule-based ToC sections
- filtered LLM section proposals
- keyword fallback sections

### 14.6 `POST /cut-plan/approve`

Stores the approved pages to keep.

### 14.7 `POST /ontology/draft`

Builds the ontology draft from the selected pages and returns the aggregated ontology review payload.

### 14.8 `GET /ontology/{pdf_id}`

Returns the current ontology pipeline state.

### 14.9 `POST /ontology/review`

Applies human-entered ontology field values and revalidates the ontology draft.

### 14.10 `POST /ontology/apply-suggestions`

Applies operator-accepted suggested relations to the ontology and re-runs schema and graph validation.

The request body carries:
- `accepted_suggestions`

### 14.11 `POST /ontology/export`

Exports the ontology instance when it is schema-compliant.

### 14.12 `POST /extract-tables`

Extracts triplets from the selected pages.

The backend returns only cleaned triplets after semantic filtering and cross-chunk deduplication.

### 14.13 `POST /generate-json`

Final export path that merges validated triplets with the ontology state when `pdf_id` is present.

The merge is semantic and scope-aware rather than append-only, and now includes fallback to a minimal ontology base if the draft ontology cannot support final export cleanly.

### 14.14 `GET /run-metrics/{pdf_id}`

Returns the aggregated run metrics payload used by the final frontend summary.

### 14.15 `GET /graph-editor/{pdf_id}`

Opens the graph editor for a saved ontology export.

### 14.16 `POST /graph-editor/{pdf_id}/api/node/{node_id}/update`

Updates a node in the working graph-editor session.

Required fields are validated before accepting the update.

### 14.17 `POST /graph-editor/{pdf_id}/api/relationship/add`

Adds a relationship in the working graph-editor session.

The backend validates:
- source node existence
- target node existence
- relation type existence in schema
- domain/range compatibility
- duplicate edge prevention

### 14.18 `POST /graph-editor/{pdf_id}/api/save`

Saves the current editor session as a new exported ontology version.

Save is blocked if the canonical export contract is invalid.

---

## 15. Startup

The application starts with:

```bash
./run.sh
```

The script:
- clears port `8000`
- activates `.venv`
- ensures required Python packages are installed
- starts Uvicorn

The frontend is served at:
- `http://127.0.0.1:8000`

---

## 16. Testing And Validation Coverage

The codebase now includes both backend regression coverage and a mock end-to-end browser flow for the operator-critical path.

### 16.1 Backend Regression Coverage

Current automated backend coverage includes tests for:
- ontology validation behavior
- ontology merge behavior
- source-aware cleanup behavior
- graph/editor validation behavior

Recent additions specifically cover:
- rejection of ontology drafts that only contain the root `Asset`
- conversion of missing required non-ID properties into `human_required_fields`
- merge-time behavior when ontology content is incomplete

### 16.2 Frontend End-To-End Flow

The codebase now includes a Playwright-based frontend test flow that exercises the critical non-rerun success path:

1. load manual
2. cut plan
3. approve pages
4. ontology draft
5. accept/reject and apply suggestions
6. fill required human input
7. continue despite remaining ontology schema issues
8. review triplets
9. generate JSON
10. render final KPI summary

The browser test is API-mocked so it does not spend live LLM tokens. Its purpose is to prove that the frontend can click through to the final JSON download path without forcing a rerun.

### 16.3 Validation Intent

This distinction is important:
- backend tests verify rules and merge logic
- frontend browser tests verify operator flow continuity

The current test strategy is specifically designed to protect against the most expensive failure mode observed during development:
- consuming tokens successfully in the backend
- then failing to reach final JSON due to frontend state bugs

---

## 17. Practical Notes

- The app is still MVP-level, but the data flow is now ontology-first rather than triplet-only.
- The ontology draft stage runs before manual triplet validation.
- The reflective loop still exists, but default retries are now zero to avoid unintended token burn.
- Suggested graph relations are now operator-optional improvements, not hidden blockers.
- Missing required non-ID ontology properties are increasingly surfaced as editable human input rather than opaque hard failures.
- Schema issues are still important, but they no longer force the operator to lose the run before triplet review.
- Final JSON generation now has a safer recovery path through `minimal_fallback` ontology export.
- End-of-run cost visibility is now part of the operator workflow, not an external calculation.
- Legacy `Printer` payloads are migrated to `Asset` before current validation rules are applied.
- The current UI and workflow are still single-pipeline, not supervisor-driven. Confidence scoring and adaptive HITL are not yet implemented.

---

## 18. Agentic Roadmap Status

The companion [roadmap_agentic.md](roadmap_agentic.md) tracks the intended evolution toward a more agentic neurosymbolic system. Its status should be read together with this specification.

Current implementation status:
- **Step 1 — Reflective Extraction Loop**: implemented
- **Step 2 — Graph Reasoning with NetworkX**: implemented
- **Step 3 — Confidence Scoring and Adaptive HITL**: not started
- **Step 4 — Multi-Agent Architecture with Supervisor**: not started

What is already operational in the codebase:
- deterministic + LLM scoping merge
- ontology chunking
- optional reflective re-extraction
- escalation to human review
- NetworkX-based graph analysis and suggested missing relations
- editable human-required ontology fields
- non-blocking continuation from ontology review to triplet review
- semantic final export merge with fallback ontology base
- run metrics and cost summary

What is not yet operational:
- per-entity or per-triplet confidence scoring
- automatic routing into `auto_approve`, `human_review`, and `auto_reject`
- supervisor-driven multi-agent orchestration
- explicit page-by-page coverage agents
- persistent run history across restarts

This matters for evaluation: the system is no longer a simple linear extractor, but it is also not yet a supervisor-style multi-agent platform.
