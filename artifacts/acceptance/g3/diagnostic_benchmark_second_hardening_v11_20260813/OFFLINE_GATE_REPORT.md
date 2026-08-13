# Offline gate report

## Result

**PASS.** The final v11 production code was replayed against the persisted real
EvidenceUnits and candidates after the real campaign.

## Test suite

- 558 tests collected;
- 558 passed;
- 0 failures, 0 errors, 0 skipped;
- JUnit artifact: `final_test_suite.xml`.

Coverage includes targeted unit tests and integration tests for relation-lineage dedup,
table/prose atomization, exact scope restriction, inspection/action separation, structural
ambiguity without an LLM call, endpoint completion, adaptive output caps, durable budget
accounting, compiler recovery, section boundaries, and SDK parse-exception accounting.

## Deterministic record-window replay

`offline_record_window_replay.json` rebuilt windows from the real EvidenceUnits:

| Manual | Windows | Result |
|---|---:|---|
| Eastman | 22 | pass |
| Danfoss | 8 | pass |
| Graco | 18 | pass |

All manuals pass: unique window IDs, unique branch occurrences, existing anchors,
root-in-scope, bounded support, anchor-bounded literal scopes, and atomic-only pairing.

## Persisted-candidate compiler replay

`offline_candidate_replay.json` recompiled all persisted v11 typed candidates with zero
real calls:

| Manual | Candidates | Before disposition | After disposition | Changed |
|---|---:|---|---|---:|
| Eastman | 31 | 4 publish, 10 review, 16 gap, 1 exclude | identical | 0 |
| Danfoss | 8 | 5 publish, 3 gap | identical | 0 |
| Graco | 18 | 17 publish, 1 gap | identical | 0 |

Generation-response and operational-database SHA-256 digests are recorded in the replay
artifact. The replay therefore confirms that the checked-in final compiler reproduces the
real-run dispositions and needs no hidden online recovery.

## Repository hygiene checks

- `git diff --check`: pass;
- frozen golden unchanged and referenced only by evaluation artifacts;
- no vendor, manual, page, or claim-gold production rule was introduced;
- prior dirty-tree changes were preserved; no reset, checkout, or commit was performed.
