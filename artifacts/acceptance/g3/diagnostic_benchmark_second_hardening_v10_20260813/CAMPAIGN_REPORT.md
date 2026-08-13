# PDF G3 diagnostic hardening — before/after report

The golden and KPI protocol are the untouched frozen artifacts from the prior campaign.
One real generation was attempted per PDF in an isolated workspace/database. A terminal
preflight stop was not retried. No revision was approved, rejected, merged, or projected
into the canonical graph.

## Before/after by manual

| Manual | Semantic recall before → v8 | Autonomous before → v8 | Review burden before → v8 | Calls before → v8 | Cost USD before → v8 | Latency before → v8 |
|---|---:|---:|---:|---:|---:|---:|
| eastman_e554 | 2/8 → 7/8 | 0/8 → 7/8 | 54 (24 blocking) → 38 (5 blocking) | 19 → 22 | 0.062266 → 0.137664 | 212.5s → 325.7s |
| danfoss_apf | 1/8 → 8/8 | 1/8 → 5/8 | 25 (14 blocking) → 15 (5 blocking) | 18 → 21 | 0.037005 → 0.137096 | 120.6s → 156.4s |
| graco_check_mate_200 | 0/18 → 18/18 | 0/18 → 17/18 | 10 (3 blocking) → 24 (1 blocking) | 14 → 29 | 0.036287 → 0.051099 | 112.4s → 212.7s |

## Campaign decision

**NO-GO** — macro semantic recall 0.958 versus 0.780; USD 0.325859/3.00; 72 calls; 694.8s.

The release decision remains NO-GO unless all three per-manual floors, the macro floor,
and every publication-integrity gate pass. Danfoss passing at its exact floor cannot
offset Eastman or the unevaluated Graco ontology run.

## Durable shared budget ledger

Ledger reconciliation: **False**; 72 reservations, 72 finalizations; USD 0.325859 charged and USD 2.674141 remaining.
All actual costs observed: False; failures: run_call_count_mismatch:danfoss_apf, run_call_model_mismatch:danfoss_apf.

| Run | Calls | Reservations/finalizations | Models | Actual USD | Fail-closed charge USD |
|---|---:|---:|---|---:|---:|
| v10:danfoss_apf | 21 | 21/21 | gpt-5.6-luna×19, gpt-5.6-terra×2 | 0.045819 | 0.137096 |
| v10:eastman_e554 | 22 | 22/22 | gpt-5.6-luna×20, gpt-5.6-terra×2 | 0.137664 | 0.137664 |
| v10:graco_check_mate_200 | 29 | 29/29 | gpt-5.6-luna×28, gpt-5.6-terra×1 | 0.051099 | 0.051099 |

The shared per-call ledger is authoritative. This attributes Graco's two paid scoping
calls even though the route-level run ledger has no ontology revision. The sum of isolated
run preflight envelopes was USD 2.017034; these are
not concurrent reservations. Every actual API call was separately reserved before dispatch
against the absolute USD 1.00 campaign ceiling.

## Per-claim result

| Manual | Claim | Expected witness | Present | Matched outcome | Best minimum field score |
|---|---|---|---|---|---:|
| eastman_e554 | E1 | complete_published_path | True | published_path | 0.850 |
| eastman_e554 | E2 | complete_published_path | True | published_path | 0.838 |
| eastman_e554 | E3 | complete_published_path | False | none | 0.000 |
| eastman_e554 | E4 | complete_published_path_or_traceable_review | True | published_path | 0.650 |
| eastman_e554 | E5 | complete_published_path | True | published_path | 0.684 |
| eastman_e554 | E6 | complete_published_path_or_traceable_review | True | published_path | 0.842 |
| eastman_e554 | E7 | complete_published_path_or_traceable_review | True | published_path | 0.845 |
| eastman_e554 | E8 | complete_published_path_or_traceable_review | True | published_path | 0.856 |
| danfoss_apf | D1 | traceable_explicit_gap | True | explicit_gap | 1.000 |
| danfoss_apf | D2 | traceable_explicit_gap | True | explicit_gap | 1.000 |
| danfoss_apf | D3 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D4 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D5 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D6 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D7 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D8 | traceable_explicit_gap | True | explicit_gap | 0.838 |
| graco_check_mate_200 | G1 | complete_published_path | True | published_path | 0.824 |
| graco_check_mate_200 | G2 | complete_published_path | True | published_path | 0.871 |
| graco_check_mate_200 | G3 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G4 | complete_published_path | True | published_path | 0.867 |
| graco_check_mate_200 | G5 | complete_published_path | True | published_path | 0.825 |
| graco_check_mate_200 | G6 | complete_published_path | True | published_path | 0.871 |
| graco_check_mate_200 | G7 | complete_published_path | True | published_path | 0.833 |
| graco_check_mate_200 | G8 | traceable_explicit_gap | True | explicit_gap | 1.000 |
| graco_check_mate_200 | G9 | complete_published_path | True | published_path | 0.906 |
| graco_check_mate_200 | G10 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G11 | complete_published_path | True | published_path | 0.843 |
| graco_check_mate_200 | G12 | complete_published_path | True | published_path | 0.857 |
| graco_check_mate_200 | G13 | complete_published_path | True | published_path | 0.733 |
| graco_check_mate_200 | G14 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G15 | complete_published_path | True | published_path | 0.900 |
| graco_check_mate_200 | G16 | complete_published_path | True | published_path | 0.857 |
| graco_check_mate_200 | G17 | complete_published_path | True | published_path | 0.867 |
| graco_check_mate_200 | G18 | complete_published_path | True | published_path | 1.000 |

## Critical interpretation by manual

### eastman_e554

- Recall is **7/8**: 7 autonomous published witness(es), 0 explicit inspection gap(s), and 0 traceable review witness(es). The frozen floor is 0.7500; pass=True.
- Autonomous claims: E1, E2, E4, E5, E6, E7, E8; explicit gaps: none; review-only claims: none; missing claims: E3.
- Published complete paths=14; outside frozen gold=7; forbidden pairings=0.
- Accounting complete=False; approval eligible=False; strict publication-integrity verdict=pass.
- Review burden: total=38, blocking=5; canonicalization_ambiguous=26, diagnostic_failure_without_component=1, pdf_diagnostic_contract_incomplete=1, pdf_diagnostic_record_gap=2, pdf_diagnostic_record_review=1, pdf_node_provenance_unresolved=1, pdf_ocr_low_confidence=1, pdf_pipeline_blocked=1, pdf_pipeline_not_reviewable=1, pdf_prepublication_graph_issue_summary=1, pdf_relation_endpoint_omitted=1, pdf_schema_instruction_not_actionable=1.
- The completed run remains fail-closed and non-approvable because candidate accounting is incomplete (diagnostic_contract_incomplete=1). Its review witnesses improve semantic traceability but provide no autonomous path.

### danfoss_apf

- Recall is **8/8**: 5 autonomous published witness(es), 3 explicit inspection gap(s), and 0 traceable review witness(es). The frozen floor is 0.7500; pass=True.
- Autonomous claims: D3, D4, D5, D6, D7; explicit gaps: D1, D2, D8; review-only claims: none; missing claims: none.
- Published complete paths=5; outside frozen gold=0; forbidden pairings=0.
- Accounting complete=True; approval eligible=False; strict publication-integrity verdict=pass.
- Review burden: total=15, blocking=5; canonicalization_ambiguous=7, pdf_diagnostic_record_gap=3, pdf_node_provenance_unresolved=1, pdf_ocr_low_confidence=1, pdf_relation_endpoint_omitted=1, pdf_schema_instruction_not_actionable=1, pdf_unreadable_pages=1.
- Candidate accounting is complete, but blocking evidence/layout review keeps the revision non-approvable. This is a safe review state, not autonomous coverage.

### graco_check_mate_200

- Recall is **18/18**: 17 autonomous published witness(es), 1 explicit inspection gap(s), and 0 traceable review witness(es). The frozen floor is 0.8333; pass=True.
- Autonomous claims: G1, G2, G3, G4, G5, G6, G7, G9, G10, G11, G12, G13, G14, G15, G16, G17, G18; explicit gaps: G8; review-only claims: none; missing claims: none.
- Published complete paths=16; outside frozen gold=0; forbidden pairings=0.
- Accounting complete=True; approval eligible=False; strict publication-integrity verdict=pass.
- Review burden: total=24, blocking=1; canonicalization_ambiguous=15, diagnostic_failure_without_component=7, pdf_diagnostic_record_gap=1, pdf_schema_instruction_not_actionable=1.
- Candidate accounting is complete, but blocking evidence/layout review keeps the revision non-approvable. This is a safe review state, not autonomous coverage.

## Exact publication and execution invariants

| Manual | Strict validation | Exact EvidenceRefs | Branch lineage | Zero isolated diagnostics | Every action linked | Canonical Asset | Forbidden / unsupported | Gold pages | Accounting / approval | Authenticated real run | No approve/merge/structured |
|---|---|---|---|---|---|---|---|---|---|---|---|
| eastman_e554 | True | 773/773 refs; 167/167 rels | True (29 rels) | True | True | True | 0 / 0 | 3/3 (True) | False / False | True | True |
| danfoss_apf | True | 547/547 refs; 56/56 rels | True (15 rels) | True | True | True | 0 / 0 | 1/1 (True) | True / False | True | True |
| graco_check_mate_200 | True | 498/498 refs; 107/107 rels | True (40 rels) | True | True | True | 0 / 0 | 1/1 (True) | True / False | True | True |

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
