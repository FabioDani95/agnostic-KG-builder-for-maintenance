# Root-cause analysis

## Executive finding

The former pipeline mixed three different decisions in a single LLM call: record
discovery, reconstruction of layout/row structure, and semantic typing. The failures
were therefore not primarily model-capacity failures. They were boundary and accounting
failures whose output happened to be probabilistic.

The final architecture separates deterministic observation from probabilistic
interpretation:

1. EvidenceUnits remain the immutable literal source inventory.
2. A deterministic structure pass inventories diagnostic roots and branches.
3. Each atomic branch gets exact allowed spans and a system-owned edge policy.
4. Structured Outputs produce a typed candidate inside that scope.
5. The compiler resolves evidence, rejects unsupported fields, and assigns a complete
   terminal state.
6. Bounded Terra recovery may add only complementary, verified branches.
7. Canonicalization preserves occurrence lineage.
8. Publication remains fail-closed and separate from human approval.
9. A durable per-call ledger and record inventory reconcile independently.

## Demonstrated causes

### Relation canonicalization could merge different occurrences

Relation identity omitted `branch_lineage_id`. Equal endpoint/type relations from two
document branches could collapse and lose the occurrence join. Relation deduplication
now includes lineage; unit and real-run integrity checks demonstrate complete joinable
lineage.

### Forward-fill leaked sibling evidence

The former table forward-fill could expose the entire prior EvidenceUnit while intending
to inherit only the problem/symptom cell. A current branch could then cite its sibling's
cause or remedy. The structure pass now copies only exact root-cell spans as context and
keeps current cause/remedy spans separate.

### A physical row was incorrectly treated as a semantic record

Rows can contain multiple causes and multiple remedies. The final pass atomizes numbered
pairs positionally, broadcasts a single explicitly shared action, and marks incompatible
cardinality ambiguous without making an LLM call. Prose lists are split into alternatives,
while an explicitly introduced procedure remains one sequential action. This eliminates
cross-row and cross-branch Cartesian products by construction.

### Compiler policy conflated inspection with absence of remedy

A candidate containing an inspection step and an explicit restorative remedy was formerly
blocked. Inspections and actions are now separate typed collections. Inspection-only
records become explicit gaps; a record with a supported restorative action may compile.
Checklist, verification, and preventive-maintenance language is never promoted to a
CorrectiveAction merely because it is imperative.

### Optional semantic decoration could destroy a complete core path

In the v9 real Graco run, two otherwise complete records were dropped because the model
invented unsupported optional `material_context`. A zero-call compiler replay proved
that removing only that unsupported optional decoration changes exactly two records from
gap to publish (15→17), without inventing Component or `AFFECTS` edges. The final compiler
performs this relation-safe recovery and records it.

### Recovery selected a winner instead of composing evidence-safe complements

The former recovery path replaced the primary result with Terra when Terra scored better.
This loses valid primary branches. The final workflow composes a union only when branches
are complementary, scope-valid, and lineage-safe; otherwise it keeps the best valid result.

### Broad prose windows were both unsafe and unstable

The v10 Eastman run used seven broad prose windows. One window contained 15 EvidenceUnits
and crossed into a later RF/EMI section. Although the evaluator found 7/8 and seven
autonomous witnesses, accounting was incomplete and the evidence boundary was too broad.
The v11 section boundary and list decomposition produce 22 Eastman atomic windows. This
intentionally converts four layout-inferred results from autonomous paths into traceable
review, while preserving 7/8 semantic recall and all safety gates.

### SDK parse failure escaped route accounting

In v10, one Danfoss SDK parse exception was durably charged but absent from route-local
metrics: 72 durable reservations versus an inconsistent run ledger, one unknown actual
cost, and a fail-closed charged total of USD 0.32585867. The gateway now attaches durable
call accounting to exceptions and disables hidden SDK retries. V11 reconciles 87/87 calls,
all with observed actual cost.

## Classification of every observed diagnostic record

Publication metrics use the requested distinctions:

- `observed_structurally_incomplete`;
- `compiled_semantically_ambiguous`;
- `inspection_only_gap`;
- `autonomously_publishable`;
- `observed_excluded`.

Parse failure, refusal, truncation, contract failure, and unaccounted windows/pages/evidence
are also terminal accounting categories and fail approval. In v11, all 57 compiled records
(31 Eastman, 8 Danfoss, 18 Graco) and all 48 deterministic windows are accounted, with no
unaccounted source evidence in the diagnostic scope.

## What was not supported by evidence

- Increasing reasoning effort globally was not necessary.
- Sending every case to Terra was not justified; only 5 of 87 calls used Terra.
- Increasing calls without first changing record boundaries was not sufficient: v10 had
  high nominal recall but failed accounting and retained unsafe broad scopes.
- Structured schema conformance alone did not guarantee semantic correctness, evidence
  locality, or branch pairing.

## Literature fit

The implemented structure-first design is consistent with primary research on
structure-aware table understanding and staged table processing:

- [TableFormer](https://arxiv.org/abs/2203.01017) models table structure explicitly rather
  than treating a page as flat text.
- [TRUST](https://arxiv.org/abs/2208.14687) treats table structure recognition as a distinct
  problem with its own data and evaluation.
- [Schema-driven information extraction from heterogeneous tables](https://aclanthology.org/2024.findings-emnlp.600/)
  supports an explicit schema/structure layer for heterogeneous layouts.
- [TableCoder](https://aclanthology.org/2025.acl-industry.98/) supports type-aware staged
  decomposition instead of a monolithic table prompt.
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
  supplies schema conformance, but the evidence and branch constraints remain application
  responsibilities.

These sources informed general architecture only; they supplied no benchmark-specific
rules.
