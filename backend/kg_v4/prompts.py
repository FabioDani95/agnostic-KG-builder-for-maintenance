"""Instructions for the model roles of the connected-graph pipeline.

Each prompt states what the role returns and the few rules that protect meaning: one entry is
one record, only what the manual writes is a cause, numbers and directions keep their value.
A change here changes the prompt hash recorded in every run report.
"""

TROUBLESHOOTING_KNOWLEDGE = """Troubleshooting knowledge names a specific fault or abnormal state of this machine or its parts:
- a fault, alarm, error or status code, or an abnormal observation (noise, leak, wear, damage, a
  reading out of range, a lamp or display indication) with its meaning, cause, check or remedy;
- a condition that requires stopping, adjusting, cleaning, repairing, replacing or contacting
  service ("if X, do Y", "X may cause Y", "replace if cracked", "inspect for blockage and clean");
- a test or measurement with an expected value or outcome, or with what to do otherwise;
- a step of a troubleshooting flowchart or decision procedure.
Not troubleshooting knowledge: general safety rules and hazard warnings, installation and
environment requirements, routine steps without a fault condition, indications of normal
operation, specifications and descriptions of how the machine works."""

TRANSCRIBE_PROMPT = """You transcribe one page of the technical manual of {asset} from its image. The page has no usable text
layer: your transcription is the only text a maintenance knowledge graph will be built from, and
every fact will cite it. Write what is printed, nothing else.

Return the page as blocks in reading order (columns left to right, each from top to bottom):
- heading: a chapter, section or table title.
- text: a paragraph, a note, a warning.
- list_item: one bullet or numbered step, with its number.
- table_row: one block per data row. Write every cell as "column title: cell text", cells
  separated by " | ", so that the row can be read on its own. A cell that spans several rows is
  repeated in each of them. Do not return the header row by itself.
- flow_step: one box of a flowchart with what leaves it, for example "Is the fuse blown? -> Yes:
  Replace the fuse. -> No: Check the door switch."
- figure: the labels and callouts of one drawing or photograph, with its caption first.

Rules:
- Keep the language of the page. Do not translate, summarise, correct, complete or explain.
- Copy numbers, units, signs, codes and part numbers character by character.
- Write [illegible] in place of a word or value you cannot read; never guess it.
- Leave out running headers and footers, logos and the page number.
- printed_page: the page number printed on the page, "" when there is none.
- language: the language of the page ("en", "it", "de", ...).
- legible: false when most of the page cannot be read. A page with no text gives no blocks.
"""

SURVEY_PROMPT = """You survey pages of the technical manual of {asset} before a maintenance knowledge graph is built
from it. Each segment starts with its ID in brackets; "=== page N ===" opens a page. Use only what
the pages say.

Return:

1. pages: one entry for every page shown.
   - kinds: what the page holds, any of: troubleshooting (symptom, cause and remedy tables or text),
     error_codes (codes, alarms, lamp or display indications with their meaning), diagnostic_test
     (tests and measurements with expected values, decision flowcharts), maintenance (inspection,
     cleaning, lubrication and adjustment schedules), repair_procedure (step-by-step repair or
     replacement), parts_list (part lists, exploded views), specifications, safety, operation, other.
   - evidence: the IDs of the segments that state troubleshooting knowledge, wherever it is written;
     empty when the page has none.

""" + TROUBLESHOOTING_KNOWLEDGE + """

2. components: the parts and subsystems of this machine that the pages name, as a technician would
   look them up.
   - name: singular, as the manual writes it, without part numbers or reference letters.
   - part_of: the assembly or subsystem it belongs to, when the page says or shows it (an assembly
     heading, a parts list numbered 202 and 202-1, "the pump's diaphragm"); otherwise "".
   - category: mechanical, electrical, electronic, hydraulic, pneumatic, optical, software, sensor,
     safety, consumable, structural or other.
   - part_number: when printed, otherwise "".
   - description: one sentence from the page saying what the part is or does, or where it sits;
     "" when the page says nothing about it.
   Only parts of the machine: not the machine itself, not what it handles or consumes (water, oil,
   workpieces, material), not tools, people or documents. From a parts list keep assemblies and the
   parts a technician inspects, adjusts or replaces; skip fasteners, labels and other hardware.
   One entry per part: "air pump, water chiller or exhaust fan" is three parts.

3. codes: every fault, alarm, error or status code the pages print: the code exactly as printed and
   its short meaning from the page.

4. machine: what these pages say the machine itself is: description (one or two sentences on what
   it is and what it is used for), brand, model and type. Leave a field "" when the pages do not
   say it.
"""

EXTRACT_PROMPT = """You read one passage of the manual of {asset} and return the troubleshooting knowledge it states,
as records for a maintenance knowledge graph. A technician will use the graph to go from what is
observed (a symptom, a code) to the possible causes, to the checks that tell them apart and to the
right actions on the right components.

The passage is split into segments, each starting with its ID in brackets. Lines marked (context)
are read-only: do not create records from them, but use them to understand the entries you own (a
table, flowchart or procedure may continue from a title in the context). The line that opens
each page names the section the page belongs to: a table, flowchart or procedure that continues
from an earlier page belongs to the problem that section names. Pages whose layout carries
meaning (flowcharts, labelled diagrams) are also shown as images, in page order; their segments
carry their place on the page as @x,y (per cent of width and height). Follow boxes, arrows and
yes/no branches on the image. A page marked (transcribed) had no text layer: its segments were
read from the image you see, which is the source.

""" + TROUBLESHOOTING_KNOWLEDGE + """
Return nothing for text that holds none.

One record per source entry: a table row, a list item, a flowchart, a numbered procedure or a
passage about one problem. Never move a cause, check or remedy from one entry to another.

problem: what the technician observes or reads.
- type Symptom: an abnormal behaviour, noise, reading, lamp or display indication.
- type ErrorCode: a printed fault, alarm or error code. Put the code exactly as printed in "code"
  and its meaning in "name". A number that only indexes a list of causes is not a code.
- A maintenance or inspection step that names an abnormal state to look for ("inspect the intake
  screen for blockage and clean as required", "replace the belt if cracked", "check hoses for leaks")
  is a record of its own: the problem is that state as a Symptom, in the manual's words ("Intake
  screen blocked", "Belt cracked", "Hose leaking"; not "Screens need inspection"); the inspection
  and the repair are actions
  directly under it, the repair with its condition ("as required", "if cracked").
- When the passage gives a faulty state together with what it leads to ("too much distance
  diffuses the beam and gives poor cuts", "if the belt becomes loose the table can go out of
  square", "insufficient tension lets the belt slip"), the effect the technician notices is the
  problem, the faulty state is its cause, and the adjustment the manual prescribes is the action
  of that cause.
- type "" when the entry names no abnormal state at all (a component test, a measurement procedure).
  Never make a problem out of a section title, a test title or a safety warning.

see_also: a pointer from this entry to another entry that holds its causes or remedies ("like 'Pump
gets too hot'", "see Oil in the pump chamber"); otherwise "". Do not turn such a pointer into a
cause or an action.

causes: the faulty states the manual writes as causes of the problem (worn, blocked, loose,
out of adjustment, failed, wrong setting). Only causes the manual writes: a check to perform, a
remedy turned around into a fault, or a repetition of the problem is not a cause.
- conditions: when this cause applies (a flowchart outcome, a threshold, a mode).
- actions: what the manual prescribes for this cause.
- no_remedy: true when the entry names this cause and gives no check or remedy for it.

actions directly under the problem: the checks and remedies the manual gives for the problem
without naming a cause, including the steps of a flowchart or test whose outcome the manual does
not name as a cause. Put the outcome that leads to an action in its conditions.

An action:
- name: a short imperative phrase that makes sense on its own ("Replace the V-belt", not "Replace").
  One action per name: "Adjust/replace belts" is two actions, "Adjust the belts" and "Replace the
  belts" (the second with its condition, "if worn").
- kind: repair (changes the machine: replace, clean, adjust, tighten, reset, refill), inspection
  (observes, measures, tests) or escalation (contact service, the dealer or the manufacturer).
  "Inspect/replace if at fault" is two actions: the check (inspection) and the repair (repair) with
  the condition "if at fault". Several remedies in one entry are several actions.
- instruction: the manual's own steps, values, tools and warnings for this action, in order and
  close to its wording; "" when the manual says no more than the name.
- expected: for an inspection, the normal value or result the manual gives ("0.2-0.5 ohm", "lamp
  lights"); otherwise "".
- conditions: objects with kind and text. kind "if" for a conditional antecedent or outcome,
  "prerequisite" for something required before, "warning" for a prohibition or constraint,
  "expected" for the result of a test, "order" for its place in a sequence.
- reference: a pointer printed with it ("Page 63", "see section 6.8", "like 'Pump gets too hot'");
  otherwise "".

component (on a problem, a cause and an action): the part of the machine it concerns: where the
symptom shows, which part is faulty, which part the action works on. Use the name from the list of
known components when it is the same part, otherwise the name the passage uses, singular; "" when
no specific part is meant. Never the machine itself, a material, a medium or a tool.

description (problem and cause): one or two sentences from the passage about the thing itself: how
it shows, when it occurs, what it leads to. Never write about the manual or its tables, never a
repetition of the name; "" when the passage adds nothing.
severity (problem): only when the passage states it (a danger, warning or caution label, alarm
versus warning, "stop immediately", the machine cannot operate): critical, high, medium or low;
otherwise "".

cite (every item): the IDs of the segments where it is written. IDs only, never text.

Keep numbers, units, codes, directions and negations exactly. Names are short English phrases with
the meaning of the source. A numbered sub-step belongs to its parent step. In a decision flowchart
each outcome that prescribes an action is its own record under the problem the flowchart starts
from, named by its title or by the section it continues ("No heat"); its first question ("Does
the oven operate?") is a check, not the problem. Never give an action the outcome of another
question. A table of normal
values is not evidence of a fault: for a component test without a symptom, return a record with
problem type "", no cause, and the measurements as inspection actions on that component with their
expected values; what the manual prescribes for an abnormal result is a repair with that result
as its "if" condition.

components: parts the passage itself describes or places in the machine (name, part_of, category,
description, cite). Leave the list empty when the passage only mentions parts in passing.
unclear: passages you cannot interpret, with their IDs.
"""

VERIFY_PROMPT = """You check statements extracted from a passage of a technical maintenance manual. You see the passage
(segments with IDs; page images when the layout carries meaning) and numbered statements. Read the
passage as a technician would: titles, table columns, numbered steps and flowchart outcomes connect
facts written in different segments.

For each statement answer:
- supported: the passage states it, even in other words.
- contradicted: the passage says something different in meaning. Give the problem:
  opposite (an opposite value, direction, outcome or negation), other_entry (the cause, check or
  remedy belongs to another row, item, branch or procedure), prerequisite (a safety step or
  prerequisite presented as the remedy), invented (the passage names no such fault, part or
  action), wrong_part (the action or fault concerns another component).
- unclear: the passage is not enough to decide.

Judge meaning, never wording: a paraphrase, a shorter name or a missing detail is supported. A
statement marked [inspection] only claims that the manual prescribes that check for that problem
or cause. A statement "is given directly for" only claims that the manual prescribes the check or
remedy for that problem without naming a cause. Do not use knowledge from outside the passage.
Give a reason of a few words for every answer that is not supported.
"""

RESOLVE_PROMPT = """You decide whether two names taken from the same maintenance manual denote the same thing: the
same part, the same symptom, the same fault or the same action. For each name you see its type,
how the manual describes it, where it is written and the facts it takes part in.

Answer same only when a technician would treat them as one thing: a singular and a plural, a
short and a full name of the same part, the same instruction in other words. Answer different when
they differ in a number, a code, an axis, a side, a direction, a polarity, a negation, a position
(inner, outer, primary, secondary) or the part they concern, or when one is a part and the other
the assembly that contains it. A note "contrast" marks a difference to look at closely. When the
evidence is not enough to be sure, answer different: two nodes for one thing can be merged later,
one node for two things corrupts the graph. Give the reason in a few words.
"""

GAP_PROMPT = """You complete a maintenance knowledge graph built from the manual of {asset}. The graph has gaps: a
cause without a remedy, a problem without a cause or remedy, a cause that no symptom or code leads
to. For each gap you see the item, where it was read, and passages of the manual chosen for it
(segments with IDs).

Answer each gap from the passages only:
- status found: the passages state what is missing. Return it with the IDs of the segments where
  it is written. For a cause without remedy: the actions the manual prescribes for that cause. For
  a problem without cause or remedy: its causes, or the actions given directly for it. For a
  cause without problem: the symptom or code the manual associates with that cause.
- status not_stated: the passages show the item and state nothing of the kind, or do not show it.
Never complete a gap from general knowledge and never take a remedy from another entry: a wrong
link is worse than a missing one. Actions follow the same rules as in extraction: a short
self-contained name, kind repair, inspection or escalation, the manual's own steps in instruction,
the expected value of a check, and the component it works on.
"""

ENRICH_PROMPT = """You write the descriptions and attributes of nodes of a maintenance knowledge graph built from the
manual of {asset}. For each node you see its type, its name and the passages of the manual where
it is written, and the pages the manual points to from there. Use only those passages.

- description: one or two sentences about the thing itself, in plain technical English: what it is
  and where it sits (a part), how it shows and when it happens (a symptom or a fault), what it does
  and what it needs (an action). Never write about the manual, its tables, pages or sections ("the
  manual lists...", "listed as a cause of...") and do not repeat which problem a cause belongs to:
  the graph holds those links. "" when the passages say nothing beyond the name.
- attributes, by node type; give "" when the passages do not allow a value:
  Symptom severity: critical, high, medium or low.
  Component category: mechanical, electrical, electronic, hydraulic, pneumatic, optical, software,
  sensor, safety, consumable, structural or other.
  CorrectiveAction instruction_text: the steps of the action as the manual gives them, in order, with
  values, tools and warnings. When the manual points to a procedure on another page ("Align laser
  beam (Page 57)"), write the steps of that procedure, short. "" when the passages give nothing more
  than the name.
  CorrectiveAction expected_result: the normal value or result of a check.
- inferred: the attributes you deduced from the passages instead of reading them (for example a
  severity deduced from "stop the machine immediately"). A value that needs outside knowledge is
  not allowed: leave it "".
"""
