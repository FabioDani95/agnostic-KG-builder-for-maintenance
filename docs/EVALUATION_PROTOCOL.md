# Evaluation Protocol for the Maintenance KG Builder

**Status:** normative — this document defines *the* procedure for measuring
extraction quality. Any performance number quoted in a report or the README
must be traceable to a run produced by this protocol.

**Audience:** developers adding golden fixtures, interpreting eval reports, or
reproducing a model/config comparison.

---

## 1. What is being measured

The system ingests a maintenance manual and produces a knowledge graph of
diagnostic knowledge: `Symptom → FailureMode → CorrectiveAction` chains,
optionally rooted in an `ErrorCode` (`ErrorCode -INDICATES-> FailureMode
-RESOLVED_BY-> CorrectiveAction`). The evaluation measures, per manual:

1. **Scoping quality** — did the pipeline keep the diagnostic pages?
2. **Extraction recall** — did it recover the annotated diagnostic chains?
3. **Extraction precision / hallucination** — is everything it produced
   supported by the source text?
4. **Contamination** — did it avoid specific known-wrong chain merges?
5. **Structural quality** — schema compliance, required relation types,
   minimum node counts.
6. **Human-in-the-loop load** — how much review the output demands.
7. **Efficiency** — wall time, tokens, and cost per run.

The unit of evaluation is the **golden fixture**: a compact manual (markdown)
plus a hand-annotated expected output (JSON). The harness is
[scripts/eval_golden.py](../scripts/eval_golden.py); fixtures live in
[tests/golden/](../tests/golden/).

## 2. Test architecture (where golden eval sits)

| Layer | What it checks | Tooling | LLM | When it runs |
|---|---|---|---|---|
| Unit / contract | services, schemas, matching rules | `pytest tests/` | mocked | every change |
| Integration | in-process pipeline flows, run store, routers | `pytest tests/` | `KG_LLM_MODE=mock` | every change |
| E2E UI | frontend flows, widgets, console | `npx playwright test` | mock backend | before release |
| **Quality (this protocol)** | **extraction quality KPIs on golden fixtures** | `scripts/eval_golden.py` | mock (CI gate) / real (measurement) | mock: every change · real: on demand |

The three layers above the line answer "is the code broken?". The golden eval
answers "is the *output* good?" — a different question that unit tests cannot
answer, because real-model quality varies run to run.

Exploratory runners (`scripts/run_manual_benchmark.py`,
`scripts/run_batch_export.py`, `scripts/live_chat_benchmark.py`) produce useful
telemetry (`benchmark_runs/`, `batch_runs/`) but **no pass/fail quality
verdict**; do not quote their numbers as performance results. See
[tests/README.md](../tests/README.md).

## 3. Golden fixture anatomy

A fixture `<fixture_id>` consists of exactly three parts:

```
tests/golden/manuals/<fixture_id>.md            # the manual (page-structured markdown)
tests/golden/expected/<fixture_id>.json         # the annotation (expected output + gates)
tests/golden/mock_responses/<fixture_id>/*.json # canned LLM replies for deterministic CI runs
```

### 3.1 The manual (`manuals/<fixture_id>.md`)

Markdown that `backend/services/manual_loader.py` splits into pseudo-pages:

- Header block with `Document type:`, `Language:`, `Asset:` metadata lines.
- Each `## Page N - <title>` heading starts page N. Content before the first
  such heading is page 1.
- For **real-manual fixtures**, pages are verbatim (lightly reflowed) text of
  the source PDF's diagnostic pages, keeping the original page numbers, plus
  cover/index pages so scoping has something to cut. Include *distractor*
  pages (preventive maintenance, installation) when the source has them —
  scoping must earn its keep.
- For **synthetic fixtures**, keep them short: they exist for cheap smoke
  coverage of one specific difficulty (ambiguity, noisy tables, …).

### 3.2 The annotation (`expected/<fixture_id>.json`)

Schema by example (all keys shown; optional blocks marked):

```jsonc
{
  "fixture_id": "haier_lma4120_washer_manual",
  "manual": "manuals/haier_lma4120_washer_manual.md",
  "asset": { "name": "...", "type": "washing machine" },

  "expected_scoping": {
    "diagnostic_sections": ["Trouble Alarm And Solve Method", "..."],
    "must_keep_pages": [16, 18, 19]        // pages scoping MUST keep
  },

  // Sample of atomic diagnostic chains. NOT exhaustive: recall is measured
  // against this sample; extra valid chains are not punished (see §4.3).
  "expected_triplets": [
    { "error_code": "E1",                   // optional; token-exact match
      "symptom": "machine does not drain or drains slowly",
      "failure_mode": "drain hose blocked",
      "corrective_action": "remove the blockage" },
    { "error_code": "E4",                   // error-code-rooted: no symptom,
      "failure_mode": "water inlet valve blocked",   // matched on the graph
      "corrective_action": "clean the water inlet valve" }
  ],

  // Precision tool: chains that must NEVER appear (known contamination,
  // e.g. a cause merged in from an adjacent table row). Optional.
  "forbidden_chains": [
    { "symptom": "No draining", "failure_mode": "machine not level" }
  ],

  // Absolute quality floors for real-model runs. Optional but required for
  // real-manual fixtures (see §6 two-phase calibration).
  "expected_quality_gates": {
    "min_recall": 0.75,
    "max_unsupported_rate": 0.0
  },

  // Review-queue bounds. Granular bounds preferred over {"required": bool}:
  // multi-cause symptoms legitimately produce advisory items.
  "expected_human_review": { "max_blocking": 0, "reason": "..." },

  "expected_export_checks": {
    "min_symptoms": 4, "min_failure_modes": 4,
    "min_corrective_actions": 4, "min_error_codes": 2,
    "required_relations": ["GENERATES_ERROR", "HAS_FAILURE_MODE", "HAS_CORRECTIVE_ACTION"]
  }
}
```

**Annotation rules** (these keep annotations comparable across fixtures):

1. One expected item = one **atomic chain** (one symptom, one failure mode,
   one corrective action) — never a merged multi-cause blob.
2. Phrase fields in the manual's own words (matching is normalized and
   token-based, but paraphrase drift lowers match reliability).
3. Model alarm codes as `error_code`, not as a symptom string like
   "display shows E4" — that would contradict the ontology's
   `ErrorCode/INDICATES` design.
4. The sample should cover: at least one error-code-rooted chain (if the
   manual has codes), at least one prose/flowchart chain, and the chains a
   domain expert would call the most safety- or downtime-critical.
5. Every expected chain must be verifiable by pointing at a specific line of
   the manual. If you cannot quote the evidence, do not annotate the chain.
6. `forbidden_chains` are added only for contamination actually observed in a
   run or plausibly induced by layout (adjacent table rows, shared columns) —
   they are regression tripwires, not an exhaustive negative set.
7. **Inspection-only steps are not corrective actions.** When the manual gives
   a cause plus check/verify steps and no restorative remedy (typical of
   error-code tables), annotate the chain with the manual's causal text
   (e.g. the *Causes* column) and **omit** `corrective_action`: the truthful
   graph is `ErrorCode → FailureMode` with a declared
   `failure_mode_without_action` gap. Annotating a check step as a remedy
   measures behaviour the restorative-action contract is designed to reject
   and makes recall oscillate on semantics, not extraction. (Decision taken
   for the Whirlpool fixture on 2026-07-14; see
   `WHIRLPOOL_W11187658_GOLDEN_EVAL.md`, Phase B complete.)

### 3.3 Mock responses (`mock_responses/<fixture_id>/<stage>.json`)

Deterministic LLM replies returned by the mock gateway
(`KG_LLM_MODE=mock`, `KG_LLM_FIXTURE=<fixture_id>` — set automatically by the
harness). Stage names: `scoping`, `sections`, `extraction`, `ontology`,
`relations`, `validation`, `node_normalization`, `resolution`. These make the
mock eval exercise the fixture's real diagnostic content, so the CI gate has
a deterministic recall-1.0 baseline. They are mock *responses*, not new
golden data.

## 4. Metrics — formal definitions

All matching operates on **atomic chains**. Projected triplets are exploded
into chains via `linked_failure_mode_id` (a wrong FM→CA pairing is therefore
a miss, not a partial credit). Error-code-rooted expectations are additionally
matched against graph chains `ErrorCode -INDICATES-> FM -RESOLVED_BY-> CA`,
independent of how the projection groups symptoms.

### 4.1 Matching rules

| Rule | Used for | Definition |
|---|---|---|
| soft match | symptom, failure_mode, corrective_action of expected chains | normalized (lowercase, alphanumeric) substring containment either way, **or** ≥ 0.6 token overlap of the expected tokens; empty actual never matches non-empty expected |
| code match | `error_code` | token-exact subset ("E1" ≠ "E17"); empty actual never matches |
| strict match | `forbidden_chains` | normalized substring containment only (no token-overlap fallback — stopword overlap must not create false violations) |

### 4.2 Recall

`recall = matched expected chains / expected chains` — per fixture, against
the annotated sample. Since the sample is not exhaustive, this is
**sample recall**: comparable across runs and models on the same fixture,
not an absolute coverage claim.

### 4.3 Precision (three-way chain classification)

Every produced chain is classified:

- **matched** — satisfies an expected item;
- **extra_grounded** — not in the expected sample, but its failure mode and
  corrective action are supported by the kept pages (node name or a verbatim
  relation-evidence quote appears in the text). Valid coverage the sample
  simply does not enumerate — *not* an error;
- **unsupported** — not grounded in the source. This is the hallucination
  bucket.

Derived metrics:

```
precision_strict    = matched / total_chains          (pessimistic; sample-dependent)
grounded_precision  = (matched + extra_grounded) / total_chains
unsupported_rate    = unsupported / total_chains      (the hallucination KPI)
```

**`unsupported_rate` is the headline precision KPI** (gate: typically 0.0).
`precision_strict` varies with branch coverage run-to-run and is reported but
not gated.

### 4.4 Other gated checks

- **Scoping**: `must_keep_pages ⊆ selected_pages` (boolean).
- **Forbidden chains**: zero strict-matches against any produced chain.
- **Export checks**: node-count floors and required relation names present.
- **Human review**: per-severity upper bounds on the review queue
  (`max_blocking` is the meaningful bar; an empty queue is not).
- **Schema compliance**: boolean + issue counts by severity (reported;
  regression-compared, see §5.3).

### 4.5 Efficiency

Per run: `duration_seconds`, prompt/completion/total tokens per stage and
total (from `run_metrics`), and cost computed offline as
`prompt_tokens/1e6 * $in + completion_tokens/1e6 * $out` at the provider's
current prices. Always record the price used — see the cost worked example in
[HAIER_LMA4120_GOLDEN_EVAL.md](HAIER_LMA4120_GOLDEN_EVAL.md).

## 5. Running an evaluation

### 5.1 Modes

```bash
# Deterministic CI gate — no API key, < 60 s, recall 1.0 baseline expected
python3 scripts/eval_golden.py --mode mock --fail-on-regression

# Real-model measurement on one fixture
python3 scripts/eval_golden.py --mode full --model gpt-5.4 \
    --fixtures haier_lma4120_washer_manual --output-dir eval_runs

# Subset of fixtures, custom baseline
python3 scripts/eval_golden.py --fixtures clean_pump_manual,haier_lma4120_washer_manual \
    --baseline eval_runs/<ts>/report.json --fail-on-regression
```

Every run writes `eval_runs/<timestamp>/`:

- `report.json` — full machine-readable report (the citable artifact);
- `report.md` — human summary;
- `artifacts/<fixture_id>/{ontology,triplets,chains,review_queue}.json` —
  full payloads, so a paid run can be re-analysed offline without re-running
  the LLM. **Never delete the artifacts of a run you have quoted.**

### 5.2 Absolute gates (no baseline needed)

With `--fail-on-regression`, the run fails (exit 1) if any fixture has:
- a `forbidden_chains` violation, or
- a failed `expected_quality_gates` entry (`min_recall`,
  `max_unsupported_rate`).

### 5.3 Baseline regression comparison

Against `--baseline` (default: the most recent prior report in the output
dir), the run fails if, on any fixture:
- recall dropped **and** the fixture has no `min_recall` floor (fixtures with
  a floor use the floor instead — real-model recall oscillates ±0.1 on
  identical code, so "never worse than last run" false-alarms on variance);
- schema compliance was true and became false;
- `unsupported_rate` increased (when the baseline has chain metrics);
- human-review expectations matched before and no longer do.

`precision_strict` is deliberately **not** regression-compared: its
denominator is total branch coverage, which varies run-to-run.

### 5.4 Reporting discipline

A quoted performance number must state: fixture id(s), mode, model, code
version (git commit), report path, and — for cost — token prices. Real-model
results in docs follow the format of
[HAIER_LMA4120_GOLDEN_EVAL.md](HAIER_LMA4120_GOLDEN_EVAL.md).

## 6. Procedure: creating a new golden fixture from a manual

This is the repeatable procedure the user-facing claim "evaluated on N
manuals" rests on. Budget ~2–4 h per real manual, plus 1–3 paid runs.

**Phase A — author (before any model run):**

1. **Select the manual and diagnostic scope.** Pick the troubleshooting /
   alarm-table / flowchart pages. Note the PDF↔printed page offset.
2. **Build the markdown manual** per §3.1: verbatim diagnostic pages with
   original page numbers + cover/index + at least one distractor page.
   Sanity-check the loader: `pytest tests/test_manual_loader.py` plus a quick
   `build_store_from_markdown` page-count check.
3. **Annotate the expected file** per §3.2 rules 1–5: `expected_scoping`,
   a 4–12 item `expected_triplets` sample, `expected_export_checks`,
   `expected_human_review` (start with `{"max_blocking": 0}`).
   Do **not** set `expected_quality_gates` or `forbidden_chains` yet.
4. **Create mock responses** (§3.3) so the new fixture passes the mock gate
   with recall 1.0: `python3 scripts/eval_golden.py --mode mock --fixtures <id>`.

**Phase B — calibrate (with real model runs):**

5. **Run the real model ≥ 2 times** (`--mode full --model <m>`). Read
   `artifacts/<id>/chains.json`: every `unsupported` chain is either a real
   hallucination (keep it unsupported) or evidence your manual page is
   missing text the model legitimately used (fix the fixture).
6. **Fix annotation bugs, not model bugs.** If an expected chain never
   matches because your phrasing paraphrases the manual, re-phrase it from
   the source. If it never matches because the model is wrong, leave it — that
   is the finding.
7. **Set the gates from observed behaviour**: `min_recall` = a floor safely
   below the observed stable recall (e.g. observed 0.75±0 → floor 0.75;
   observed 0.8–1.0 → floor 0.7); `max_unsupported_rate` = 0.0 unless the
   fixture has a known benign exception. Add `forbidden_chains` for every
   contamination actually observed (§3.2 rule 6).
8. **Freeze and document.** Commit fixture + a short
   `docs/<FIXTURE>_GOLDEN_EVAL.md` recording: source PDF, expected-chain
   rationale, the calibration runs (report paths), gate values and why.
   After freezing, annotation changes require re-running Phase B and a note
   in the fixture doc — silent gate loosening invalidates comparability.

**Definition of done:** mock eval recall 1.0 for the fixture; `pytest` green;
one committed real-run report demonstrating the gates hold; fixture doc in
`docs/`.

## 7. Protocol for model/config comparisons

When deciding which model or configuration to ship — or benchmarking a change
before it reaches customers:

1. **Fix the code**: one git commit for the whole comparison; record it.
2. **Fixture set**: all real-manual fixtures (synthetic fixtures are smoke
   tests — report them separately or not at all).
3. **Repetitions**: ≥ 3 runs per (model, fixture) — observed recall variance
   on identical code is ±0.1, so single-run comparisons are not meaningful.
   Report mean ± range (or all points) per metric.
4. **Primary metrics**: sample recall, `unsupported_rate`,
   `grounded_precision`, forbidden-chain violations, blocking-review count.
   Secondary: tokens, cost, duration, schema issues.
5. **No post-hoc annotation edits** once comparison runs start (§6 step 8).
6. Keep every `eval_runs/<ts>/` directory referenced in the decision; the
   artifacts are the audit trail.

## 8. Current fixture inventory & roadmap

| Fixture | Kind | Difficulty axis | Gates |
|---|---|---|---|
| `clean_pump_manual` | synthetic | clean prose baseline | export/review only |
| `ambiguous_conveyor_manual` | synthetic | one symptom, multiple causes | export/review only |
| `noisy_table_robot_manual` | synthetic | split/noisy table wording | export/review only |
| `eagle_s3l_laser_cutter_manual` | real (laser cutter) | prose troubleshooting + PM distractors | min_recall 0.7, unsupported 0.0 |
| `haier_lma4120_washer_manual` | real (washer) | alarm codes + flowcharts | min_recall 0.75, unsupported 0.0 |
| `lg_lmh2235st_microwave_manual` | real (microwave) | CA-less self-diagnosis codes + test-point flowcharts | min_recall 0.85, unsupported 0.0 |
| `fanuc_vb_series_cnc_manual` | real (CNC) | scattered knowledge: terse alarm list w/ embedded CAs, prose procedures, cross-page references | min_recall 0.8, unsupported 0.0 |
| `abb_irc5_controller_troubleshooting_manual` | real (robot controller) | symptom-level pairing: causes listed by probability + separate action tables | min_recall 0.85, unsupported 0.0 |
| `whirlpool_w11187658_dishwasher_manual` | real (dishwasher) | error-code table w/ indicator aliases + all-caps multi-cause symptom table | min_recall 0.7, unsupported 0.0 |

Gaps this protocol does not yet cover (candidate future work): exhaustive
(non-sample) recall on one fully-annotated manual; inter-annotator agreement
on expected files; non-English manuals; end-to-end HITL console flows.
