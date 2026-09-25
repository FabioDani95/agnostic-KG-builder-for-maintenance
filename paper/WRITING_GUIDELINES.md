# Academic paper writing guidelines

These guidelines govern the manuscript and its scholarly supplements. They adapt
the author's EU proposal guidelines to a journal article on evidence-grounded
maintenance knowledge graph construction. Journal instructions take precedence
for submission format. Author instructions take precedence over these defaults.
Read this file at the start of each writing or substantive revision task.

## Argument and paragraph structure

Write in academic British English for researchers and maintenance practitioners.
Identify the technical problem, research question and proposed contribution early.
Introduce the industrial need before the architecture. Each paragraph should
advance one main claim and explain its relationship to the preceding paragraph.
Connect the problem, design choice, evidence and implication. Avoid introductory
facts or citations that never become part of the argument.

Use specific subjects, verbs and objects: preserve diagnostic branch identity,
verify a source span, reject an unsupported relation, measure review effort.
Explain why a design choice addresses a particular failure mode. Avoid technology
lists in place of reasoning. State the distinctive contribution once and let the
method and experiments establish it.

Distinguish implementation facts, prior findings, hypotheses, planned experiments
and measured results. Use present tense for the described method and established
knowledge; use a consistent tense for performed experiments. Do not describe a
planned evaluation as completed. Internal notes may contain clearly labelled
placeholders; a circulated draft must identify unresolved items explicitly.

## Terminology and claims

Define knowledge graph (KG), large language model (LLM) and other recurring
specialised abbreviations on first use in the main text. An abstract may require
its own definitions. Do not add an opening glossary unless the journal requires
one. Write a term in full if its abbreviation would appear only once.

Use a stable vocabulary for diagnostic record, branch, evidence, graph relation,
publishable output, review item and gap. Define the unit of evaluation before
using a score. Do not equate accounting coverage with correct autonomous
extraction, schema validity with semantic correctness, or a literal quotation
with support for the entire relation.

Define 'deterministic' by naming its boundary: a versioned graph, canonical input,
fixed query or rule and stable output ordering. LLM extraction remains stochastic.
A graph does not prove causality, completeness, operational safety or a reduction
in downtime. Such claims require their own evidence.

Qualify 'agnostic'. The current diagnostic schema and model provider are specific.
Manufacturer transfer can be evaluated; ontology, language and provider independence
must not be inferred from it. Avoid claiming a first, unique or general solution
without a defensible comparison with the literature.

## Restrained prose

Avoid em dashes and vertical separators in titles or running text. Mathematical
notation and genuine comparison tables may use their conventional symbols.
Avoid routine mirrored contrasts, including 'not only X but also Y' and 'not X
but Y'. State the intended proposition directly.

Remove promotional adjectives, unsupported superlatives, repeated conclusions and
stock transitions. Avoid phrases such as 'delve into', 'foster', 'leverage',
'pivotal', 'seamless' and 'it is worth noting'. Technical terms such as robustness
are acceptable when the property and measurement are defined.

Do not force three-item lists, parallel sentence rhythms or generic closing
paragraphs. Use connected prose for reasoning and lists for genuinely parallel
items. Keep headings informative. Avoid decorative boldface, emojis and tables
whose only purpose is to hold prose. Edit for a concrete subject in each sentence.
These rules support clear writing; they are not an AI-authorship detector.

## Sources and citation practice

Cite external claims close to the statement they support. Prefer primary research,
standards and original datasets. Use reviews for synthesis and follow important
claims back to their original evidence. A standard supports formal properties,
not measured benefits in maintenance. A proposed use case in another paper must
not be described as a demonstrated industrial outcome.

Maintain `references.bib`. Check author names, title, year, venue and DOI or stable
URL against the source. Never invent a DOI, publication status or citation. Use
journal-compatible in-text citations and a reference list, not the proposal's
page-footnote system. Link editorial evidence notes to code and artifacts in
`STATUS.md`; internal plans are not external scientific evidence.

Summarise sources accurately and in original wording. Quote only when needed,
with attribution. Distinguish the authors' argument from this paper's inference.
Record access dates for changing API/model documentation and preserve the pricing
basis used for each experiment.

## Methods and quantitative evidence

Specify corpus selection, inclusion and exclusion rules, annotation unit, dataset
splits and exposure history. Freeze gold independently of model predictions.
Explain annotation disagreement and adjudication. Keep development examples out
of claims about blind generalisation.

For every numerical result record the denominator, metric definition, split,
model, code revision, configuration and artifact location. Label macro and micro
averages correctly. Report uncertainty and repeated-run variability. State when
precision cannot be estimated because gold is partial. Report failed runs and
abstentions rather than silently deleting them.

Compare systems on the same input, gold and scoring rules. Separate model changes
from pipeline ablations. Distinguish technical tests from scientific evaluations:
passing unit tests does not demonstrate extraction quality. Report review effort
and token costs separately. Record estimated API cost as an estimate; do not
present it as an invoice or as the full cost of knowledge acquisition.

## Manuscript and document layout

Use a conventional journal structure adapted to the argument: introduction,
related work, method, experimental design, results, discussion and conclusion.
Include an explicit motivation for the maintenance graph and its downstream use.
Keep detailed annotation instructions and reproducibility material in supplements
when that improves readability.

The journal template governs page size, fonts, citation style and length. Until
selected, use semantic headings, readable tables and numbered figures with
self-contained captions. For an informal Word draft, A4 and Times New Roman
11 pt are acceptable defaults. Use styles rather than manual spacing. There is
no two-page limit. Restrained colour is acceptable in scientific figures when it
encodes information and remains legible in greyscale. Render every exported Word
or PDF page and inspect equations, citations, breaks and figure legibility.

## Review before circulation

Read the title and opening paragraph together, then the sequence of paragraph
openings. Verify that the contribution is coherent and each section advances it.
Check every numerical claim against a frozen artifact and every external claim
against its source. Check terminology, abbreviation definitions and citation keys.
Remove repetition, decorative structure and unsupported generality. Ensure the
abstract and conclusions describe the evidence actually reported. Include
limitations and unresolved coauthor questions without disguising them as results.

The EU call identifier, partner recruitment, TRLs, exploitation promises, funding
impact language and proposal-specific footnote/layout rules are deliberately
excluded. The original guideline file is preserved under `reference_material/`
for provenance and must not be treated as active paper instructions.
