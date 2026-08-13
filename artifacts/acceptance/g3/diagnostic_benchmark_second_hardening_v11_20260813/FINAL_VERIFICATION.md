# Final verification

## Release-gate statement

The exact v11 code/config recorded by all three runtime profiles meets every frozen semantic
floor and every mandatory publication-integrity invariant. The campaign verdict is `go`.

This verdict authorizes progression past the benchmark gate only. It does not authorize an
automatic approval/merge: each revision is still `reviewing` and `approval_eligible=false`.

## Frozen KPI verification

- Eastman semantic recall: 87.50% ≥ 75%; autonomous recall: 37.50%.
- Danfoss semantic recall: 100% ≥ 75%; autonomous recall: 62.50%.
- Graco semantic recall: 100% ≥ 83.33%; autonomous recall: 94.44%.
- Macro semantic recall: 95.8333% ≥ 78%; macro autonomous recall: 73.53%.

## Safety verification

- zero forbidden pairings and zero unsupported published paths;
- 1,928/1,928 exact literal EvidenceRefs;
- strict schema/domain/range/endpoint/graph validation passes;
- no isolated diagnostic nodes;
- every action has incoming `RESOLVED_BY`;
- one canonical original Asset per source;
- complete branch lineage through canonicalization/publication;
- no cross-row Cartesian product;
- complete candidate, window, page and evidence accounting;
- explicit inspection-only gaps remain gaps;
- blocking review/accounting states keep approval fail-closed.

## Execution verification

- three authenticated completed real runs, each in an isolated workspace and DB;
- 87 calls: 82 Luna, 5 Terra;
- USD 0.23741620 actual and charged;
- 87 durable reservations and 87 finalizations;
- zero failed ledger entries and zero unknown actual costs;
- 727.656 seconds total;
- 558/558 final tests passed;
- deterministic record replay and persisted-candidate replay passed.

## Residual risks

1. Eastman retains one missing frozen claim (E5) and substantial review burden. Four of its
   seven semantic witnesses are deliberately non-autonomous after safer layout splitting.
2. Structural extraction remains high-volume (267 Component nodes across the three
   revisions) and generates canonicalization review. The diagnostic subgraph is strict,
   but the surrounding structural graph still needs a separate precision benchmark.
3. The three-manual set demonstrates the frozen gate, not generalization to arbitrary
   manuals. Add structure-stratified holdout manuals before unattended production use.
4. Review quality and reviewer throughput are not measured by recall. They require their
   own acceptance test before enabling approvals at scale.

## Recommended next gate

Keep v11 as the diagnostic acceptance baseline. Do not increase Terra share globally.
The next cycle should measure structural-component precision and review calibration on a
vendor-independent holdout set, while preserving the deterministic inventory, exact scope,
lineage, and durable accounting invariants introduced here.
