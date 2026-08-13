# Final verification — PDF diagnostic hardening v8

Date: 2026-08-12

## Code and offline verification

- Complete repository suite after the final compiler/gateway changes: **543 passed,
  0 failed, 0 errors, 0 skipped** in 64.631 seconds.
- Ruff across `backend`, `scripts`, `tests` and the campaign runner/analyzer: **pass**.
- `git diff --check`: **pass**.
- Deterministic EvidenceUnit replay: Eastman 8 windows, Danfoss 6, Graco 18; all
  uniqueness, membership, bounded-support and cross-row isolation invariants pass.
- Persisted-candidate replay after the final mechanical repair used zero real calls:
  Eastman 9 review/2 gap → 8 review/3 gap/0 publish; Danfoss unchanged at
  3 publish/3 review/2 gap. Non-exact and ellipsis-bearing quotes remain review.

JUnit: `final_test_suite.xml`
Record-window replay: `post_campaign_record_window_replay.json`
Candidate replay: `post_campaign_candidate_replay.json`

## Frozen inputs and ordinary configuration

- `golden.json` SHA-256:
  `c92ba0a8bcb1721055f6fc8c10c3d0a6a57eb3dc35134755d06574d6272a5291`
- `KPI_PROTOCOL.md` SHA-256:
  `1f29839ea4bd7fc3ec5346c06ed287b812429a3358fffa818e53fd20827db00d`
- `config.yaml` SHA-256:
  `890fb78193811a0331813b6f6956b4b391fb8a20492d8e5b80f082e099b9b0fa`
- `config.yaml` is byte-identical to commit `0548796`. Ordinary caps are restored:
  Luna low, diagnostic output 8000, Terra escalation disabled/max 0, preferred/hard
  PDF cost caps 0.35/0.49.

The golden and protocol were never edited.

## Real campaign execution

| Manual | Terminal state | Calls | Cost USD | Latency | Revision |
|---|---|---:|---:|---:|---|
| Eastman | completed | 22 | 0.11938223 | 297.179s | reviewing, non-approvable |
| Danfoss | completed | 18 | 0.05541445 | 133.659s | reviewing, non-approvable |
| Graco | stopped_without_retry at post-scoping preflight | 2 | 0.00264810 | 6.954s | none |

Shared authoritative budget ledger:

- 42 reservations / 42 finalizations;
- USD 0.17744478 actual and charged;
- USD 0.82255522 remaining of USD 1.00;
- zero active reservations, budget breaches, orphan finalizations or unknown costs;
- 40 succeeded and 2 failed-with-observed-usage calls;
- no full-manual retry.

The route-local Graco ledger reports no ontology calls because no revision/metrics were
created; the shared pre-call ledger authoritatively retains its two paid scoping calls.

## Mutation audit

- Three distinct workspaces, sources, operational databases and raw stores.
- No revision approved, rejected or merged.
- No canonical graph mutation.
- No structured source processed.
- No production rule contains the benchmark vendors, manual IDs, frozen pages or gold
  claim text.

## Release decision

**NO-GO.** Macro semantic recall is 41.67% against the frozen 78% floor. Danfoss passes
at 6/8; Eastman is 4/8 with zero autonomous witnesses and incomplete accounting; Graco
did not reach ontology generation. Completed revisions retain strict safety invariants,
but diagnostic recall and full three-manual evaluability remain release blockers.
