# Root-cause analysis — PDF diagnostic recall collapse

Date: 2026-08-12
Starting commit: `0548796`
Frozen comparison campaign: `diagnostic_benchmark_20260812`

## Executive finding

The 12.5% macro recall was not caused by PDF scoping: every frozen gold page was
retained. It was caused by a recall architecture that removed the baseline recovery
passes while simultaneously requiring one model response to satisfy a new, brittle
typed evidence contract.

Commit `136fb45` made the main architectural recall trade-off: role-partitioned PDF
chunks became relation-first, the separate relation and semantic-validation passes
were bypassed, reflective retries were disabled, and legacy coverage/resolution
completion no longer ran. Commit `0548796` then added the strict typed compiler and
selective escalation framework, but left escalation disabled and changed ontology
reasoning from Luna medium to Luna low. Precision and fail-closed behavior improved;
there was no typed replacement for the 77 Eastman calls that previously performed
relation extraction, validation, re-extraction, coverage, and resolution recovery.

Model quality was therefore only one factor. Several deterministic defects could erase
or reject correct source records regardless of model choice.

## Evidence from the frozen artifacts

| Eastman path | Calls | Recall | Important behavior |
|---|---:|---:|---|
| Pre-hardening Luna baseline | 96 | 8/8 | 18 relation, 29 validation, 10 re-extraction, 1 coverage, 17 resolution calls |
| Frozen typed campaign | 19 | 2/8 semantic, 0/8 autonomous | Luna low; no relation/validation/completion/recovery calls |
| Hardened v8 real run | 22 | 4/8 semantic, 0/8 autonomous | record windows + Luna medium + one selective Terra window |

The pre-hardening 8/8 result was not a safe target architecture: it contained 399
nodes, 369 relations, 33 isolated nodes, two imperfectly grounded relations and about
250 review items, at USD 0.320466 for Eastman alone. The objective was to recover its
diagnostic coverage without restoring that permissive graph.

In the frozen typed campaign, the dominant persisted record failures were:

- Eastman: 14 `quote_not_in_anchored_evidence`, 9 `missing_actions`, 3
  `lineage_anchor_outside_bundle`, plus check/action and missing-claim failures.
- Danfoss: 9/9 reviewed records had `quote_not_in_anchored_evidence`; 6 also had
  lineage failures.
- Graco: the dense typed response approached its 8k cap and the complete record set
  disappeared after a compiler exception; only unrelated exclude dispositions remained.

## Causal mechanisms

### 1. Page chunks were the wrong unit of diagnostic reasoning

The current workflow packed up to eight pages plus overlap. A dense troubleshooting
table therefore had to be reconstructed into many complete typed branches in one
response. Graco page 11 already contained canonical table EvidenceUnits with row
indices, but the model received a page-scale diagnostic chunk. This caused large output,
branch contamination and truncation risk even though record boundaries were already
available deterministically.

### 2. Repeated semantic entities could erase a complete chunk

Node IDs were semantic and intentionally excluded provenance. `CorrectiveAction`,
however, stored a row-specific `source_reference`. Two rows containing the same action
therefore produced the same ID and different node values. The compiler raised a
deterministic-ID collision; the chunk-level exception handler replaced the entire parsed
output with an empty record list. The observed repeated “clear restriction” action in
Graco reproduced this failure offline.

### 3. Evidence exactness was coupled to a single anchor

The compiler required each model quote to occur in one EvidenceUnit. Problem, cause and
remedy text often crossed adjacent native blocks or pages. A list of atomic exact spans
was supported in theory, but a model-produced combined quote could not be decomposed.
This rejected semantically correct records while correctly refusing fuzzy grounding.

The real v8 run exposed the remaining variant: a quote can be exact elsewhere inside
the immutable record window but echoed with the wrong anchor, or contain a synthetic
ellipsis. The former can be repaired deterministically only when the exact in-window
match is unique; the latter must remain review.

### 4. Lineage validation amplified evidence failures

Record and branch anchors were supplied by the model, then checked against the subset
of spans that had already resolved. A quote failure could consequently generate a
second lineage failure. Cross-page/table header choices also conflicted with a stricter
compiler rule than the prompt described. Lineage needed to be assigned by the
system-owned row window and validated independently from claim grounding.

### 5. Rejected paid output was not auditable

Compilation reports persisted dispositions, reason codes and some EvidenceRefs, but not
the original typed candidate. A compiler exception could remove even those entries.
This made accounting incomplete and prevented deterministic offline replay of the exact
failure. Merge deduplication could also suppress conflicting overlap observations.

### 6. Accounting conflated “disposed” with “publishable”

The old metric required `unresolved_count == 0`, so a correctly persisted inspection gap
made `diagnostic_accounting_complete=false`. Record/branch anchors were also added after
the accounted-evidence set was computed. Accounting must answer whether every inventoried
window has a durable disposition; approval eligibility must separately answer whether
blocking review remains.

### 7. Inspection and maintenance semantics were not a publication gate

The compiler could publish an action-stated record even when its instruction was only
“check” or “inspect”. Actionability warnings happened later and did not stop diagnostic
nodes. This explains how maintenance/checklist material could become synthetic
troubleshooting while genuine table rows stayed in review.

### 8. Recovery existed only as a disabled, coarse replacement

Terra eligibility was triggered by any unresolved record, including legitimate gaps;
it retried a whole chunk and selected one result by counts rather than preserving the
union of compatible attempts. Legacy completion was unsafe to restore because it reused
one EvidenceRef across distinct edges. Recovery had to be per record window, restricted
to mechanical/incomplete failures, and compiled with evidence for every edge.

### 9. Budget protection was run-level, not call-level

The frozen runner checked a manual envelope before generation and wrote actual cost at
the end. It did not reserve the cumulative worst case immediately before each provider
call. A crash or concurrent run could therefore leave spend unaccounted. The v8 campaign
also revealed a separate operational issue: Graco's post-scoping envelope was USD
0.627536, above the temporary USD 0.60 manual ceiling, so the one-shot stopped before
ontology despite USD 0.941937 remaining globally. It was not retried.

## Generic corrections implemented

- Deterministic record/table-row windows precede the LLM. Blank symptom cells forward
  fill only within one logical table; prior row causes/remedies are never exposed.
- `window_id`, allowed anchors, record anchor and branch anchor are system-owned.
- Semantic nodes are reusable across rows; provenance lives on grounded branch-aware
  relation occurrences, removing repeated-action collisions and Cartesian projections.
- Exact composite quotes can be split only over unique adjacent canonical EvidenceUnits.
  A model-misrouted quote can move to another anchor only when it has one normalized
  verbatim match inside the immutable window and the same source page. No fuzzy,
  ellipsis, ambiguous or cross-window evidence is accepted.
- Every parsed, rejected, truncated or compiler-failed window receives a durable payload,
  attempt metadata, disposition, reason codes and referenced/resolved evidence inventory.
- Inspection-only records become explicit gaps and emit no partial diagnostic nodes.
- Accounting is inventory-to-disposition completeness; review/gap remains independently
  blocking for approval.
- Luna medium is the acceptance primary. Terra medium can recover at most one eligible
  failed window per manual; it is not a whole-manual replacement.
- A shared atomic JSONL ledger reserves and fsyncs every worst-case envelope before the
  provider call, then replaces it with observed usage. SDK-internal retries are disabled
  while this guard is active.

No production rule contains a vendor, manual identifier, frozen page number or gold
claim text.

## What the real campaign proved

### Danfoss

Recall improved from 1/8 to 6/8 at the exact 75% floor: D3, D6 and D7 were autonomous
grounded paths; D1, D2 and D8 were correct explicit inspection gaps. D4 and D5 remained
missing. Accounting was complete, forbidden pairings were zero, diagnostic branch
lineage was complete, and the revision stayed non-approvable.

### Eastman

Semantic traceability improved from 2/8 to 4/8, but E4/E6/E7/E8 were all review-only;
autonomous recall stayed 0/8. All eight windows received dispositions, but one Luna
response exhausted 6000 completion/reasoning tokens and its single Terra recovery
exhausted 4000. The aggregate typed contract was therefore incomplete. The durable
ledger exposed remaining exact-anchor/lineage and inspection-status failures rather
than losing them.

### Graco

Offline replay still deterministically produces 18 safe table-row windows with no ID
collision. The real one-shot, however, ended after two scoping calls because the
post-scoping cost envelope exceeded the temporary per-run cap. No revision existed, so
0/18 is a campaign failure/unevaluated ontology run, not evidence of a successful empty
extraction. The manual was not retried.

## Post-campaign offline replay

The real responses were not mutated or re-scored as campaign outputs. Their persisted
typed candidates were replayed through the final deterministic compiler with zero API
calls. Eastman changed from 2 gap / 9 review to 3 gap / 8 review: system-owned lineage
removed four spurious lineage-only reasons, and unique exact in-window relocation removed
quote errors from two records. No record became publishable because the remaining
inspection-status and missing-failure semantics correctly stayed fail-closed. Danfoss
remained 3 publish / 2 gap / 3 review because its residual quotes contained omitted
intermediate text or ellipses and were not exact. This replay demonstrates that the
mechanical repairs do not weaken grounding or manufacture recall.

## Conclusion

The implementation fixes the principal deterministic data-loss, pairing, persistence
and accounting defects while preserving strict publication safety. It materially
improves Danfoss and review traceability, but it does not meet the release objective:
macro recall is 41.67% versus 78%, Eastman has zero autonomous gold paths, and Graco was
not evaluated beyond scoping. The correct decision is **NO-GO**.
