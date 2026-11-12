# Documentation

These guides describe the executable application. Start with the task you need:

| Task | Read |
| --- | --- |
| Install, process a PDF or explore a saved graph | [Getting started](getting-started.md) |
| Understand the data flow and locate the implementation | [Architecture](architecture.md) |
| Choose models, reviewers, OCR settings or budgets | [Configuration](configuration.md) |
| Correct a graph and accept a new version | [Graph editor](EDITOR_GRAFO.md) |
| Develop, test or contribute | [Development](development.md) |
| Measure a graph: quality card, losses, recall, what is not measured yet | [Evaluation](evaluation.md) |
| Use the optional quality profile and its evaluation tools | [Quality profile](kg_quality/README.md) |

The application also has an English/Italian **Guide** at `/guida`, accessible
from its navigation. Its content lives in `frontend/src/help/guide.en.ts` and
`frontend/src/help/guide.ts`.

## Scope and sources of truth

The code and configuration define current behaviour. The
[ontology](../ontology_schema.JSON) defines permitted node and relation types.
The [campaign guide](../campaign/README.md) covers evaluation data and workflows.
Manuscript materials and their scientific status register are maintained in a
private workspace outside the shared code. Keep implementation facts, measured
results and proposed experiments distinct.

Operational guides do not promote historical measurements into current results.
Some linked research and campaign assets exist only in the author's local
workspace; use your own PDF for a first run. A plan or past report is background
evidence, not an instruction to run experiments or spend API credit.
