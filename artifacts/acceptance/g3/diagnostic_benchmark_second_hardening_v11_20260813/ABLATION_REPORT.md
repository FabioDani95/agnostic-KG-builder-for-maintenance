# Ablation report

## Question under test

Is quality primarily improved by a larger model/more calls, or by deterministic structure,
typed completion, recovery, and complete accounting?

## Results

| Variant | Key change | Calls | Actual / charged USD | E / D / G semantic recall | Autonomous witnesses | Gate result |
|---|---|---:|---:|---|---|---|
| Prior hardening | broad windows, sparse recovery | 42 | 0.17744478 | 4/8, 6/8, not evaluated | 0, 3, n/a | NO-GO |
| v9 | deterministic rows + typed compiler | 75 | 0.28842689 | 7/8, 8/8, 16/18 | 6, 5, 15 | intermediate; two deterministic Graco drops |
| v9 compiler replay | remove unsupported optional context only | **0 new** | **0** | Graco 16/18→18/18 under final evaluation | Graco publish 15→17 | proves non-model recovery value |
| v10 | material recovery + evaluator normalization | 72 | 0.23458117 actual / 0.32585867 fail-closed | 7/8, 8/8, 18/18 | 7, 5, 17 | NO-GO: accounting mismatch; Eastman scope broad |
| **v11** | atomic prose branches + section boundary + exception accounting | **87** | **0.23741620** | **7/8, 8/8, 18/18** | **3, 5, 17** | **GO** |

Recall values for v9/v10 above use the final evaluation-only analyzer so the comparison is
consistent. They do not retroactively make those code versions releasable.

## Interpretation of individual ablations

### Deterministic inventory before LLM: required

Graco exposes 18 table branches deterministically and v11 accounts for all 18. Eastman
expands from 7 broad prose records to 22 structure-bounded branches. The improvement is
not merely more requests: each extra request corresponds to an independent source record
and carries a smaller allowed evidence set.

### Two-phase pipeline: required

The effective phases are (1) record/branch structure and exact spans, then (2) typed
semantic extraction. Moving pairing into phase 1 prevents the LLM from inventing joins.
The compiler/canonicalizer/publication stages then operate on stable occurrence lineage.

### Typed completion: necessary but insufficient

Structured Outputs eliminates output-shape ambiguity, yet v9 still showed an unsupported
optional field and v10 still showed unsafe scope and accounting failures. Schema validity
must be combined with literal evidence validation and structure-owned pairing.

### More calls: selectively necessary

V11 uses 87 calls versus 42 in the previous hardening campaign, but remains below the old
noisy Eastman-only baseline of 96 calls / USD 0.320466. The increase is justified by the
48 atomic source windows and bounded recovery, not by retrying the same ambiguous prompt.
Eastman used 37 calls because it contains 22 atomic prose windows; Danfoss and Graco stayed
at 21 and 29.

### Luna/Terra routing: bounded safety net, not main driver

Luna handled 82/87 calls. Terra handled only 5 selected recovery windows (2 Eastman,
2 Danfoss, 1 Graco). Earlier runs showed that selecting Terra as a replacement could lose
valid primary content. Verified union composition is useful, but global Terra routing is
not supported by the ablation evidence.

### Compiler recovery: high leverage when relation-safe

The Graco zero-call replay repaired exactly two records by discarding an unsupported
optional context field. It did not relax required evidence, create components, or add
relationships. This is the right class of deterministic recovery: remove unsupported
decoration while preserving the grounded core.

### Evaluation normalization: necessary for measurement, not production

The analyzer now normalizes PDF line-break hyphenation and conservative morphology and
requires discriminating tokens for forbidden matches. This removed false negatives and
false forbidden positives without changing the golden, threshold (0.55), or any production
decision. The golden remains post-generation only.

## Conclusion

The supported combination is: deterministic inventory + two-phase structure/semantics +
typed completion + literal compiler validation + relation-safe deterministic recovery +
bounded Luna/Terra union + fail-closed accounting. Neither “more model” nor “more calls”
alone explains or guarantees the result.
