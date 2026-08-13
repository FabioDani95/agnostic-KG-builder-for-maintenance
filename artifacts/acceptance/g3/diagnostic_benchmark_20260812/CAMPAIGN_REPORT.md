# PDF G3 diagnostic benchmark - final report

Frozen gold and KPI protocol were prepared before the real generations. Each PDF was generated exactly once; no revision was approved, rejected or merged.

| Manual | Gold recall | Floor | Autonomous paths relevant to gold | All published paths | Fail-closed integrity | Cost (USD) | Calls |
|---|---:|---:|---:|---:|---|---:|---:|
| eastman_e554 | 2/8 (0.250) | 0.750 | 0 | 12 | pass | 0.062266 | 19 |
| danfoss_apf | 1/8 (0.125) | 0.750 | 1 | 1 | pass | 0.037005 | 18 |
| graco_check_mate_200 | 0/18 (0.000) | 0.833 | 0 | 0 | pass | 0.036287 | 14 |

## Campaign verdict

**NO_GO**. Macro gold recall 0.125 versus floor 0.780. Measured spend USD 0.135558 of USD 3.00; 51 calls in 445.4 seconds.

## Critical interpretation

- Page discovery retained every frozen gold page, so the principal failure is downstream of retrieval.
- Graco published only Asset/Component structure. The dense troubleshooting table produced no diagnostic path and candidate accounting remained incomplete.
- Danfoss published one correct table branch (Fuse blowout -> broken input fuse -> contact service personnel); the remaining table branches stayed in review/unaccounted states, including inspection-only rows that were not persisted as traceable explicit gaps.
- Eastman published twelve complete paths, but none matches the frozen troubleshooting sample. Two of eight frozen claims survive only as traceable review records (vacuum filters and focusing lens). The published paths are mostly maintenance instructions reframed as diagnostic paths.
- Schema and exact EvidenceRef checks pass for all three revisions, and the revisions correctly remain non-approvable. This is good fail-closed behavior, not evidence of useful diagnostic completeness.
- Review artifacts persist reasons and evidence anchors but not the rejected typed records. That makes post-run semantic audit of latent candidates unnecessarily difficult.

## Recommended next fixes

1. Fix deterministic-ID collisions for repeated actions/causes within dense tables, preserving row identity without duplicating semantic nodes.
2. Persist every typed diagnostic candidate and its compiler disposition, even when publication fails.
3. Treat troubleshooting tables as row/branch structures and test row lineage before broad extraction of maintenance procedures.
4. Rerun this frozen suite only after the compiler/accounting fixes; do not tune the gold to these outputs.
