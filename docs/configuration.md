# Configuration

## Configuration layers

| Location | Controls |
| --- | --- |
| `.env` or process environment | API key and shared model fallback |
| `config.yaml` | PDF reading and selective OCR |
| CLI arguments / `RunConfig` | Extraction model, reasoning, reads, reviewers, concurrency and run behaviour |
| Quality JSON passed with `--quality-config` | Optional evidence, branch and review extensions |
| `workspace/settings.json` | Interface preferences and optional local API-key override |
| `UiSettings` / `Limits` in Python | UI paths, catalogue and development spending limits |

Run the application from the repository root so `.env` resolves consistently.
Do not put unrelated legacy variables in `.env`: `backend/config.py` only defines
`OPENAI_API_KEY`, `KG_GENERATION_MODEL` and the older `MODEL_NAME` fallback.

## Credentials and models

```dotenv
OPENAI_API_KEY=your-key
KG_GENERATION_MODEL=gpt-6-luna
```

`KG_GENERATION_MODEL` takes precedence over `MODEL_NAME` when the shared settings
resolve a model. However, `scripts/kg_v3.py` supplies its own explicit defaults:
use `--model` for extraction and `--agent-model` for gate review. Changing only
`.env` does not override those CLI defaults.

| CLI setting | Default |
| --- | --- |
| `--model` | `gpt-6-luna` |
| `--reasoning` | `low` |
| `--reads` | `2` |
| `--agent-model` | `gpt-6-luna` |
| `--agent-reasoning` | `medium` |
| `--human-questions` | `10` |
| `--gates` | `agent` |

The interface exposes extraction reasoning and number of reads, reviewer model
and reasoning, and the human-question limit. Its model dropdown selects the
**reviewer**, not the primary extraction model. Existing runs retain their saved
model settings when resumed.

The gateway uses OpenAI clients. Provider interchangeability and arbitrary local
endpoints are not validated features of this application. Model availability,
accepted parameters and repository pricing must agree before a real run. The
quality profile can configure separate review, verification and vision roles;
see [the specialist guide](kg_quality/README.md).

A key saved in UI settings overrides the environment key for UI work. It is stored
as plaintext in the local settings file; the API returns only its source and
last four characters. Keep `.env`, workspace settings and provider archives out
of shared commits.

## Connected-graph pipeline settings

`scripts/kg_build.py` takes its settings from the command line; they are recorded in
`report.provenance.config`. Defaults are in `BuildConfig`
(`backend/kg_v4/pipeline.py`).

| Setting | Default | Effect |
| --- | --- | --- |
| `--model`, `--reasoning` | `gpt-6-luna`, `low` | One model for every role |
| `--no-verify` | verification on | Without it facts stay `unchecked` (medium confidence) and nothing is rejected |
| `--no-transcribe` | transcription on | Without it pages without usable text stay unread and are listed in `report.unreadable_pages` |
| `--transcribe-pages` | 120 | Most pages read from their image, one call each, in page order; pages beyond the limit are listed in `report.transcription.pages_over_the_limit` and the run ends `incomplete` |
| `--gap-calls` | 24 | Most calls of the gap search over at most two rounds; gaps beyond the budget are reported as open, never guessed |
| `--enrich-calls` | 40 | Most calls of node enrichment, ten nodes per call; nodes beyond the budget keep what extraction read |
| `--pages` | none | Extra PDF pages read whatever the survey decides |
| `--approval` | `automatic` | `person` leaves the finished graph waiting for approval in the interface |
| `--authorize-spend`, `--budget`, `--ledger` | required for real calls | See [Spending and archives](#spending-and-archives) |

Unit size (9000 characters), page images for flowcharts, the second read of unused
table rows and the links from names to parts are on by default and can be changed
only in code. This pipeline has no reviewer gates.

## Reviewer gates

The gates below belong to the V3 pipeline.

| Preset | Page map | Doubts | Final approval |
| --- | --- | --- | --- |
| `agent` (CLI default) | Agent | Agent | Automatic |
| `auto` | Automatic | Automatic | Automatic |
| `interactive` | Agent | Agent, then human | Human question |
| `ui-agent` | Agent | Agent | UI button |
| `ui-interactive` | Agent | Agent, then human | UI button |
| `ui-human` | Agent | Human | UI button |

The UI labels these doubt-review modes as agent, agent with human help, and human.
Even `ui-human` uses an agent for the page map. A human reviewer queues a question;
it does not prompt on standard input. Questions become effective when their
answers are applied during a resume. Automatic approval can still be blocked by
pipeline completeness or validation checks.

`RunConfig` also defines internal settings such as extraction concurrency (`6`),
agent concurrency (`8`), maximum reading units (`150`) and unit character limit
(`9000`). Not every field has a CLI flag. See
[`backend/kg_v3/run.py`](../backend/kg_v3/run.py) before adding programmatic overrides.

## Spending and archives

For standalone work, supply `--ledger` and `--budget` explicitly. The CLI default
is the historical `campaign/real_call_budget.jsonl` with a cumulative USD 20 cap.
A ledger is cumulative across runs that share it; starting a new output directory
does not reset spending. `--spend-ceiling` adds a stricter cumulative ceiling.

The CLI configures `KG_REAL_CALL_BUDGET_LEDGER`, `KG_REAL_CALL_BUDGET_USD`,
`KG_REAL_CALL_RUN_ID`, `KG_REAL_CALL_PDF_ID`, `KG_LLM_MODE` and `KG_LLM_TRACE_DIR`
for its gateway. Prefer CLI arguments over setting those implementation variables
manually. Real quality-configured runs additionally require `--authorize-spend`
and an explicitly supplied `--budget`. Base runs do not require that flag.

The gateway accounts for attempts and reservations, including failures. It can
retain a conservative charge when provider usage is unavailable. Do not delete
or edit a ledger to bypass a cap. Read `report.json` for per-run usage and retain
`provider_responses/` with the run for reproducibility.

## Interface storage and limits

The default application uses:

- `campaign/` for existing manuals and saved campaign versions;
- `workspace/` for uploads, new manuals, UI runs, revisions and settings;
- `campaign/real_call_budget.jsonl` for model-call accounting.

To move UI data, set the process environment before launch:

```bash
KG_UI_WORKSPACE=/absolute/path/kg-workspace .venv/bin/python scripts/ui.py
```

This changes only the workspace. It does **not** move the campaign, ledger or
budget limits. The current `Limits` defaults are USD 20 ledger budget, USD 15
cumulative ceiling and USD 0.50 for UI work. They are development defaults in
[`backend/ui/budget.py`](../backend/ui/budget.py), not account credit or a new
spending authorisation. `UiSettings` supports programmatic configuration; the
standard launcher does not expose these fields as flags. `Jobs` also builds CLI
commands using campaign defaults, so changing only an injected UI ledger/limit
is not a complete reconfiguration of subprocess accounting.

New UI runs require a cost estimate from existing campaign run history. With no
such history, start is refused. Use the CLI for independent first runs rather
than inventing cost-history records. Applying answers or approval resumes the
pipeline and currently requires budget headroom too.

The launcher supports `--port` and `--dev`. Development mode's frontend proxy is
fixed to API port 8765 in `frontend/vite.config.ts`; keep that port for the normal
development command. The server has no user authentication or configurable
upload-size enforcement in its current UI API.

## PDF reading and OCR

`config.yaml` sets `pdf_ingestion.preserve_all_pages: true` and these OCR defaults:

| Setting | Value |
| --- | --- |
| `enabled` | `true` |
| `language` | `eng` |
| `dpi` | `200` |
| `min_native_chars` | `80` |
| `min_confidence` | `0.80` |
| `bootstrap_pages` / `bootstrap_max_pages` | `15` / `5` |
| `selected_max_pages` / `inventory_max_pages` | `24` / `24` |

The OCR confidence is a text-quality proxy, not a calibrated probability of
correct transcription. Missing OCR resources and low-quality text are recorded
rather than silently treated as reliable evidence. Install the language data
needed by PyMuPDF/Tesseract for your PDFs. Reader/OCR changes can alter segment
identifiers and invalidate saved runs or gold alignment.

The connected-graph pipeline does not depend on these settings. After the reader,
it transcribes with the model the pages that still have no usable text: fewer
than 80 characters under a picture covering a quarter of the page or a drawing of
at least 200 strokes, or text in which three words out of ten hold unusable
characters. A page the reader already gave good text for, native or from
Tesseract, is never sent. Transcribed segments have their own IDs and never
replace an ID the reader gives to a page with text, so gold citations of text
pages stay valid.
