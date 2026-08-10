# PDF G3 implementation and E-554 retest — decision report

## Decision

**NO-GO for production enablement.** The implementation is valuable as an experimental checkpoint: it enforces clean publication invariants, exact relation grounding, ontology-derived projections and a bounded cost. The real semantic acceptance criterion did not pass, however: the retained full generation has **0/8 gold chains** (with **0/3 forbidden pairings**) and the post-fix one-call micro-benchmark also has **0/8 complete paths** because it produced no direct causal relations.

Do not approve, merge or publish the experimental revision. The retained Luna baseline and the experimental revision both remain `reviewing`, without decisions.

## 1. Why the old graph was dirty despite 8/8 gold

The old extraction contract optimized local entity recall, then tried to repair topology. It admitted standalone diagnostic nodes, treated maintenance/inspection/installation procedures as possible `CorrectiveAction`, derived `AFFECTS` from lexical proximity, fragmented 30 pages into 19 chunks, canonicalized only locally and exposed the canonical graph without a diagnostic projection. Strict validation checked schema shape and endpoint consistency, not publication completeness. Therefore 8 known chains could coexist with 33 isolated nodes, 28 orphan actions, 155 structurally-only components and many near duplicates.

The gold suite measured minimum recall, not precision or publication topology. Passing it never implied that the rest of the graph was clean.

## 2. Pipeline versus model

The measured failures are predominantly pipeline-contract failures:

- Full v5 run: page 39 contained explicit `Problem`/`Troubleshooting` records but was assigned to the structural role because a ToC boundary labelled it as an electrical/pneumatic section. Four gold branches were therefore unavailable to diagnostic extraction.
- The first relation-first prompt required a chain to be in the same `EvidenceUnit`; the canonical PDF adapter splits headings, descriptions, causes and remedy steps into contiguous evidence units. This contract was stricter than the source representation.
- The v6 micro-benchmark extracted most expected entities from pages 37–39, including the pause, calibration, mapping and laser-loss concepts, but its coerced ontology contained only 34 derived `HAS_COMPONENT` relations and no `MAY_INDICATE`/`RESOLVED_BY` relations. That is a response-contract/coercion failure, not evidence that Luna cannot identify the concepts.
- One safe plural merge did not rewrite `FailureMode.material_context`; this created a false schema warning. The current code now remaps it.

Model variability still affects completeness and phrasing, but replacing Luna globally is not justified. The one-call v6 test spent $0.011023 and found the concepts; a stronger model would not repair role classification, output-shape coercion or publication policy.

## 3. Implemented strategy

The implementation combines:

1. role-aware relation-first extraction;
2. deterministic publication gate;
3. canonical, diagnostic and structural projections over one ontology graph;
4. global conservative cross-chunk canonicalization;
5. full-manual retrieval for bounded completion;
6. exact quote-plus-anchor relation grounding;
7. serial calls, zero SDK/manual/parse retries and a hard cost preflight;
8. target-specific gaps and a persisted review queue;
9. diagnostic-view default in the UI.

After the real v5 failure, v6 narrows diagnostic drafting to explicit diagnostic section titles or page-level diagnostic record structure. Preventive maintenance, inspection, calibration and installation pages become Component/retrieval context unless their content contains explicit diagnostic records. This rule is manual-, vendor-, machine- and domain-independent.

## 4. Exact code changes

- `backend/services/pdf_source_subgraph_generation.py`
  - `PDF_SUBGRAPH_GENERATOR_VERSION` v6;
  - operator-canonical Asset evidence;
  - diagnostic/structural/retrieval page roles;
  - exact quote/anchor retention in `RelationEvidenceRef`;
  - publication gate and strict grounded validation;
  - persisted projections, metrics, gaps, canonicalization and review queue.
- `backend/services/cutplan_service.py`
  - `is_diagnostic_section` and `page_has_diagnostic_record`;
  - content guard for inaccurate ToC boundaries;
  - multilingual diagnostic-record semantics, with procedural chapters excluded from the diagnostic role.
- `backend/services/ontology_workflow.py`
  - contiguous bounded page packing;
  - serial diagnostic/structural role chunks;
  - relation-first finalization, no similarity closure;
  - global canonicalization;
  - conservative cost preflight;
  - per-call persisted ledger.
- `backend/prompts/ontology_prompt.py`
  - relation-first diagnostic bundles may span contiguous evidence units/page breaks;
  - each relation must have its own exact support;
  - no standalone diagnostic nodes;
  - preventive/safety/inspection/installation procedures are not corrective actions without an explicit failure relation;
  - structural role emits Component nodes only;
  - removed the E-554-like example from the production prompt.
- `backend/services/diagnostic_publication_service.py`
  - schema-derived relation names/domain/range;
  - publishes only grounded complete diagnostic paths and grounded structural ownership;
  - zero isolates and zero orphan `CorrectiveAction` by construction;
  - canonical, diagnostic and structural ID-only views.
- `backend/services/ontology_canonicalization_service.py`
  - safe morphology/type-compatible merges;
  - conservative action semantics;
  - relation endpoint and `material_context` remapping;
  - ambiguous candidate clusters remain reviewable instead of auto-merged.
- `backend/services/evidence_grounding_service.py` and `backend/services/source_subgraph_generation.py`
  - exact grounding for all published relation types;
  - strict publication invariants for symptoms, failures, actions, Asset and components.
- `backend/services/pdf_cost_guard.py`, `backend/services/llm_gateway.py`, `backend/services/llm_service.py`, `backend/services/resolution_completion_service.py`
  - no-cache conservative ceiling;
  - serial/no-retry real-call envelope.
- `frontend/app/graph.js`, `frontend/app/detail.js`, `frontend/app/state.js`, `frontend/app/i18n.js`
  - diagnostic projection is the default;
  - structural/canonical switches;
  - target gaps and exact relation quote/anchor in the inspector.

The next required implementation—not yet done because the real result is a no-go—is a typed intermediate `DiagnosticBundle` response contract (or provider structured output) compiled deterministically into ontology nodes/relations. Production must reject a diagnostic draft that has diagnostic nodes but zero direct causal relations. Generic alias support alone is insufficient because the raw v6 response was not retained.

## 5. Ontology preservation

- Node and relation types are loaded from the configured ontology.
- Publication completeness uses relation domain/range (`Symptom→FailureMode`, `FailureMode→CorrectiveAction`, optional `FailureMode→Component`, Asset ownership/error paths).
- No new production node type, relation type or graph attribute was introduced.
- `GraphProjection`, relation evidence references, review metadata and gaps are transport/review metadata, not ontology assertions.
- Structural and diagnostic views contain IDs from the same canonical graph; there is no duplicated ontology.
- The Asset remains the exact operator-canonical workspace entity.

## 6. Agnosticism evidence

- Production code and prompts contain no E-554 gold phrase, manufacturer, model, page-specific rule or machine-specific vocabulary.
- Page-role tests cover generic English, Italian and German diagnostic records and reject preventive/installation prose.
- The final mock replay covers nine heterogeneous fixtures: ABB robot controller, FANUC CNC, laser cutter, pump, conveyor, robot/noisy table, washer, microwave and dishwasher. Result: 9/9 schema compliant, average triplet recall 1.0, no regression.
- All canonicalization and publication decisions use ontology types, normalized morphology, evidence and topology.

This demonstrates structural agnosticism, not semantic production readiness: E-554 real acceptance still failed.

## 7. Cost and duration

Measured full v5 run:

- 19 calls (2 scoping, 10 draft, 1 coverage, 6 resolution);
- 142,261 prompt tokens, 42,784 completion tokens, 185,045 total;
- $0.079794;
- 278.811 s persisted generation duration (278.918 s harness wall time).

The runtime preflight estimated $0.109314 centrally and $0.315142 conservatively. For current v6, an offline deterministic replay of the same selected pages produces 9 chunks, a central estimate of **$0.101170** and a conservative no-cache maximum of **$0.292889**. Thus the cost target is met, but cost success cannot compensate for 0/8 acceptance.

## 8. Real API budget ledger

- Full generation: $0.079794.
- One post-fix micro-benchmark: $0.011023.
- **Cumulative exact estimated list-price spend: $0.090817.**
- Remaining authorized budget: $0.409183.
- Calls: 20 total, fully itemized; per-call sum equals cumulative spend.
- Full generations: 1 started, 1 completed; no retry and no second full generation.
- No concurrent calls, CSV, merge, approval or rejection.

## 9. Measured graph result, risks and alternatives

Full v5 canonical graph (measured): 180 nodes, 175 relations, 0 isolates, 175/175 grounded relations, strict validation passed. The default diagnostic projection has 42 nodes and 31 relations; the structural projection has 145 nodes and 144 `HAS_COMPONENT` relations. All 11 published symptoms have a complete path; all 13 published actions have an incoming `RESOLVED_BY`. Review queue fell from 250 to 82.

The decisive regression is coverage: 0/8 gold. The 0/3 forbidden result is not sufficient because missing all expected chains trivially avoids forbidden pairings.

Principal risks:

- free-form ontology JSON can contain good entities but omit or mis-shape relations;
- strict publication correctly hides incomplete chains, making a relation-recall failure look clean;
- content headings vary by language/manual layout, so role classification needs a broader annotated corpus;
- structural Component extraction remains large (144 components measured), although isolated from the default diagnostic view;
- ambiguous near-duplicate review can still grow on component-heavy manuals.

Preferred alternative: typed diagnostic bundles with explicit symptom/failure/action members and per-edge evidence, compiled through the ontology schema. Secondary alternative: selective structured-output escalation only when a diagnostic chunk returns entities but no causal relations. Do not switch the entire pipeline to a stronger model without a multi-manual measured benefit.

## 10. Go/no-go criteria

Current decision: **NO-GO**.

Authorize production enablement only after all of the following pass on E-554 and a heterogeneous annotated manual set:

- 8/8 gold and 0/3 forbidden;
- 0 published isolates;
- every published Symptom/ErrorCode reaches a FailureMode and CorrectiveAction, otherwise it is a gap and not a complete chain;
- 0 orphan CorrectiveAction;
- 100% exact relation quote/anchor grounding;
- strict ontology validation passes;
- exact operator Asset preserved;
- diagnostic and structural projections remain coherent views of the same graph;
- no gold/vendor/model/page vocabulary in production code or prompts;
- real cost ≤$0.35 and conservative preflight ≤$0.49;
- review queue decreases without hiding blocking diagnostic gaps;
- no diagnostic chunk with extracted diagnostic entities and zero direct causal relations is accepted as ready.

Until those gates pass, keep the experimental code/revision as a reviewable checkpoint only.
