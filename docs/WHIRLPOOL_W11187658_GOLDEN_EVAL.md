# Whirlpool W11187658 Dishwasher — Golden Fixture Evaluation

**Fixture:** `whirlpool_w11187658_dishwasher_manual`
**Status:** Phase A complete. Two resumed Phase-B measurements are saved,
but calibration is **not frozen** and gates remain unset: the results expose
an annotation-semantics decision and a real dangling-relation defect described
below. Do not quote an aggregate performance claim from this fixture yet.

## Source

- **PDF:** Whirlpool Corporation, *18" & 24" ADA Built-In Dishwashers —
  Service Manual*, part no. W11187658 (Job Aid W10329932, © 2018), 64 pages.
  Local copy: `data/25e8e011-f735-4037-a7ed-d23d958f74a3.pdf`.
- **Diagnostic scope:** Section 2 *Diagnostics & Troubleshooting* —
  Service Error Codes (PDF page 18), Troubleshooting Guide (19–22),
  Customer Troubleshooting Guide (23). The fixture also keeps cover, index,
  the specifications page, section-2 intro and one Service Mode page as
  distractors. Page numbers are PDF page numbers.

## Difficulty axis

Appliance service-manual **error-code table** (E1/E3/E4/E6/E7 with
indicator-lamp aliases, merged cause + "what to check" columns) plus an
all-caps **symptom→causes→checks table** where most corrective actions are
phrased as inspection steps ("check X") rather than restorative actions.
Stresses: ErrorCode node extraction, multi-cause symptom rows, and the
restorative-action semantic validator.

## Expected sample (10 chains)

4 error-code-rooted chains (E1, E3, E4, E6) + 6 prose/table chains covering
won't-run, fill, wash-pump, drain (×2) and dispenser symptoms. All chains
quote the manual's own wording.

## Phase B log

| Run | Report | Recall | unsupported_rate | Outcome |
|---|---|---|---|---|
| 1 | `eval_runs/20260706T172744Z` | 0.0 (0/10) | 0.0 (0/12) | **invalid as calibration** — see finding below |
| 2 | `eval_runs/20260706T173538Z` | — | — | aborted: OpenAI `insufficient_quota` before this fixture started |
| 3 | `eval_runs/20260711T190612Z` | 0.4 (4/10) | 0.0 (0/59) | valid run; all must-keep pages selected; no blocking review items |
| 4 | `eval_runs/20260711T191059Z` | 0.5 (5/10) | 0.0 (0/49) | valid run; three blocking review items from dangling relations |

### Finding from run 1 (pipeline, not annotation)

The ontology-draft chunk covering the dense troubleshooting-guide pages was
**truncated at the completion-token limit**; the retry was also truncated
and the pipeline fell back to an empty draft chunk
(`fallback_empty_draft_chunk` in the run log). Consequences observed:

1. Pages 19–23 content missing from the graph → all 6 symptom chains and
   most nodes lost (11 FM / 11 CA / 3 Symptom survived, from page 18 only).
2. **Zero ErrorCode nodes**: E1/E3/E4 were folded into Symptom names
   ("WATER INLET FAILURE Dishwasher displays E1 …") instead of
   `ErrorCode -INDICATES-> FailureMode` — consistent with the known
   extraction-quality audit findings.
3. All 12 produced chains were nonetheless grounded (unsupported_rate 0.0).

Root cause hypothesis: `config.yaml` sets `extraction_max_output_tokens`
and `extraction_retry_max_output_tokens` both to 16000, so the retry adds
no real headroom (the code caps the retry at max(16000, 16000+4000) =
20000), and reasoning-token usage of `gpt-5.4` counts against the same
`max_completion_tokens` budget.

### Resumed calibration — 2026-07-11

Both measurements used `gpt-5.4-2026-03-05` in `full` mode at code commit
`0359801`. The preceding execution fix was committed before the runs:

1. `0012376` raises a truncation retry from 16k to 24k output tokens;
2. `0359801` caps unsectioned manuals at five pages per ontology chunk.

Whirlpool was consequently processed in three ontology chunks rather than one
oversized chunk. Both runs performed one JSON repair/retry but neither emitted
`fallback_empty_draft_chunk`; each produced `report.json`, `report.md`, and
the full ontology/triplet/chain/review-queue artifacts.

| Metric | Run 3 | Run 4 |
|---|---:|---:|
| Duration | 212.6 s | 236.2 s |
| Prompt / completion tokens | 163,227 / 49,767 | 225,027 / 69,405 |
| Estimated cost | $1.14 | $1.37 |
| Scoping must-keep | pass | pass |
| Recall | 4/10 | 5/10 |
| Grounded precision / unsupported rate | 1.0 / 0.0 | 1.0 / 0.0 |
| Export checks | pass | pass |
| Blocking review items | 0 | 3 |

### Findings before freezing gates

1. The truncation failure is resolved: ErrorCode nodes are present (five in
   both resumed runs), all selected diagnostic pages are represented, and no
   unsupported chain was found.
2. All four expected error-code chains are missed in both runs. The source
   defines their `What to check` entries as inspection steps; the pipeline's
   restorative-action rule intentionally does not attach most of them as
   `RESOLVED_BY` actions. It instead models the textual cause (for example,
   “flow meter cannot detect correct fill” for E1) rather than the error-table
   heading (“water inlet failure”). The current expectation uses the heading
   as failure mode and an inspection as corrective action. This needs an
   explicit annotation-semantics decision before changing the golden.
3. The `won't run / no power` sample chain is missed in both runs because no
   linked action is emitted. The obstructed-drain chain is additionally
   missed in Run 3 but recovered in Run 4. These are model/pipeline recall
   findings, not annotation changes to make silently.
4. Run 4 has three blocking review items caused by `INDICATES`, `AFFECTS`,
   and `RESOLVED_BY` relations pointing to a missing `fm_overflow` node. The
   existing `max_blocking: 0` expectation therefore correctly fails on that
   run and must not be relaxed.

### Remaining Phase B work

1. Decide whether inspection-only “check” steps in error-code tables should
   be represented as diagnostic actions, or revise those four expectations to
   the manual's causal text with no corrective action (the latter matches the
   current restorative-action contract). Re-score the saved artifacts after
   the decision; no paid rerun is needed for an annotation-only correction.
2. Fix the dangling `fm_overflow` relations and the missing code/action or
   no-power links as product work, then repeat the two real runs on the new
   commit.
3. Only after both the recall semantics and `max_blocking: 0` are stable, set
   `min_recall` / `max_unsupported_rate`, freeze the annotation, and update
   this document to Phase B complete.

## Mock gate

Mock eval recall is 1.0 and `pytest` is green with this fixture included,
so it already serves as a deterministic CI regression guard while Phase B
is pending.
