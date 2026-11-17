# Maintenance knowledge graphs from PDF manuals

Build and review a knowledge graph of symptoms, error codes, faults, corrective
actions and components from a technical PDF. The application keeps source
evidence with extracted relations and lets a person inspect, correct and accept
a new graph version.

This is a local research prototype: a Python extraction pipeline, a FastAPI API
and a React interface in English and Italian. It uses a fixed
[maintenance ontology](ontology_schema.JSON) and the OpenAI client interface.
The repository name does not imply unrestricted ontology or provider support.

```text
PDF → read → survey → extract → verify → resolve → gaps → enrich → graph and evidence
                                                                        ↓
                                                    human editing → accepted revision
```

Two pipelines produce the same graph format. The connected-graph pipeline above
(`scripts/kg_build.py`) runs without asking anyone, reads pages without a text
layer from their image and is built to give connected, described graphs. It has
been measured on three development manuals against an AI-made reference; the
[evaluation guide](docs/evaluation.md#measured-so-far) gives the numbers and their
limits. The earlier V3 pipeline (`scripts/kg_v3.py`) is the one the interface
starts and the baseline every measurement is compared with.

## Start here

Use Python 3.12 or later and a POSIX environment (macOS, Linux or WSL). The web
interface also needs Node.js 22.13+ or 24 LTS and npm. Run commands from the
repository root.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/python scripts/ui.py
```

Keep an existing `.env` instead of overwriting it. Open
[the local interface](http://127.0.0.1:8765). The launcher installs and builds the
frontend when needed. A real extraction needs your API key in `.env` and incurs
usage charges; browsing saved graphs, replaying their progress and manual editing
make no model calls.

A fresh checkout may have no local manuals or run history. The interface currently
requires campaign cost history before it starts an extraction. Use the
[first-run CLI instructions](docs/getting-started.md#extract-a-pdf-from-the-command-line)
to process your own PDF with an explicit budget and a separate ledger.

## Documentation

The [documentation index](docs/README.md) is the entry point for colleagues.

| Guide | Purpose |
| --- | --- |
| [Getting started](docs/getting-started.md) | Installation, first extraction, interface workflow, replay and output files |
| [Architecture](docs/architecture.md) | Pipeline, evidence, graph formats, persistence and source map |
| [Configuration](docs/configuration.md) | Actual settings, model selection, gates, OCR and spending limits |
| [Graph editor](docs/EDITOR_GRAFO.md) | Corrections, evidence, acceptance and revision API |
| [Development](docs/development.md) | Local development, offline checks and contribution boundaries |
| [Evaluation](docs/evaluation.md) | Quality cards, loss analysis, recall, results so far and what is not measured yet |
| [Test plan](docs/test-plan.md) | Runs, measures and rules for comparing the new pipeline with earlier versions |
| [Roadmap](docs/roadmap.md) | Primary goal, position against published work, the three new points, journal and order of work |

The optional [quality profile](docs/kg_quality/README.md) has its own specialist
guide. It adds evidence and branch contracts, coverage accounting and bounded
review. It is opt-in; the CLI and interface default to `base_safe`.

## What the output means

Relations can carry green, yellow or red verification tiers. The exported graph
includes green and yellow relations; yellow means `trusted: false`, and red
relations are recorded separately. Programmatically derived asset links are
marked as such. A certificate records the checks performed, rather than proving
that a maintenance instruction is technically correct.

Workflow approval, source support and completeness are separate. In particular,
the default CLI gate preset can approve automatically, whereas the interface
requires a person's approval. A manually accepted revision may still contain
acknowledged warnings or unverified content. Human review does not train the model.

Current extraction quality, generalisation and savings in review effort need
version-matched evaluation. Historical campaign results cannot be transferred to
the current code. [Campaign documentation](campaign/README.md) describes the
evaluation workspace. Manuscript materials are maintained separately in a private
local workspace and are excluded from this repository. Local PDFs, credentials
and run archives are not necessarily included in a clone.

## Development and licence

```bash
.venv/bin/python scripts/test_offline.py -q
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build
```

These check software behaviour, not extraction accuracy. See the
[development guide](docs/development.md) for linting and fixture-based checks,
[CONTRIBUTING.md](CONTRIBUTING.md) before changing the repository, and
[LICENSE](LICENSE) for the code licence.
