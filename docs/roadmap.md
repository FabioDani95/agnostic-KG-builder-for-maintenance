# Roadmap

This guide says where the application is going and why. It records goals,
decisions still open and the order of work; it is not a result. What is built
and measured today is in [Architecture](architecture.md) and
[Evaluation](evaluation.md).

## Primary goal

The primary goal is a journal article, Q1 if possible: a new, agentic way to
create the knowledge of a machine together with a person. The application is
built to the minimum the article needs. Backend and agent come first; the
interface follows later.

Using the graph is the motivation, not the subject. A maintenance agent that
answers from the graph comes after this work. The subject here is **creating**
the graph well, with model calls paid for building, testing and validating it on
real manuals.

## The idea

A person uploads files about one machine. A **knowledge creator agent**, a
capable model with tools, looks at each file and decides how to turn it into
knowledge. It runs the right tool, places the result in the graph of that
machine and asks the person only what it cannot settle alone. The graph grows
with every file. Every fact keeps its source, and every human decision is kept
as a source too.

```text
files about one machine
  (PDF manual, CSV log, report, image, ...)
            │
            ▼
  knowledge creator agent ──── questions ────► person
     │      plans, checks          ◄── answers, decisions
     ▼
  tools: read a manual · read a log · search the graph ·
         merge · find gaps · check the ontology · propose a change
            │
            ▼
  graph of the machine, under the application's ontology
```

The machine is the object. Its knowledge is held in the
[ontology](../ontology_schema.JSON) the application gives: symptoms, error
codes, faults, actions, components and the relations between them. The ontology
is fixed for every run but not carved in stone. The agent may propose a change
with a reason and examples; a person accepts it, and it becomes a new ontology
version.

## What exists today

| Piece | State |
| --- | --- |
| Tool for PDF manuals (`backend/kg_v4/`) | Built and measured on three development manuals: autonomous, page and section on every fact |
| Pages without text (scans, drawn lettering) | Read from their image by the model inside the manual tool |
| Ontology 3.0 | Fixed in the application, extended once with a stated reason for each new relation |
| Budget ledger, replay, run state | Built: every call is reserved, archived and can be replayed |
| Gold and measures | Gold v2 (AI-made) for three manuals; recall judge, quality card, loss analysis, comparison |
| Questions to a person, answers, approval | Built in V3 only (gates); the manual tool has none |
| Graph editor and accepted revisions | Built; makes no model calls |
| Agent that chooses tools | Not built |
| Other source types (logs, reports, images) | Not built |
| One graph per machine fed by several files | Not built: today one run gives one graph |

## Target architecture

**Machine workspace.** One graph per machine. Each uploaded file is registered
with its hash and type. Each change to the graph is a version that says which
file, tool, agent step or person produced it.

**Knowledge creator agent.** It reads what a file is and what it says about the
machine, chooses a tool and checks the tool's output against the graph:
conflicts, duplicates, gaps. It decides what is worth a question. It works
within a budget of calls, money and questions, and its steps are recorded so that
a run can be replayed.

**Tools.** Each tool is a pipeline or a bounded model step with a clear input and
output. Tools that add knowledge:

- `read_manual`: the connected-graph pipeline, as it is today.
- `read_log`: a CSV of alarms or events. The agent maps its columns (time, code,
  message, component) with the person's confirmation. The tool gives the codes
  seen, how often and with what, and links them to the manual's codes.
- Later: maintenance reports (what was observed, found and done), photos and
  drawings, spare-parts lists.

Tools that work on the graph: search, merge, find gaps, check against the
ontology, compare two versions.

Tools that involve the person: `ask_person`, a question with options, the
evidence and why it matters; and `propose_ontology_change`.

**Human and AI together.** The person does what the sources cannot:

1. Confirms which machine it is and what is in scope.
2. Settles conflicts between sources.
3. Adds what no file says. Expert knowledge becomes a source with provenance
   "person".
4. Accepts ontology changes and graph versions.

Questions are few, grouped and ranked by what they change in the graph. The
person never has to review the whole graph.

## What could make it publishable

The single techniques are not new. Extraction bound to source citations, model
judges of triples, interactive graph refinement and splitting work between
person and model by uncertainty all have direct precedents. An article that sells
one of them as new would be rejected. The contribution has to be the
architecture as a whole, measured. Candidates, each to be checked against recent
literature before it is claimed:

| Candidate contribution | What would show it |
| --- | --- |
| Agentic, tool-based creation of the knowledge graph of one machine from different kinds of files, under a governed ontology | The same agent handles manuals and logs; it is compared with a fixed pipeline per file type |
| Fusion across sources with provenance | Facts only the log gives; correct links between log codes and manual entries; conflicts found |
| Bounded co-creation between a person and an agent | Graph quality with no questions, with a budget of questions and with full review, against the person's minutes |
| Expert knowledge captured as a source | Facts the person added, cited as such and kept across versions |
| Ontology that evolves under control | Changes proposed with reasons, accepted or refused, and their effect on the graph |
| Evaluation on real documents | Gold, manuals kept out of development, human precision, cost per machine |

Wording follows the evidence. "Human-in-the-loop" and "human–AI co-creation"
describe what is built. "Symbiosis" or "less human effort" need a measurement of
that effect; without one they are not used.

## Minimum for the article

Needed:

1. The agent with at least two source types: PDF manuals (built) and one machine
   source, a CSV log of alarms or events. It needs a real machine with both a
   manual and a log; finding that data is the main risk.
2. Questions to the person within a budget, through the API or the command line.
   A new interface is not needed for the article.
3. Ontology change proposals with the person's decision.
4. Evaluation:
   - knowledge found: recall against a gold on the development manuals and on
     two or three manuals kept out of development; precision on a blind sample
     judged by people;
   - fusion: on the machine with a log, what the log adds and whether the links
     are right;
   - co-creation: quality at zero, some and unlimited questions, and the person's
     time;
   - the agent against the fixed pipelines on the same files;
   - cost and time per machine.
5. Release of code, ontology and gold where the manuals' licences allow.

Useful but optional: a small test of a maintenance agent answering the gold v2
questions with the graph, against retrieval on the PDF.

Not needed: a polished interface, many file types, the maintenance agent as a
product.

## Order of work

1. Finish the current measurements and documentation.
2. Literature check on the three open points: agentic or multi-agent graph
   construction, maintenance graphs that join logs and manuals, and human–AI
   co-creation of knowledge graphs. Then fix the claims.
3. Choose the data: a machine with manual and log, the manuals kept out of
   development, the people who answer and judge.
4. Machine workspace, file registry and a common tool interface; the manual
   pipeline becomes the first tool.
5. The creator agent: reads a file, chooses a tool, checks the result, keeps to
   its budgets, can be replayed.
6. The log tool.
7. `ask_person` and ontology proposals; human answers stored as sources.
8. Freeze the code, run the evaluation once, write the article.

## Decisions for the project owner

- The second source type (a CSV log is proposed) and the machine and data for it.
- The manuals kept out of development.
- Who answers the agent's questions and who judges precision, and for how many
  hours.
- The journal. Advanced Engineering Informatics is the working choice; Journal of
  Manufacturing Systems, Computers in Industry and Journal of Industrial
  Information Integration are alternatives.
- The budget for building and evaluation.
- Whether the V3 question gates are reused or rebuilt around the agent.
