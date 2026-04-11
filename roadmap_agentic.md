# Roadmap: Agentic Neurosymbolic KG Builder

This document tracks the planned extensions to the current MVP, organized by implementation step.
Each step is designed to be independently mergeable and testable.

The overarching goal is to evolve the current linear LangGraph pipeline into a genuinely agentic,
neurosymbolic system with adaptive human-in-the-loop (HITL) — suitable for publication in a Q1 journal.

---

## Narrative Arc (for the paper)

Current state: **reflective multi-agent system (Phase 1)** — specialized agent wrappers over the
same LangGraph pipeline, with supervisor observability, graph reasoning, and schema-aware confidence
scoring. Steps 1–3 are complete on the backend. The frontend still reflects the original Classic UI.

Target state: **fully agentic frontend** where the operator sees confidence-stratified node cards,
acts on structured escalation messages from the Supervisor, and reviews only what the system cannot
resolve autonomously.

The three pillars of the contribution:
1. **Agentic**: self-correcting loops, specialized agents, supervisor orchestration
2. **Neurosymbolic**: symbolic constraints embedded in the reasoning loop (not just post-hoc filters)
3. **Adaptive HITL**: human effort is proportional to extraction uncertainty, not uniform across all cases

---

## Current Stability Checkpoint (2026-04-10)

**Backend status**: partially stable.

What is stable today:
- The base ontology draft path is now materially stronger on Alex Duetto 3.0.
- The previous "1 Asset only" collapse in the **initial draft** was fixed by:
  - raising ontology extraction output budget
  - retrying once when GPT-5.4 returns visible `{}` at the completion cap
  - accepting the raw relation alias key `relation`
- `HAS_COMPONENT` is now completed deterministically during normalization and after multi-chunk merge.
- A dedicated **relation-only second pass** was added, constrained to the existing ontology relations
  and fed with a compact node payload plus a filtered subset of pages.

What is **not** stable yet:
- The **reflective re-extraction path** is not production-stable.
- On the same manual and same date, the backend currently shows this matrix:

| Setting | retry_count | total_nodes | total_relations | Notes |
|---|---:|---:|---:|---|
| `max_retries=0` | 0 | **99** | **132** | Best current baseline |
| `max_retries=1` | 1 | **1** | **0** | Re-extraction collapsed the chunk to Asset-only |
| `max_retries=2` | 1 | **94** | **121** | Usable, but still unstable and variable |

Interpretation:
- The extraction baseline is now good enough to inspect ontology quality.
- The **retry loop is the main blocker** before frontend planning.
- Frontend work should not be treated as stable until the reflective loop stops producing destructive regressions.

Likely root cause of the `max_retries=1` collapse, based on code and log inspection:
- `extract` and `re_extract` do **not** use equivalent contracts.
- The base extraction prompt is strongly schema-prescriptive and coverage-oriented.
- The re-extraction prompt is much looser: it says "fix issues" and "keep what was already correct",
  but it does **not** restate the full extraction obligations for all 6 node types / all ontology relations.
- This leaves GPT-5.4 an easy escape hatch: when semantic issues are raised, the model can satisfy the
  prompt conservatively by dropping disputed content and returning the smallest possible ontology,
  which normalization then turns into "Asset only".
- There is also no safety gate that rejects a re-extracted ontology when it catastrophically regresses
  versus the previous draft.
- The new relation pass cannot rescue this situation, because once re-extraction collapses to Asset-only,
  the relation pass is skipped due to insufficient candidate node types.

Backend implication:
- The current system is suitable for evaluating the **draft + relation pass** path.
- It is **not yet suitable** for claiming a stable self-correcting reflective loop.

---

## Step 1 — Reflective Extraction Loop (LangGraph conditional edges)

**Status**: ✅ done (2026-03-30)

### What was built

The linear `StateGraph` was replaced with a reflective loop:
```
extract → normalize → semantic_validate ──[issues found, retries < N]──→ re_extract (with feedback)
                                        └──[issues found, retries >= N]──→ human_review
                                        └──[no issues]──────────────────→ schema_validate → END
```

Key implementation details:
- `retry_count` and `last_issues` fields in `PipelineState`
- `re_extract` node feeds back structured issue list (severity, code, fix_hint) into the prompt
- `human_review` node flags state when max retries exhausted
- `max_retries` and `retry_on_severity` configurable in `config.yaml`

### Benchmark findings (Alex Duetto 3.0, 2026-04-10)

Tested on `manuals/alex_duetto_3_owners_manual.pdf` (26 PDF pages, 18 selected by scoping):

- With `max_retries=0`: semantic validator skipped entirely; 0 issues found
- With `max_retries=2` and `retry_on_severity=error`: semantic validator runs on each chunk;
  **12 warnings found**, **0 errors** → loop did not trigger (correct behaviour — warnings only)
- With `max_retries=2` and `retry_on_severity=warning`: loop triggers; re-extraction ran but
  produced truncated JSON because `re_extract_max_output_tokens=9000` was too low for the full
  ontology with evidence on every relation. Fixed by raising to 14000.
- LLM calls jump from 2 → 4-8 when retries are active; cost from $0.16 → $0.22–0.60

### Updated findings after extraction + relation-pass fixes (2026-04-10)

The baseline extraction path improved substantially, but the retry path became the dominant risk.

Latest observed matrix:

| Configuration | retry_count | Nodes | Relations | Outcome |
|---|---:|---:|---:|---|
| `max_retries=0` | 0 | **99** | **132** | best run; stable enough for ontology inspection |
| `max_retries=1` | 1 | **1** | **0** | catastrophic regression after re-extraction |
| `max_retries=2` | 1 | **94** | **121** | acceptable output, but retry behaviour still unstable |

This changes the interpretation of Step 1:
- The loop is wired correctly and does trigger when semantic issues of configured severity are found.
- The unresolved problem is no longer "loop does not trigger".
- The unresolved problem is **destructive re-extraction quality**.

Current diagnosis:
- The `re_extract` prompt under-specifies the ontology contract compared to the base `extract` prompt.
- The re-extraction path lacks a regression guard such as:
  - reject retry outputs that remove most substantive nodes
  - keep previous ontology when retry output is clearly degenerate
  - retry only targeted substructures instead of redrafting the whole chunk
- Until that is fixed, `max_retries=0` remains the operationally safest configuration.

### Config baseline (as of 2026-04-10)
```yaml
reflective_loop:
  max_retries: 2
  retry_on_severity: "error"
  re_extract_max_output_tokens: 14000
```

### What this enables for the paper
- First real "agentic" behaviour: the system observes its own output and self-corrects
- Measurable: compare extraction quality with/without loop (precision/recall on held-out manuals)
- Cite: ReAct (Yao et al. 2022), Reflexion (Shinn et al. 2023)

### Files modified
- `backend/services/ontology_pipeline.py`
- `backend/prompts/ontology_prompt.py` (re-extraction prompt)
- `config.yaml`

---

## Step 2 — Graph Reasoning with NetworkX

**Status**: ✅ done (2026-03-30)

### What was built

`backend/services/graph_reasoning.py` with:
- `build_nx_graph(ontology)` → `nx.DiGraph`
- `detect_chain_gaps(G, ontology, schema)` → incomplete Symptom → FM → CA chains
- `detect_orphans(G, ontology)` → nodes not reachable from any Asset
- `detect_invalid_cycles(G)` → cycles in the relation DAG
- `detect_affects_missing_components(G, ontology)` → AFFECTS pointing to non-existent components
- `suggest_missing_relations(G, ontology, schema)` → semantic-similarity-based suggestions

Output integrated into `PipelineState` as `graph_issues: list[GraphIssue]` and
`suggested_relations: list[SuggestedRelation]`, both surfaced in `OntologyPipelineResponse`.

### Benchmark findings (Alex Duetto 3.0, 2026-04-10)

- `graph_issues`: 6–14 per run (varies with extraction quality — more nodes → more detected gaps)
- `suggested_relations`: 15–22 per run
- The "Suggested Relations" review panel is already rendered in the Classic frontend (`app.js:914`)
  via `renderSuggestedRelations()`. Operator can accept/reject each suggestion before export.
- Graph reasoning runs in <1s (pure NetworkX, no LLM calls)

### What this enables for the paper
- Symbolic reasoning on the KG structure — the "symbolic" in neurosymbolic
- Graph completeness metric: % of chains with no gaps before vs. after agent intervention

### Files created / modified
- `backend/services/graph_reasoning.py` (new)
- `backend/services/ontology_pipeline.py` (new `graph_validate` LangGraph node)
- `backend/routers/ontology.py` (graph analysis re-run on `apply_suggestions`)
- `frontend/app.js` (suggested relations panel — already present in Classic UI)

---

## Step 3 — Confidence Scoring and Adaptive HITL

**Status**: ✅ done backend (2026-04-10) — **frontend integration pending**

### What was built

`backend/services/confidence.py` — schema-aware, pure, zero-LLM scoring layer:

**Five signals** (weights configurable in `config.yaml`, normalized to sum 1.0):
| Signal | Weight | Description |
|---|---|---|
| `evidence_present` | 0.25 | Node has provenance (own evidence OR propagated from incident relations) |
| `corroboration` | 0.15 | Distinct source pages (own: full weight; propagated: 0.5 weight) |
| `required_props_complete` | 0.25 | Fraction of schema-required properties present and non-empty |
| `chain_participation` | 0.20 | Fraction of schema-expected outgoing/incoming relations actually present |
| `clean_extraction` | 0.15 | 1.0 if no issues + no retries; 0.5 if retries but node not targeted; 0.0 if direct issue target |

**Two penalties** (subtracted after weighted sum):
| Penalty | Default | Description |
|---|---|---|
| `human_binding_required` | 0.20 | Node has a pending HumanRequiredField entry |
| `per_retry` | 0.02 | Per reflective loop retry (capped at 3×) |

**Classification buckets** (thresholds configurable):
- `auto_approve`: score ≥ θ_high (0.80)
- `human_review`: θ_low ≤ score < θ_high (0.45–0.80)
- `auto_reject`: score < θ_low — **disabled by default** (`auto_reject_enabled: false`)

**Evidence propagation (Soluzione B)**: relations carry `source_page` evidence even when nodes do not.
A node appearing in a relation that cites page P inherits P as weak provenance. This was necessary
because the extraction prompt asks for evidence on relations, not on nodes. The prompt was also
updated to explicitly require evidence on every relation with an example JSON shape.

**Integration points**:
- New `confidence_score` LangGraph node, runs after `graph_validate` in every pipeline run
- Re-scored in `apply_human_binding` (bindings change penalties)
- Re-scored in `POST /ontology/apply-suggestions` (new relations change `chain_participation`)
- Re-scored on the merged ontology after multi-chunk extraction (avoids stale per-chunk scores)
- 41 unit tests in `tests/test_confidence.py`

### Benchmark findings (Alex Duetto 3.0, 2026-04-10)

Three consecutive runs on the same manual:

| Configuration | auto_approve | human_review | Cost | Notes |
|---|---|---|---|---|
| `max_retries=0`, old prompt (no evidence on relations) | 0% | 100% | $0.187 | All nodes lacked evidence |
| `max_retries=0`, new prompt (evidence on relations) | **90% (53/59)** | **10% (6/59)** | $0.162 | Prompt fix unlocked scoring |
| `max_retries=2`, all fixes | **80% (47/59)** | **20% (12/59)** | $0.223 | `clean_extraction=0.5` for retry runs |

Key observations:
- The **6 human_review nodes in the best run** split cleanly into two groups:
  - 4 Symptoms with score ~0.40: no evidence on their `MAY_INDICATE` relations (LLM omitted quotes)
  - 2 FailureModes with score ~0.75: evidence propagated but missing RESOLVED_BY (real gap)
- The 12 nodes in the retry run reflect the discount from `clean_extraction=0.5`
  (retry occurred at chunk level, not node level — an area for future refinement)
- Run-to-run variability is real: CorrectiveAction count varied from 6 to 11 across runs
  on the same document. For the paper, metrics must be averaged over ≥3 runs per manual.

### What remains before the paper claim is complete

**Backend**:
- [x] Investigate the persistent `schema_issue` that kept status at `blocked`
  Result: it was `empty_draft_content` propagated from a cover-page-only chunk; filtered at merge.
- [ ] Stabilise reflective re-extraction: fix the `max_retries=1` collapse-to-Asset-only failure mode
- [ ] Align `re_extract` contract with base extraction contract, or constrain retry to targeted repairs only
- [ ] Add a regression guard so retry outputs cannot silently replace a rich draft with a degenerate ontology
- [ ] Re-run `retry_on_severity=warning` only after the destructive re-extraction bug is fixed
- [ ] Test on at least 2 additional manuals from `manuals/` to verify score distribution generalises
- [ ] `auto_reject` calibration: enable on a held-out set and measure precision/recall

**Frontend (not started)**:
- [ ] Wait for backend retry stability before treating confidence/retry UX as final
- [ ] Confidence badge on each node card in the ontology review screen: colour-coded
  (green = auto_approve, yellow = human_review, red = auto_reject) with score and top reason
- [ ] Pre-sort node list by confidence score ascending (weakest nodes reviewed first)
- [ ] "Auto-approve all above θ_high" bulk action button — skips sending those nodes to human
- [ ] Confidence summary header: counts of auto_approve / human_review / auto_reject before review begins
- [ ] Audit log panel: list of every auto-approved node with score and signals (for paper reproducibility)
- [ ] The **existing Classic UI** (`frontend/app.js`) has screens for: upload → scoping → cut-plan
  approval → ontology draft → human binding → suggested relations → export. None of these screens
  show confidence information. All changes listed above are **additive** to the existing ontology
  review screen — the Classic flow does not need to be restructured, only augmented.

### Files created / modified
- `backend/services/confidence.py` (new)
- `backend/models.py` (`ConfidenceEntry`, `ConfidenceReport`, `confidence_report` on response)
- `backend/app_config.py` (`get_confidence_config()`)
- `backend/services/ontology_pipeline.py` (`confidence_score` node, state propagation)
- `backend/services/ontology_workflow.py` (re-score after multi-chunk merge)
- `backend/routers/ontology.py` (re-score on apply-suggestions)
- `backend/prompts/ontology_prompt.py` (evidence instruction on relations, in both extraction and re-extraction prompts)
- `config.yaml` (new `confidence:` section)
- `tests/test_confidence.py` (new, 41 tests)

---

## Step 4 — Multi-Agent Architecture with Supervisor

**Status**: 🔄 Phase 1 complete (2026-04-10) — Phase 2 not started

### What Phase 1 built (already on branch `feature/multi-agent-pipeline`)

The codebase has been restructured with agent wrappers and observability infrastructure,
without changing the underlying pipeline logic:

**Agent wrappers** (`backend/agents/`):
| File | Agent | What it does |
|---|---|---|
| `scoping_agent.py` | ScopingAgent | Wraps `create_cut_plan_workflow`, updates graph state |
| `ontology_draft_agent.py` | OntologyDraftAgent | Wraps `draft_ontology_workflow`, updates graph state |
| `extraction_agent.py` | ExtractionAgent | Wraps `extract_triplets_workflow`, updates graph state |
| `validation_agent.py` | ValidationAgent | Wraps validation logic |
| `refiner_agent.py` | RefinerAgent | Stub — not yet active |
| `coverage_agent.py` | CoverageAgent | Stub — not yet active |
| `grounding_agent.py` | GroundingAgent | Stub — not yet active |
| `conflict_resolution_agent.py` | ConflictResolutionAgent | Stub — not yet active |
| `ontology_draft_agent.py` | OntologyDraftAgent | Active |

**Supervisor** (`backend/graph/supervisor.py`):
- Deterministic routing (`decision_type: "deterministic"`) — no LLM calls yet
- Records phase transitions with timestamp, state hash, token budget, and routing reason
- Exposes structured audit log via `GET /multi-agent/audit/{run_id}`

**Graph state** (`backend/graph/`):
- `state.py`: `GraphPhase` enum, phase history, token ledger
- `store.py`: phase transitions, supervisor log, per-phase metrics
- `backend/routers/multi_agent.py`: observability endpoints (`/status`, `/audit`)

**Mode switching**: `config.yaml → pipeline.mode: multi_agent` routes requests through agent
wrappers; `classic` routes directly to workflows. Both modes currently produce identical KG outputs —
Phase 1 is a structural refactor with observability, not a behavioural change.

### What Phase 2 needs to build

Phase 2 is where the Supervisor gains real decision-making power. This is the publishable contribution.

**Supervisor logic upgrade** (currently deterministic → should become policy-driven):
```
Supervisor receives ConfidenceReport after each agent run:
  if all nodes >= θ_high and no critical graph_issues:
      → advance to next phase or END
  elif retry_count < max_retries and issues are "error" severity:
      → route to RefinerAgent with structured feedback
  elif any node < θ_low or unresolvable graph_issues:
      → emit EscalationMessage → HITL pause
      → resume after operator decision (approve / reject / edit / skip)
  else:
      → advance (warnings tolerated)
```

**EscalationMessage model** (not yet implemented):
```json
{
  "escalation_id": "esc-001",
  "phase": "validation",
  "agent": "ValidationAgent",
  "issue": "FailureMode fm_channel_2_unplugged has no RESOLVED_BY. Confidence 0.60.",
  "options": ["approve_as_is", "reject_node", "provide_correction", "skip"],
  "context": {
    "node_type": "FailureMode",
    "node_id": "fm_channel_2_unplugged",
    "score": 0.60,
    "suggested_relation": {"name": "RESOLVED_BY", "target_id": "ca_check_temperature_sensor_connections_coffee_boiler"}
  }
}
```

**Frontend changes needed (Phase 2 — not started)**:

The current `frontend/app.js` Classic UI uses **fixed sequential screens**:
```
Upload → Scoping/CutPlan → Ontology Draft → Human Binding → Suggested Relations → Export
```

This needs to become a **dynamic escalation-driven flow**:
```
Upload → [Agent pipeline runs] → Supervisor emits escalation cards as needed → Export
```

Specifically:
- [ ] Replace the static ontology-review screen with a **confidence-stratified node list**:
  - Nodes auto_approve: collapsed by default, expandable for audit
  - Nodes human_review: expanded cards sorted by score ascending (weakest first)
  - Each card shows: node type/id, score, colour-coded badge, top reasons, signals breakdown
- [ ] Add **EscalationMessage card renderer**: structured decision cards (not generic forms)
  - Shows what the agent attempted, what the issue is, what options the operator has
  - Operator responds with a structured action (approve / reject / edit / skip)
- [ ] Replace static "Suggested Relations" panel with **Supervisor-driven graph fix cards**
  (currently already exists in Classic UI as `renderSuggestedRelations()` — needs to feed
  from Supervisor rather than from the pipeline response directly)
- [ ] Add **pipeline progress indicator** showing current phase and agent, powered by
  `GET /multi-agent/status/{run_id}` (endpoint exists, not yet wired to UI)
- [ ] Add **audit trail panel** (collapsible): shows supervisor routing decisions with timestamps,
  powered by `GET /multi-agent/audit/{run_id}` (endpoint exists, not yet wired to UI)

### What this enables for the paper
- True multi-agent architecture with Supervisor-as-HITL-coordinator
- Measurable: number of escalations per manual; reduction in human review items vs. Step 3 baseline
- The frontend becomes part of the contribution: structured escalation UI is novel in this domain
- Cite: LangGraph multi-agent patterns, human-AI teaming, maintenance domain KG literature

---

## Implementation Order (updated)

```
Step 1 ✅  Step 2 ✅  Step 3 (backend) ✅
                              ↓
                   Step 3 frontend (confidence badges, bulk approve)
                              ↓
                   Step 4 Phase 2 (Supervisor policy + EscalationMessage)
                              ↓
                   Step 4 frontend (escalation cards, dynamic flow)
```

Steps 3-frontend and Step 4 can proceed in parallel: the backend contracts
(`ConfidenceReport`, `EscalationMessage`) are stable enough to build against.

---

## Benchmark Summary — Alex Duetto 3.0 (2026-04-10)

Reference manual: `manuals/alex_duetto_3_owners_manual.pdf`  
Benchmark script: `scripts/run_manual_benchmark.py --pdf ... --page-offset 1 --phase scoping+ontology`  
Reports saved in: `benchmark_runs/`

### Scoping
- 26 total pages, **18 selected** (69%), 2 keyword-based sections
- ToC not found (manual has no machine-readable index) → keyword fallback
- Product identified correctly: "Alex Duetto 3.0 Espresso Machine / Owner's Manual"
- Scoping cost: ~$0.001 (1 LLM call, cached on repeated runs)

### Ontology extraction (best run: max_retries=0, evidence prompt)
| Metric | Value |
|---|---|
| Nodes extracted | 59 (1 Asset, 25 Component, 9 Symptom, 12 FailureMode, 6 CorrectiveAction, 6 ErrorCode) |
| Relations | 60 (HAS_COMPONENT×25, AFFECTS×10, MAY_INDICATE×7, RESOLVED_BY×6, GENERATES_ERROR×6, INDICATES×6) |
| Graph issues | 14 |
| Suggested relations | 16 |
| Schema issues | 1 (status `blocked` — under investigation) |
| Cost | $0.162 (2 LLM calls, 2 chunks) |
| Duration | ~75s |

### Confidence scoring (best run)
| Classification | Count | % |
|---|---|---|
| auto_approve (≥ 0.80) | 53 | **90%** |
| human_review (0.45–0.80) | 6 | 10% |
| auto_reject | 0 | 0% (disabled) |

Target from roadmap: < 40% items for human review. **Achieved: 10%.**

### Known issues from benchmarking
- **`status: blocked`** due to 1 persistent schema_issue — not yet investigated
- **Run-to-run variability**: CorrectiveAction count ranged 6–11 across runs on the same PDF.
  For the paper, must report mean ± std over ≥3 runs per manual.
- **4 Symptoms consistently score ~0.40**: their `MAY_INDICATE` relations lack `source_page`
  (LLM sometimes omits quotes for short/implicit relations). Possible fix: lower θ_low or
  add a post-processing pass to infer page from surrounding CorrectiveAction evidence.
- **`re_extract_max_output_tokens`** must be ≥14000 when evidence is required on relations;
  the default 9000 caused JSON truncation during retry runs.

---

## Metrics to track for the paper (updated)

| Metric | Baseline (Classic, no agentic) | Current (Steps 1–3 backend) | Target |
|---|---|---|---|
| Operator review items per manual | 100% of nodes | **10% (best run)** | < 40% |
| Extraction retries per manual | N/A | 0 (warnings only, loop not triggered) | ≤ 2 in 80% of cases |
| Graph completeness (chains with no gaps) | not measured | 14 graph_issues found | ≥ 90% gap-free after suggestions |
| Precision of auto-approved nodes | N/A | not yet measured (need ground truth) | ≥ 0.85 |
| Cost per manual (scoping + ontology) | ~$0.19 (no evidence prompt) | **$0.16 (with evidence prompt)** | < $0.25 |
| Run-to-run node count stability | not measured | ±5–10 nodes | < ±3 nodes (3-run avg) |

---

## Notes for the paper framing

- **Domain-agnostic documents, schema-driven extraction**: the system uses a fixed ontology schema
  (`ontology_schema.JSON`) applicable to any maintenance manual — robots, espresso machines,
  industrial controllers. The schema defines what to extract; the LLM finds where it is in the text.
- **Neurosymbolic confidence**: the five scoring signals combine learned evidence (LLM-generated
  `source_page` quotes) with symbolic structural checks (NetworkX chain completeness, schema required
  props). Neither alone is sufficient — the combination is the contribution.
- **Adaptive HITL**: the 10% human review result on Alex Duetto is a concrete early measurement.
  The paper claim is that this ratio is stable across manuals and that auto-approved nodes meet
  precision ≥ 0.85. Both require held-out ground truth annotation — not yet done.
- **Reproducibility**: all benchmark runs are saved as JSON in `benchmark_runs/`. The benchmark
  script `scripts/run_manual_benchmark.py` is deterministic modulo LLM non-determinism (temperature=0).
