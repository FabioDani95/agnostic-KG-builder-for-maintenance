# Handoff — PDF G3 diagnostic graph optimization

Last updated: 2026-08-12  
Repository: `agnostic-KG-builder-for-maintenance`  
Current branch: `main`

## Executive status

The PDF G3 pipeline hardening work has been implemented and committed as an experimental checkpoint, but it is **not ready for production enablement**.

Current decision: **NO-GO**.

The new publication policy produces a substantially smaller, grounded and topologically valid graph at very low cost. The real E-554 acceptance run did not preserve the required diagnostic coverage: it scored **0/8 gold chains**, although it retained **0/3 forbidden cross-pairings**. A clean graph with missing diagnostic knowledge is not an acceptable result.

Do not approve, reject, merge or regenerate the retained baseline revision. Do not interpret passing unit tests as semantic acceptance of the new pipeline.

## Commits

- `3cbb9f4 chore: preserve G3 Luna validation baseline`
  - Captures all intentional pre-existing worktree changes and the initial diagnosis/optimization-plan artifacts.
- `136fb45 feat: harden PDF G3 publication pipeline`
  - Implements the experimental relation-first flow, publication gate, projections, exact grounding, canonicalization, UI changes, budget guard, tests and real-run artifacts.

## Protected baseline

The original Luna revision must remain unchanged:

- workspace: `ws_ebXgqKWDDgsjKdrGbFDiQQ`
- source revision: `sgrev_OR8HyabEt7ntt0Z00LZEoA`
- configuration hash: `a56332c883f2ab0f6372aabad39c2e49c568bd0d8efc9a58bcff695af3b871e6`
- status: `reviewing`
- decision: none
- Asset:
  - `asset_mF-1RBkvmra24woUH3T6iQ`
  - Eastman Eagle S3L

Verified after all tests: the baseline is still `reviewing` with no approval/rejection decision.

## Experimental real run

The single authorized full generation was executed in a separate workspace:

- manual: `/Users/fabiodaniele/Downloads/E-554.pdf`
- manual SHA-256: `a7467316234f2d84550e7c267bf709fda55e1023055d9569dc27348f192641d0`
- workspace: `ws_PFJFoXKzA2TjEW4pUS8Yqg`
- source: `src_SZQuae1zPnJcWZbJpblu4w`
- revision: `sgrev_SFIdPe_n3ITEJyqxUkFPrw`
- persisted pipeline version: `pdf-g3-relation-first-publication-v5`
- status: `reviewing`
- decision: none
- CSV processed: no
- merge started: no

### Measured full-run results

| Metric | Baseline Luna | Experimental v5 |
|---|---:|---:|
| Selected pages | 30 | 30 |
| Chunks | 19 | 10 |
| LLM calls | 96 | 19 |
| Prompt tokens | 668,862 | 142,261 |
| Completion tokens | 163,700 | 42,784 |
| Total tokens | 832,562 | 185,045 |
| Duration | 444.690 s | 278.811 s |
| Cost | $0.320466 | $0.079794 |
| Nodes | 399 | 180 |
| Relations | 369 | 175 |
| Isolated nodes | 33 | 0 |
| Grounded published relations | 172/174 | 175/175 |
| Review queue | 250 observed | 82 persisted |
| Gold chains | 8/8 | **0/8** |
| Forbidden pairings | 0/3 | 0/3 |

Experimental graph projections:

- diagnostic: 42 nodes, 31 relations;
- structural: 145 nodes, 144 relations;
- canonical: 180 nodes, 175 relations.

Within the published v5 graph:

- 0 isolated nodes;
- all 11 published Symptoms have a complete path to a CorrectiveAction;
- all 13 published CorrectiveActions have an incoming `RESOLVED_BY`;
- strict validation passes;
- all 175 published relations have exact resolvable quote/anchor grounding.

These publication invariants pass because incomplete candidates are excluded or represented as gaps. They do not prove that the pipeline extracted all required diagnostic knowledge.

## Why semantic acceptance failed

The failure is primarily in the pipeline contract, not evidence that Luna must be replaced globally.

### 1. Incorrect role boundary

PDF page 39 contains explicit `Problem` and `Troubleshooting` records, including four gold branches. The table-of-contents range classified that page as part of an electrical/pneumatic structural section. In v5, page 39 was therefore sent to the Component-only structural role and its diagnostic records were unavailable to the diagnostic extractor.

### 2. EvidenceUnit boundary was too strict

The v5 relation-first prompt effectively required the complete diagnostic chain to occur in one EvidenceUnit. The PDF adapter correctly splits headings, problem descriptions, causes and remedy steps into contiguous evidence units. A diagnostic record may also cross a page boundary. The extraction contract was stricter than the canonical evidence representation.

### 3. Free-form relation response remains unreliable

The v6 micro-benchmark sent canonical pages 37–39 through the current production diagnostic prompt in one real Luna call. Luna extracted most expected Symptoms, FailureModes and CorrectiveActions, but after coercion the result contained only 34 derived `HAS_COMPONENT` relations and no direct `MAY_INDICATE` or `RESOLVED_BY` relations.

This means the current free-form ontology JSON contract can recognize entities while omitting or mis-shaping causal relations. The deterministic publication gate then correctly excludes the incomplete chains, yielding 0/8.

The raw provider response was not persisted, so it is not currently possible to distinguish conclusively between model omission and coercion loss. Add raw-response contract diagnostics before the next real test.

## Code currently implemented

### Publication and ontology integrity

- `backend/services/diagnostic_publication_service.py`
  - Schema-derived domain/range checks.
  - Publishes only grounded complete diagnostic paths and grounded structural ownership.
  - Builds canonical, diagnostic and structural projections from the same graph IDs.
  - Excludes orphan actions, incomplete chains and ungrounded relations.
- `backend/services/ontology_canonicalization_service.py`
  - Conservative global cross-chunk merges.
  - Safe plural/morphology handling.
  - Relation endpoint and `FailureMode.material_context` remapping.
  - Ambiguous candidates remain review items rather than forced merges.
- `backend/services/source_subgraph_generation.py`
  - Strict publication validation requires zero isolates, complete published chains, no orphan actions and exact relation grounding.

### PDF roles, extraction and grounding

- `backend/services/pdf_source_subgraph_generation.py`
  - Current code version: `pdf-g3-relation-first-publication-v6`.
  - Preserves the operator-canonical Asset.
  - Keeps relation-specific evidence refs with quote and anchor.
  - Persists projections, publication metrics, review queue and canonicalization report.
- `backend/services/cutplan_service.py`
  - Adds generic multilingual `is_diagnostic_section` and `page_has_diagnostic_record` rules.
  - Rejects diagrams/schematics and procedural maintenance/installation prose as diagnostic unless page content has explicit diagnostic record structure.
- `backend/prompts/ontology_prompt.py`
  - Diagnostic bundles may span contiguous evidence units or a page boundary.
  - Every relation must be independently grounded.
  - Preventive maintenance, safety, inspection and installation are not CorrectiveActions unless explicitly linked to a FailureMode.
  - Structural role emits Components only.
  - No E-554, vendor, model, page or gold terms are present in the production prompt.
- `backend/services/ontology_workflow.py`
  - Contiguous bounded chunk packing.
  - Serial diagnostic/structural extraction.
  - No lexical graph closure in relation-first mode.
  - Per-call token/cost ledger.

### Cost controls

- `backend/services/pdf_cost_guard.py`
  - Conservative no-cache ceiling.
  - One-character-per-token worst-case prompt estimate.
  - Bounded completion outputs and resolution targets.
- SDK retries: 0.
- Manual retries: 0.
- Draft parse retries in relation-first mode: 0.
- Chunk concurrency: 1.

### UI

- Diagnostic projection is the default graph view.
- Structural and canonical projection selectors are available.
- Relation inspector shows exact evidence quote and anchor.
- Target-specific gaps are attached to the relevant graph entities.

## Current v6 offline result

Applying the v6 generic role classifier to the same persisted E-554 scope produces:

- diagnostic pages: 37, 38, 39;
- structural pages: 27 selected pages;
- retrieval pages: all 54 physical pages;
- 9 estimated chunks.

Estimated v6 cost on the same input:

- central estimate: $0.101170;
- conservative no-cache maximum: $0.292889.

This satisfies the cost target, but v6 is not semantically accepted because the one-call real diagnostic micro-benchmark still produced 0/8 complete paths.

## API budget consumed

The activity had an absolute additional OpenAI budget of $0.50.

- full generation: $0.079794;
- v6 one-call micro-benchmark: $0.011023;
- cumulative spend: **$0.090817**;
- remaining budget: $0.409183;
- total calls: 20;
- full generations: exactly 1;
- concurrent calls: none;
- manual retries: none.

Every call, token count, model, effort and estimated list-price cost is recorded in:

`artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/real_api_ledger.json`

Do not run another full generation under the previous authorization: its one-full-generation allowance has been consumed. Obtain explicit user authorization before any additional real full run.

## Validation completed

- Entire pytest suite: **436 tests passed**.
- Python lint: passed.
- JavaScript syntax checks: passed.
- JSON artifact validation: passed.
- No API-key pattern found in committed artifacts.
- No E-554/Eastman/model/page-specific terms found in production code or configuration.
- Final mock golden replay:
  - 9 heterogeneous manuals/fixtures;
  - average triplet recall: 1.0;
  - schema compliant: 9/9.

Fixture coverage includes robot controllers, CNC, laser cutter, pump, conveyor, washer, microwave and dishwasher. This demonstrates structural/manual agnosticism, not real semantic readiness.

## Required next implementation

The recommended next step is a typed intermediate diagnostic contract, not another prompt-only change.

Introduce a schema-driven `DiagnosticBundle` or equivalent structured-output contract containing:

- one observed indicator (`Symptom` or `ErrorCode`);
- one explicit `FailureMode`;
- one or more explicit `CorrectiveAction` items;
- optional affected `Component`;
- exact evidence quote and anchor for every edge;
- a stable record/branch identity so branches from different troubleshooting records cannot be cross-paired.

Compile each validated bundle deterministically into the configured ontology. Do not ask the model to emit arbitrary ontology relations directly and then infer completeness from their presence.

Also add these fail-closed diagnostics:

1. If a diagnostic chunk emits diagnostic nodes but zero direct causal relations/bundles, mark the chunk invalid and create a blocking gap.
2. Persist a redacted raw-response digest and coercion statistics:
   - raw node count;
   - raw relation/bundle count;
   - coerced relation/bundle count;
   - dropped items by reason;
   - output finish reason.
3. Use selective escalation only for invalid/ambiguous bundles. Do not replace Luna for the entire pipeline without measured multi-manual benefit.
4. Keep structural Component extraction separate from the diagnostic view.
5. Retain the deterministic publication gate after bundle compilation.

## Acceptance gates for the next real run

Production enablement is allowed only when all of the following pass:

- E-554 gold coverage: 8/8;
- forbidden pairings: 0/3;
- zero published isolated nodes;
- every published Symptom/ErrorCode reaches a FailureMode and CorrectiveAction;
- incomplete observed indicators are explicit gaps and are not shown as complete chains;
- zero published CorrectiveActions without incoming `RESOLVED_BY`;
- 100% published relation quote/anchor grounding;
- strict ontology validation passes;
- exact operator-canonical Asset preserved;
- diagnostic and structural projections remain views over one canonical graph;
- no gold/vendor/model/page-specific production rule;
- real generation cost at or below $0.35;
- conservative preflight below the configured $0.49 ceiling;
- no diagnostic chunk containing candidate diagnostic nodes is silently accepted with zero direct bundles/causal relations;
- heterogeneous annotated manuals pass, not only E-554.

## Important artifacts

- Full decision report:  
  `artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/report.md`
- Structured measured comparison:  
  `artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/post_implementation_analysis.json`
- Real API ledger:  
  `artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/real_api_ledger.json`
- Full experimental response:  
  `artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/generation_response.json`
- v6 real one-call micro-benchmark:  
  `artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/v6_diagnostic_microbenchmark.json`
- v6 offline cost projection:  
  `artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/v6_offline_cost_projection.json`
- Initial diagnosis and plan:  
  `artifacts/acceptance/g3/e554/luna_optimization_plan/`

## Safe resume checklist

Before continuing:

1. Confirm both revisions still have status `reviewing` and no decision.
2. Confirm the worktree is clean.
3. Read this handoff and the full post-implementation report.
4. Implement the typed bundle contract with offline and mock tests first.
5. Do not use gold data in prompts, extraction code, scoping or production heuristics.
6. Request explicit authorization and a new real-test budget before another full generation.
7. Use a new isolated experimental workspace/revision for every authorized real run.
8. Never approve/reject the protected baseline, process CSV or start merge during optimization tests.
