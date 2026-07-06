# LG LMH2235ST Golden Evaluation

Fixture created 2026-07-05 following
[EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md) §6 — the first fixture
authored end-to-end under the formal procedure.

## Source

`manuals/LG_MICROWAVE.pdf` — 49-page English service manual for the LG
LMH2235ST microwave oven. Printed page numbers match PDF page numbers
(offset 0). Diagnostic content: self-diagnosis error codes (page 12) and six
troubleshooting flowcharts (pages 13–23).

## Files

- Golden manual: `tests/golden/manuals/lg_lmh2235st_microwave_manual.md`
- Expected output: `tests/golden/expected/lg_lmh2235st_microwave_manual.json`
- Mock LLM response: `tests/golden/mock_responses/lg_lmh2235st_microwave_manual/ontology.json`

## Fixture design

Pages kept in the markdown fixture: cover (1), index (2), specifications
distractor (4), general-service distractor (11), self-diagnosis error codes
(12), basic check summary (13), No Display or Dead (15), Keypad Failure
(16–17), No Heat / No Cook (18–21), Turntable Motor Does Not Work (22),
Turns On Automatically (23), microwave leakage distractor (24).
`must_keep_pages`: 12, 15, 17, 20, 21, 22 — the pages holding expected
chains.

Difficulty axes this fixture adds over the existing set:
- **CA-less error codes**: F-1/F-2/F-4 are self-diagnosis codes with a named
  failure but *no* corrective action in the manual — the pipeline must not
  invent one, and legitimately reports the missing RESOLVED_BY as *open*
  review items (hence granular `max_blocking: 0`, not "queue empty").
- **Test-point flowcharts**: failure modes are phrased as measurements
  ("resistance of the high voltage transformer out of range"), not as plain
  component states — a paraphrase-robustness test for matching.
- **Branch separation across near-identical steps**: the latch-board check
  appears in three different flowcharts (Keypad Failure, No Heat, Turns On
  Automatically); merging them across symptoms is the contamination to watch.

## Expected chains (9)

| # | Error code | Symptom | Failure mode | Corrective action |
|---|---|---|---|---|
| 1 | F-2 | (code-rooted) | PCB thermistor open | — |
| 2 | F-4 | (code-rooted) | Humidity sensor open or short | — |
| 3 | | No Display or Dead | fuse has no continuity (open fuse) | replace the fuse |
| 4 | | No Display or Dead | noise filter has no continuity | replace the noise filter |
| 5 | | Keypad Failure | latch board secondary switch has no continuity | adjust the latch board |
| 6 | | No Heat / No Cook | HV transformer resistance out of range | replace the HV transformer |
| 7 | | No Heat / No Cook | HV capacitor resistance out of range | replace the HV capacitor |
| 8 | | No Heat / No Cook | HV diode resistance out of range | replace the HV diode |
| 9 | | Turntable motor does not work | turntable motor does not operate although the oven lamp turns on | replace the turntable motor |

## Phase A result (mock, deterministic baseline)

Recall 1.0 (9/9), unsupported 0, scoping must-keep pass, export checks pass,
human review matched (0 blocking; 3 *open* items are the CA-less F-codes,
which is correct per the manual). Full suite: 6/6 fixtures green.

Note: two authoring fixes were needed during Phase A — (a) pages 22–23 needed
their section header ("6-4. Troubleshooting") spelled out because the
deterministic keyword scoping has no signal for "Turntable Motor Does Not
Work"; (b) the mock ontology needed Component nodes because
`FailureMode.material_context` is schema-required.

## Phase B — calibration runs (real model, gpt-5.4, 2026-07-05)

Command:

```bash
python3 scripts/eval_golden.py --mode full --model gpt-5.4 \
    --fixtures lg_lmh2235st_microwave_manual --output-dir eval_runs
```

Recall values below are against the **final** (frozen) annotation; the
"as-run" column shows what the run reported against the annotation as it
stood at run time. Re-scores were computed offline from
`eval_runs/<ts>/artifacts/` (protocol §5.1) — no LLM re-run.

| Run | Report | Recall (final) | Recall (as-run) | unsupported_rate | grounded_precision | Blocking | Prompt/completion tokens | Est. cost |
|---|---|---|---|---|---|---|---|---|
| 1 | `eval_runs/20260705T190435Z` | **1.0** (9/9) | 0.889 | 0.0 | 1.0 | 0 | 119,933 / 16,673 | $0.55 |
| 2 | `eval_runs/20260705T190852Z` | **1.0** (9/9) | 0.778 | 0.0 | 1.0 | 0 | 65,829 / 16,052 | $0.39 |

Two annotation bugs surfaced and fixed during calibration (§6 step 6 — both
were over-specified matching keys, in each case the model had extracted the
chain correctly):

1. **Turntable FM key**: the annotation used the full flowchart condition
   ("turntable motor does not operate although the oven lamp turns on") as
   the failure-mode key; the model names the FM "Turntable motor faulty".
   Key reduced to "turntable motor" — still unique because the chain is
   pinned by symptom + corrective action.
2. **Disjunctive symptom title**: "No Display or Dead" is a section title
   covering two symptoms; the model (correctly) splits it into "Dead" and
   "No display". Key reduced to "No display", which matches both the split
   and the combined phrasing.

Model-behaviour observations (not annotation issues):
- Zero unsupported chains in both runs — everything extracted is grounded in
  the kept pages. Extra coverage is large (29 and 40 extra grounded chains):
  the flowcharts contain many more valid branches than the 9-item sample.
- Run 2 emitted 5 schema warnings and split symptoms more aggressively than
  run 1 (11 vs 45 total chains projected) — precision_strict is accordingly
  noisy (0.17 / 0.11), which is exactly why it is reported but not gated.
- No contamination observed (no cross-flowchart FM merges), so
  `forbidden_chains` stays empty for now.

## Frozen gates (§6 step 7)

```json
"expected_quality_gates": { "min_recall": 0.85, "max_unsupported_rate": 0.0 }
```

Observed recall was 1.0 in both calibration runs; the 0.85 floor tolerates
exactly one missed chain (8/9 = 0.889) as run-to-run variance headroom, while
two misses (0.778) fail. `max_unsupported_rate` 0.0 was observed in both
runs. Annotation frozen as of 2026-07-05; further edits require a new Phase B
per protocol §6 step 8.
