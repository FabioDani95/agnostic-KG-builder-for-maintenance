# Handoff — PDF G3 diagnostic graph optimization

Last updated: 2026-08-12  
Repository: `agnostic-KG-builder-for-maintenance`  
Current branch: `main`

## Current v7 continuation status — supersedes the implementation status below

This section records the 2026-08-12 continuation from the historical v5/v6
checkpoint documented below. The older measurements and protected-revision
instructions remain valid historical evidence, but their "required next
implementation" has now been implemented in the local worktree.

### Decision

The identified direction is confirmed: a typed diagnostic-record contract,
deterministic ontology compilation, exact edge evidence and fail-closed
candidate accounting are the correct path for producing clean, high-coverage,
ontology-compliant PDF graphs without vendor-specific rules.

Current production decision remains **NO-GO**. Real autonomous E-554 runs were
executed under the user-authorized $1 envelope; they prove that publication is
schema-valid, exactly grounded and topologically clean, but they do not yet
recover the frozen troubleshooting coverage autonomously.

### Real v7 acceptance outcome — 2026-08-12

The strongest completed run is retained at
`v7_second_real_run_retry_misprioritized/`:

| Metric | Result |
|---|---:|
| Measured ledger cost | $0.092457 |
| Calls | 18 (17 Luna, 1 Terra) |
| Published nodes / relations | 197 / 196 |
| Global weak components / isolated nodes | 1 / 0 |
| Complete diagnostic paths | 12 |
| Relation grounding | 196/196 |
| Exact relation EvidenceRefs | 845/845 |
| Schema/domain/range/topology errors | 0 |
| Frozen E-554 chains recovered | 0/8 |
| Forbidden cross-pairings | 0/3 |
| Blocking review items | 15 |

This revision remains `reviewing`, is not approval-eligible, and was never
approved, rejected or merged. The verdict is deliberately split:

- **GO for the architecture:** typed candidates, deterministic compilation,
  exact edge evidence, ontology validation and the approved connectivity
  interpretation all behave correctly.
- **NO-GO for autonomous semantic coverage:** the production extractor did not
  publish the eight frozen page-37–39 troubleshooting chains. A clean graph
  containing the wrong subset is not a production-quality manual graph.

The runs exposed and fixed three provider/control-plane defects generically:

1. strict provider schema cannot use Pydantic's `oneOf` indicator union; the
   wire contract is now flat with local kind-specific validation;
2. the single Terra retry used to be consumed by the first eligible chunk;
   run-level selection now ranks truncation/parse failure first, then ranks
   ambiguous chunks by unresolved-record coverage;
3. OpenAI SDK length exceptions previously lost usage accounting. Usage is now
   recovered from the exception's completion object and the failure is recorded
   with `finish_reason=length`.

One corrected run sent Terra/medium to the page-36–40 chunk, but all 8,000
completion tokens were consumed as reasoning and no JSON was returned. A later
Luna run completed the same chunk and found nine candidate records, eight of
which failed exact lineage/quote checks; this confirms that the remaining issue
is record assembly/evidence anchoring, not merely model scale. The last proposed
run was stopped before semantic generation because its conservative preflight
maximum ($0.563769) exceeded the remaining $0.50 ceiling.

Because SDK length exceptions in earlier runs were not yet ledgered, total
spend cannot be claimed exactly from stored ledgers. The operator envelope was
therefore enforced conservatively by reserving $0.50 for all prior attempts and
allowing only a $0.50 final ceiling; no further calls were made after the
preflight block. Checked-in defaults have been restored to $0.35 preferred /
$0.49 hard ceiling with Terra disabled (`max_chunks_per_run: 0`).

Repository state:

- remote baseline pulled to `5010af2` on `main`;
- v7 implementation, tests and retained acceptance artifacts are committed on
  `main` (`feat: harden typed PDF diagnostic pipeline`);
- the worktree was clean immediately after that commit;
- the protected baseline and the retained v5 experimental revision were not
  approved, rejected, merged or regenerated;
- the historical PDF was recovered temporarily from Git for testing only and
  was not restored to the worktree.

### Implemented v7 architecture

The semantic path is now two-level and record-first:

1. Luna emits strict `DiagnosticRecordCandidate` records, including incomplete
   records and explicit dispositions. A record can contain both an ErrorCode and
   a Symptom. FailureMode and actions may be absent only as an explicit gap; the
   model is not encouraged to invent missing knowledge.
2. A deterministic validator/compiler resolves exact EvidenceUnit anchors,
   verifies record and branch lineage, assigns system-owned IDs and relation
   names, and emits only schema-valid ontology nodes and edges.
3. Publication remains a separate fail-closed gate. Every diagnostic candidate
   must end in exactly one disposition: publish, gap, review or exclude.
   Unaccounted, refused, truncated, ungrounded or compiler-failed candidates
   block automatic approval.

Other implemented hardening:

- all physical pages are inventoried before scoping; page roles may overlap;
- bounded high-recall diagnostic candidate discovery is no longer limited to
  the selected cut-plan pages;
- diagnostic chunks overlap by one page and retain record/branch identity;
- coverage and recovery use the same typed edge-evidence contract;
- each `MAY_INDICATE`/`INDICATES`, `RESOLVED_BY` and optional `AFFECTS` edge has
  its own support set; evidence can span multiple blocks/pages;
- exact grounding accepts a generated quote only when it is contained in the
  canonical EvidenceUnit text. The old inverse containment shortcut is gone;
- global node IDs are unique across types, relation IDs are order-invariant,
  and cross-branch endpoint mixing is rejected;
- merge/normalization failures, structured-output refusal/truncation and empty
  diagnostic chunks can no longer disappear during multi-chunk merge;
- the PDF adapter is versioned as `pdf-v3`. Layout-aware ordering preserves
  two-column troubleshooting records, block coordinates and source order;
- stale pre-v3 inventories are reparsed into a superseding preparation while
  historical rows remain preserved;
- low-text/unreadable/OCR-unavailable pages receive an explicit disposition and
  can block approval rather than silently vanishing;
- Luna remains the primary model. Terra is available only as a bounded retry
  when a diagnostic chunk is semantically invalid or ambiguous and its result
  is accepted only if its contract score is strictly better;
- the cost preflight reserves the complete retry envelope before post-scoping
  calls and accounts for Structured Output schema context, cache writes and
  long-context pricing.

Production code/configuration contains no Eastman, E-554, page-number or gold
chain rules. The same typed contract is exercised against heterogeneous manual
fixtures; those fixtures demonstrate architectural agnosticism, not yet real
multi-vendor semantic acceptance.

### Real-PDF offline replay

The original 54-page E-554 PDF was recovered read-only from Git history. Its
SHA-256 exactly matches the earlier real-run source:
`a7467316234f2d84550e7c267bf709fda55e1023055d9569dc27348f192641d0`.

Pages 37–39 were parsed with the production `pdf-v3` adapter into 67 canonical
EvidenceUnits. A test-only typed oracle fixture was then passed through the real
validator/compiler; neither the LLM nor a production extraction rule was
stubbed into the compiler.

| Offline v7 contract metric | Result |
|---|---:|
| Gold diagnostic records published | 8/8 |
| Forbidden cross-pairings found | 0/3 |
| `MAY_INDICATE` edges | 8 |
| `RESOLVED_BY` edges | 8 |
| Edge EvidenceRefs grounded exactly | 24/24 |
| Schema errors | 0 |
| Isolated diagnostic nodes | 0 |
| Incomplete published diagnostic paths | 0 |

This proves that the PDF evidence representation, typed contract, lineage
checks, deterministic compiler and grounding gate can represent all eight
expected records without cross-pairing. It does **not** prove that Luna will
autonomously produce those eight records. Records 4, 6, 7 and 8 should remain
human-review candidates because their causal meaning is conveyed by the
Problem/Troubleshooting layout rather than repeated as one explicit causal
sentence.

The standalone typed diagnostic output has six weakly connected components.
That is expected at the compiler boundary: canonical Asset injection and
grounded structural ownership happen in the outer publication merge. There are
no isolated diagnostic nodes and every published diagnostic root has a complete
indicator → failure → action path.

### Meaning of "connected"

The current ontology does not define an Asset-to-diagnostic-root relation and
`AFFECTS` is optional. Therefore the evidence-safe invariant implemented by v7
is:

- zero isolated published nodes;
- every diagnostic root belongs to a complete grounded diagnostic branch;
- every action has an incoming grounded `RESOLVED_BY`;
- structural ownership and `AFFECTS` are added only when the manual supports
  them.

It does not promise one global weakly connected component. Requiring literal
single-component connectivity needs an ontology decision: either require a
grounded `AFFECTS` for every failure (which would lose valid asset-level
knowledge), or introduce a new Asset-to-diagnostic-record/root relation. The
pipeline must not invent `AFFECTS` merely to connect components.

### Validation completed for v7

- full pytest suite: all tests pass; the single loopback security test must run
  outside the filesystem/network sandbox and passed there;
- Ruff over backend and tests: passed;
- `git diff --check`: passed;
- typed E-554 replay and evidence audit: **9 tests passed**;
- mock golden evaluator: 9 heterogeneous fixtures, average triplet recall 1.0,
  schema compliant 9/9;
- no vendor/model/gold-page vocabulary found in production code/configuration.

The legacy Markdown golden evaluator does not exercise the real PDF G3 semantic
path. New integration tests now exercise strict Structured Output parsing,
EvidenceUnit-backed compilation, page-boundary overlap, exact per-edge evidence,
candidate accounting and approval blocking without monkeypatching the semantic
core.

### Remaining acceptance step and budget

The $1 authorization is closed. Do not make another real call without a new
explicit budget. The next engineering step should be offline: split dense
diagnostic windows by record/table row before model extraction, preserving
overlap and branch anchors, so the model does not need to emit a large mixed
candidate array and quotes remain local to their canonical EvidenceUnits. Then
rerun the frozen PDF harness and at least one annotated manual from another
manufacturer. Terra should remain a selective recovery tool, not a substitute
for deterministic record-window assembly.

Production enablement still requires the autonomous run to satisfy all gates in
"Acceptance gates for the next real run" below. In addition, a real annotated
sample from other manufacturers is needed before claiming broad semantic
generalization.

### Current review limitation

The backend now produces record-level publish/gap/review/exclude accounting and
can group human attention around ambiguous records. The current G3 API/UI still
approves or rejects the whole revision; append-only record-level
confirm/edit/exclude/merge adjudication that recompiles an immutable revision is
a remaining product feature, not a blocker for the isolated acceptance run.

### New v7 artifacts

- `artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/offline_typed_replay_real_pdf_result.json`
- `artifacts/acceptance/g3/e554/luna_optimization_plan/post_implementation_e554/offline_typed_replay_evidence_audit.json`
- `tests/fixtures/e554_offline_replay/diagnostic_chunk_output.json`
- `tests/test_e554_offline_typed_replay.py`
- `tests/test_e554_offline_typed_replay_audit.py`

Everything below this point describes the retained v5/v6 checkpoint and should
be read as historical context unless the v7 section explicitly refers to it.

## Historical v5/v6 executive status

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
