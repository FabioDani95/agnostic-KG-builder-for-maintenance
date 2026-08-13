# PDF G3 diagnostic pipeline — current v11 baseline

Last updated: 2026-08-13

## Status

The current production path is `pdf-g3-atomic-record-publication-v11`.
It is the normal workspace PDF G3 path, not a benchmark-only fork. The PDF
generator builds deterministic diagnostic record windows before typed semantic
extraction, then uses the normal compiler, canonicalizer, publication gate and
accounting services.

The frozen three-manual campaign verdict is **GO for the semantic KPI and
publication-integrity gate**. It is not an approval or merge decision. All
three generated revisions remain `reviewing` and `approval_eligible=false`.

| Manual | Semantic recall | Autonomous recall |
|---|---:|---:|
| Eastman E-554 | 7/8 = 87.50% | 3/8 = 37.50% |
| Danfoss APF | 8/8 = 100% | 5/8 = 62.50% |
| Graco Check-Mate 200 | 18/18 = 100% | 17/18 = 94.44% |
| **Macro** | **95.8333%** | **25/34 = 73.53%** |

The real campaign used 87 calls (82 Luna, 5 selective Terra), cost
USD 0.23741620 and took 727.656 seconds. The durable ledger reconciles 87
reservations and 87 finalizations with zero unknown costs or failures.

## Current architecture

1. Canonical PDF EvidenceUnits form the immutable literal inventory.
2. A deterministic, vendor-independent pass identifies table/prose roots and
   produces exact, bounded atomic branches.
3. Structured Outputs extract typed semantic candidates inside each scope.
4. The compiler validates literal evidence and assigns publish, review, gap or
   exclude dispositions.
5. Deterministic recovery may remove unsupported optional decoration but may
   not invent required nodes or relations.
6. Bounded Terra recovery is composed with the Luna primary only when the
   branches are complementary and evidence-safe.
7. Canonicalization preserves `branch_lineage_id` on relation occurrences.
8. Publication, approval and accounting remain separate fail-closed gates.

The implementation contains no rule keyed by Eastman, Danfoss, Graco, vendor,
manual name, benchmark page or golden claim. The golden is used only by the
post-generation campaign analyzer.

## Verified invariants

- zero forbidden cross-pairings and unsupported published paths;
- 1,928/1,928 exact literal EvidenceRefs;
- strict schema, domain, range, endpoint and topology validation;
- no isolated diagnostic nodes;
- every CorrectiveAction has incoming `RESOLVED_BY`;
- one original canonical Asset per manual;
- branch lineage complete through publication;
- no cross-row Cartesian product;
- complete record/window/page/evidence accounting;
- inspection-only material remains a gap, not a restorative action;
- revisions with review or accounting problems remain non-approvable.

Final offline verification: 558/558 tests, 48/48 deterministic real-EvidenceUnit
windows passing all structure invariants, and a zero-call replay of 57 persisted
typed candidates with no changed disposition.

## Reproducibility

- recorded Git HEAD: `054879670aea2dbf0dca59f5728a29a096453d11`;
- dirty code-tree digest:
  `a393c883c1072ce5fa5b6589791dfa9bd296d7545234db5b0d3205e16df9eb95`;
- effective configuration digest:
  `6596187241ebcccc123daf143e0c76de11c9edbfd9479dc01b206e18735b61fd`;
- frozen golden digest:
  `c92ba0a8bcb1721055f6fc8c10c3d0a6a57eb3dc35134755d06574d6272a5291`;
- PyMuPDF: `1.27.1`.

Authoritative evidence is under
`artifacts/acceptance/g3/diagnostic_benchmark_second_hardening_v11_20260813/`:

- `CAMPAIGN_REPORT.md`;
- `ROOT_CAUSE_ANALYSIS.md`;
- `ABLATION_REPORT.md`;
- `FINAL_VERIFICATION.md`;
- `OFFLINE_GATE_REPORT.md`;
- `campaign_results.json`;
- complete real generation responses, runtime profiles and ledgers.

The isolated SQLite databases and duplicated raw PDF stores are retained
locally but ignored by Git. Their SHA-256 digests are recorded by the replay
artifacts; they are execution stores, not source-controlled report payloads.

## Limits and next acceptance step

The production rules are vendor-agnostic, but out-of-sample generalization is
not yet demonstrated. The rules were developed while observing three manuals
and assume common English diagnostic labels, adapter-provided table cells,
numeric/alpha lists and recognizable native-PDF layout.

The next meaningful gate is a blind holdout on an English, born-digital manual
from a new manufacturer and a structurally different equipment class. Freeze
the v11 code/config and the PDF SHA-256 before execution; keep operational
manifest data separate from the gold; run once; create the gold annotation only
after generation. Do not tune on that result and still call it a holdout.

Later holdouts should separately introduce complex tables, scanned/OCR input
and non-English text. Structural-Component precision and reviewer calibration
also need their own metrics before unattended production use.
