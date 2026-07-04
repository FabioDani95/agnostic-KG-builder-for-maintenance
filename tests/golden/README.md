# Golden Maintenance Fixtures

This folder contains small synthetic manuals and minimal expected outputs for
future golden/evaluation tests.

The fixtures are intentionally short so they can be used in cheap smoke tests,
mocked extraction tests, or low-token LLM evaluation runs.

## Layout

- `manuals/clean_pump_manual.md`: straightforward diagnostic content.
- `manuals/ambiguous_conveyor_manual.md`: one symptom with multiple possible causes.
- `manuals/noisy_table_robot_manual.md`: diagnostic table with split/noisy wording.
- `manuals/eagle_s3l_laser_cutter_manual.md`: real laser cutter troubleshooting prose with preventive-maintenance distractors.
- `expected/*.json`: minimal expected entities, triplets, human-review hints, and export checks.

## Intended Use

Do not treat these expected files as a full ontology contract. They are a stable
baseline for regression detection:

- Did scoping keep the diagnostic pages?
- Did extraction find the core symptom/failure/action chains?
- Did ontology/export preserve required asset and relationship information?
- Did the pipeline avoid unnecessary human intervention on clean content?
- Did ambiguous content produce review candidates instead of silently collapsing causes?

Future evaluation code should compare semantic keys and normalized labels rather
than exact free-text wording.

## Mock Responses (`mock_responses/`)

`mock_responses/<fixture_id>/<stage>.json` holds the deterministic LLM replies
the mock gateway (`KG_LLM_MODE=mock`) returns while evaluating that fixture
(`KG_LLM_FIXTURE=<fixture_id>`, set automatically by `scripts/eval_golden.py`).
Stage names match the gateway's prompt detection: `scoping`, `sections`,
`extraction`, `ontology`, `relations`, `validation`, `node_normalization`,
`resolution`. A file holding only a `"content"` key is returned as raw text;
any other JSON payload is returned dumped verbatim. Stages without a file fall
back to the generic mock reply.

These files are mock *responses*, not new golden manuals: they exist so the
mock eval exercises each fixture's real diagnostic content (recall 1.0 is the
deterministic baseline) instead of a one-size-fits-all reply that pins every
quality metric to zero.
