# Whirlpool W11187658 Dishwasher — Golden Fixture Evaluation

**Fixture:** `whirlpool_w11187658_dishwasher_manual`
**Status:** Phase A complete, **Phase B in progress — gates NOT set yet.**
Do not quote real-model numbers for this fixture as performance results
until Phase B is completed and this doc is updated.

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

### Remaining Phase B work (blocked on API quota)

1. Raise the retry output-token budget (or split dense chunks) and commit
   the change *before* calibration runs.
2. Re-run `--mode full` ≥ 2×; inspect `chains.json`; fix annotation
   phrasing only where the manual wording differs.
3. Set `min_recall` / `max_unsupported_rate` from observed behaviour and
   update this doc.

## Mock gate

Mock eval recall is 1.0 and `pytest` is green with this fixture included,
so it already serves as a deterministic CI regression guard while Phase B
is pending.
