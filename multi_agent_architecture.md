# Multi-Agent Architecture Specification

## Upgrade from Classic Pipeline to GraphChain Multi-Agent System

This document specifies the architectural changes required to transform the current classic extraction pipeline into a neurosymbolic, ontology-grounded, domain-agnostic multi-agent system orchestrated via a state graph (LangGraph).

The design preserves the existing `classic` pipeline mode as a fallback and introduces `multi_agent` as the new execution mode under `pipeline.mode` in `config.yaml`.

---

## 1. Design Principles

Every architectural decision in this document follows these constraints:

- **Domain-agnostic**: No agent embeds domain-specific logic. Domain knowledge flows exclusively through the ontology schema and the source document. The system must process automotive manuals, medical devices, industrial machinery, or any other technical domain without code changes.
- **Ontology-grounded**: Every extracted entity and relation must trace back to the ontology schema. No agent produces output that is not validated against the schema contract.
- **Neurosymbolic**: LLM capabilities (semantic understanding, extraction, generation) are always paired with deterministic symbolic checks (schema validation, graph reasoning, rule-based routing). Neither layer operates alone.
- **Auditable**: Every agent decision, state transition, and routing choice is logged with reasoning, timestamps, and provenance. An operator can reconstruct why any entity was accepted, rejected, refined, or escalated.
- **Token-aware, not token-restricted**: Agents have visibility into token budgets and report consumption, but token limits never silently degrade output quality. When a budget would force quality loss, the agent escalates instead of producing inferior output.

---

## 2. Agent Inventory

### 2.1 Core Agents

| Agent | Responsibility | Primary Mode | Model Tier |
|-------|---------------|-------------|------------|
| **ScopingAgent** | Document analysis, ToC detection, keyword scan, page selection, cut plan generation | Hybrid (deterministic + LLM) | Small |
| **OntologyDraftAgent** | Ontology instance extraction from selected pages, normalization, schema alignment | LLM + deterministic post-processing | Strong |
| **ExtractionAgent** | Triplet extraction (Symptom, FailureMode, CorrectiveAction) from approved pages | LLM + deterministic cleanup | Strong |
| **ValidationAgent** | Page-level grounding verification, coverage analysis, ontology chain integrity | LLM + symbolic checks | Strong |
| **RefinerAgent** | Targeted re-extraction and correction of rejected or weak entities | LLM with surgical scope | Strong |
| **Supervisor** | State evaluation, conditional routing, escalation decisions, run orchestration | Deterministic + LLM fallback | Small (LLM path only) |

### 2.2 Extended Agents (Pluggable)

| Agent | Responsibility | Primary Mode | Model Tier |
|-------|---------------|-------------|------------|
| **CoverageAgent** | Page-by-page gap analysis: what exists in the document vs what was extracted | Hybrid | Small/Strong |
| **GroundingAgent** | Deep entity-vs-source-text verification for each CorrectiveAction, Symptom, FailureMode | LLM + text comparison | Strong |
| **ConflictResolutionAgent** | Cross-chunk deduplication, contradiction detection, merge-or-escalate decisions | LLM + graph analysis | Strong |
| **TranslationQAAgent** | Post-translation quality check: terminology consistency, untranslatable terms preserved | LLM | Small |
| **SchemaEvolutionAgent** | Proposes ontology schema extensions when extracted content doesn't fit current schema | LLM + schema analysis | Strong |
| **MetaReviewAgent** | End-of-run quality assessment: structural completeness, KPI anomaly detection, confidence distribution analysis | Hybrid | Small |

### 2.3 Agent Registration and Discovery

Agents are registered in `config.yaml` under a new `agents` section:

```yaml
agents:
  scoping:
    enabled: true
    model: "gpt-5.4-nano"
    timeout: 60
    max_retries: 1
  ontology_draft:
    enabled: true
    model: "gpt-5.4"
    timeout: 120
    max_retries: 1
  extraction:
    enabled: true
    model: "gpt-5.4"
    timeout: 120
    max_retries: 1
  validation:
    enabled: true
    model: "gpt-5.4"
    timeout: 90
    max_retries: 2
  refiner:
    enabled: true
    model: "gpt-5.4"
    timeout: 90
    max_retries: 2
  coverage:
    enabled: true
    model: "gpt-5.4-nano"
    timeout: 60
  grounding:
    enabled: true
    model: "gpt-5.4"
    timeout: 90
  conflict_resolution:
    enabled: true
    model: "gpt-5.4"
    timeout: 60
  translation_qa:
    enabled: false
    model: "gpt-5.4-nano"
    timeout: 30
  schema_evolution:
    enabled: false
    model: "gpt-5.4"
    timeout: 60
  meta_review:
    enabled: false
    model: "gpt-5.4-nano"
    timeout: 30
```

Disabling an agent causes the Supervisor to skip that node in the graph. The pipeline remains functional with only the core agents enabled.

---

## 3. Shared State (GraphState)

All agents read from and write to a single shared state object. This is the LangGraph `State` that flows through the graph.

### 3.1 State Schema

```python
from typing import TypedDict, Optional
from enum import Enum

class RunPhase(str, Enum):
    SCOPING = "scoping"
    ONTOLOGY_DRAFT = "ontology_draft"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    REFINEMENT = "refinement"
    COVERAGE = "coverage"
    GROUNDING = "grounding"
    CONFLICT_RESOLUTION = "conflict_resolution"
    HITL_REVIEW = "hitl_review"
    EXPORT = "export"
    COMPLETED = "completed"

class EntityVerdict(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REFINEMENT = "needs_refinement"
    NEEDS_HUMAN = "needs_human"

class GraphState(TypedDict):
    # --- Run identity ---
    pdf_id: str
    run_id: str
    current_phase: RunPhase
    phase_history: list[dict]  # [{phase, timestamp, agent, decision, reasoning}]

    # --- Document ---
    filename: str
    total_pages: int
    page_texts: dict[int, str]  # page_number -> extracted text
    source_language: str

    # --- Scoping ---
    cut_plan: Optional[dict]
    selected_pages: list[int]
    scoping_metadata: dict  # product_name, source_title, toc, etc.

    # --- Ontology ---
    ontology_draft: Optional[dict]
    ontology_issues: list[dict]  # [{type, severity, detail, agent}]
    human_required_fields: list[dict]
    suggested_relations: list[dict]
    schema_compliant: bool

    # --- Extraction ---
    raw_triplets: list[dict]  # pre-cleanup
    cleaned_triplets: list[dict]  # post-cleanup
    extraction_chunks: list[dict]  # chunk metadata for parallel processing

    # --- Validation verdicts ---
    entity_verdicts: list[dict]
    # Each: {entity_id, entity_type, verdict: EntityVerdict,
    #        reasons: list[str], source_page: int,
    #        grounding_score: float, agent: str}

    # --- Coverage ---
    coverage_map: Optional[dict]
    # {page_number: {has_content: bool, extracted_entities: list,
    #                gap_type: str|None, recommendation: str|None}}

    # --- Grounding ---
    grounding_results: list[dict]
    # Each: {entity_id, entity_type, source_page: int,
    #        grounding_score: float, supporting_text: str|None,
    #        issues: list[str]}

    # --- Conflict resolution ---
    conflicts: list[dict]
    # Each: {entity_ids: list, conflict_type: str,
    #        resolution: str|None, resolved_entity: dict|None}

    # --- Refinement tracking ---
    refinement_attempts: dict[str, int]  # entity_id -> attempt count
    refinement_log: list[dict]  # [{entity_id, attempt, result, reasoning}]

    # --- HITL ---
    hitl_queue: list[dict]
    # Each: {entity_id, entity_type, reason: str, context: dict,
    #        agent_trail: list[str], suggested_action: str}
    hitl_decisions: list[dict]  # operator responses

    # --- Token accounting ---
    token_ledger: dict
    # {agent_name: {calls: int, prompt_tokens: int,
    #               completion_tokens: int, cached_tokens: int,
    #               estimated_cost: float}}

    # --- Supervisor ---
    supervisor_log: list[dict]
    # Each: {timestamp, state_snapshot_hash, decision, reasoning,
    #        next_agent: str, condition_met: str}

    # --- Export ---
    export_base: Optional[str]  # "ontology_draft" | "minimal_fallback"
    final_json: Optional[dict]

    # --- Config ---
    config_overrides: dict  # runtime overrides from operator
```

### 3.2 State Contracts Between Agents

Each agent has an explicit input/output contract:

| Agent | Reads | Writes |
|-------|-------|--------|
| ScopingAgent | `page_texts`, config | `cut_plan`, `selected_pages`, `scoping_metadata`, `source_language` |
| OntologyDraftAgent | `selected_pages`, `page_texts`, `scoping_metadata` | `ontology_draft`, `ontology_issues`, `human_required_fields`, `suggested_relations`, `schema_compliant` |
| ExtractionAgent | `selected_pages`, `page_texts`, `ontology_draft`, `scoping_metadata` | `raw_triplets`, `cleaned_triplets`, `extraction_chunks` |
| ValidationAgent | `cleaned_triplets`, `ontology_draft`, `page_texts` | `entity_verdicts` |
| RefinerAgent | `entity_verdicts` (filtered: needs_refinement), `page_texts`, `ontology_draft` | updated entries in `cleaned_triplets`, `entity_verdicts`, `refinement_log` |
| CoverageAgent | `selected_pages`, `page_texts`, `cleaned_triplets`, `entity_verdicts` | `coverage_map` |
| GroundingAgent | `cleaned_triplets`, `page_texts` | `grounding_results`, updates to `entity_verdicts` |
| ConflictResolutionAgent | `cleaned_triplets`, `entity_verdicts`, `ontology_draft` | `conflicts`, updated `cleaned_triplets` |
| Supervisor | entire `GraphState` | `current_phase`, `phase_history`, `supervisor_log`, `hitl_queue` |

---

## 4. State Graph Topology

### 4.1 Graph Structure

```
                    ┌──────────────┐
                    │    START     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ ScopingAgent │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  HITL: Cut   │
                    │  Plan Review │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Ontology    │
                    │  DraftAgent  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  HITL:       │
                    │  Ontology    │
                    │  Review      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Extraction  │
                    │  Agent       │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
              ┌─────┤  Supervisor  ├─────┐
              │     │  (Router)    │     │
              │     └──────┬───────┘     │
              │            │             │
     ┌────────▼──┐  ┌──────▼───────┐  ┌──▼────────┐
     │ Validation│  │  Coverage    │  │ Grounding │
     │ Agent     │  │  Agent       │  │ Agent     │
     └────────┬──┘  └──────┬───────┘  └──┬────────┘
              │            │             │
              └────────────┼─────────────┘
                           │
                    ┌──────▼───────┐
                    │  Supervisor  │
                    │  (Evaluate)  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼──┐  ┌──────▼───────┐  ┌─▼──────────┐
     │  Refiner  │  │  Conflict    │  │   HITL:     │
     │  Agent    │  │  Resolution  │  │   Triplet   │
     └────────┬──┘  └──────┬───────┘  │   Review    │
              │            │          └─┬───────────┘
              └────────────┼────────────┘
                           │
                    ┌──────▼───────┐
                    │  Supervisor  │
                    │  (Converge)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Export     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  MetaReview  │
                    │  (optional)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │     END      │
                    └──────────────┘
```

### 4.2 Conditional Edges

The Supervisor's routing logic is defined through conditional edges. Each edge evaluates the current `GraphState` and returns the next node.

```python
# Post-extraction routing
def route_after_extraction(state: GraphState) -> list[str]:
    """Determines which verification agents to run in parallel."""
    targets = []
    if is_agent_enabled("validation"):
        targets.append("validation_agent")
    if is_agent_enabled("coverage"):
        targets.append("coverage_agent")
    if is_agent_enabled("grounding"):
        targets.append("grounding_agent")
    # If no verification agents enabled, go straight to HITL
    return targets if targets else ["hitl_triplet_review"]


# Post-validation routing
def route_after_validation(state: GraphState) -> str:
    """Supervisor evaluates combined verification results."""
    verdicts = state["entity_verdicts"]
    grounding = state["grounding_results"]
    coverage = state["coverage_map"]

    needs_refinement = [v for v in verdicts
                        if v["verdict"] == EntityVerdict.NEEDS_REFINEMENT]
    needs_human = [v for v in verdicts
                   if v["verdict"] == EntityVerdict.NEEDS_HUMAN]

    has_conflicts = any(c["resolution"] is None for c in state["conflicts"])
    has_coverage_gaps = coverage and any(
        p["gap_type"] == "missing_extraction"
        for p in coverage.values()
        if p.get("gap_type")
    )

    # Refinement possible and budget allows?
    if needs_refinement and can_refine(state, needs_refinement):
        return "refiner_agent"

    # Unresolved conflicts?
    if has_conflicts and is_agent_enabled("conflict_resolution"):
        return "conflict_resolution_agent"

    # Coverage gaps that warrant re-extraction?
    if has_coverage_gaps and should_reextract_for_coverage(state):
        return "extraction_agent"  # targeted re-extraction

    # Anything left goes to HITL
    if needs_human or needs_refinement:
        return "hitl_triplet_review"

    # Everything accepted
    return "export"


# Refinement convergence check
def route_after_refinement(state: GraphState) -> str:
    """Check if refinement resolved issues or needs escalation."""
    still_failing = [v for v in state["entity_verdicts"]
                     if v["verdict"] == EntityVerdict.NEEDS_REFINEMENT
                     and state["refinement_attempts"].get(v["entity_id"], 0)
                        >= max_refinement_retries()]

    if still_failing:
        # Escalate to HITL with full trail
        enqueue_for_hitl(state, still_failing, reason="refinement_exhausted")
        return "hitl_triplet_review"

    # Re-validate refined entities
    return "validation_agent"
```

### 4.3 Parallelism

The state graph supports parallel execution at two levels:

**Level 1 — Verification fan-out**: After extraction, ValidationAgent, CoverageAgent, and GroundingAgent run in parallel on the same state. Their outputs are written to separate state keys, so there is no write conflict.

**Level 2 — Chunk-level parallelism**: ExtractionAgent and OntologyDraftAgent can process multiple page chunks in parallel. Each chunk produces independent output that is aggregated before the next phase.

LangGraph supports both patterns natively through `Send()` for fan-out and parallel node execution.

---

## 5. Supervisor Detail

### 5.1 Decision Model

The Supervisor is **deterministic-first, LLM-fallback**. The decision tree:

```
1. Read current GraphState
2. Evaluate deterministic rules (priority order):
   a. All verdicts == ACCEPTED and no conflicts → route to EXPORT
   b. Any verdict == NEEDS_HUMAN → route to HITL
   c. Any verdict == NEEDS_REFINEMENT and retries < max → route to REFINER
   d. Coverage gaps with extractable pages → route to EXTRACTION (targeted)
   e. Unresolved conflicts → route to CONFLICT_RESOLUTION
   f. Refinement exhausted → escalate to HITL with full context
3. If no deterministic rule matches (ambiguous state):
   a. Call LLM with state summary
   b. LLM returns {next_agent, reasoning}
   c. Log as "llm_routed" in supervisor_log
```

### 5.2 Escalation Policy

The Supervisor never drops entities silently. Every entity reaches one of three terminal states:

| Terminal State | Meaning |
|---------------|---------|
| `ACCEPTED` | Passed validation, grounded in source, no conflicts |
| `REJECTED` | Explicitly rejected by operator during HITL review |
| `EXPORTED_WITH_FLAG` | Accepted by operator despite validation warnings |

### 5.3 HITL Queue Construction

When the Supervisor routes to HITL, it constructs the queue with context:

```python
hitl_entry = {
    "entity_id": entity.id,
    "entity_type": entity.type,
    "reason": "grounding_score_below_threshold",  # or: refinement_exhausted, conflict_unresolved, coverage_gap
    "context": {
        "source_page": entity.source_page,
        "source_text_excerpt": page_texts[entity.source_page][:500],
        "grounding_score": 0.43,
        "validation_issues": ["instruction_text not found in cited page"],
        "refinement_history": [
            {"attempt": 1, "result": "still_ungrounded", "changes_made": "..."}
        ]
    },
    "agent_trail": ["ExtractionAgent", "ValidationAgent", "RefinerAgent"],
    "suggested_action": "edit_source_page"  # or: accept_as_is, reject, merge_with
}
```

The operator sees only what needs attention, with full trail of what was already tried.

### 5.4 Supervisor Audit Log

Every Supervisor decision is logged:

```python
supervisor_log_entry = {
    "timestamp": "2026-04-09T14:32:01Z",
    "run_id": "run_abc123",
    "phase_from": "validation",
    "phase_to": "refinement",
    "decision_type": "deterministic",  # or "llm_routed"
    "condition_met": "needs_refinement_count=5, retries_remaining=2",
    "entities_affected": ["CA_001", "CA_003", "CA_007", "FM_002", "SY_004"],
    "reasoning": "5 entities need refinement, all under retry limit",
    "token_budget_remaining": 45000,
    "token_budget_used_this_phase": 12300
}
```

---

## 6. Agent Specifications

### 6.1 ScopingAgent

**No architectural change from classic pipeline.** The existing scoping logic (keyword scan + ToC detection + rule-based scoring + LLM section selection) is wrapped as an agent node.

Changes:
- Writes to `GraphState` instead of `pdf_store`
- Reports token usage to `token_ledger`
- Emits scoping audit entry to `phase_history`

### 6.2 OntologyDraftAgent

**Wraps existing `ontology_pipeline.py` logic.** Chunking, normalization, semantic validation, schema validation, and graph reasoning remain unchanged.

Changes:
- Reads `selected_pages` and `page_texts` from `GraphState`
- Writes `ontology_draft`, `ontology_issues`, `human_required_fields`, `suggested_relations` to `GraphState`
- Reflective loop is now internal to this agent (not orchestrated by Supervisor), because ontology refinement is structurally different from triplet refinement
- Reports token usage per chunk to `token_ledger`

### 6.3 ExtractionAgent

**Wraps existing extraction + semantic cleanup.** The existing extraction prompt, Pydantic parsing, and deterministic cleanup layer are preserved.

Changes:
- Supports targeted re-extraction: when called with a `target_pages` parameter in state, extracts only from those pages instead of all `selected_pages`
- Chunk-level parallelism: each chunk can be processed independently
- Writes `raw_triplets` and `cleaned_triplets` to `GraphState`
- Cross-chunk deduplication runs after all chunks complete

### 6.4 ValidationAgent

**New agent.** This is the core quality gate that replaces the current coarse-grained cleanup-only approach.

Responsibilities:
- For each extracted triplet, verify:
  - Symptom is grounded in source text
  - FailureMode is grounded and distinct from verification outcomes
  - CorrectiveAction is actionable (not inspection-only) and grounded in cited page
  - Ontology chain integrity: the triplet's entities exist in and are consistent with the ontology draft
  - Page attribution accuracy: cited `source_page` actually contains supporting text
- Assign `EntityVerdict` to each entity
- Assign `grounding_score` (0.0-1.0) based on text overlap and semantic alignment

Verdict assignment rules:
```
grounding_score >= 0.8 AND no ontology issues    → ACCEPTED
grounding_score >= 0.5 AND recoverable issues    → NEEDS_REFINEMENT
grounding_score < 0.5 OR structural issues       → NEEDS_HUMAN
```

Thresholds are configurable in `config.yaml`:
```yaml
validation:
  grounding_accept_threshold: 0.8
  grounding_refine_threshold: 0.5
  check_ontology_chain: true
  check_page_attribution: true
```

### 6.5 RefinerAgent

**New agent.** Performs surgical corrections on entities that received `NEEDS_REFINEMENT` verdict.

Behavior:
- Receives only the failing entities, not the full extraction set
- For each entity:
  - Reads the cited `source_page` text
  - Re-extracts or corrects the specific field that failed validation
  - Preserves all fields that passed
- Does NOT re-run the full extraction prompt
- Reports what changed and why in `refinement_log`

Token efficiency: a typical refinement call processes 1-5 entities against 1-3 pages, costing roughly 5-10% of a full extraction run.

Max retries per entity are configured in `config.yaml`:
```yaml
refiner:
  max_retries_per_entity: 2
  escalate_after_exhaustion: true  # send to HITL if retries exhausted
```

### 6.6 CoverageAgent

**New agent.** Answers: "what did we miss?"

Behavior:
- Iterates over each `selected_page`
- For each page, checks which entities cite it as `source_page`
- Compares page content against extracted entities to identify:
  - Pages with troubleshooting content but zero extractions
  - Pages with partial extraction (e.g., symptoms found but no corrective actions)
  - Pages that were selected but contain no diagnostic content (false positive in scoping)
- Produces a `coverage_map` with gap types:
  - `fully_covered`: page content adequately represented in extractions
  - `partially_covered`: some content extracted, gaps identified
  - `missing_extraction`: diagnostic content present but not extracted
  - `no_diagnostic_content`: page selected but contains no relevant content

The Supervisor uses `coverage_map` to decide if targeted re-extraction is worthwhile.

### 6.7 GroundingAgent

**New agent.** Deep verification specialist. Different from ValidationAgent: the ValidationAgent does broad structural checks, the GroundingAgent does focused text-level verification.

Behavior:
- For each CorrectiveAction:
  - Loads the full text of `source_page`
  - Verifies that `instruction_text` is semantically supported by the page content
  - Checks that procedural steps are present in the source (not hallucinated)
  - Verifies that referenced components exist in the page context
- For each Symptom and FailureMode:
  - Verifies description matches source text semantics
  - Checks that severity/category assignments are supported

Output: `grounding_results` with per-entity scores and supporting evidence.

### 6.8 ConflictResolutionAgent

**New agent.** Handles cross-chunk inconsistencies.

Conflict types detected:
- **Duplicate entities**: semantically identical entities from different chunks with different IDs
- **Contradictory severity**: same failure mode assigned different severity levels in different chunks
- **Overlapping corrective actions**: similar but not identical actions for the same failure mode
- **Broken references**: entity references another entity that was deduplicated or removed

Resolution strategies:
- `merge`: combine into single entity, keep richest description
- `prefer_higher_confidence`: keep the entity with higher grounding score
- `escalate`: cannot resolve automatically, send to HITL with both versions

### 6.9 TranslationQAAgent (Extended, Optional)

Post-translation checks:
- Technical term consistency across all translated entities
- Terms that should remain untranslated (model numbers, error codes, part numbers)
- Back-translation spot check on critical fields

### 6.10 SchemaEvolutionAgent (Extended, Optional)

When extraction produces entities that don't fit the current ontology schema cleanly:
- Proposes new node types or relation types
- Validates proposals against ontology design principles
- Queues proposals for operator approval
- Does NOT auto-modify the schema

### 6.11 MetaReviewAgent (Extended, Optional)

End-of-run quality assessment:
- Coverage completeness score
- Grounding score distribution analysis
- KPI anomaly detection (e.g., cost per triplet outlier)
- Structural completeness (orphan nodes, disconnected subgraphs)
- Comparison with historical run statistics if available

---

## 7. Token Accounting

### 7.1 Token Ledger

Every LLM call made by any agent is recorded in `token_ledger`:

```python
token_ledger = {
    "scoping_agent": {
        "calls": 2,
        "prompt_tokens": 3400,
        "completion_tokens": 800,
        "cached_tokens": 1200,
        "estimated_cost": 0.012,
        "model": "gpt-5.4-nano"
    },
    "extraction_agent": {
        "calls": 4,
        "prompt_tokens": 28000,
        "completion_tokens": 6200,
        "cached_tokens": 8000,
        "estimated_cost": 0.15,
        "model": "gpt-5.4"
    },
    # ... per agent
}
```

### 7.2 Budget Visibility, Not Hard Caps

The system tracks token consumption per agent and per run, but does NOT enforce hard caps that would silently degrade quality. Instead:

- Each agent reports estimated token cost before making an LLM call
- The Supervisor has visibility into cumulative spend
- If cumulative spend exceeds a configurable `soft_warning_threshold`, the Supervisor logs a warning but does NOT block the call
- If cumulative spend exceeds `hard_escalation_threshold`, the Supervisor routes to HITL with a cost alert instead of continuing autonomous processing

```yaml
token_budget:
  soft_warning_threshold_usd: 2.00
  hard_escalation_threshold_usd: 10.00
  log_every_call: true
  # No agent is ever silently degraded by token limits
```

### 7.3 Model Mixing Strategy

Different agents use different model tiers to optimize cost without sacrificing quality where it matters:

| Agent | Recommended Tier | Rationale |
|-------|-----------------|-----------|
| ScopingAgent | Small (nano) | Keyword + ToC analysis is mostly deterministic, LLM does lightweight section selection |
| OntologyDraftAgent | Strong | Ontology quality drives everything downstream |
| ExtractionAgent | Strong | Extraction accuracy directly impacts final output |
| ValidationAgent | Strong | Must catch subtle grounding issues |
| RefinerAgent | Strong | Surgical correction needs high capability |
| CoverageAgent | Small | Page scanning is mostly comparison, not generation |
| GroundingAgent | Strong | Text-level semantic matching needs strong model |
| ConflictResolutionAgent | Strong | Semantic deduplication requires nuance |
| Supervisor (LLM path) | Small | Routing decisions are simple even when ambiguous |

---

## 8. Checkpointing (Optional, Configurable)

### 8.1 Rationale

The current system loses all state on restart. Checkpointing enables resume-after-crash without re-spending tokens.

### 8.2 Configuration

```yaml
checkpointing:
  enabled: false  # opt-in
  backend: "sqlite"  # or "filesystem"
  path: "data/checkpoints/"
  checkpoint_after: ["scoping", "ontology_draft", "extraction", "validation"]
  max_checkpoints_per_run: 10
```

### 8.3 Behavior

When enabled:
- After each configured phase, the full `GraphState` is serialized and stored
- On restart, the system detects incomplete runs and offers to resume from last checkpoint
- LangGraph's built-in checkpointing integrates directly with this

When disabled:
- Behavior is identical to current classic pipeline (in-memory only)

---

## 9. API Changes

### 9.1 New Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `POST /multi-agent/run` | POST | Starts a full multi-agent run. Replaces the sequential manual calls to `/cut-plan`, `/ontology/draft`, `/extract-tables` |
| `GET /multi-agent/status/{run_id}` | GET | Returns current `GraphState` phase, progress, and agent activity |
| `GET /multi-agent/audit/{run_id}` | GET | Returns full `supervisor_log` and `phase_history` |
| `POST /multi-agent/hitl/{run_id}` | POST | Submits operator decisions for HITL queue items |
| `GET /multi-agent/token-ledger/{run_id}` | GET | Returns current token accounting |
| `POST /multi-agent/resume/{run_id}` | POST | Resumes from checkpoint (if enabled) |

### 9.2 Preserved Endpoints

All existing endpoints remain functional when `pipeline.mode: classic`. The multi-agent mode does NOT break backward compatibility.

### 9.3 HITL Interaction Model

In multi-agent mode, HITL is event-driven rather than screen-sequential:

```
Classic mode:
  cut plan screen → ontology screen → triplet screen → export screen

Multi-agent mode:
  run starts → agents work autonomously → HITL events arrive when needed
  operator sees: queue of items requiring attention, each with full context
  operator acts: approve / reject / edit per item
  run continues from where it paused
```

The frontend needs a new "Agent Dashboard" view that shows:
- Current run phase
- Agent activity log (live)
- HITL queue with prioritized items
- Token consumption (live)
- Coverage map visualization
- Supervisor decision trail

### 9.4 SSE/WebSocket for Live Updates

Multi-agent runs are long-lived. The frontend subscribes to a Server-Sent Events stream:

```
GET /multi-agent/stream/{run_id}
```

Events emitted:
- `phase_changed`: agent started/completed
- `hitl_required`: new item added to HITL queue
- `entity_verdict`: validation result for an entity
- `token_update`: periodic token consumption update
- `run_completed`: final state ready
- `error`: agent failure with context

---

## 10. Migration Strategy

### 10.1 Incremental Approach

The migration is NOT a rewrite. It is a progressive wrapping:

**Phase 1 — Agent wrappers**: Wrap existing service modules (`cutplan_service`, `ontology_pipeline`, extraction logic, `semantic cleanup`) as LangGraph nodes with `GraphState` I/O. The internal logic of each service remains unchanged.

**Phase 2 — Supervisor + routing**: Add Supervisor node with deterministic routing rules. At this point, the system runs as a graph but follows the same sequence as classic mode.

**Phase 3 — New agents**: Add ValidationAgent, RefinerAgent, CoverageAgent, GroundingAgent as new nodes. Enable conditional routing so the Supervisor can invoke them based on state.

**Phase 4 — Parallel execution**: Enable fan-out for verification agents and chunk-level parallelism for extraction.

**Phase 5 — Extended agents**: Add ConflictResolutionAgent, TranslationQAAgent, SchemaEvolutionAgent, MetaReviewAgent as opt-in nodes.

### 10.2 Coexistence

Both modes coexist permanently:

```yaml
pipeline:
  mode: "classic"  # or "multi_agent"
```

The classic mode is never removed. It serves as:
- Fallback for production stability
- Baseline for A/B quality comparison
- Cost reference (multi-agent should show clear quality improvement to justify any additional token spend)

### 10.3 Backend Module Changes

New modules to add:

```
backend/
  agents/
    base_agent.py          # Abstract agent interface
    scoping_agent.py       # Wraps cutplan_service
    ontology_agent.py      # Wraps ontology_pipeline
    extraction_agent.py    # Wraps extraction logic
    validation_agent.py    # New
    refiner_agent.py       # New
    coverage_agent.py      # New
    grounding_agent.py     # New
    conflict_agent.py      # New
    translation_qa.py      # New (optional)
    schema_evolution.py    # New (optional)
    meta_review.py         # New (optional)
  graph/
    state.py               # GraphState definition
    supervisor.py          # Supervisor logic + routing rules
    graph_builder.py       # LangGraph graph construction
    checkpointer.py        # Optional persistence
  routers/
    multi_agent.py         # New API endpoints
```

Existing modules in `backend/services/` remain untouched. Agent wrappers import and delegate to them.

---

## 11. Auditability Contract

Every run produces a complete audit trail accessible via `GET /multi-agent/audit/{run_id}`:

```json
{
  "run_id": "run_abc123",
  "pdf_id": "manual_xyz",
  "started_at": "2026-04-09T14:00:00Z",
  "completed_at": "2026-04-09T14:08:32Z",
  "phases": [
    {
      "phase": "scoping",
      "agent": "ScopingAgent",
      "started_at": "...",
      "completed_at": "...",
      "decision": "selected 42 pages from 180",
      "pages_selected": [3, 4, 5, 12, 13, ...],
      "tokens_used": 4200
    },
    {
      "phase": "validation",
      "agent": "ValidationAgent",
      "verdicts_summary": {
        "accepted": 18,
        "needs_refinement": 5,
        "needs_human": 2
      }
    },
    {
      "phase": "refinement",
      "agent": "RefinerAgent",
      "entities_refined": ["CA_003", "CA_007", "FM_002"],
      "entities_recovered": ["CA_003", "FM_002"],
      "entities_escalated": ["CA_007"]
    },
    {
      "phase": "supervisor_decision",
      "decision_type": "deterministic",
      "condition": "1 entity escalated after refinement exhaustion",
      "routed_to": "hitl_review"
    }
  ],
  "token_ledger": { "...": "..." },
  "final_verdict": {
    "total_entities": 25,
    "auto_accepted": 20,
    "refined_and_accepted": 2,
    "human_reviewed": 3,
    "rejected": 0
  }
}
```

This audit trail enables:
- Post-run quality analysis
- Agent performance comparison
- Cost attribution per agent
- Identification of systematic extraction weaknesses
- Academic benchmarking and reproducibility

---

## 12. Configuration Summary

Complete `config.yaml` additions for multi-agent mode:

```yaml
pipeline:
  mode: "multi_agent"  # or "classic"

agents:
  scoping:
    enabled: true
    model: "gpt-5.4-nano"
    timeout: 60
  ontology_draft:
    enabled: true
    model: "gpt-5.4"
    timeout: 120
  extraction:
    enabled: true
    model: "gpt-5.4"
    timeout: 120
  validation:
    enabled: true
    model: "gpt-5.4"
    timeout: 90
    grounding_accept_threshold: 0.8
    grounding_refine_threshold: 0.5
    check_ontology_chain: true
    check_page_attribution: true
  refiner:
    enabled: true
    model: "gpt-5.4"
    timeout: 90
    max_retries_per_entity: 2
    escalate_after_exhaustion: true
  coverage:
    enabled: true
    model: "gpt-5.4-nano"
    timeout: 60
  grounding:
    enabled: true
    model: "gpt-5.4"
    timeout: 90
  conflict_resolution:
    enabled: true
    model: "gpt-5.4"
    timeout: 60
  translation_qa:
    enabled: false
    model: "gpt-5.4-nano"
  schema_evolution:
    enabled: false
    model: "gpt-5.4"
  meta_review:
    enabled: false
    model: "gpt-5.4-nano"

supervisor:
  mode: "hybrid"  # "deterministic" | "hybrid" | "llm"
  llm_model: "gpt-5.4-nano"
  llm_timeout: 15

token_budget:
  soft_warning_threshold_usd: 2.00
  hard_escalation_threshold_usd: 10.00
  log_every_call: true

checkpointing:
  enabled: false
  backend: "sqlite"
  path: "data/checkpoints/"
  checkpoint_after: ["scoping", "ontology_draft", "extraction", "validation"]
```

---

## 13. Quality Metrics Comparison Framework

To validate that multi-agent mode justifies its complexity, each run should be measurable against these KPIs:

| KPI | Classic Baseline | Multi-Agent Target |
|-----|-----------------|-------------------|
| Grounding accuracy (% entities with score >= 0.8) | Not measured | >= 90% |
| Coverage (% selected pages with at least one extraction) | Not measured | >= 85% |
| HITL items per run | All triplets reviewed | Only flagged items |
| Token cost per accepted entity | Measured but not segmented | Segmented per agent |
| Retry waste (tokens spent on ultimately rejected entities) | High (full rerun) | Low (surgical refinement) |
| Time to final export | Measured | Measured + breakdown per agent |

The MetaReviewAgent (when enabled) can produce these comparisons automatically at run end.




# Multi-Agent Migration Plan

## Summary
- Migrate by layering a minimal `GraphState` and agent wrappers around the existing flow, not by replacing the current routers/UI/export path.
- Keep `pipeline.mode: classic` as the untouched baseline; in `multi_agent`, reuse the same sequential UI and endpoint contracts first.
- Treat the current production-critical path as non-negotiable: `load manual -> cut plan -> ontology review -> triplet review -> /generate-json -> graph editor`.

## 1. Current-State Mapping
- **ScopingAgent already exists in pieces**: deterministic selection lives in [backend/services/cutplan_service.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/cutplan_service.py); LLM scoping lives in [backend/services/llm_service.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/llm_service.py); orchestration still sits in [backend/routers/cutplan.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/cutplan.py).
- **OntologyDraftAgent mostly exists already**: [backend/services/ontology_pipeline.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/ontology_pipeline.py) already runs extract -> normalize -> semantic validate -> optional re-extract -> schema validate -> graph validate, and it already uses `langgraph`; [backend/routers/ontology.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/ontology.py) adds chunking, parallel chunk execution, merge, and persistence.
- **ExtractionAgent mostly exists already**: [backend/services/llm_service.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/llm_service.py) already does chunking, prompt execution, parsing, deterministic cleanup, page-support pruning, semantic dedup, and ID regeneration; [backend/routers/extract.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/extract.py) is just a thin wrapper plus metrics.
- **Validation/Grounding exist only implicitly**: extraction cleanup already rejects incomplete triads and unsupported corrective actions; ontology validation already exists; human triplet review in [frontend/app.js](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/frontend/app.js) is still the real validation layer.
- **Conflict resolution exists only as deterministic dedup**: ontology chunk merge in [backend/routers/ontology.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/ontology.py) and extraction merge in [backend/services/llm_service.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/llm_service.py) already collapse duplicates, but there is no explicit conflict object, contradiction handling, or escalation logic.
- **Shared state exists only as `pdf_store`**: [backend/routers/upload.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/upload.py) stores `filename`, `pdf_path`, `pages`, `page_count`, `source_type`, `source_title`, plus later `cut_plan`, `ontology_pipeline`, `run_metrics`, and `ontology_path`.
- **Token accounting exists only by stage**: [backend/services/run_metrics.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/run_metrics.py) already captures per-stage and by-model usage, but not per-agent ledger, phase history, or supervisor decisions.
- **Final export is already smarter than the architecture spec implies**: [backend/routers/generate.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/generate.py) already tries ontology draft first, then minimal fallback, semantically merges validated triplets, validates candidates, translates only at export, persists the export, and feeds the graph editor.
- **Major mismatches vs spec**:
- `pipeline.mode` exists in config/API, but the frontend does not use it and the backend does not branch on it yet.
- The code already contains `langgraph`, but only inside ontology drafting, not as an app-wide multi-agent supervisor graph.
- Orchestration for scoping and ontology lives in routers, so wrappering is not plug-and-play yet.
- Extraction does not currently consume `ontology_draft`.
- There is no `run_id`, `phase_history`, `supervisor_log`, `hitl_queue`, `coverage_map`, `grounding_results`, or checkpoint store.
- Reviewed triplet edits stay in browser state until `/generate-json`; they are not server-persisted.

## 2. Gap Analysis
- **Easy**: add a minimal `GraphState`; wrap current scoping/ontology/extraction as agent functions; backfill `pdf_store`; project existing metrics into a token ledger; keep existing endpoints/UI unchanged.
- **Medium**: extract router-owned orchestration into reusable workflow functions; persist agent phase history without changing response shapes; store selected model/config snapshot per run; add read-only status/audit endpoints.
- **Risky**: replacing the sequential UI with `/multi-agent/run`, SSE, or an Agent Dashboard; introducing automatic routing that bypasses current triplet review; adding checkpoint/resume before reviewed triplets and HITL decisions are server-side.
- **Underspecified**: entity-level verdict schema for triplets, how reviewed triplet edits re-enter `GraphState`, what exact HITL queue items look like, whether `run_id` is one-to-one with `pdf_id`, and what thresholds should trigger auto-refinement instead of operator review.

## 3. Recommended Implementation Phases
- **Phase 1: smallest viable multi-agent baseline**: add `GraphState` plus `ScopingAgent`, `OntologyDraftAgent`, and `ExtractionAgent` wrappers; keep the existing screens and existing endpoints; in `multi_agent`, those endpoints call the wrappers and persist graph state, but response bodies stay identical.
- **Phase 2: quality-improving extensions**: add a deterministic Supervisor and read-only `/multi-agent/status` and `/multi-agent/audit`; add a conservative ValidationAgent that scores/flags but does not bypass the current triplet review UI; keep export path unchanged.
- **Phase 3: optional advanced agents**: add CoverageAgent, GroundingAgent, targeted RefinerAgent, ConflictResolutionAgent, and optional checkpointing only after reviewed triplets/HITL decisions are server-persisted; dashboard/SSE belongs here, not earlier.

## 4. Exact Files/Modules To Add Or Modify
- Add [backend/services/scoping_workflow.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/scoping_workflow.py): move the current `cutplan.py` orchestration into a reusable pure workflow; dependency order `1`.
- Add [backend/services/ontology_workflow.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/ontology_workflow.py): move ontology chunk split/parallel run/merge/metrics logic out of the router; dependency order `1`.
- Add [backend/services/extraction_workflow.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/extraction_workflow.py): wrap extraction + metrics persistence in a reusable function; dependency order `1`.
- Add [backend/graph/state.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/graph/state.py): define a **reduced v1 GraphState** aligned to actual repo needs, not the full architecture-spec state; dependency order `2`.
- Add [backend/graph/store.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/graph/store.py): seed/load/update graph state inside `pdf_store[pdf_id]["graph_state"]` and keep classic keys mirrored; dependency order `3`.
- Add [backend/agents/scoping_agent.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/agents/scoping_agent.py): thin wrapper over `scoping_workflow`; dependency order `4`.
- Add [backend/agents/ontology_draft_agent.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/agents/ontology_draft_agent.py): thin wrapper over `ontology_workflow`; dependency order `4`.
- Add [backend/agents/extraction_agent.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/agents/extraction_agent.py): thin wrapper over `extraction_workflow`; dependency order `4`.
- Modify [backend/routers/upload.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/upload.py): seed `run_id`, selected model placeholders, config snapshot, and initial `graph_state`; dependency order `5`.
- Modify [backend/routers/cutplan.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/cutplan.py): delegate to workflow; branch by `pipeline.mode`; keep current response/store semantics unchanged; dependency order `6`.
- Modify [backend/routers/ontology.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/ontology.py): delegate to workflow; branch by `pipeline.mode`; persist graph state and keep current review/suggestions API unchanged; dependency order `6`.
- Modify [backend/routers/extract.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/extract.py): delegate to workflow; persist cleaned triplets and extraction chunk metadata into graph state; dependency order `6`.
- Modify [backend/routers/generate.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/generate.py): read ontology/export context from graph state first in `multi_agent`, but preserve current draft-first/minimal-fallback export logic exactly; dependency order `7`.
- Modify [backend/services/run_metrics.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/services/run_metrics.py): add a projection from existing stage metrics to a per-agent ledger view without breaking current KPI payload; dependency order `7`.
- Modify [backend/app_config.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/app_config.py) and [config.yaml](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/config.yaml): add optional `agents`/`supervisor`/`checkpointing` sections with safe defaults and keep `pipeline.mode: classic`; dependency order `8`.
- Add [backend/graph/supervisor.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/graph/supervisor.py) and [backend/routers/multi_agent.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/backend/routers/multi_agent.py) in Phase 2 only.
- Add [tests/test_multi_agent_state.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/tests/test_multi_agent_state.py) and [tests/test_multi_agent_mode_flow.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/tests/test_multi_agent_mode_flow.py); update [tests/frontend_flow.spec.js](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/tests/frontend_flow.spec.js) to run the same mocked UI flow against `classic` and `multi_agent`; fix stale expectation in [tests/test_ontology_pipeline_validation.py](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/tests/test_ontology_pipeline_validation.py).

## 5. Risks And Compatibility Concerns
- **State handling**: do not replace `pdf_store`; layer `graph_state` into it and mirror `cut_plan`, `ontology_pipeline`, `run_metrics`, and `ontology_path` so existing routers/export/editor keep working.
- **Current UI flow**: keep [frontend/app.js](/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance/frontend/app.js) screen order intact in Phase 1; `pipeline.mode=multi_agent` should still drive the same cut-plan/ontology/triplet-review screens.
- **Current tests**: backend subset currently runs as `PYTHONPATH=. python3 -m pytest`; 28 passed and 1 failed due a stale field-key expectation after wildcard deduping. Fix that before using the suite as migration protection.
- **Export compatibility**: do not alter `/generate-json` candidate ordering, minimal fallback behavior, translation timing, or graph-editor file manifest semantics.
- **Persistence/checkpointing**: keep checkpointing off until reviewed triplets and HITL decisions are server-persisted; otherwise “resume” will restart from an incomplete truth source.
- **Token accounting**: use existing stage metrics as the source for initial agent ledger entries; do not add budget-based hard stops in v1.
- **Human-in-the-loop continuity**: current triplet review remains the durable recovery path; new validation/refinement agents may flag or pre-sort, but must not remove operator access to the full reviewed set.

## 6. Definition Of Done
- **Phase 1**:
- Code: `GraphState` exists; three core wrappers exist; existing routers branch on `pipeline.mode`; classic logic remains functionally identical.
- Tests: current classic regressions still pass; new tests prove `multi_agent` returns the same response shapes for `/cut-plan`, `/ontology/draft`, `/extract-tables`, and `/generate-json`.
- API behavior: no frontend-breaking changes; existing endpoints remain the operator path in both modes.
- UI behavior: current browser flow still reaches automatic JSON download and graph editor.
- **Phase 2**:
- Code: Supervisor exists as deterministic routing/audit logic; ValidationAgent produces non-blocking verdicts/flags; status/audit endpoints are read-only and optional.
- Tests: verdict routing, phase history, and token ledger are covered; classic behavior unchanged.
- API behavior: new `/multi-agent/status` and `/multi-agent/audit` are additive only.
- UI behavior: sequential review flow still works; any new status view is informational, not required.
- **Phase 3**:
- Code: advanced agents are behind feature flags; checkpointing only ships with persisted review state.
- Tests: disabled agents are a no-op; enabled-agent fan-out/merge paths are covered.
- API behavior: dashboard/SSE/resume are opt-in and do not replace existing endpoints.
- UI behavior: classic sequential UI remains available even if dashboard mode is added.

## 7. Final Recommendation
- Implement first: Phase 1 only. The right v1 is **GraphState + wrappers + router refactor**, not a new dashboard and not a new autonomous run API.
- Postpone: `/multi-agent/run`, SSE/WebSocket streaming, event-driven HITL queues, checkpoint resume, Coverage/Grounding/Conflict agents, and any routing that reduces operator visibility before the current review flow is server-persisted.
- Remove or simplify from the architecture spec for v1:
- Drop `base_agent.py`; plain typed functions are enough.
- Do not implement the full spec `GraphState` up front; start with the fields the repo actually uses.
- Do not split `ValidationAgent` and `GroundingAgent` in v1; one conservative validation pass is enough.
- Do not add `ConflictResolutionAgent`, `TranslationQAAgent`, `SchemaEvolutionAgent`, or `MetaReviewAgent` in the first delivery.

## Phased Roadmap
- **Roadmap**: Phase 1 backend-only wrapper migration; Phase 2 deterministic supervisor plus read-only observability; Phase 3 optional advanced agents and only then optional new UI/dashboard.

## Dependency-Ordered Task List
1. Extract router-owned scoping/ontology/extraction orchestration into shared workflow modules.
2. Add minimal `GraphState` and a `pdf_store` bridge/store.
3. Add three core agent wrappers around the shared workflows.
4. Seed `run_id`, config snapshot, and graph state at manual load.
5. Branch existing routers on `pipeline.mode`, keeping classic responses identical.
6. Project current stage metrics into a per-agent ledger and phase history.
7. Add multi-agent regression tests; fix the stale wildcard-field backend test.
8. Add Supervisor plus read-only status/audit endpoints.
9. Add conservative validation flags only after the sequential flow is stable.
10. Defer advanced agents, checkpointing, and dashboard/SSE until reviewed triplets are persisted server-side.

## Realistic Effort Estimate
- **Phase 1**: 6-8 engineer days.
- **Phase 2**: 4-6 engineer days.
- **Phase 3**: 8-15 engineer days, depending on whether dashboard/SSE and checkpoint resume are included.
- **Total for safe v1 + quality layer**: about 2.5-3 weeks for one engineer.
- **Full spec including dashboard/resume/advanced agents**: more realistically 4-6 weeks, and it should not be the first migration target.
