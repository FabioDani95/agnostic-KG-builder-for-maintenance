# Test plan: connected-graph pipeline against the earlier versions

This plan says which runs to make, what is measured on each, how versions are
compared and when a result counts. It is written to be followed step by step and
to leave every number traceable to a file. Every paid step needs an explicit
authorisation with an amount.

| Phase | State |
| --- | --- |
| T0 Offline | Done |
| T1 Smoke | Done: Graco runs complete and open in the interface |
| T2 Development | Done for `kg_v4` (two replicas per manual per round) and `V3 base` (two replicas); the stage-off variants were not run |
| T3 Breadth | Not run. One scanned manual outside the campaign, with no gold, was built to check transcription |
| T4 Precision | Not run |
| T5 Held out | Not run: the held-out manuals are not chosen |

The numbers measured so far are in [Evaluation](evaluation.md#measured-so-far).

## 1. What is compared

| Name | What it is | Where its graphs come from |
| --- | --- | --- |
| `V3 F` | V3 as measured in campaign F (September 2026) | Saved: `campaign/<manual>/runs/v3_r1..3`. No cost |
| `V3 base` | V3 with the base profile, the strongest earlier version | Run again for the test (`--gates agent`), two replicas, with the same model and date as the new runs |
| `quality_v1` | V3 with the quality profile | Saved for Grizzly and LG (pilot, `ALL`). Not run again: it measured below the base profile |
| `kg_v4` | The connected-graph pipeline | New runs |
| `kg_v4` variants | `kg_v4` with one stage off (`--no-verify`, `--gap-calls 0`, `--enrich-calls 0`) | New runs, development manuals only |

A saved graph is compared as it is and labelled with its date and code version.
A number is never moved from one version to another.

## 2. Manuals

| Role | Manuals | Use |
| --- | --- | --- |
| Smoke | Graco GTX 2000EX (18 pages) | First real run: does the pipeline complete, is the output sane |
| Development | Grizzly G0872, LG LMH2235ST | Prompts and rules may be changed after looking at these |
| Breadth | ABB ACS580, Atlas Copco DRB, Grundfos Paco, Haas Mill, Lincoln POWER MIG | Run after each frozen change; never tuned on one of them alone |
| Held out | Two or three manuals never processed, chosen by the project owner | Run once, after the code is frozen, with a gold written before the run |

`campaign/<manual>/info.yaml` still marks Grizzly and LG as `split: test`; from
iteration F they are development manuals and are reported as such. Graco,
Grizzly and LG are scored on gold v2, which is written by an AI (see
[Evaluation](evaluation.md#gold-v2-made-by-an-ai)); results on it say so.

## 3. Measures

Every measure is computed by a tool from saved files. "Judge" marks the ones that
need a model or a person.

| Measure | Tool | Judge |
| --- | --- | --- |
| Recall, strict: branches whose claims were all found | `kg_v3_kpi.py`, then `kg_compare.py` | LLM, three votes |
| Recall, partial credit: mean share of claims found per branch | `kg_compare.py` | same judgement |
| Recall, claims found over all claims | `kg_compare.py` | same judgement |
| Where the lost claims stopped | `kg_loss_analysis.py` | same judgement |
| Precision, strict and tolerant | blind sheet (`kg_v3_precision_sheet.py`) | person |
| Grounded connectivity, with and without derived links | `kg_scorecard.py` | none |
| Causes with an action or a declared absence; complete chains | `kg_scorecard.py` | none |
| Descriptions, attributes, placeholders, generic names | `kg_scorecard.py` | none |
| Duplicates and merged false friends | pairs listed by `kg_scorecard.py` | person |
| Cost, tokens, time | run report | none |
| Stability | range over replicas of the same system | none |

The three views of recall exist so that one missing step does not hide a branch
that is otherwise right: a branch with four of five claims found counts 0 in the
strict view and 0.8 in the partial-credit view. All three are always shown.

## 4. How judging stays fair without being rigid

- **Meaning, not wording.** The recall judge is asked whether two facts say the
  same thing; a paraphrase, a shorter name or extra detail is "same". This is the
  judge already used for every earlier version, so old and new graphs are judged
  by the same rule.
- **The judge is checked.** After each judged phase the owner reads 30 pairs the
  judge called "different", drawn at random and shown without the system's name.
  The share the owner would call "same" is reported next to recall as the judge's
  error rate. An earlier audit found about one in five.
- **Precision has three answers.** For each sampled fact the reader sees the
  manual passage and the fact, not the system, and answers: *correct*; *acceptable*
  (imprecise in a detail, still what a technician needs); *wrong*. Strict precision
  counts only *correct*; tolerant precision counts *correct* and *acceptable*. Both
  are reported. Forty facts per manual and system, spread over relation types and
  confidence levels; about one hour per manual.
- **Every system on the same scorer.** Gold v2 names no cause for most flowchart
  and maintenance facts; judge with `--unnamed-causes problem` and never compare a
  number from it with one from the historical `record` scorer.
- **Differences smaller than the noise are not differences.** Two values within 3
  points, or within the range between replicas when that is wider, are reported as
  "same". `kg_compare.py` marks each measure ▲, ＝ or ▼ against the baseline.
- **Disagreements are kept.** A fact the reader is unsure about is recorded as
  unsure and shown as a range, not forced into a class.

## 5. Phases

Costs for `kg_v4` come from `scripts/kg_build.py --estimate`; a `kg_v4` run cost
0.02–0.15 USD on the development manuals, a V3 run about 0.20 USD. Judging costs
about 0.10 USD per 1,000 pairs; with gold v2 and `--unnamed-causes problem` a
development manual has 1,900–2,600 pairs per run, Graco 200–300.

| Phase | Runs | Estimated cost | Stop and decide |
| --- | --- | --- | --- |
| T0 Offline | Cards of all saved graphs; comparison of the saved versions | 0 | Done before any spending |
| T1 Smoke | `kg_v4` on Graco, one run | 0.05–0.09 USD | Run completes; graph opens in the interface; no stage reports failures |
| T2 Development | `kg_v4` ×2 and `V3 base` ×1 on Grizzly and LG; judge all six runs; three variants of `kg_v4` on both | about 2.5 USD | Compare with section 6; change prompts or rules; repeat `kg_v4` (about 0.5 USD per repeat) |
| T3 Breadth | `kg_v4` ×1 on the five breadth manuals and Graco; judge them and the saved `V3 F` graphs of Atlas Copco and Grundfos | 1.3–2.4 USD | No manual clearly worse than its saved V3 graph |
| T4 Precision | Blind sheets for `kg_v4` and `V3 base` on the development manuals and two breadth manuals | owner's time | Tolerant and strict precision per system |
| T5 Held out | Freeze and tag the code; `kg_v4` and `V3 base` once on the held-out manuals; judge | about 1 USD plus the gold | Reported as the only numbers on unseen manuals |

Proposed cap for T1–T3: 8 USD on one new ledger, with a spend ceiling per phase.
The ledger reserves the worst case of every call, so the cap needs room above the
estimate.

## 6. When a result counts

These are reading rules, not gates that discard work.

| Question | `kg_v4` is ahead when |
| --- | --- |
| Does it find as much? | Partial-credit recall is ▲ or ＝ against `V3 base` on both development manuals, and ▲ on at least one |
| Is it right? | Tolerant precision is ＝ or ▲ against `V3 base`; strict precision is reported beside it |
| Is the graph connected? | Largest grounded component ▲, also when the links derived from names are left out |
| Are nodes usable? | Descriptions and attributes from the manual ▲; no generic node used as a bridge |
| Did merging break anything? | No false friend merged among the pairs a person checked |
| Does it hold elsewhere? | On the breadth manuals, no measure ▼ on more than one manual without an explanation from the loss analysis |
| What does it cost? | Cost and time are shown; a higher cost is acceptable when stated |

If recall is ▼ on a development manual, the loss analysis says at which stage the
claims stop, and the next change targets that stage. A variant that changes no
measure is a stage to remove.

## 7. Commands

One folder per test, never an existing one. `<T>` is that folder, for example
`experiments/kg4_test_1`.

```bash
# T0: what the saved versions measure, with no spending
.venv/bin/python scripts/kg_scorecard.py --discover --out <T>/cards_saved
.venv/bin/python scripts/kg_compare.py --manuals grizzly_g0872,lg_lmh2235st \
  --system "V3 F=campaign/{manual}/runs/v3_r1" --recall "V3 F=campaign/results/kpi_F.json:v3_r1" \
  --system "V3 base=experiments/kg_quality_pilot_20261001/fixed_v1/runs/{manual}/Bsafe/r1" \
  --recall "V3 base=experiments/kg_quality_pilot_20261001/gold_measurement_v1/historical_scores.json:Bsafe/r1" \
  --baseline "V3 base" --out <T>/comparison_saved

# T1, T2: new runs (after authorisation; the amounts are examples)
.venv/bin/python scripts/kg_build.py --manual grizzly_g0872 --estimate
.venv/bin/python scripts/kg_build.py --manual grizzly_g0872 --out <T>/runs/grizzly_g0872/kg4_r1 \
  --authorize-spend --budget 8 --spend-ceiling 3 --ledger <T>/budget.jsonl
.venv/bin/python scripts/kg_v3.py --manual grizzly_g0872 --out <T>/runs/grizzly_g0872/base_r1 \
  --gates agent --budget 8 --spend-ceiling 3 --ledger <T>/budget.jsonl

# Judge every run of the folder on gold v2 (paid: same ledger)
.venv/bin/python scripts/kg_v3_kpi.py --manuals grizzly_g0872,lg_lmh2235st --runs <T>/runs \
  --v3-only --gold gold_v2 --kg4-view full --unnamed-causes problem \
  --out <T>/kpi.json --budget 8 --spend-ceiling 3 --ledger <T>/budget.jsonl

# Compare, find where claims were lost, write the cards (offline)
.venv/bin/python scripts/kg_compare.py --manuals grizzly_g0872,lg_lmh2235st \
  --system "V3 base=<T>/runs/{manual}/base_r1" --recall "V3 base=<T>/kpi.json:v3_base_r1" \
  --system "kg_v4=<T>/runs/{manual}/kg4_r1" --recall "kg_v4=<T>/kpi.json:v3_kg4_r1" \
  --baseline "V3 base" --out <T>/comparison
.venv/bin/python scripts/kg_loss_analysis.py --manual grizzly_g0872 --run <T>/runs/grizzly_g0872/kg4_r1 \
  --kpi <T>/kpi.json --system v3_kg4_r1 --out <T>/losses/grizzly_kg4_r1.json
.venv/bin/python scripts/kg_scorecard.py <T>/runs/*/*/graph.json --out <T>/cards
```

The KPI file names every run `v3_<folder name>`, whichever pipeline made it.

## 8. What each test leaves behind

| File | Content |
| --- | --- |
| `<T>/budget.jsonl` | Every call reserved and spent |
| `<T>/runs/<manual>/<run>/` | Graph, report, state of every step, archived provider responses |
| `<T>/kpi.json` | The judgement: claims found per run, judge usage |
| `<T>/comparison/COMPARISON.md` | The table of section 3 for every manual and system, with ▲ ＝ ▼ |
| `<T>/losses/` | For each run, the stage where each lost claim stopped |
| `<T>/cards/SCHEDE.md` | Quality card of every graph |
| `<T>/precision/` | Blind sheets and, apart, their keys |
| `<T>/NOTES.md` | What was changed between repeats and why; failed runs are listed, not removed |

## 9. Not covered yet

- The agent benchmark (questions derived from the gold, answered with the graph,
  with retrieval on the PDF and by direct extraction) is not built.
- External baselines are not installed.
- Pages with no usable text are read by `kg_v4` from their image; V3 reads them only
  where Tesseract is installed. The transcription has been checked by an AI on a
  few pages of one scanned manual, not measured.
- The blind-sheet tool was written for V3 graphs; the new graphs have the same
  shape, and this is checked at T1 before T4 relies on it.
