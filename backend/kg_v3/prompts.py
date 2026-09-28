"""Versioned instructions for the V3 model roles.

The reviewer brief is hashed into every agent answer, so a decision can be
traced to the exact instructions that produced it.
"""

REVIEWER_BRIEF = """You review a knowledge graph extracted automatically from a technical maintenance manual.
Each question shows what the manual says (excerpts with segment IDs and pages) and what the
system proposes. Answer as an experienced maintenance engineer would.

1. Judge meaning, not wording. A paraphrase with the same technical logic is correct.
2. Use only the excerpts shown. Do not add or remove facts from outside knowledge.
3. A cause, check or remedy belongs to the entry (table row, list item, paragraph) that states
   it. Reject a proposal that joins parts of different entries.
4. A statement marked [inspection] is correct when the manual prescribes that check or test for
   that problem or cause; it does not need to repair anything. A statement without that mark
   claims a remedy: a check alone does not support it.
5. Conditions, negations, numbers, units and codes must keep the meaning they have in the source.
   A cause that only repeats the problem, or a check presented as a cause, is not correct. A cause
   marked (not written in the manual) is correct when the manual gives that problem with that check
   or remedy; its name is the system's reading of the check, not a claim that the manual states it.
6. For a page map, a page is diagnostic when it helps find or fix a fault (troubleshooting tables,
   fault or alarm codes, tests); procedure pages hold steps that diagnostic pages rely on.
7. Choose exactly one listed option ID. If only some numbered statements are right, choose
   correct and list their numbers in keep_statements. For a page map, choose correct and list
   each page whose label must change.
8. Cite the segment IDs you relied on and give a one-sentence rationale.
9. If the excerpts are not enough to decide, set confident to false instead of guessing.
"""

MAP_PROMPT = """You label the pages of a technical maintenance manual so that the pages holding troubleshooting
knowledge can be read in detail. Each input line is one page: its number, whether it has tables,
and its first words.

Labels:
- diagnostic: helps find or fix a fault: troubleshooting tables, fault, error or alarm codes and
  what they mean, symptom/cause/remedy text, LED or display indications, diagnostic tests and
  checks with their outcomes.
- procedure: step-by-step service, repair, adjustment or replacement instructions.
- parts: part lists, exploded views, spare parts.
- other: anything else (safety, specifications, installation, operation, index, legal).

When a page could be diagnostic, label it diagnostic and set unsure to true. Give every page a
short section name taken from its headings. Return one entry for every input page.
"""

SCAN_PROMPT = """You scan the full text of pages of a technical maintenance manual for troubleshooting knowledge,
wherever it is written: troubleshooting sections, but also operation, maintenance, installation,
test or glossary pages. Each segment starts with its ID in brackets.

Troubleshooting knowledge names a specific fault or abnormal state of this machine or its parts:
- a fault, alarm, error or status code, or an abnormal observation (noise, leak, wear, damage,
  a reading out of range, a lamp or display indication) with its meaning, cause, check or remedy;
- a condition that requires stopping, adjusting, cleaning, repairing, replacing or contacting
  service ("if X, do Y", "X may cause Y", "replace if cracked", "inspect for blockage and clean");
- a test or measurement with an expected value or outcome, or with what to do otherwise;
- a step of a troubleshooting flowchart or decision procedure.
Not troubleshooting knowledge: general safety rules and hazard warnings (what may happen if an
instruction is ignored), installation and environment requirements, routine steps without a
fault condition, specifications, part lists and descriptions of how the machine works.

Return only the pages that contain troubleshooting knowledge, each with the IDs of the segments
that state it. Cite only IDs shown in the input.
"""

EXTRACTION_PROMPT = """You build a maintenance knowledge graph from a technical manual. The graph follows this
fixed ontology; the asset itself ({asset}) already exists, never create it.

{ontology}

The input is a part of the manual split into segments, each starting with its ID in brackets.
Lines marked (context) are read-only: do not create standalone branches from them. Preserve
prerequisites and warnings from them when they govern actions in the owned section.

Rules:
1. Extract every troubleshooting fact the text states: observed symptoms or error codes, their
   possible causes (failure modes), the affected components, and the actions that fix them or
   the checks to perform.
2. Every entity and relation lists in "cite" the IDs of the segments where it is written. Give IDs
   only, never copy text.
3. Names are short English phrases with the same meaning as the source. Keep numbers, units,
   codes, directions and negations. Each name must make sense on its own: an action says what it
   acts on ("Clear the restricted air line", not "Clear"), taking the object from the entry.
   Entity keys are local labels such as E1, E2.
4. Give one "record" label (R1, R2, ...) per source entry: a table row, a list item or a passage
   about one problem. Relations from the same entry share it. Never join a cause, check or remedy
   to a problem from another entry.
5. For an error or alarm code, put the printed code in "code" and a short meaning in "name". An
   entry about a code is an ErrorCode linked with its own relation; do not add a Symptom for the
   same indication unless the manual describes a separate observation (a lamp, a noise, a behaviour).
   A number indexing a numbered cause list referenced by a matrix is not an ErrorCode.
   Resolve it to the cited list entry and connect the matrix symptom to that cause.
   Never invent the contents of a missing numbered entry; report it in unclear.
6. When one entry lists several remedies or checks ("clear the valve; replace the seals"), create
   one action per remedy or check, each linked to the failure. For a corrective action set "kind": repair for actions that fix the fault, inspection for
   checks, tests and measurements, escalation for contacting service or a dealer. Link checks to
   the failure with the same relation as repairs, with kind inspection. Other types use "".
7. stated is true only for a cause the manual writes as a cause. If the manual gives an action or
   check for a symptom without naming a cause, create a failure mode with stated false: name it
   after the fault the check or remedy points to when that is clear ("Incorrect input voltage" for
   "make sure the correct voltage is applied"), otherwise "Unspecified cause of <symptom>".
8. Every relation's conditions are objects with kind, text and cite. Use kind "if" for a
   conditional antecedent or threshold, "prerequisite" for something required before the action,
   "warning" for a prohibition or constraint during it, "expected" for the result of a test,
   and "order" for its place in a sequence. Never turn a test outcome into a prerequisite.
   Preserve prohibitions even when the main corrective action is already extracted.
   In section_context list prerequisites/warnings governing a whole table or procedure,
   including those in preceding read-only context. Cite the original block and list every
   applicable record label in records. The code attaches this context to those records' actions.
9. A failure mode is a faulty state or cause the manual names (worn, blocked, loose, not mapped,
   out of adjustment). A check to perform is never a failure mode: "the valves need checking" is
   a check. When the manual lists only checks for a problem, link them to a failure mode with
   stated false as in rule 7. A cause that only repeats the problem is not a cause. A cause derived
   from a check or remedy is never stated: "check for the proper size liner" names a check, so
   "liner of the wrong size" may only appear with stated false.
10. Numbered steps are marked (step 5), sub-steps (step 5a). A sub-step belongs to its parent
   step: link it only to the problem or cause of that step, never to another step's cause.
   Parts of one sentence may be split across several IDs on the same line; cite all of them.
11. kind repair: the step changes the machine (repair, replace, clean, adjust, tighten, refill).
   kind inspection: it only observes, measures or tests. A test that decides between possible
   causes is linked to each cause it confirms, with the condition it checks.
12. Link a component with AFFECTS only when the source says that this part is worn, damaged,
   blocked, faulty or out of adjustment in that fault. A part that is only used in the remedy
   is not affected.
13. Ignore specifications and part lists unless they state a fault, its cause or its remedy.
    Preserve warnings that govern the extracted actions as typed context, not standalone faults.
    List passages you cannot interpret in "unclear".
"""

VERIFY_PROMPT = """You check statements extracted from a technical maintenance manual. For each statement you
see only the manual text it cites. Answer supported when that text expresses the same meaning,
even in different words; not_supported when the text does not say it or says something different
(another entry, opposite condition, different code or number); unclear when the text is not
enough to decide. A statement marked [inspection] only claims that the manual prescribes that check
or test for that problem or cause. A cause listed among several causes of a problem supports that
problem-cause link; a remedy supports only the cause it is written for. Numbered troubleshooting steps
shown with the problem they belong to are remedies or checks for the cause that problem names, unless
a step or its parent step points to another cause. A numbered sub-step belongs to its parent step only. Answer not_supported when a statement marked [inspection] actually repairs,
replaces, cleans or adjusts, when a remedy statement only checks, and when the cause is a check to
perform, only repeats the problem, or is a check or remedy turned around into a fault that the text
never states as a cause. A cause marked (not written in the manual) only claims that the manual gives
this problem, check or remedy without naming a cause: judge the problem and the check or remedy, not
the cause name.
Context is typed: if=antecedent, prerequisite=before, warning=constraint/prohibition,
expected=test outcome, order=sequence. Check each item's role and scope against the cited source.
"""

_VERIFY_RULES = VERIFY_PROMPT.split("enough to decide. ", 1)[1]

VERIFY_PASSAGE_PROMPT = """You check statements extracted from a passage of a technical maintenance manual. You see the
whole passage the statements were read from (segments with IDs; page images when the layout carries
meaning) and, for each statement, the IDs it cites. Read the passage as a technician would: titles,
table columns, numbered steps, and flowchart questions with their yes/no outcomes and arrows
("go to No. 6") connect facts written in different segments, possibly on different pages.
Answer supported when the passage, read this way, states the same meaning, even in other words, and
the cited segments are where its parts are written (the problem, the test and its outcome, the
action). Answer not_supported when the passage does not say it or says something different
(opposite outcome or condition, another code or number), or when the statement joins parts of
different entries: a cause or remedy of a neighbouring table row, list item, flowchart branch or
procedure. Answer unclear when the passage is not enough to decide. """ + _VERIFY_RULES

MERGE_PROMPT = """You decide whether two names extracted from the same maintenance manual denote the same thing.
Answer same only when they mean the same fault, symptom, component or action. Different numbers,
codes, directions (for example up and down), sides, polarities or negations mean different.
The supplied branches and cited source determine identity. Different entries with different
remedies normally denote different entities, even when their names resemble each other.
Answer same only with positive evidence of equivalence; explain that evidence in rationale
and cite its segment IDs in cited_segments. Explain why differing branches are compatible
before proposing same. Answer unsure when you cannot tell.
"""
