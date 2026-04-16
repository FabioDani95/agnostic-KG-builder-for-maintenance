# Technical Architecture Reference — Agnostic KG Builder for Maintenance
> Source material for APMS 2026 paper. Architecture & implementation details only — results/benchmarks to be added separately.
> Document role: primary technical reference for the architecture currently implemented in the repo.
> For product flow details, use [specification.md](specification.md). For future work and open stability gaps, use [roadmap_agentic.md](roadmap_agentic.md).

---

## 1. System Overview

The system is a **neurosymbolic, agentic knowledge graph extraction pipeline** that converts unstructured technical maintenance manuals (PDF) into structured diagnostic ontologies. The output targets maintenance knowledge graphs linking symptoms, failure modes, corrective actions, components, and error codes.

**Key design decisions:**
- Domain-agnostic schema driven by a pluggable `ontology_schema.JSON`
- Multi-agent architecture with deterministic supervisor routing
- Adaptive HITL: schema-aware confidence scoring determines which nodes require human review
- Reflective loop for self-correction (semantic validation → re-extraction with feedback)
- Advisory-only validation agents (no blocking without Phase 2 policy)

---

## 2. Overall Pipeline

### 2.1 High-Level Data Flow

```
PDF Upload
    ↓
[ScopingAgent]   → CutPlan (selected pages) → Operator Review
    ↓
[OntologyDraftAgent]  → Ontology draft (nodes + relations) → Operator Review
    ↓
[ExtractionAgent]  → Triplets (Symptom → FailureMode → CorrectiveAction)
    ↓
[Advisory Agents — optional, parallel]
    ├─ ValidationAgent    (grounding-based verdict: accepted / needs_refinement / needs_human)
    ├─ CoverageAgent      (page-level gap detection)
    ├─ GroundingAgent     (entity text-to-source matching)
    ├─ ConflictResolutionAgent (duplicate / contradiction detection)
    └─ RefinerAgent       (targeted fixes for flagged entities)
    ↓
Operator Final Review → Export JSON
```

### 2.2 Execution Modes

| Mode | Description |
|------|-------------|
| `classic` | Linear workflow, no agent overhead, no graph state |
| `multi_agent` | Requests routed through agent wrappers; full graph state tracking; supervisor audit log |

Current default: `multi_agent`.

### 2.3 Ontology Schema

Six node types and six relation types are defined in `ontology_schema.JSON`:

| Node Types | Relation Types |
|------------|---------------|
| Asset | HAS_COMPONENT |
| Component | AFFECTS |
| Symptom | MAY_INDICATE |
| FailureMode | RESOLVED_BY |
| CorrectiveAction | GENERATES_ERROR |
| ErrorCode | INDICATES |

The schema defines required properties per node type. The confidence scoring and graph reasoning layers consume the schema at runtime — adding a new node type requires no code change.

---

## 3. Multi-Agent Architecture

### 3.1 Agent Definitions

Core pipeline agents are thin wrappers over workflow functions. Advisory agents contain more local logic, but all run state still lives in `GraphState` and is persisted via `persist_graph_state()` on every state-changing operation.

| Agent | File | Role | Implementation |
|-------|------|------|----------------|
| ScopingAgent | `backend/agents/scoping_agent.py` | Page selection (ML + rule-based ToC/keyword merge) | Calls `create_cut_plan_workflow()` |
| OntologyDraftAgent | `backend/agents/ontology_draft_agent.py` | Multi-chunk ontology extraction (nodes + relations + evidence) | Calls `draft_ontology_workflow()` |
| ExtractionAgent | `backend/agents/extraction_agent.py` | Triplet extraction (Symptom→FailureMode→CorrectiveAction) | Calls `extract_triplets_workflow()` |
| ValidationAgent | `backend/agents/validation_agent.py` | Advisory grounding-based verdict scoring per entity | Core logic in agent file (331 lines) |
| RefinerAgent | `backend/agents/refiner_agent.py` | Targeted text segment substitution for flagged entities | Core logic in agent file (261 lines) |
| CoverageAgent | `backend/agents/coverage_agent.py` | Page-level gap analysis | Core logic in agent file (145 lines) |
| GroundingAgent | `backend/agents/grounding_agent.py` | Entity fragment matching against source pages | Core logic in agent file (353 lines) |
| ConflictResolutionAgent | `backend/agents/conflict_resolution_agent.py` | Duplicate/contradiction detection via semantic matching | Core logic in agent file (165 lines) |

### 3.2 Graph State

Defined in `backend/graph/state.py`. Single `GraphState` TypedDict shared across all agents for a given run.

**Phase enum (`GraphPhase`):**
```
LOADED → SCOPING → ONTOLOGY_DRAFT → EXTRACTION → VALIDATION →
COVERAGE → GROUNDING → CONFLICT_RESOLUTION → REFINEMENT → EXPORT → COMPLETED
```

**Key fields:**
```python
# Lifecycle
pdf_id, run_id, current_phase, run_status, next_step
started_at, updated_at, completed_at, phase_history

# Source metadata
filename, total_pages, source_type, source_title, source_language

# Scoping outputs
selected_pages, cut_plan, scoping_metadata

# Ontology outputs
ontology_pipeline, ontology_draft, ontology_issues, human_required_fields
suggested_relations, schema_compliant

# Extraction outputs
raw_triplets, cleaned_triplets, extraction_chunks, entity_verdicts

# Advisory agent outputs
validation_summary, coverage_map, grounding_results, conflicts

# Refinement tracking
refinement_attempts, refinement_log, supervisor_log

# Export & metrics
export_base, final_json, token_ledger, config_snapshot, selected_models
```

**Phase history entries:**
```python
{phase, agent, timestamp, decision, tokens_used, llm_calls, details}
```

### 3.3 Supervisor

**File**: `backend/graph/supervisor.py`

The supervisor implements **deterministic routing** (no LLM decisions in Phase 1). Each transition emits a structured `SupervisorLog` entry.

**Routing table:**

| From | To | Condition |
|------|----|-----------|
| SCOPING | cut_plan_review | Always |
| cut_plan_review | ONTOLOGY_DRAFT | Operator approved pages |
| ONTOLOGY_DRAFT | ontology_review | Always |
| ontology_review | EXTRACTION | Ontology reviewed |
| EXTRACTION | VALIDATION or triplet_review | `validation.enabled` flag |
| VALIDATION | COVERAGE / GROUNDING / CONFLICT / triplet_review | Advisory flags |
| COVERAGE | next advisory agent or triplet_review | Advisory flags |
| GROUNDING | next advisory agent or triplet_review | Advisory flags |
| CONFLICT_RESOLUTION | triplet_review | Always |
| REFINEMENT | VALIDATION | After targeted fixes |
| EXPORT | COMPLETED | Always |

**Supervisor log entry structure:**
```python
{
  timestamp, run_id,
  phase_from, phase_to,
  decision_type: "deterministic",
  condition_met: bool,
  reasoning: str,
  state_snapshot_hash: str,
  next_agent: str,
  token_budget_used_this_phase: int,
  validation_summary: dict
}
```

Accessible via REST:
```
GET /multi-agent/audit/{run_id}
GET /multi-agent/status/{run_id}
```

---

## 4. Ontology Extraction Pipeline (LangGraph Reflective Loop)

**File**: `backend/services/ontology_pipeline.py`

The ontology extraction is a **LangGraph state machine** implementing a reflective loop with self-correction.

### 4.1 LangGraph Node Graph

```
extract
  ↓
normalize
  ↓
semantic_validate ──[issues found AND retries < max_retries]──→ re_extract (with feedback)
                  └──[issues found AND retries >= max_retries]──→ needs_human_review flag
                  └──[no issues OR only warnings]──────────────→ schema_validate
                                                                      ↓
                                                               graph_validate
                                                                      ↓
                                                              confidence_score
                                                                      ↓
                                                                     END
```

### 4.2 Pipeline State

```python
class PipelineState(TypedDict):
    # Extraction outputs
    ontology: OntologyInstance
    raw_json: dict
    
    # Reflective loop control
    retry_count: int
    last_issues: list[PipelineIssue]   # {severity, code, message, target_type, target_id, fix_hint}
    needs_human_review: bool
    
    # Downstream outputs
    schema_issues: list
    graph_issues: list
    confidence_report: ConfidenceReport
```

### 4.3 Node Descriptions

| Node | Role |
|------|------|
| `extract` | LLM extraction: 6 node types + 6 relations + evidence required on every relation |
| `normalize` | Dedupe, fill Asset node, infer HAS_COMPONENT, infer AFFECTS |
| `semantic_validate` | Check semantic integrity: inconsistent relations, missing chains, orphan nodes |
| `re_extract` | Re-extraction with issue feedback (reflective correction) |
| `schema_validate` | Check schema compliance, required properties present and non-empty |
| `graph_validate` | NetworkX analysis: chain gaps, orphan detection, cycle detection, missing relation suggestions |
| `confidence_score` | Assign confidence scores to each node (5 signals + 2 penalties) |

### 4.4 Multi-Chunk Orchestration

**File**: `backend/services/ontology_workflow.py`

For documents exceeding the chunk size threshold:

1. Selected pages split into chunks (default: 30 pages/chunk, configurable)
2. Each chunk runs the full LangGraph pipeline independently
3. **Merge step**: Deduplicate by ID or normalized name; keep richest version; merge relations with ID remapping; re-score confidence on merged ontology

---

## 5. Reflective Loop (Self-Correction)

### 5.1 Trigger Conditions

The reflective loop triggers when `semantic_validate` finds issues at or above the configured severity threshold.

**Configuration** (`config.yaml`):
```yaml
reflective_loop:
  max_retries: 2
  retry_on_severity: "error"   # Trigger on "error" only (not "warning")
  re_extract_max_output_tokens: 14000
```

**Issue severity levels**: `warning` → `error` → `critical`

### 5.2 Re-Extraction Prompt

The `re_extract` node calls `RE_EXTRACTION_PROMPT_TEMPLATE` which includes:
- Full list of detected issues with `fix_hint` per issue
- Instruction to keep all correct nodes and relations unchanged
- Same evidence requirements as the base extraction prompt

**File**: `backend/prompts/ontology_prompt.py`

### 5.3 Known Limitation

The re-extraction prompt is looser than the base extraction prompt. In adversarial conditions (many issues + high retry count), re-extraction can catastrophically regress (collapse to a minimal ontology). 

**Current workaround**: for conservative runs, override `reflective_loop.max_retries` to `0` at runtime and use the linear baseline. The checked-in config currently keeps `max_retries: 2`, so stable benchmarking depends on whether retries are actively used.

---

## 6. Confidence Scoring

**File**: `backend/services/confidence.py`

### 6.1 Five Scoring Signals

All signals are normalized to [0.0, 1.0]. Weights sum to 1.0.

| Signal | Default Weight | Computation |
|--------|---------------|-------------|
| `evidence_present` | 0.25 | 1.0 if node has `source_page`, else 0.0 |
| `corroboration` | 0.15 | Saturating function of distinct source pages: 1 page → 0.50, 2 → 0.83, 3+ → 1.0 |
| `required_props_complete` | 0.25 | Fraction of schema-required properties present and non-empty |
| `chain_participation` | 0.20 | Fraction of schema-expected relations actually present on this node |
| `clean_extraction` | 0.15 | 1.0 (no retries, no issues) / 0.5 (retries but node not targeted) / 0.0 (node was direct retry target) |

### 6.2 Two Penalties

| Penalty | Default Value | Trigger |
|---------|--------------|---------|
| `human_binding_required` | −0.20 | Node has unresolved `HumanRequiredField` binding |
| `per_retry` | −0.02 per retry, capped at 3× | Node was involved in a retry cycle |

### 6.3 Classification Thresholds

```
score ≥ θ_high (0.80)   → auto_approve
θ_low (0.45) ≤ score < θ_high   → human_review
score < θ_low (0.45)   → auto_reject (disabled by default)
```

`auto_reject_enabled: false` by default — nodes below θ_low are sent to human review rather than discarded.

### 6.4 Evidence Propagation (Soluzione B)

Relations carry `source_page` evidence fields. Nodes without their own evidence inherit pages from incident relations at **0.5 weight**:

```python
# backend/services/confidence.py — _build_relation_page_index()
# A node appearing in a relation citing page P inherits P as weak provenance
node_page_index[node_id] = {page: 0.5 * weight for page in relation.source_pages}
```

This decouples node evidence completeness from the quality of the relation evidence, enabling high auto-approve rates even when nodes lack standalone `source_page` annotations.

### 6.5 Schema-Driven Design

The `_required_property_names()` and `_expected_relations_for_type()` functions read from the live `OntologySchemaDefinition` at runtime. Adding a new node type to `ontology_schema.JSON` requires zero code change in the confidence layer.

### 6.6 Confidence Entry Structure

```python
class ConfidenceEntry:
    node_type: str
    node_id: str
    score: float            # Final score ∈ [0.0, 1.0]
    classification: str     # "auto_approve" | "human_review" | "auto_reject"
    signals: dict           # {signal_name → value}
    penalties: dict         # {penalty_name → value}
    reasons: list[str]      # Human-readable explanation of low scores
```

---

## 7. Graph Reasoning

**File**: `backend/services/graph_reasoning.py`

Uses **NetworkX** for structural analysis of the extracted ontology graph.

### 7.1 Analyses Performed

| Analysis | Description |
|----------|-------------|
| Chain gap detection | Checks Symptom → MAY_INDICATE → FailureMode → RESOLVED_BY → CorrectiveAction chains for breaks |
| Orphan detection | Nodes with no incident relations |
| Cycle detection | Circular dependencies in the directed graph |
| Missing relation suggestions | Similarity-based suggestions for likely missing links between nodes |

### 7.2 Graph Issue Structure

```python
class GraphIssue:
    severity: str       # "warning" | "error" | "critical"
    code: str           # e.g., "chain_gap", "orphan_node", "cycle_detected"
    message: str
    target_type: str    # Node type affected
    target_id: str
    fix_hint: str       # Suggested repair
```

### 7.3 Suggested Relations

The `graph_reasoning` service generates candidate relations between nodes with high semantic similarity but no existing link. These are surfaced in `suggested_relations` (operator can accept/reject in the ontology review step).

---

## 8. Scoping Pipeline

**File**: `backend/services/scoping_workflow.py`

### 8.1 Stages

1. **Keyword scan**: 15+ maintenance-domain keywords (maintenance, diagnostic, fault, error, alarm, troubleshooting, repair, …)
2. **ToC detection**: Regex + heuristics on first 12 pages
3. **Rule-based section scoring**: Boosts troubleshooting/repair sections; suppresses safety/copyright sections
4. **LLM section selection**: GPT-5.4-nano merges LLM + rule-based + keyword section scores
5. **Output**: `CutPlanResponse` with `pages_to_keep`, `sections[]`, `product_info`

### 8.2 Configuration

```yaml
scoping:
  small_doc_threshold: 15   # Skip cut plan for docs with fewer pages
```

---

## 9. Advisory Validation Agents

All advisory agents are `advisory_only: true` — they flag issues but do not block export. The operator sees flagged verdicts and decides.

### 9.1 ValidationAgent (`backend/agents/validation_agent.py`)

Assigns verdicts per entity: `ACCEPTED` / `NEEDS_REFINEMENT` / `NEEDS_HUMAN`

- Computes grounding score: entity text fragment matched against source page text
- Accept threshold: `validation.grounding_accept_threshold: 0.8` (configurable)
- Flags entities below threshold for refinement or human review

### 9.2 CoverageAgent (`backend/agents/coverage_agent.py`)

Page-level gap map: `fully_covered` / `partially_covered` / `missing_extraction`

- Identifies selected pages with no extracted entities referencing them
- Output: `coverage_map: {page_number → coverage_status}`

### 9.3 GroundingAgent (`backend/agents/grounding_agent.py`)

Entity text-to-source matching:
- Extracts entity name/description fragments
- Matches against source page text using semantic similarity
- Returns per-entity grounding scores

### 9.4 ConflictResolutionAgent (`backend/agents/conflict_resolution_agent.py`)

Duplicate/contradiction detection via semantic matching:
- Clusters nodes of the same type by name similarity
- Flags clusters with conflicting properties or descriptions
- Output: `conflicts: [{node_ids, conflict_type, suggested_merge}]`

### 9.5 RefinerAgent (`backend/agents/refiner_agent.py`)

Targeted text segment substitution for entities flagged `NEEDS_REFINEMENT`:
- Retrieves original source text for the entity's `source_page`
- Applies LLM refinement constrained to the source segment
- Updates entity in ontology; re-runs ValidationAgent

---

## 10. HITL Design

### 10.1 Current HITL Checkpoints (Phase 1)

| Checkpoint | What operator does |
|------------|-------------------|
| Cut Plan Review | Approve/edit selected pages before extraction |
| Ontology Review | Fill `HumanRequiredField` bindings; accept/reject suggested relations |
| Triplet Review | Validate extracted symptom→failure→action chains |
| Final Export | Download JSON or re-run |

### 10.2 Human-Required Fields

Some node properties cannot be auto-extracted (e.g., asset serial number format, maintenance interval). These are surfaced as `HumanRequiredField` entries:

```python
class HumanRequiredField:
    node_type: str
    node_id: str
    field_name: str
    reason: str
    suggested_value: str | None
```

Unresolved bindings incur a `−0.20` confidence penalty.

### 10.3 Phase 2 Escalation Design (Not Yet Implemented)

Planned `EscalationMessage` structure:
```json
{
  "escalation_id": "...",
  "phase": "ONTOLOGY_DRAFT",
  "agent": "OntologyDraftAgent",
  "issue": "...",
  "options": ["approve_as_is", "reject", "provide_correction", "skip"],
  "context": {
    "node_type": "Symptom",
    "node_id": "...",
    "score": 0.42,
    "suggested_relation": "..."
  }
}
```

Planned supervisor policy (Phase 2):
```
if all nodes ≥ θ_high AND no critical graph_issues:
    → advance or END
elif retry_count < max_retries AND issues are "error" severity:
    → route to RefinerAgent
elif any node < θ_low OR unresolvable graph_issues:
    → emit EscalationMessage → HITL pause (blocking)
else:
    → advance (warnings tolerated)
```

---

## 11. Prompts & Evidence

**File**: `backend/prompts/ontology_prompt.py`

### 11.1 Base Extraction Prompt (`EXTRACTION_PROMPT_TEMPLATE`)

- Defines all 6 node types with property contracts
- Defines all 6 relation types
- **Requires evidence on every relation** (mandatory constraint):
  ```
  evidence shape: {source_page: int, source_reference: "PAGE N", quote: str}
  Use page markers ("--- PAGE N ---") from text
  ```
- Output: JSON with `nodes[]` and `relations[]`

### 11.2 Re-Extraction Prompt (`RE_EXTRACTION_PROMPT_TEMPLATE`)

- Same evidence requirements as base
- Receives `issues[]` with `fix_hint` per issue
- Instructions: fix flagged issues, keep all correct entities unchanged

### 11.3 Relation-Only Second Pass (`RELATION_EXTRACTION_PROMPT_TEMPLATE`)

Used when nodes are extracted but relations are incomplete:
- Input: already-extracted nodes + source text
- Output: relations only (no new nodes)

---

## 12. Key Configuration Parameters

**File**: `config.yaml`

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `pipeline.mode` | `multi_agent` | Routing mode |
| `agents.*.enabled` | varies | Enable/disable per agent |
| `agents.*.model` | `gpt-5.4` or `gpt-5.4-nano` | LLM per agent |
| `agents.*.timeout` | 60–120s | Per-agent timeout |
| `ontology.max_pages_per_chunk` | 30 | Multi-chunk page budget |
| `ontology.always_include_first_pages` | 5 | Leading pages always included |
| `ontology.extraction_max_output_tokens` | 20000 | Base extraction output budget |
| `ontology.extraction_retry_max_output_tokens` | 24000 | Re-extraction output budget |
| `reflective_loop.max_retries` | 2 | Max self-correction attempts |
| `reflective_loop.retry_on_severity` | `"error"` | Trigger severity threshold |
| `reflective_loop.re_extract_max_output_tokens` | 14000 | Re-extraction token limit |
| `confidence.enabled` | `true` | Enable/disable scoring layer |
| `confidence.theta_high` | 0.80 | Auto-approve threshold |
| `confidence.theta_low` | 0.45 | Auto-reject threshold |
| `confidence.auto_reject_enabled` | `false` | Auto-rejection (disabled for safety) |
| `scoping.small_doc_threshold` | 15 | Skip scoping for small docs |
| `validation.grounding_accept_threshold` | 0.8 | ValidationAgent accept threshold |
| `supervisor.mode` | `"deterministic"` | Supervisor policy |

---

## 13. File Map

### Backend Core

| Path | Role |
|------|------|
| `backend/main.py` | FastAPI app, route registration |
| `backend/models.py` | All Pydantic models (GraphState, Ontology*, Confidence*, GraphIssue) |
| `backend/config.py` | Environment variables (OPENAI_API_KEY, MODEL_NAME) |
| `backend/app_config.py` | Config loaders from `config.yaml` |

### Graph State & Supervisor

| Path | Role |
|------|------|
| `backend/graph/state.py` | `GraphPhase` enum, `GraphState` TypedDict, initialization |
| `backend/graph/supervisor.py` | Deterministic routing logic, audit log generation |
| `backend/graph/store.py` | GraphState persistence, state sync, phase transitions |

### Services

| Path | Role |
|------|------|
| `backend/services/confidence.py` | Confidence scoring: 5 signals + 2 penalties, classification |
| `backend/services/ontology_pipeline.py` | LangGraph reflective loop |
| `backend/services/ontology_workflow.py` | Multi-chunk orchestration, merge logic |
| `backend/services/extraction_workflow.py` | Triplet extraction pipeline |
| `backend/services/scoping_workflow.py` | CutPlan generation |
| `backend/services/graph_reasoning.py` | NetworkX graph analysis |
| `backend/services/ontology_semantics.py` | Semantic matching, text normalization |
| `backend/services/llm_service.py` | LLM calls, prompt engineering, evidence extraction |
| `backend/services/run_metrics.py` | Token usage tracking, cost estimation, stage timing |

### Routers

| Path | Endpoints |
|------|-----------|
| `backend/routers/multi_agent.py` | `/multi-agent/status/{run_id}`, `/multi-agent/audit/{run_id}` |
| `backend/routers/ontology.py` | `/ontology/draft`, `/ontology/review`, `/ontology/apply-suggestions` |
| `backend/routers/extract.py` | `/extract/triplets` |
| `backend/routers/cutplan.py` | `/cutplan/draft`, `/cutplan/approve` |
| `backend/routers/upload.py` | `/upload` |
| `backend/routers/generate.py` | `/generate/json` |

### Data & Config

| Path | Role |
|------|------|
| `config.yaml` | Master configuration |
| `ontology_schema.JSON` | Schema: 6 node types, 6 relations, required properties |
| `multi_agent_architecture.md` | Architecture design doc |
| `roadmap_agentic.md` | Implementation roadmap with benchmark results |
| `specification.md` | Product specification |

---

## 14. Observability

### REST API

```
GET /multi-agent/status/{run_id}   → current phase, run_status, next_step
GET /multi-agent/audit/{run_id}    → full supervisor log (all phase transitions)
```

### Token Ledger

Tracked per-agent and per-stage in `run_metrics.py`. `token_ledger` in `GraphState` projects cumulative usage.

### Phase History

Every state-changing operation appends to `phase_history`:
```python
{phase, agent, timestamp, decision, tokens_used, llm_calls, details}
```

---

## 15. Implementation Status

| Component | Status |
|-----------|--------|
| Agent wrappers (Phase 1) | Stable |
| Supervisor deterministic routing | Stable |
| Confidence scoring (backend) | Stable |
| Graph reasoning | Stable |
| Multi-agent observability | Stable |
| Reflective loop | Wired; destructive retry bug — disabled in production |
| Supervisor policy / escalations (Phase 2) | Not implemented |
| Frontend HITL integration (Phase 3) | Not implemented |
