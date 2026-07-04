# Haier LMA4120WBAB0 Golden Evaluation

## Scope

This document records the first real-manual golden evaluation created from
`/Users/fabio.daniele/Downloads/Manual-de-usuario-LMA4120WBAB0.pdf`.

The source PDF is a 24-page English service manual for Haier/MABE automatic
washing machine models including `LMA4120WBAB0`. The golden fixture is a compact
markdown extraction of the cover/index and diagnostic pages 16, 18, and 19.

## Files

- Golden manual: `tests/golden/manuals/haier_lma4120_washer_manual.md`
- Expected output: `tests/golden/expected/haier_lma4120_washer_manual.json`
- Mock LLM response: `tests/golden/mock_responses/haier_lma4120_washer_manual/ontology.json`
- Latest real gpt-5.4 report with actual triplets: `eval_runs/20260704T122734Z/report.json`
- Prior real gpt-5.4 report: `eval_runs/20260704T121400Z/report.json`
- Real gpt-5.5 report: `eval_runs/20260704T121745Z/report.json`

## Expected Diagnostic Triplets

| # | Error code | Symptom | Failure mode | Corrective action |
|---|---|---|---|---|
| 1 | E1 | machine does not drain or drains slowly | drain hose blocked | remove the blockage |
| 2 | E4 | (error-code-rooted, no symptom required) | water inlet valve blocked | clean the water inlet valve |
| 3 |  | No draining | drain motor does not act when voltage exists | replace the drain motor |
| 4 |  | Keep filling water | water can fill into the water inlet valve without power | replace the water inlet valve |

Expectation #2 is intentionally rooted on the error code, not on a symptom
string: modelling "display shows E4" as a Symptom would contradict the
ontology's own ErrorCode/INDICATES design. The evaluator matches error-code
expectations against the graph chain
`ErrorCode -INDICATES-> FailureMode -RESOLVED_BY-> CorrectiveAction`
(and against projected triplets that carry the code), so the gate does not
depend on how the projection groups symptoms.

## Evaluator Contract (updated)

- Matching is per atomic chain (symptom → failure mode → corrective action,
  paired via `linked_failure_mode_id`), not per concatenated symptom blob, so
  a wrong FM→CA pairing is a miss.
- `error_code` comparisons are token-exact ("E1" does not match "E17") and an
  empty actual code never matches a non-empty expectation.
- Extra chains are classified as `extra_grounded` (valid manual coverage the
  golden simply does not enumerate) or `unsupported` (true false positive);
  see `triplets.chains` for `precision_strict`, `grounded_precision`, and
  `unsupported_rate`.
- `forbidden_chains` in the expected file assert that specific contaminated
  links (e.g. a cause merged in from another alarm-table row) never appear;
  violations fail `--fail-on-regression` even without a baseline.
- `expected_human_review` supports granular bounds (`max_blocking`,
  `max_open`, ...) because flowchart symptoms are legitimately multi-cause:
  the meaningful bar is "nothing blocking", not "queue empty".
- Full payloads (`ontology.json`, `triplets.json`, `chains.json`,
  `review_queue.json`) are persisted under `eval_runs/<run>/artifacts/` so a
  paid run can be re-analysed offline; `triplets.actual_chains` supersedes the
  old `triplets.actual_triplets` blob.

Pipeline changes shipped with this contract: the projection now carries error
codes from INDICATES edges onto triplets, and the graph closure no longer
auto-applies MAY_INDICATE (causal) edges from page-level co-occurrence — the
source of the cross-row contamination observed in the first real runs.

## Latest gpt-5.4 Run

Command:

```bash
python3 scripts/eval_golden.py --mode full --model gpt-5.4 --fixtures haier_lma4120_washer_manual --output-dir eval_runs
```

Report: `eval_runs/20260704T122734Z/report.json`

| Metric | Value |
|---|---:|
| Scoping must-keep pages | pass |
| Matched expected triplets | 3 / 4 |
| Recall | 0.75 |
| Approximate precision | 0.4286 |
| Actual triplets emitted | 7 |
| Schema compliant | false |
| Schema issues | 10 warnings |
| Review queue | 17 items |
| Export checks | pass |
| Prompt tokens | 112,266 |
| Completion tokens | 50,328 |
| Total tokens | 162,594 |

Using the requested gpt-5.4 prices, $2.50/input MTok and $15/output MTok,
this run costs approximately:

```text
(112,266 / 1,000,000 * 2.50) + (50,328 / 1,000,000 * 15) = $1.035585
```

## Actual Triplets Extracted By gpt-5.4

The evaluator normalizes each projected triplet into symptom, failure mode,
corrective action, and error code text. The latest run produced:

1. Symptom: Machine does not drain or drains slowly.
   Failure modes included: drain hose blocked; machine not level.
   Corrective actions included: remove drain hose blockage; level the machine.
   Match: expected triplet #1.

2. Symptom: Machine stops running.
   Failure mode: top lid not closed.
   Corrective action: close top lid.
   Match: not part of this golden expected set.

3. Symptom: Machine does not spin.
   Failure modes included: laundry unevenly placed; machine not level; water inlet valve failed.
   Corrective actions included: redistribute load; level the machine; replace water inlet valve.
   Match: not part of this golden expected set.

4. Symptom: No water filling.
   Failure modes included: water inlet valve filter screen contaminated; water pressure too low;
   water inlet valve failed; wire unit disconnected; computer sequencer output failed;
   water inlet valve blocked; laundry unevenly placed.
   Corrective actions included: remove foreign materials; restore/raise water pressure;
   replace water inlet valve; replace wire unit; replace computer sequencer; clean water inlet valve;
   redistribute load.
   Match: did not match expected triplet #2 because the symptom was generalized to
   "No water filling" instead of "display shows E4" and the chain mixed multiple branches.

5. Symptom: No rotation in washing.
   Failure modes included: bearing locking clutch; capacitor broken circuit; capacitor short circuit; motor failed.
   Corrective actions included: replace capacitor; replace motor.
   Match: not part of this golden expected set.

6. Symptom: No draining.
   Failure modes included: drain motor failed; wire unit disconnected to drain motor;
   computer sequencer output failed for drain; machine not level.
   Corrective actions included: replace drain motor; replace wire unit; replace computer sequencer; level the machine.
   Match: expected triplet #3.

7. Symptom: Keep filling water.
   Failure modes included: water inlet valve leaking open; computer sequencer failed;
   wire unit bad between board and water level sensor; gas cell contains water and leaks gas;
   gas guide system leaks gas; gas guide system blocked; water level switch failed.
   Corrective actions included: replace water inlet valve; replace computer sequencer;
   replace wire unit; repair gas guide system; clear foreign materials; replace water level switch.
   Match: expected triplet #4.

## Interpretation

The model is extracting the right diagnostic region and it captures many valid
branches from the flowcharts. However, the graph projection currently collapses
multiple branches under one symptom, which lowers precision and makes exact
golden matching fragile.

The missing expected item is the E4 alarm chain:

```text
display shows E4 -> water inlet valve blocked -> clean the water inlet valve
```

The model did extract the relevant concepts, but under the broader symptom
`No water filling` and mixed them with other possible water-fill causes/actions.
That is useful troubleshooting content, but it does not preserve the specific
alarm-code chain required by the golden set.

## Comparison Notes

- gpt-5.4 performed better than gpt-5.5 on this golden.
- gpt-5.4 recall was stable at 0.75 across two real runs, but precision,
  schema warnings, and triplet count varied.
- gpt-5.5 produced 0/4 matched triplets and failed export checks in the tested run.
- The primary failure mode is not missing text retrieval. It is over-grouping:
  multiple flowchart branches become a single broad triplet.

## Recommendations

1. Preserve alarm-code chains as first-class triplets before broad symptom merging.
2. Split flowchart branches into separate candidate chains instead of attaching all
   possible causes/actions to one symptom.
3. Add an evaluator field for exact actual chain text, now implemented as
   `triplets.actual_chains` plus full artifacts under `eval_runs/<run>/artifacts/`,
   so future runs can be audited without rerunning LLM calls.
4. Keep this Haier fixture as a real-manual regression test because it exposes
   weaknesses hidden by the synthetic golden manuals.
