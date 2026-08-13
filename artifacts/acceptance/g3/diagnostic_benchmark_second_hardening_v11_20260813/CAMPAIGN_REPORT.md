# PDF G3 diagnostic second hardening — v11 campaign report

## Decision

**GO for the frozen KPI and publication-integrity gate.** This is not an automatic
approval of any generated revision: all three revisions remain in `reviewing` and are
`approval_eligible=false` because review items or explicit gaps are still present.

The untouched frozen golden was used only after generation by the campaign analyzer.
No golden claim, vendor, manual, or page identifier entered production prompts,
segmentation, routing, configuration, or compiler rules.

| Manual | Semantic recall | Floor | Autonomous recall | Traceable non-autonomous witnesses | Calls | Cost USD | Time |
|---|---:|---:|---:|---:|---:|---:|---:|
| Eastman E-554 | 7/8 = 87.50% | 75% | 3/8 = 37.50% | 4 review; 1 missing | 37 | 0.12311593 | 377.233 s |
| Danfoss APF | 8/8 = 100% | 75% | 5/8 = 62.50% | 3 inspection-only gaps | 21 | 0.05830691 | 146.944 s |
| Graco Check-Mate 200 | 18/18 = 100% | 83.33% | 17/18 = 94.44% | 1 inspection-only gap | 29 | 0.05599336 | 203.479 s |
| **Macro** | **95.8333%** | **78%** | **25/34 = 73.53%** | 8 accounted non-autonomous/missing | **87** | **0.23741620** | **727.656 s** |

Eastman's four review witnesses are claim-traceable but not counted as autonomous.
The missing witness is E5. Danfoss D1, D2, D8 and Graco G8 are explicit
inspection-only gaps, not corrective actions.

## Mandatory invariants

All publication-integrity checks passed for every completed revision:

- forbidden cross-pairings: 0;
- unsupported published paths: 0;
- exact literal EvidenceRefs: 1,928/1,928; relation EvidenceRefs: 338/338;
- schema, domain, range, endpoint and graph invariant errors: 0;
- isolated diagnostic nodes: 0;
- every CorrectiveAction has an incoming `RESOLVED_BY`;
- exactly one original canonical Asset per manual;
- branch lineage complete and joinable through publication;
- no cross-row Cartesian products;
- every candidate window, page, and evidence anchor has a terminal disposition;
- no revision was approved, merged, projected, or structured-processed.

| Manual | Atomic windows | Disposed compiler records | Accounting states | Review total / blocking | Approval eligible |
|---|---:|---:|---|---:|---|
| Eastman | 22 | 31/31 | 4 publish; 7 ambiguous; 12 inspection gap; 7 structural incomplete; 1 exclude | 48 / 21 | false |
| Danfoss | 8 | 8/8 | 5 publish; 3 inspection gap | 19 / 5 | false |
| Graco | 18 | 18/18 | 17 publish; 1 inspection gap | 23 / 1 | false |

The compiler record count can exceed the deterministic window count when verified
primary/recovery branches are composed. The accounting still requires every composed
record and every originating window to be disposed.

## Reproducibility and cost

- pipeline: `pdf-g3-atomic-record-publication-v11`;
- Git HEAD recorded before each run: `054879670aea2dbf0dca59f5728a29a096453d11`;
- dirty-code tree digest: `a393c883c1072ce5fa5b6589791dfa9bd296d7545234db5b0d3205e16df9eb95`;
- effective config digest: `6596187241ebcccc123daf143e0c76de11c9edbfd9479dc01b206e18735b61fd`;
- campaign runner digest: `b656f8a6a4da4e6a69af8147d04782de7d4dab6eda6bbf6e53f94f8322acf597`;
- PyMuPDF: `1.27.1`;
- frozen golden digest: `c92ba0a8bcb1721055f6fc8c10c3d0a6a57eb3dc35134755d06574d6272a5291`, marked `post_generation_evaluation_only`.

The durable ledger reconciles 87 reservations with 87 finalizations, zero failures,
zero unknown actual costs, and USD 2.76258380 remaining from the authorized USD 3.00.
Model routing was 82 Luna calls and 5 bounded Terra recoveries. Isolated workspace,
source, operational database, and raw-store checks all passed.

## Interpretation

The decisive intervention was architectural: a deterministic record inventory and
structure pass precedes typed semantic extraction. The LLM no longer decides which
physical table cells belong together. It receives exact field spans and a system-owned
branch policy. More calls are used only when the document exposes more independent
records; Terra is a bounded recovery route, not a global quality lever.

The remaining risk is concentrated in Eastman review burden and the broad structural
component graph. Therefore `GO` means the frozen diagnostic acceptance gate passes; it
does not mean review-free autonomous publication is ready.
