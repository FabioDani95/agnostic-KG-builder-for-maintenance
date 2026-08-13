# PDF G3 diagnostic hardening — before/after report

The golden and KPI protocol are the untouched frozen artifacts from the prior campaign.
One real generation was attempted per PDF in an isolated workspace/database. A terminal
preflight stop was not retried. No revision was approved, rejected, merged, or projected
into the canonical graph.

## Before/after by manual

| Manual | Semantic recall before → v8 | Autonomous before → v8 | Review burden before → v8 | Calls before → v8 | Cost USD before → v8 | Latency before → v8 |
|---|---:|---:|---:|---:|---:|---:|
| eastman_e554 | 2/8 → 7/8 | 0/8 → 6/8 | 54 (24 blocking) → 39 (6 blocking) | 19 → 22 | 0.062266 → 0.168439 | 212.5s → 380.3s |
| danfoss_apf | 1/8 → 8/8 | 1/8 → 5/8 | 25 (14 blocking) → 15 (5 blocking) | 18 → 24 | 0.037005 → 0.060631 | 120.6s → 192.3s |
| graco_check_mate_200 | 0/18 → 16/18 | 0/18 → 15/18 | 10 (3 blocking) → 22 (3 blocking) | 14 → 29 | 0.036287 → 0.059357 | 112.4s → 251.6s |

## Campaign decision

**GO** — macro semantic recall 0.921 versus 0.780; USD 0.288427/3.00; 75 calls; 824.1s.

The release decision remains NO-GO unless all three per-manual floors, the macro floor,
and every publication-integrity gate pass. Danfoss passing at its exact floor cannot
offset Eastman or the unevaluated Graco ontology run.

## Durable shared budget ledger

Ledger reconciliation: **True**; 75 reservations, 75 finalizations; USD 0.288427 charged and USD 2.711573 remaining.
All actual costs observed: True; failures: none.

| Run | Calls | Reservations/finalizations | Models | Actual USD | Fail-closed charge USD |
|---|---:|---:|---|---:|---:|
| v9:danfoss_apf | 24 | 24/24 | gpt-5.6-luna×22, gpt-5.6-terra×2 | 0.060631 | 0.060631 |
| v9:eastman_e554 | 22 | 22/22 | gpt-5.6-luna×20, gpt-5.6-terra×2 | 0.168439 | 0.168439 |
| v9:graco_check_mate_200 | 29 | 29/29 | gpt-5.6-luna×28, gpt-5.6-terra×1 | 0.059357 | 0.059357 |

The shared per-call ledger is authoritative. This attributes Graco's two paid scoping
calls even though the route-level run ledger has no ontology revision. The sum of isolated
run preflight envelopes was USD 2.089339; these are
not concurrent reservations. Every actual API call was separately reserved before dispatch
against the absolute USD 1.00 campaign ceiling.

## Per-claim result

| Manual | Claim | Expected witness | Present | Matched outcome | Best minimum field score |
|---|---|---|---|---|---:|
| eastman_e554 | E1 | complete_published_path | False | none | 0.475 |
| eastman_e554 | E2 | complete_published_path | True | published_path | 1.000 |
| eastman_e554 | E3 | complete_published_path | True | published_path | 0.580 |
| eastman_e554 | E4 | complete_published_path_or_traceable_review | True | traceable_review | 0.964 |
| eastman_e554 | E5 | complete_published_path | True | published_path | 0.800 |
| eastman_e554 | E6 | complete_published_path_or_traceable_review | True | published_path | 0.750 |
| eastman_e554 | E7 | complete_published_path_or_traceable_review | True | published_path | 0.600 |
| eastman_e554 | E8 | complete_published_path_or_traceable_review | True | published_path | 0.800 |
| danfoss_apf | D1 | traceable_explicit_gap | True | explicit_gap | 1.000 |
| danfoss_apf | D2 | traceable_explicit_gap | True | explicit_gap | 1.000 |
| danfoss_apf | D3 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D4 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D5 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D6 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D7 | complete_published_path | True | published_path | 1.000 |
| danfoss_apf | D8 | traceable_explicit_gap | True | explicit_gap | 0.675 |
| graco_check_mate_200 | G1 | complete_published_path | True | published_path | 0.833 |
| graco_check_mate_200 | G2 | complete_published_path | True | published_path | 0.909 |
| graco_check_mate_200 | G3 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G4 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G5 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G6 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G7 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G8 | traceable_explicit_gap | True | explicit_gap | 1.000 |
| graco_check_mate_200 | G9 | complete_published_path | False | none | 0.201 |
| graco_check_mate_200 | G10 | complete_published_path | True | published_path | 0.571 |
| graco_check_mate_200 | G11 | complete_published_path | False | none | 0.201 |
| graco_check_mate_200 | G12 | complete_published_path | True | published_path | 0.792 |
| graco_check_mate_200 | G13 | complete_published_path | True | published_path | 0.792 |
| graco_check_mate_200 | G14 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G15 | complete_published_path | True | published_path | 0.964 |
| graco_check_mate_200 | G16 | complete_published_path | True | published_path | 1.000 |
| graco_check_mate_200 | G17 | complete_published_path | True | published_path | 0.914 |
| graco_check_mate_200 | G18 | complete_published_path | True | published_path | 1.000 |

## Critical interpretation by manual

### eastman_e554

- Recall is **7/8**: 6 autonomous published witness(es), 0 explicit inspection gap(s), and 1 traceable review witness(es). The frozen floor is 0.7500; pass=True.
- Autonomous claims: E2, E3, E5, E6, E7, E8; explicit gaps: none; review-only claims: E4; missing claims: E1.
- Published complete paths=7; outside frozen gold=1; forbidden pairings=0.
- Accounting complete=True; approval eligible=False; strict publication-integrity verdict=pass.
- Review burden: total=39, blocking=6; canonicalization_ambiguous=28, diagnostic_failure_without_component=1, pdf_diagnostic_record_gap=3, pdf_diagnostic_record_review=2, pdf_node_provenance_unresolved=1, pdf_ocr_low_confidence=1, pdf_prepublication_graph_issue_summary=1, pdf_relation_endpoint_omitted=1, pdf_schema_instruction_not_actionable=1.
- Candidate accounting is complete, but blocking evidence/layout review keeps the revision non-approvable. This is a safe review state, not autonomous coverage.

### danfoss_apf

- Recall is **8/8**: 5 autonomous published witness(es), 3 explicit inspection gap(s), and 0 traceable review witness(es). The frozen floor is 0.7500; pass=True.
- Autonomous claims: D3, D4, D5, D6, D7; explicit gaps: D1, D2, D8; review-only claims: none; missing claims: none.
- Published complete paths=5; outside frozen gold=0; forbidden pairings=0.
- Accounting complete=True; approval eligible=False; strict publication-integrity verdict=pass.
- Review burden: total=15, blocking=5; canonicalization_ambiguous=6, diagnostic_failure_without_component=1, pdf_diagnostic_record_gap=3, pdf_node_provenance_unresolved=1, pdf_ocr_low_confidence=1, pdf_relation_endpoint_omitted=1, pdf_schema_instruction_not_actionable=1, pdf_unreadable_pages=1.
- Candidate accounting is complete, but blocking evidence/layout review keeps the revision non-approvable. This is a safe review state, not autonomous coverage.

### graco_check_mate_200

- Recall is **16/18**: 15 autonomous published witness(es), 1 explicit inspection gap(s), and 0 traceable review witness(es). The frozen floor is 0.8333; pass=True.
- Autonomous claims: G1, G2, G3, G4, G5, G6, G7, G10, G12, G13, G14, G15, G16, G17, G18; explicit gaps: G8; review-only claims: none; missing claims: G9, G11.
- Published complete paths=15; outside frozen gold=0; forbidden pairings=0.
- Accounting complete=True; approval eligible=False; strict publication-integrity verdict=pass.
- Review burden: total=22, blocking=3; canonicalization_ambiguous=12, diagnostic_failure_without_component=4, pdf_diagnostic_record_gap=3, pdf_node_provenance_unresolved=1, pdf_relation_endpoint_omitted=1, pdf_schema_instruction_not_actionable=1.
- Candidate accounting is complete, but blocking evidence/layout review keeps the revision non-approvable. This is a safe review state, not autonomous coverage.

## Exact publication and execution invariants

| Manual | Strict validation | Exact EvidenceRefs | Branch lineage | Zero isolated diagnostics | Every action linked | Canonical Asset | Forbidden / unsupported | Gold pages | Accounting / approval | Authenticated real run | No approve/merge/structured |
|---|---|---|---|---|---|---|---|---|---|---|---|
| eastman_e554 | True | 915/915 refs; 197/197 rels | True (20 rels) | True | True | True | 0 / 0 | 3/3 (True) | True / False | True | True |
| danfoss_apf | True | 336/336 refs; 54/54 rels | True (14 rels) | True | True | True | 0 / 0 | 1/1 (True) | True / False | True | True |
| graco_check_mate_200 | True | 521/521 refs; 111/111 rels | True (40 rels) | True | True | True | 0 / 0 | 1/1 (True) | True / False | True | True |

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
