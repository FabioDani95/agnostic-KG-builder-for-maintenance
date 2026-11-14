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
- **Node quality.** Descriptions that say more than the name, and how many come from
  the manual rather than from the graph context; required attributes filled from the
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

Judging is a paid model call. It needs the same explicit authorisation and ledger
as an extraction.

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
| `lg_lmh2235st` | In progress | 49 | | | | | | |

The other five campaign manuals have no gold v2: the work was limited to these three
to contain its cost.

## What is not measured yet

| Measure | State | What it needs |
| --- | --- | --- |
| Branch recall of the connected-graph pipeline | Not measured | Authorised runs on the development manuals, then the judge |
| Precision | Never measured for any version | A blind, stratified sample of facts judged by people against the manual. Sheets for earlier graphs exist and are unjudged; `scripts/kg_v3_precision_sheet.py` writes blind sheets. An LLM judge may be added only as a declared secondary measure |
| Residual duplicates, wrongly merged false friends | Screens only | A person judges the pairs the card lists |
| Agent utility | Not built | The questions of gold v2 exist for its closed manuals; still needed: a set of diagnostic questions per manual derived from the gold (a symptom or code: causes and actions), answered by an agent with the graph, by retrieval on the PDF text and by direct extraction with the same model, scored by the same pair judge or by people |
| External baselines | Not run | The same input text and scoring for every system |

## Proposed acceptance targets

Proposals to be confirmed by the project owner before any freeze; none is met or
measured today.

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
