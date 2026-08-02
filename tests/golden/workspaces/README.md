# Multisource golden workspaces

`DS-003` is a future fixture contract, not a completed dataset. A concrete
workspace belongs in `tests/golden/workspaces/<workspace_id>/` and must contain:

- immutable raw sources;
- label-free ingestion views;
- `expected.json`, valid against `../ds003_expected.schema.json`;
- a checksum file covering every raw source and ingestion view.

The evaluator validates the schema, verifies every declared SHA-256, checks
that `claim_count` equals the number of expected node, property and relationship
claims, resolves every evidence locator, and reads `negative_claims` only after
predictions are frozen. Ingestion adapters receive only files referenced by
`sources[].ingestion_view`; they never receive `expected.json`, source splits,
or evaluator-only labels.

The schema enforces the minimum source mix (two PDFs, CSV, XLSX with at least
two sheets, and JSON/JSONL) and rejects known label fields in structured
ingestion-view column declarations. The acceptance gate still requires at
least 30 atomic expected claims and the semantic thresholds in `AC-SEM-001`.
