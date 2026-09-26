# v22 PDF diagnostic status

> Superseded as default by the V3 pipeline ([plan](PIANO_V3.md), [results](V3_RISULTATI_SVILUPPO.md)).
> This page documents the v22 generator, still selectable as `legacy_v22`.

Generator: `pdf-g3-structured-recovery-v22`. Evidence checkpoint: C9–C12,
2026-09-26. This page describes the implemented workspace PDF path and its
measured limitations; it is not a production acceptance certificate.

## What is implemented

The pipeline retains canonical PDF evidence, layout and diagnostic record
identity; extracts typed candidates; compiles supported graph relations; and
records review items, explicit gaps and exclusions. Bounded recovery can repair
selected parsing/evidence failures. Repair feedback never becomes document
proof. Supplementary procedure packets can include continuation pages classified
as structural. Escalation preserves previously accepted branches.

The graph review screen now includes **Revisione dei record**. Select a record,
inspect its source evidence, edit the structured fields and citations, enter
reviewer and reason, then save. The backend recompiles that record into a new
revision and keeps a before/after history. Stale revisions are rejected; remaining
blockers still prevent approval. Invalid corrections can remain review items;
saving does not certify their meaning or approve the graph.

Symptoms/codes, possible causes, components and corrective actions use the
existing ontology. Conditions, inspections and raw ordered procedure context
remain metadata linked to branches. Source context is available to the reviewer;
it is not automatically a complete or executable procedure.

## Observed document results

| Manual | Graph branches | Unresolved records | Review notifications | Approval eligible |
| --- | ---: | ---: | ---: | --- |
| Eastman E-554 | 9 | 57 | 75 | No |
| Danfoss APF | 8 | 9 | 26 | No |
| Graco Check-Mate 200 | 19 | 36 | 64 | No |
| Hypertherm Powermax30 AIR | 21 | 145 | 157 | No |

These are counts, not precision/recall. Branches can be duplicates or incomplete;
notifications are not independent human decisions. Source audits found locally
supported relationships, missing prerequisites, unresolved references and a
conflicting distance recommendation within Eastman. Global semantic precision
and recall are unavailable without adequate independent annotations.

C12 preserves all 17 Hypertherm branches from C11 and adds four source-supported
Test 9 terminal outcomes. None of those four is verified as a complete operational
path. Against C8, Hypertherm review notifications rise from 111 to 157 and
unresolved records from 93 to 145. Graco also regresses quantitatively. Reduced
human workload has not been demonstrated.

## Evidence and cost boundaries

C11 consists of four new complete extractions. C12 reuses exact C11 requests and
makes two additional calls for Hypertherm pages 96–100; the other three graphs
retain identical nodes and relations. C12 is an incremental verification, not
an independent stochastic replication. Four subsequent exact offline replays
reproduce the final nodes, relations, diagnostic records and review counts with
network access denied.

The final Python suite passed 612 tests. Targeted API and browser checks exercised
single-record correction on a database copy; 152 unrelated relations were
preserved, stale edits and residual approval were rejected, and an invented quote
remained unpublished. Software checks do not validate overall extraction quality.

The campaign's cumulative API accounting is **USD 1.644144695 of the same USD 20
cap**, with 681 attempts finalized and no active reservation at this checkpoint.
This includes conservative charges when usage was unavailable, retries and failed
runs. It is not an invoice or the full cost including human review. New calls
must use the existing ledger rather than reset the budget.

## Current limitations and next evaluation

Independent technician annotations A/B remain empty; agent audits are explicitly
prediction-exposed. The next evaluation should separate new development manuals
from held-out documents, freeze code and comparisons before runs, and measure
branch correctness/completeness plus human decisions and time. Manufacturer
transfer, provider/language independence and operational safety are not established.
The current schema and provider are specific; “agnostic” is not a demonstrated
property across all these dimensions.

- [Campaign report](../paper/experiments/robustness_continuation_20260926/REPORT.md)
- [Final machine-readable results](../paper/experiments/robustness_continuation_20260926/final_results.json)
- [Reproduction](../paper/experiments/robustness_continuation_20260926/REPRODUCE.md)
- [Technician procedure](../paper/experiments/robustness_continuation_20260926/PROCEDURA_TECNICI.md)
- [Scientific status](../paper/STATUS.md) and [work plan](../paper/WORKPLAN.md)

Source snapshots, responses, reports and ledgers are versioned. SQLite source
stores and duplicated raw files remain local under the existing ignore rules.
Exact reproduction from a fresh clone requires these external inputs, checked
against the campaign manifests; the Git checkout alone is not self-contained.
