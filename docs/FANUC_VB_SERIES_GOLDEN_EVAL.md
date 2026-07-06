# Fryer VB Series (FANUC 0i-MF) Golden Evaluation

Fixture created 2026-07-05 following
[EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md) §6. This is the
industrial-CNC fixture — the closest to the target client domain and by
design the hardest of the set.

## Source

`manuals/VB SERIES FANUC MAINTENANCE MANUAL Ver 1.0.pdf` — 114-page English
maintenance manual (Fryer Machine Systems, FANUC 0i-MF control). Printed
page = PDF page − 1. Roughly half the manual is drawings/parts lists with
little machine-readable text.

## Files

- Golden manual: `tests/golden/manuals/fanuc_vb_series_cnc_manual.md`
- Expected output: `tests/golden/expected/fanuc_vb_series_cnc_manual.json`
- Mock LLM response: `tests/golden/mock_responses/fanuc_vb_series_cnc_manual/ontology.json`

## Why this manual is hard (difficulty axes)

Unlike the Haier/LG fixtures there is **no symptom/cause/remedy table** in
machine-readable text. The diagnostic knowledge is scattered:

1. **PLC alarm list** (printed p. 30): 18 codes with terse ALL-CAPS messages.
   Most carry no corrective action; some embed one *inside the message*
   ("ATC CAR. MISCOUNT - DO M61 !!!!") that cross-references the M-code table
   on another page (M61 = home ATC carousel to pocket 1, p. 29).
2. **Prose procedures**: the absolute-encoder-alarm recovery (p. 20) and the
   backlash check/compensation (p. 21) hold symptom→cause→action chains
   buried in narrative text.
3. **Image-only troubleshooting**: the "ATC TROUBLESHOOTING" chart (printed
   p. 47) is a drawing with no extractable text. Excluded from expectations
   — the text pipeline cannot see it. (A future OCR/vision ingestion axis.)
4. **Distractors**: maintenance schedule chart, ATC repair procedures,
   safety pages — plenty of imperative "replace/remove" text that is *not*
   diagnostic.

Fixture pages (printed numbering): 1, 2, 4, 13, 20, 21, 29, 30, 46, 47.
`must_keep_pages`: 20, 21, 30.

## Expected chains (6)

| # | Error code | Symptom | Failure mode | Corrective action |
|---|---|---|---|---|
| 1 | 1001 | (code-rooted) | low way lube | — |
| 2 | 1002 | (code-rooted) | low air pressure | — |
| 3 | 1014 | (code-rooted) | door interlock open | — |
| 4 | 1011 | (code-rooted) | ATC carousel miscount | M61 |
| 5 | | machine home position is lost | battery for the absolute encoder goes dead | reference the axis |
| 6 | | loss of motion in the axis | backlash | adjust backlash compensation |

## Phase A findings (worth keeping)

- **Mock stage-detection fragility**: the mock gateway sniffs the whole
  prompt for stage markers; the fixture's "Table of Contents" page heading
  made the ontology-draft prompt match the *scoping* branch, yielding an
  empty draft. Worked around by renaming the heading "Manual Index";
  hardening task filed (see `_stage_mock_content` in
  `backend/services/llm_gateway.py`).
- **Actionability heuristic gap**: `has_actionable_instruction` recognizes
  workshop verbs (replace/repair/clean/...) but not CNC-control verbs
  (execute, run M61, reference, jog, power down). Real corrective actions on
  this asset class trigger `instruction_not_actionable` warnings. Candidate
  pipeline improvement; mock baseline phrased with recognized verbs
  (restore/reset) to stay deterministic.

Phase A gate: mock recall 1.0 (6/6), 0 unsupported, all 7 fixtures green.

## Phase B — calibration runs (real model, gpt-5.4, 2026-07-05)

Command:

```bash
python3 scripts/eval_golden.py --mode full --model gpt-5.4 \
    --fixtures fanuc_vb_series_cnc_manual --output-dir eval_runs
```

Recall (final) is against the frozen annotation, re-scored offline from
`eval_runs/<ts>/artifacts/` (protocol §5.1); "as-run" is what the run
reported against the annotation at run time.

| Run | Report | Recall (final) | Recall (as-run) | unsupported_rate | grounded_precision | Blocking | Tokens (prompt/completion) | Est. cost |
|---|---|---|---|---|---|---|---|---|
| 1 | `eval_runs/20260705T192621Z` | **1.0** (6/6) | 0.833 | 0.0 | 1.0 | 0 | 82,958 / 16,563 | $0.46 |
| 2 | `eval_runs/20260705T193058Z` | **0.833** (5/6) | 0.667 | 0.0 | 1.0 | 0 | 44,172 / 18,828 | $0.38 |

Two annotation calibrations (§6 step 6 — over-specified keys, model output
was correct):

1. **Backlash chain direction**: the annotation fixed "loss of motion" as
   symptom and "backlash" as failure mode; the model (defensibly) inverted
   them ("Axis backlash out of specification" → "Ballscrew or linear guide
   motion loss"). Keys relaxed to symptom "backlash" / FM "ballscrew",
   pinned by the corrective action.
2. **Encoder chain symptom split**: the manual's trigger is disjunctive
   (encoder disconnected OR battery dead OR parameters reloaded); run 2
   split it into two symptom nodes and attached the battery FM to the
   "alarm displayed" symptom rather than "home position lost". The expected
   item is now symptom-agnostic (FM "battery for the absolute encoder goes
   dead" → CA "reference the axis").

Model-behaviour findings (real findings, kept in the annotation):

- **Backlash chain instability**: extracted in run 1, *entirely absent* in
  run 2 (page 21 was kept both times). First observed run-to-run content
  dropout across the fixture set — prose procedures without alarm codes are
  the least stable extraction target. The expected item stays: it is the
  regression signal.
- Zero unsupported chains in both runs; alarm-message chains (way lube, air
  pressure, door interlock, M61 miscount) were stable across both runs,
  including the embedded-CA cross-reference to the M-code table.
- `instruction_not_actionable` warnings persist on real runs (CNC verbs not
  in the repair-verb lexicon — see Phase A findings).

## Frozen gates (§6 step 7)

```json
"expected_quality_gates": { "min_recall": 0.8, "max_unsupported_rate": 0.0 }
```

Observed recall 1.0 / 0.833: the 0.8 floor tolerates exactly one missed
chain (5/6 = 0.833, the backlash dropout) while two misses (0.667) fail.
`max_unsupported_rate` 0.0 observed in both runs. Annotation frozen
2026-07-05; edits require a new Phase B per protocol §6 step 8.
