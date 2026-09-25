# Extraction model decision

Verified against official documentation on 2026-09-25:

- [Model catalogue](https://developers.openai.com/api/docs/models)
- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [Pricing](https://developers.openai.com/api/docs/pricing)
- [GPT-6 migration](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra#migration-quickstart)

GPT-6 Luna is the selected extraction candidate. Standard short-context rates
per million tokens are USD 0.10 input, 0.01 cached input, 0.125 cache writes and
0.50 output. GPT-5.6 Luna is USD 0.20 input and 1.20 output at the checked rates.
Lower token prices do not establish lower total cost at equal quality.
Long-context pricing applies above 272,000 input tokens to the full request:
2x input/cache rates and 1.5x output. These are Standard estimates; service-tier
and regional premiums require an explicit pricing configuration in a campaign.

The model supports structured outputs and Chat Completions. Extraction can retain
the existing `response_format` path. Reasoning supports none, low, medium, high,
xhigh and max, with medium as the provider default. Explicit configured low
reasoning is preserved. Custom temperature is omitted. Chat Completions function
calling with reasoning is a different constraint: Luna requires effort none for
function calling on that endpoint; a reasoning agent using tools would need
Responses. This increment does not migrate the chat agent or add tool calls to
extraction.

## Code increment

`config.yaml` selects GPT-6 Luna for scoping, ontology drafting and extraction,
retains the historical models as selectable comparators, and aligns the dormant
escalation primary model. The generic generation fallback and `.env.example`
use Luna. Existing environment variables or saved per-run selections still take
precedence; the actual `.env` is not edited. The gateway preserves explicit
reasoning and omits incompatible temperature. Cost estimation recognises Luna
instead of silently applying the fallback model's tariff.

The dedicated regression tests cover reasoning validation, request construction,
model identity, cache writes and the long-context threshold. Existing structured
output and diagnostic tests are also run. These offline tests establish local
integration behaviour, not provider access or extraction quality.

## Promotion gate

Before the scientific campaign, run a real structured-output smoke test and an
A/B pilot against GPT-5.6 Luna on development material using identical inputs,
prompts, schema and scoring. Record actual returned model, truncations, retries,
quality, review rate and costs. Freeze reasoning effort after the pilot. Preserve
historical results unchanged and do not label this configuration scientifically
validated until this gate passes.

No new paid extraction or API smoke test has been executed in this increment.
The first live run follows the gold/scoring preparation described in the protocol.

## Verification record

The complete offline suite passed: 563 tests in the isolated run, plus the one
loopback-origin test rerun with local-port permission, for 564 unique passing
tests. Ruff passed on all changed Python files. The five new test cases cover
GPT-6 Luna integration; the existing escalation-default assertion was updated
without changing historical explicit-model fixtures.

Verification used Python 3.12, OpenAI 2.54.0, PyMuPDF 1.27.1 and OpenPyXL 3.1.5,
with dependencies overlaid in an isolated audit environment to match the current
requirements. The existing repository virtual environment was not modified.
The snapshot excluded the user's .env and runtime data; historical replay tests
used a complete Git history. Five PyMuPDF/SWIG deprecation warnings remain.
No browser E2E or real provider call is implied by these results.

The original writing guideline file is byte-identical to the supplied document.
All local paper links and all five initial bibliography keys were checked.
