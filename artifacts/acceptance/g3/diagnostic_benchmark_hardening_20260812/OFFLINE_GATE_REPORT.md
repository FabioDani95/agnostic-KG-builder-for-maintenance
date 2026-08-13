# Offline gate — PDF diagnostic hardening v8

Date: 2026-08-12
Real OpenAI spend before this gate: **USD 0.00**

## Decision

**PASS.** The real campaign may start. No golden label, vendor, manual identifier,
page number, or expected claim text is used by production extraction.

## Root causes reproduced

1. Page-sized typed chunks forced dense tables into one near-8k response.
2. Repeated semantic actions had the same deterministic ID but a different
   row-specific `source_reference`, raising a collision that erased a complete chunk.
3. Quote validation accepted one lexical span in one EvidenceUnit only; real
   Problem/Cause/Remedy records often cross adjacent canonical blocks.
4. Lineage was checked against the subset of already-resolved quotes, causing
   quote errors to cascade into false lineage errors.
5. The typed path removed relation extraction, validation, re-extraction,
   coverage completion and resolution completion without replacing them with a
   typed, record-local recovery path.
6. Rejected candidates were represented only by reason codes and a few anchors.
7. Accounting incorrectly required zero gap/review records and omitted lineage
   anchors because of update order.

## Deterministic changes under test

- System-owned record/table-row windows before the LLM.
- Table symptom forward-fill limited to the same logical table; causes/actions
  from the prior row are never exposed.
- Stable semantic node identity with provenance kept on branch-aware grounded edges.
- Exact multi-unit quote splitting only over adjacent canonical EvidenceUnits.
- Full candidate payload, referenced/resolved evidence, disposition and attempts
  persisted in the immutable revision ledger.
- Inspection-only instructions publish no CorrectiveAction and become traceable gaps.
- Luna medium primary; at most one Terra medium recovery window per manual,
  eligible only for mechanical/incomplete typed failures.
- Durable campaign-wide per-call reservation ledger; reserve + fsync occurs before
  the client invocation and blocks before a call that exceeds the remaining USD 1.00.

## Tests

- Focused hardening/integration/acceptance gate: **84 passed**.
- Complete non-planned repository suite: **429 passed**.
- Ruff on all modified production/test files: **passed**.
- No test failure in the selected suites.

The focused fixtures cover repeated causes/actions, one cause with multiple
remedies, multiple causes under one symptom, exact adjacent multi-unit support,
non-contiguous rejection, cross-page records, row contamination, long-record
splitting, inspection-only gaps, compiler failure persistence, cost reservation,
and branch-aware projection.

## Replay of the frozen real EvidenceUnit inventories

| Manual | Windows | Kind | Result |
|---|---:|---|---|
| Eastman | 8 | contiguous record blocks (7 roots; one long root safely split) | PASS |
| Danfoss | 6 | troubleshooting table rows | PASS |
| Graco | 18 | troubleshooting table rows | PASS |

All window IDs and branch anchors are unique; every allowed anchor resolves to a
canonical EvidenceUnit; support is bounded; no non-root support unit is reused
across windows. Details are in `offline_record_window_replay.json`.

## Route-level mock replay of the three PDFs

| Manual | Calls | Conservative preflight | Windows disposed | Accounting | Approval |
|---|---:|---:|---:|---|---|
| Eastman | 22 | USD 0.569684 | 8/8 | complete | false |
| Danfoss | 17 | USD 0.473504 | 6/6 | complete | false |
| Graco | 27 | USD 0.574623 | 18/18 | complete | false |

The mock provider intentionally returned no typed records. Every omitted window
was nevertheless persisted as an explicit review disposition; accounting stayed
complete, while every revision remained non-approvable. This proves the required
separation between accounting and publication eligibility.

## Invariants demonstrated offline

- zero deterministic ID collisions;
- no cross-row or cross-branch pairing in compiler/projection fixtures;
- every published diagnostic relation has exact edge evidence;
- no partial/isolated diagnostic nodes are emitted from a gap/review;
- every published CorrectiveAction has an incoming `RESOLVED_BY` edge;
- canonical Asset identity remains system-owned;
- schema/domain/range/endpoint validation remains strict;
- accounting is complete for publish/gap/review/exclude dispositions;
- review/gap records remain blocking for approval.
