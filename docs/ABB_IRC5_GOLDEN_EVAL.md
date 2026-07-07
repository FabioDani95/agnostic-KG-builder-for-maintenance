# ABB IRC5 Trouble Shooting — Golden Fixture Evaluation

**Fixture:** `abb_irc5_controller_troubleshooting_manual`
**Status:** frozen (Phase B complete, gates set)
**Calibration date:** 2026-07-06

## Source

- **PDF:** ABB Robotics, *Operating manual — Trouble shooting, IRC5*,
  document ID 3HAC020738-001, revision K (© 2005-2010 ABB), 80 pages.
  Local copy: `data/3cd2ff8d-2741-44e2-9e20-2ff679b34dd2.pdf` (several
  duplicate uploads of the same PDF exist in `data/` under other UUIDs).
- **Diagnostic scope:** chapter 3 *Troubleshooting by fault symptoms*
  (sections 3.1–3.16). The fixture keeps eight symptom sections verbatim
  (3.1, 3.2, 3.4, 3.5, 3.9, 3.12, 3.13, 3.14, 3.15) plus cover, index,
  manual overview, one safety page (ESD) and one chapter-4 stub page as
  distractors. Page numbers in the fixture are **PDF page numbers** (the
  printed page numbers are offset by −2 and appear in cross-references
  inside the text; they are left as-is).

## Difficulty axis

Prose troubleshooting with **symptom-level pairing**: each section lists
possible causes "in order of probability" and a *separate* numbered action
table. The cause→action pairing is mostly implicit (positional), so the
extractor must reconstruct atomic FailureMode→CorrectiveAction chains from
two parallel lists. One annotated chain (3.9 joystick) deliberately has no
corrective action, because the manual's actions for that symptom are
symptom-level checks that do not map to the cause.

## Expected sample (12 chains)

4–12 chains per §3.2 of the protocol; this fixture annotates 12 across all
eight kept symptom sections, including the safety-critical ones a domain
expert would prioritise (manipulator crashes on power down, brakes not
releasing). Every chain is verifiable against a specific line of the kept
pages. No error codes exist in the kept pages, so no error-code-rooted
chains and no `min_error_codes` export check.

## Calibration runs (Phase B)

| Run | Report | Recall | unsupported_rate | Blocking reviews | Notes |
|---|---|---|---|---|---|
| 1 | `eval_runs/20260706T172744Z` | 1.0 (12/12) | 0.0 (0/40) | 0 | full report; 28 extra-grounded chains |
| 2 | `eval_runs/20260706T173538Z` (artifacts only) | 1.0 (12/12) | 0.0 (0/76) | 0 | run aborted on the *next* fixture (OpenAI `insufficient_quota`); ABB artifacts complete, metrics recomputed offline from `artifacts/` with the harness matcher |

Model: `gpt-5.4`, mode `full`. Run 1 cost ≈ $0.88, 160k tokens, ~222 s
(from `run_metrics`; prices as configured in the metrics service on the run
date). Code version: working tree at commit following `f8d79af` (fixture
introduction commit).

## Gates (set from observed behaviour)

- `min_recall: 0.85` — observed 1.0 on both runs; floor set below the
  observed stable value per §6 step 7 (real-model recall oscillates ±0.1 on
  identical code).
- `max_unsupported_rate: 0.0` — zero hallucinated chains in both runs.
- No `forbidden_chains`: no contamination observed in either run.

## Annotation decisions worth remembering

- Symptom names are the section titles (e.g. "All LEDs are OFF at
  Controller") because that is the manual's own wording.
- Cause phrasing keeps the manual's identifiers ("main fuse (Q1)",
  "circuit breaker F6", "brake contactor (K44)", "24V BRAKE") — token-based
  matching relies on these anchors.
- The two "hot gearbox oil" duplicated action blocks (3.12/3.13) are left
  as-is in the fixture; they are a realistic source of extra grounded
  chains, not contamination.
