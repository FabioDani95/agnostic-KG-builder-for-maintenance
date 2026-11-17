# Evaluation

This guide lists what is measured about a graph, with which tool, and what is still
missing. Passing software tests says nothing about extraction quality: quality is
measured on real manuals, and every number belongs to the code and model version
that produced the graph.

## Measures that need no judge

All three tools are offline and read-only. They work on graphs of both pipelines
and on manuals without a gold.

| Tool | Question it answers |
| --- | --- |
| `scripts/kg_scorecard.py` | How connected, complete and well described is this graph? |
| `scripts/kg_loss_analysis.py` | At which stage did a saved run lose each gold claim? |
| `scripts/kg_rebuild_from_v3.py` | What do the new assembly rules change on a graph V3 already extracted? |
| `scripts/kg_compare.py` | How do pipeline versions compare on the same manuals? See the [test plan](test-plan.md) |

```bash
.venv/bin/python scripts/kg_scorecard.py --discover --out experiments/my_cards
.venv/bin/python scripts/kg_scorecard.py path/to/run/graph.json --out experiments/my_cards
```

The quality card (`backend/kg_v4/metrics.py`) holds:

- **Grounded connectivity.** The asset node and its derived links are left out: a
  graph hung on one artificial hub is connected only on paper. Components, share of
  the largest component, causes with an action, causes reachable from a symptom or
  code, symptoms and codes with a complete chain, share of excluded relations. Two
  variants are always reported: without the links the code derives from names
  (`name_mention`) and from the survey's hierarchy, and without escalation actions
  ("contact service" joins unrelated entries).
- **Declared absences.** A cause for which the manual gives no remedy and says so in
  `remedy_status` counts as complete, apart from the causes with an action.
- **Node quality.** Descriptions that say more than the name and describe the thing,
  not the manual ("listed as a cause of...", "the manual identifies..." do not count);
  actions whose instruction only repeats the name or points to another page; action
  names that join two actions ("Adjust/replace"); required attributes filled from the
  manual, left as placeholders, or repeating the name; generic, noisy and truncated
  names; generic nodes used as bridges; exact duplicates.
- **Duplicate and false-friend screens.** Pairs of close names not kept apart by a
  difference of kind, and nodes whose aliases differ by a number, an axis, a side or
  an opposite. These are lexical screens that select pairs for a person: they are not
  a semantic verdict and must not be reported as a duplicate rate.
- **Provenance.** Share of facts with page and with section, by anchor and confidence.
- **Cost.** Calls, tokens, estimated cost and time from the run report.

`kg_loss_analysis.py` needs a saved judgement (a campaign `kpi_*.json`) and the run
state. It places each claim at the stage where its weakest link stopped: page not
read, never extracted, discarded by a gate, in the graph but not matched by the
judge, recovered. A "candidate" is chosen with the scorer's own rule (same segment
or similar names), so stages before "recovered" are upper bounds.

`kg_rebuild_from_v3.py` is an estimate on old extractions, not a run of the new
pipeline. Do not report its numbers as results of `kg_v4`.

## Branch recall

The gold of each campaign manual (`campaign/<manual>/gold/gold.json`) lists
diagnostic branches as claims: problem, cause, action, with the segments where they
are written. `scripts/kg_v3_evaluate.py:score_system` matches trusted edges to
claims and an LLM judge with three votes decides each pair; a branch counts when all
its claims are recovered. `scripts/kg_v3_kpi.py` runs it and reads graphs of both
pipelines. The judge is a model of the same family as the extractor: a human audit
of 40 pairs found it wrong on about one in five "different" verdicts. Recall figures
are therefore reported with the judge named, and a saved judgement is valid only
for the graph it judged.

Where the manual names no cause (most flowchart and maintenance claims of gold v2:
369 of 375 for the LG manual, 374 of 460 for Grizzly), the scorer has two ways to
find the extracted fact, chosen with `--unnamed-causes`:

- `record`, the default and the behaviour of every judgement saved before
  2026-11-16: the extracted fact must cite the very segment the gold cites, and each
  source record of a problem takes one of the eight places shown to the judge. On a
  flowchart with thirty outcomes most extracted steps never reach the judge.
- `problem`: the fact is found by the words the manual does give, and the unnamed
  causes of one problem count as one. Use it for manuals with flowcharts, and
  judge every system you compare with the same choice; the result file records it
  in `unnamed_causes`.

Judging is a paid model call, about 0.10 USD per 1,000 pairs with `gpt-6-luna`.
It needs the same explicit authorisation and ledger as an extraction.

## Gold v2, made by an AI

A second gold, `campaign/<manual>/gold_v2/gold.json`, lists all the diagnostic knowledge
of a manual page by page, not only its troubleshooting pages. **It is written by an AI,
not by a person**: annotators, an independent verifier, a second annotator on 25% of
the diagnostic pages and an adjudicator are Claude Opus 5.5, coordinated by Claude
Fable 5.2, which checks samples on the PDF. Until the owner fills
`REVISIONE_FABIO.md` the file says `human_review: false`, and results scored on it
must say that the reference is AI-made. Gold v1 stays frozen and was compared only
after each gold v2 was closed (`CONFRONTO_V1.md`).

Every item has a category and a scope, and the evaluation chooses the perimeter:
`core` (faults, error codes, flowchart outcomes), `extended` (component tests,
maintenance with a failure condition, repair procedures) and `context` (safety,
routine). The file also holds a page map of the whole PDF, an inventory of components,
symptoms, codes, false friends and synonyms, and 15 to 30 questions for an agent whose
answers are item IDs. `verification.independent_scopes` says which scopes the
independent verifier checked; the others were annotated once.

`scripts/kg_gold_v2.py validate <manual>` checks schema, segment IDs of the current
reader, quotes, page coverage, references and questions; `stats` counts items;
`export-claims` writes `claims_v1_format.json`, the same gold in the claim format of
gold v1 with `category` and `scope` on every claim, so the scorer above runs unchanged.
No command calls a model.

| Manual | State | Pages (diagnostic) | Core | Extended | Context | Questions | Verified scopes | Against gold v1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `graco_gtx_2000ex` | Closed 2026-11-14 | 18 (5) | 19 | 6 | 9 | 22 | core, extended, context | 19 v1 branches: 16 confirmed, 3 corrected from the PDF, 0 missing in v2 |
| `grizzly_g0872` | Closed 2026-11-14 | 80 (37) | 56 | 43 | 174 | 28 | core, extended | 66 v1 branches: 56 confirmed, 10 corrected from the PDF, 0 missing in v2 |
| `lg_lmh2235st` | Closed 2026-11-14 | 49 (28) | 46 | 34 | 54 | 28 | core, extended | 74 v1 branches: 47 confirmed, 25 corrected from the PDF (mostly finer granularity of flowchart paths), 2 added to v2 after the comparison |

The other five campaign manuals have no gold v2: the work was limited to these three
to contain its cost.

## Measured so far

These are development measurements, not results on unseen manuals. Graphs:
`kg_v4` with the extraction prompts of commit `4c239377`, the current ones (a
later change that returned flowchart questions as checks showed no gain and was
reverted), and V3 with the base profile (`scripts/kg_v3.py --gates agent`); both
with `gpt-6-luna` at low reasoning, November 2026, two replicas each. Reference:
gold v2, **written by an AI**, scopes core and extended. Judge: `gpt-6-luna`, three
votes, `--kg4-view full --unnamed-causes problem`; the verdicts are automatic.
Coverage is the mean share of each branch's claims that was found; claims found
are in brackets.

| Manual | Branches / claims | V3 base r1 / r2 | `kg_v4` r1 / r2 |
| --- | ---: | ---: | ---: |
| Graco GTX 2000EX | 21 / 39 | 89% / 90% (34 / 35) | 93% / 90% (37 / 35) |
| Grizzly G0872 | 91 / 193 | 60% / 54% (115 / 105) | 68% / 66% (135 / 126) |
| LG LMH2235ST | 64 / 289 | 40% / 49% (94 / 115) | 65% / 60% (210 / 191) |
| All three, share of claims found | 521 claims | 47% / 49% | 73% / 68% |

- **Graco**: the same within the noise.
- **Grizzly**: `kg_v4` finds much more of the extended scope (maintenance with a
  failure condition, component tests: 63% / 49% against 31% / 24%); on the core
  scope the two are close (70% / 77% against 80% / 74%).
- **LG**: `kg_v4` finds most flowchart outcomes (core 74% / 74% against 32% /
  44%) but less of the extended scope (48% / 31% against 56% / 61%): the component
  tests and door procedures of pages 28 to 30 are often missed.
- **Structure** (quality card of the same graphs): `kg_v4` has 85 to 100% of nodes
  in the largest grounded component against 41 to 94%, no generic node used as a
  bridge against 11 to 35 on Grizzly and LG, descriptions that say more than the
  name for 83 to 97% of nodes against none, and page and section on every fact.
  A run cost 0.014 to 0.146 USD and 96 to 337 seconds, against 0.016 to 0.245 USD
  and 94 to 783 seconds for V3.
- **Pages without text**: on a scanned machine-tool manual outside the campaign,
  with no gold, 74 of 114 pages were read from their image with no failure. An AI
  check of two of them found the transcript faithful row by row; this is not a
  measurement.

Limits: the reference is AI-made; the judge belongs to the model family of the
extractor; two replicas; prompts were tuned on Grizzly and LG; precision is not
measured. With the historical scorer (`record`) the numbers differ, most on LG,
and numbers from the two scorers are never compared with each other. The
judgements are kept with the runs in local experiment folders, outside version
control.

## What is not measured yet

| Measure | State | What it needs |
| --- | --- | --- |
| Branch recall on manuals other than the three with gold v2 | Not measured | A gold for the breadth manuals, or held-out manuals with a gold written before the run |
| Error rate of the judge on gold v2 | Not measured | A person reads a sample of "different" verdicts, as in the [test plan](test-plan.md#4-how-judging-stays-fair-without-being-rigid) |
| Transcription of pages without text | Checked by an AI on a few pages | A person compares transcripts of a sample of pages with the page |
| Precision | Never measured for any version | A blind, stratified sample of facts judged by people against the manual. Sheets for earlier graphs exist and are unjudged; `scripts/kg_v3_precision_sheet.py` writes blind sheets. An LLM judge may be added only as a declared secondary measure |
| Residual duplicates, wrongly merged false friends | Screens only | A person judges the pairs the card lists |
| Agent utility | Not built | The questions of gold v2 exist for its closed manuals; still needed: a set of diagnostic questions per manual derived from the gold (a symptom or code: causes and actions), answered by an agent with the graph, by retrieval on the PDF text and by direct extraction with the same model, scored by the same pair judge or by people |
| External baselines | Not run | The same input text and scoring for every system |

## Proposed acceptance targets

Proposals to be confirmed by the project owner before any freeze. They are judged
only on frozen code and on manuals kept out of development; the development
numbers above do not meet or fail them.

| Target | Value |
| --- | --- |
| Micro branch recall on the development manuals | at least 65%, and never below the V3 base profile on any manual |
| Precision on a blind human sample | at least 0.90 |
| Nodes in the largest grounded component | at least 90% |
| Causes with an action or a declared absence | at least 90% |
| Causes reachable from a symptom or code, where the manual gives one | at least 90% |
| Descriptions that say more than the name | at least 95% |
| Placeholders | only where the manual is silent |
| Generic nodes used as bridges, merged false friends | none |
| Residual semantic duplicates in the judged sample | below 2% |

The node targets hold for every test manual, small ones included.

## Development and evaluation manuals

Grizzly G0872 and LG LMH2235ST are development manuals: prompts and rules may be
tuned on them. The other campaign manuals check that a change does not fit two
documents only. Claims about manuals the system has never seen need manuals kept
out of development and run once, after the code is frozen; which ones is a decision
of the project owner. A manual that has been read during development never becomes
a blind test afterwards.
