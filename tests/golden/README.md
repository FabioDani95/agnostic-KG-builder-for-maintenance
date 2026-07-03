# Golden Maintenance Fixtures

This folder contains small synthetic manuals and minimal expected outputs for
future golden/evaluation tests.

The fixtures are intentionally short so they can be used in cheap smoke tests,
mocked extraction tests, or low-token LLM evaluation runs.

## Layout

- `manuals/clean_pump_manual.md`: straightforward diagnostic content.
- `manuals/ambiguous_conveyor_manual.md`: one symptom with multiple possible causes.
- `manuals/noisy_table_robot_manual.md`: diagnostic table with split/noisy wording.
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
