# Roadmap

This guide says where the application is going and why: the goal, the position
against published work, the three points that make the article new, the journal,
and the order of work. It is not a result. What is built and measured today is in
[Architecture](architecture.md) and [Evaluation](evaluation.md).

## Primary goal

The primary goal is a journal article, Q1 if possible. The application is built
to the minimum the article needs: backend and agent first, interface later. The
step must be new and relevant, but small enough to start from what exists.

Using the graph is the motivation, not the subject. A maintenance agent that
answers from the graph comes after this work. The subject here is **creating**
the knowledge of one machine well, together with a person.

## The idea

A person uploads files about one machine. A **knowledge creator agent**, a
capable model with tools, looks at each file and decides how to turn it into
knowledge. It runs the right tool, places the result in the graph of that
machine and asks the person only what the files cannot tell. The graph grows
with every file. Every fact keeps its source, and a person's answer is kept as a
source too.

```text
files about one machine
  (PDF manual, CSV alarm log, later reports and images)
            │
            ▼
  knowledge creator agent ──── few ranked questions ────► person
     │  plans, checks, keeps to a budget   ◄── answers, approvals
     ▼
  tools: read a manual · read a log · search the graph · merge ·
         find what a diagnosis misses · check the ontology · propose a change
            │
            ▼
  graph of the machine, under the application's ontology (versioned)
```

The machine is the object. Its knowledge is held in the
[ontology](../ontology_schema.JSON) the application gives: symptoms, error
codes, faults, actions, components and their relations. The ontology is fixed
for every run but not carved in stone: the agent may propose a change with
evidence and a reason, a person accepts or refuses it, and an accepted change is
a new ontology version.

## What exists today

| Piece | State |
| --- | --- |
| Tool for PDF manuals (`backend/kg_v4/`) | Built: autonomous, one survey of the whole manual before extraction, meaning checks, look-alikes kept apart, page and section on every fact |
| Pages without text (scans, drawn lettering) | Read from their image inside the manual tool |
| Search for what a diagnosis misses | Built inside the manual tool: causes without a remedy, problems without an explanation and causes no symptom leads to are searched for in the manual, and stated as absent when nothing is written |
| Measurements | Three development manuals with an AI-made gold: the manual tool finds 68 to 73% of the claims against 47 to 49% for the earlier pipeline, with connected, described graphs ([details](evaluation.md#measured-so-far)) |
| Ontology 3.0 | Fixed in the application; extended once, by hand, with a stated reason for each new relation |
| Budget ledger, replay, run state | Built: every call is reserved, archived and can be replayed; cost per run is known |
| Questions to a person, answers, approval | Built in the earlier V3 pipeline only (question store, gates, interface) |
| Graph editor and accepted revisions | Built; makes no model calls |
| Agent that chooses tools | Not built |
| Log tool, one graph per machine fed by several files | Not built |

## Position against published work (November 2026)

A literature search of work published up to November 2026 gives a clear picture.
Agents that build knowledge graphs exist, mostly in other domains and on text
only. Ontology-guided LLM extraction for maintenance is common. Fusing manuals,
logs and work orders into maintenance graphs exists, usually by pooling the text
of a whole equipment class. Graph construction with expert review exists. So none
of these alone is new, and the article must not claim them.

The closest works and what each already covers:

| Work | Covers | Where it stops |
| --- | --- | --- |
| Plant Memory (arXiv preprint, October 2026) | Maintenance graph from work orders, ISO 14224 ontology, facts with evidence and verification state, targeted questions to technicians, approval of new ontology terms | Synthetic data, rule-first extraction, no agent choosing tools, no measured effort |
| MAGG, multi-agent construction with domain-expert review (arXiv preprint, August 2026) | Agents build the graph; triples admitted after review with audit metadata | Schema induced from text, generic benchmarks, human effort not measured |
| GRACE (AKBC workshop at EMNLP 2026) | Asks an expert only when a claim is worth the cost; verified claims become evidence | Works on model claims, not on documents of a machine; the abstract does not say whether the experts were real people |
| Juhlin et al. (SKGi 2025) and the ABB pipeline | Expert-defined ontology over manuals, logs and reports; fault codes linked to service cases | Experts review every triple; recall against a gold is not reported |
| Mandarapu and Kunkunuru (VLDB 2026 workshop) | Typed asset graph over CSV events and work orders; model-added facts tagged | Benchmark data, no real manual, construction quality not measured |
| Zhang et al., Advanced Engineering Informatics 2025 (MllmDA-KGC) | Multi-source, multimodal LLM graph for equipment operation and maintenance | Equipment-class level; provenance per fact not described |
| Li et al., Engineering Applications of AI 2026; Tsaneva et al., Information Processing and Management 2025 | The model finds semantic gaps and updates the graph; LLM plus human validation beats either alone | No question budget in maintenance; no time measured |
| OntoExtend (SEMANTiCS 2026), DRAGON-AI (J. Biomedical Semantics 2024), OntoKGen | LLM drafts ontology extensions; people approve | Driven by competency questions or curators, not by evidence met while extracting |
| Gil de Avalle et al. (IFAC 2026, APMS 2026) | Vision models read troubleshooting flowcharts against an expert gold | Flowcharts only, not whole manuals |

The full search, with links and how each source was checked, is kept with the
manuscript materials. A paper on maintenance knowledge graphs in *Engineering*
(2025) is marked as retracted by its publisher and must not be cited as support.

## Three points that make the article new

Each point extends what exists. None needs a new research programme.

### 1. Ask only what the documents cannot tell, and measure what each answer buys

**What is open.** Published systems either review everything, ask with simulated
experts, or do not measure the person's time. No work shows, for maintenance
knowledge, how graph quality grows with the number of questions and the minutes
of a real person.

**How.** The search for what a diagnosis misses already exists. When the files
do not fill a gap (a code with no explanation, a cause with no remedy, a symptom
with no cause), the agent turns it into a question. Questions are grouped,
ranked by what they change for a diagnosis and kept within a budget. The answer
enters the graph as a source with provenance "person", and a stated rule decides
what happens when it contradicts the manual.

**Shown by.** Four question policies on the same machines (no questions, random
questions, the agent's ranked questions, review of everything) at a few budgets,
answered by real people with their time measured. Quality is recall and precision
against the gold and the share of diagnosis paths left incomplete.

### 2. One machine, two kinds of source: the manual and its alarm log

**What is open.** Graphs that link a machine's own log codes to its manual's
entries, with frequency on the edge, provenance per source and a gold for the
links, were not found. The closest maintenance paper of this kind is retracted;
an evaluation on technical manuals reports that linking observed codes to manual
codes is hard.

**How.** A `read_log` tool reads a CSV of alarms or events. The agent proposes
which column is the time, the code, the message and the component; the person
confirms. The tool gives each code's count and what it co-occurs with, and links
it to the manual's entry for that code. A code in the log that the manual does
not explain becomes a gap, and therefore a question (point 1).

**Shown by.** Precision and recall of the code-to-entry links against a small
gold; codes found only in the log; the agent against the fixed manual pipeline
at the same cost, with the cost of each correct fact.

### 3. An ontology that changes only on evidence, with a person deciding

**What is open.** Ontology extensions drafted by a model and approved by people
exist, but they start from competency questions or curators. A change triggered
by facts that do not fit, met while extracting, with its acceptance rate and its
effect on the graph measured, was not found.

**How.** The extractor already writes notes; it also records facts that do not
fit the ontology. The agent groups them into one proposal with the evidence and
a reason. The person accepts or refuses. An accepted change is a new ontology
version, and only the affected passages are read again.

**Shown by.** This project's own history is the test: version 3.0 added four
relations (`PART_OF`, `ACTS_ON`, `ADDRESSED_BY`, `CLEARED_BY`) by hand because of
measured defects. Starting from version 2.0, does the agent propose them from the
evidence, and what do the accepted changes add to the graph?

### What carries the three points

Two things are not claimed as new but make the article credible: an evaluation on
real documents (development manuals, manuals kept out of development, precision
judged by people, cost per machine) and an ablation of the agent against the
fixed pipelines. The earlier pipeline gives a baseline that already exists.

## Journal and angle

**Advanced Engineering Informatics** is the recommended journal. Its scope asks
for explicit representation and use of knowledge in engineering, which is this
work; the closest competitors publish there, so reviewers will see the position
quickly. Impact factor 11.5 (2025, from the publisher's page). Its quartile was not
checked in the citation index. Risks: the journal is crowded with LLM plus graph
papers and expects evidence of generality, which the manuals kept out of
development and the ablations must give.

**Computers in Industry** is the backup: industrial, application-oriented, with
knowledge engineering, intelligent agents and product documentation in scope, and
recent papers on maintenance documents. Impact factor 10.0 (2025). The
**Journal of Industrial Information Integration** fits if the article leads with
the joining of sources.

**Angle.** The article is not "an agent builds a graph". It is how a person and an
agent share the work of creating one machine's knowledge under a governed
ontology, and what each minute of the person buys. Words follow the evidence:
"human–AI co-creation" for what is built; "less effort" only with the time
measured; "symbiosis" not used.

Elsevier requires a declaration of generative AI used in preparing the
manuscript, and an AI cannot be an author. The model calls of the method belong in
the methods section, and the AI-made gold must be declared as such.

## Minimum for the article

Needed:

1. The agent with two tools that add knowledge (manual, log), the graph tools and
   `ask_person`, through the API or the command line. A new interface is not needed.
2. One graph per machine fed by several files, with provenance per source and
   person.
3. Ontology proposals with the person's decision and versioning.
4. Data: the three development manuals; two or three manuals kept out of
   development, with a gold written before the run; one real machine with its
   manual and an alarm log.
5. People: two or three who answer the questions, timed, and who judge a blind
   sample for precision.
6. Release of code, ontology and gold where the manuals' licences allow.

Useful but optional: a small test of a maintenance agent answering the gold v2
questions with the graph, against retrieval on the PDF.

Not done for this article: sensor time series, photos and drawings as sources,
work orders, a polished interface, the maintenance agent as a product.

## Order of work

1. Choose the data: the machine with manual and log, the manuals kept out of
   development, the people. This is the main risk; it is decided first.
2. Machine workspace, file registry and a common tool interface; the manual
   pipeline becomes the first tool.
3. The creator agent: reads a file, chooses a tool, checks the result, keeps to
   its budgets, can be replayed.
4. `ask_person` on the gaps the documents leave, with ranking, budget and the rule
   for conflicts (point 1).
5. The log tool and the links to the manual (point 2).
6. Facts that do not fit the ontology and the proposals (point 3), first on the
   2.0 to 3.0 replay.
7. Freeze the code; gold for the held-out manuals and the links; run once;
   sessions with people; write.

## Decisions for the project owner

- The machine with manual and alarm log, and how to obtain the log.
- The manuals kept out of development.
- Who answers the agent's questions and who judges precision, and for how many
  hours.
- The journal: Advanced Engineering Informatics is recommended, Computers in
  Industry is the backup.
- The budget for building and evaluation.
- Whether the V3 question store is reused for `ask_person` or rebuilt around the
  agent.
