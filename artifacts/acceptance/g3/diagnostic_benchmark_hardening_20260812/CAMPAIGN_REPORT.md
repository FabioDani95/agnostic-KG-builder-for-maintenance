# PDF G3 diagnostic hardening — before/after report

The golden and KPI protocol are the untouched frozen artifacts from the prior campaign.
One real generation was attempted per PDF in an isolated workspace/database. A terminal
preflight stop was not retried. No revision was approved, rejected, merged, or projected
into the canonical graph.

## Before/after by manual

| Manual | Semantic recall before → v8 | Autonomous before → v8 | Review burden before → v8 | Calls before → v8 | Cost USD before → v8 | Latency before → v8 |
|---|---:|---:|---:|---:|---:|---:|
| eastman_e554 | 2/8 → 4/8 | 0/8 → 0/8 | 54 (24 blocking) → 32 (10 blocking) | 19 → 22 | 0.062266 → 0.119382 | 212.5s → 297.2s |
| danfoss_apf | 1/8 → 6/8 | 1/8 → 3/8 | 25 (14 blocking) → 15 (6 blocking) | 18 → 18 | 0.037005 → 0.055414 | 120.6s → 133.7s |
| graco_check_mate_200 | 0/18 → 0/18 | 0/18 → 0/18 | 10 (3 blocking) → 0 (no revision) | 14 → 2 | 0.036287 → 0.002648 | 112.4s → 7.0s |

## Campaign decision

**NO-GO** — macro semantic recall 0.417 versus 0.780; USD 0.177445/1.00; 42 calls; 437.8s.

The release decision remains NO-GO unless all three per-manual floors, the macro floor,
and every publication-integrity gate pass. Danfoss passing at its exact floor cannot
offset Eastman or the unevaluated Graco ontology run.

## Durable shared budget ledger

Ledger reconciliation: **True**; 42 reservations, 42 finalizations; USD 0.177445 charged and USD 0.822555 remaining.
All actual costs observed: True; failures: none.

| Run | Calls | Reservations/finalizations | Models | Actual USD | Fail-closed charge USD |
|---|---:|---:|---|---:|---:|
| v8:danfoss_apf | 18 | 18/18 | gpt-5.6-luna×17, gpt-5.6-terra×1 | 0.055414 | 0.055414 |
| v8:eastman_e554 | 22 | 22/22 | gpt-5.6-luna×21, gpt-5.6-terra×1 | 0.119382 | 0.119382 |
| v8:graco_check_mate_200 | 2 | 2/2 | gpt-5.6-luna×2 | 0.002648 | 0.002648 |

The shared per-call ledger is authoritative. This attributes Graco's two paid scoping
calls even though the route-level run ledger has no ontology revision. The sum of isolated
run preflight envelopes was USD 1.689894; these are
not concurrent reservations. Every actual API call was separately reserved before dispatch
against the absolute USD 1.00 campaign ceiling.

## Per-claim result

| Manual | Claim | Expected witness | Present | Matched outcome | Best minimum field score |
|---|---|---|---|---|---:|
| eastman_e554 | E1 | complete_published_path | False | none | 0.000 |
| eastman_e554 | E2 | complete_published_path | False | none | 0.000 |
| eastman_e554 | E3 | complete_published_path | False | none | 0.000 |
| eastman_e554 | E4 | complete_published_path_or_traceable_review | True | traceable_review | 0.640 |
| eastman_e554 | E5 | complete_published_path | False | none | 0.000 |
| eastman_e554 | E6 | complete_published_path_or_traceable_review | True | traceable_review | 0.827 |
| eastman_e554 | E7 | complete_published_path_or_traceable_review | True | traceable_review | 0.823 |
| eastman_e554 | E8 | complete_published_path_or_traceable_review | True | traceable_review | 0.827 |
| danfoss_apf | D1 | traceable_explicit_gap | True | explicit_gap | 1.000 |
| danfoss_apf | D2 | traceable_explicit_gap | True | explicit_gap | 1.000 |
| danfoss_apf | D3 | complete_published_path | True | published_path | 0.750 |
| danfoss_apf | D4 | complete_published_path | False | none | 0.000 |
| danfoss_apf | D5 | complete_published_path | False | none | 0.000 |
| danfoss_apf | D6 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D7 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D8 | traceable_explicit_gap | True | explicit_gap | 0.672 |
| graco_check_mate_200 | G1 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G2 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G3 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G4 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G5 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G6 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G7 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G8 | traceable_explicit_gap | False | none | 0.000 |
| graco_check_mate_200 | G9 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G10 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G11 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G12 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G13 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G14 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G15 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G16 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G17 | complete_published_path | False | none | 0.000 |
| graco_check_mate_200 | G18 | complete_published_path | False | none | 0.000 |

## Critical interpretation by manual

### eastman_e554

- Recall is **4/8**: 0 autonomous published witness(es), 0 explicit inspection gap(s), and 4 traceable review witness(es). The frozen floor is 0.7500; pass=False.
- Autonomous claims: none; explicit gaps: none; review-only claims: E4, E6, E7, E8; missing claims: E1, E2, E3, E5.
- Published complete paths=0; outside frozen gold=0; forbidden pairings=0.
- Accounting complete=False; approval eligible=False; strict publication-integrity verdict=pass.
- Review burden: total=32, blocking=10; canonicalization_ambiguous=17, pdf_diagnostic_contract_incomplete=1, pdf_diagnostic_record_gap=2, pdf_diagnostic_record_review=6, pdf_node_provenance_unresolved=1, pdf_ocr_low_confidence=1, pdf_pipeline_blocked=1, pdf_pipeline_not_reviewable=1, pdf_pipeline_schema_noncompliant=1, pdf_relation_endpoint_omitted=1.
- The completed run remains fail-closed and non-approvable because candidate accounting is incomplete (diagnostic_contract_incomplete=1). Its review witnesses improve semantic traceability but provide no autonomous path.

### danfoss_apf

- Recall is **6/8**: 3 autonomous published witness(es), 3 explicit inspection gap(s), and 0 traceable review witness(es). The frozen floor is 0.7500; pass=True.
- Autonomous claims: D3, D6, D7; explicit gaps: D1, D2, D8; review-only claims: none; missing claims: D4, D5.
- Published complete paths=3; outside frozen gold=0; forbidden pairings=0.
- Accounting complete=True; approval eligible=False; strict publication-integrity verdict=pass.
- Review burden: total=15, blocking=6; canonicalization_ambiguous=6, pdf_diagnostic_record_gap=2, pdf_diagnostic_record_review=2, pdf_node_provenance_unresolved=1, pdf_ocr_low_confidence=1, pdf_relation_endpoint_omitted=1, pdf_schema_instruction_not_actionable=1, pdf_unreadable_pages=1.
- Candidate accounting is complete, but blocking evidence/layout review keeps the revision non-approvable. This is a safe review state, not autonomous coverage.

### graco_check_mate_200

- Recall is **0/18**: 0 autonomous published witness(es), 0 explicit inspection gap(s), and 0 traceable review witness(es). The frozen floor is 0.8333; pass=False.
- Autonomous claims: none; explicit gaps: none; review-only claims: none; missing claims: G1, G2, G3, G4, G5, G6, G7, G8, G9, G10, G11, G12, G13, G14, G15, G16, G17, G18.
- Published complete paths=0; outside frozen gold=0; forbidden pairings=0.
- Accounting complete=False; approval eligible=False; strict publication-integrity verdict=fail.
- Review burden: total=0, blocking=0; none.
- The one-shot ended as `stopped_without_retry` before an ontology revision existed: La costruzione semantica del PDF non è riuscita: PDF generation cost preflight failed: conservative maximum $0.627536 exceeds the $0.60 ceiling.
- Therefore graph counts and recall are zero for this campaign attempt, not a successful empty extraction. The shared ledger still records 2 paid scoping calls costing USD 0.002648; no retry was made.

## Exact publication and execution invariants

| Manual | Strict validation | Exact EvidenceRefs | Branch lineage | Zero isolated diagnostics | Every action linked | Canonical Asset | Forbidden / unsupported | Gold pages | Accounting / approval | Authenticated real run | No approve/merge/structured |
|---|---|---|---|---|---|---|---|---|---|---|---|
| eastman_e554 | True | 936/936 refs; 153/153 rels | True (0 rels; vacuous) | True | True | True | 0 / 0 | 3/3 (True) | False / False | True | True |
| danfoss_apf | True | 617/617 refs; 48/48 rels | True (9 rels) | True | True | True | 0 / 0 | 1/1 (True) | True / False | True | True |
| graco_check_mate_200 | False | 0/0 refs; 0/0 rels | False (no revision) | False | False | False | 0 / 0 | 0/1 (False) | False / False | False | True |

For completed revisions, strict validation, exact lexical grounding, branch-safe joins,
topology, canonical Asset identity, and zero forbidden pairings all pass. Graco's false
graph invariants mean `no revision to validate`; they do not describe published bad edges.

## Resolved versus remaining blockers

Resolved and demonstrated offline/where a revision completed: record-level segmentation,
repeated-entity collision safety, exact adjacent multi-unit evidence, system-owned row
lineage, rejected-candidate persistence, branch-aware relations, explicit inspection gaps,
and accounting/publicability separation. Danfoss demonstrates the intended mixed result:
three safe autonomous paths plus three traceable inspection gaps, with no cross-pairing.

Remaining blockers: Eastman is below its recall floor, has zero autonomous gold paths and
incomplete candidate accounting; Graco never passed the post-scoping cost preflight, so its
18-claim ontology behavior was not evaluated by this one-shot. Those failures dominate the
macro result. The correct critical decision is **NO-GO** even though all paid calls stayed
well inside the absolute budget and completed revisions retained strict safety invariants.
