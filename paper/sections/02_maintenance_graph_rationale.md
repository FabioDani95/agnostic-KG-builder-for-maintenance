# Why a knowledge graph for maintenance diagnosis?

Maintenance diagnosis requires relationships between observations, components,
possible failure modes and the actions or inspections associated with them.
These relationships can be distributed across technical documents and operational
systems. In field service engineering for powertrains, Juhlin et al.
[@juhlin2025fieldservice] propose a knowledge integration framework that connects
heterogeneous sources through an expert-defined ontology. This provides a
concrete industrial motivation for making diagnostic relationships explicit.
Ontology-guided extraction from maintenance short texts has also been studied
[@vancauter2024maintenance]. The contribution considered here concerns how such
relationships can be recovered from manuals with evidence and preserved branch
context; the use of a language model to construct a graph is established prior art.

A graph makes the identity and type of each relationship available to a program.
For example, an application can request the candidate failure modes associated
with an observed error code, restrict them to the relevant component and return
the documented inspections with their source references. These operations can
be composed without asking a language model to reconstruct the relationships
on every request. Formal graph query languages provide an established basis
for expressing graph patterns and paths [@w3c2013sparql]. The present
implementation uses a typed property graph rather than an RDF store. SPARQL
therefore provides a reference for the query semantics, not a claim about the
software currently implemented.

This representation is useful only if it preserves the conditions under which a
relationship holds. Two troubleshooting branches can share a symptom while
requiring different inspections and corrective actions. Merging them solely
because their labels resemble each other can create a path that the manual
never states. We consequently treat branch identity, conditions and evidence
as part of the diagnostic information to preserve. Structural constraints can
identify inadmissible combinations or missing fields. SHACL illustrates this
separation between a graph and constraints used to validate it [@w3c2017shacl].
In our implementation, typed schemas and application checks fulfil this role;
SHACL conformance has not been implemented. Structural acceptance alone does
not establish that a relation is supported by the source.

Evidence links serve a different purpose. They allow a reviewer to inspect the
passage supporting an assertion, understand its origin and resolve conflicts.
PROV-O supplies a general vocabulary for representing provenance
[@w3c2013provo]. Our current evidence records use application-specific source
and location identifiers; a PROV-O mapping would be an interoperability extension.
A matching quotation establishes that text occurs in the document. Determining
whether it supports the asserted diagnostic relationship requires a separate
semantic judgement. This distinction motivates evaluating evidence localisation
and relation correctness independently.

A verified graph can also act as the knowledge layer for a bounded maintenance
agent. We use 'deterministic execution' to denote a specified interface: for a
fixed graph version, canonical observations and a fixed query or rule, the
executor returns the same ordered candidates, evidence references and explicit
missing-information states. This is a proposed application contract, not an
empirical finding from the existing extraction experiments. It requires stable
identifiers, defined traversal rules, deterministic tie-breaking and a versioned
rule set. A language model may translate an operator's request or explain the
result, but those operations introduce separate sources of variability. Neither
the graph nor the executor makes uncertain diagnostic knowledge certain.

The practical benefit must therefore be tested. A graph introduces construction,
validation and maintenance costs, and straightforward document lookup may remain
adequate for some questions. Our planned downstream evaluation compares typed
graph queries with retrieval over the same evidence and uses a structured-record
baseline to isolate the effect of graph organisation. It measures whether each
method returns the required diagnostic relationships with correct branch context
and supporting evidence. Questions with absent or ambiguous information test
whether the system reports the limitation. Improvements in equipment reliability,
repair time or autonomous physical intervention fall outside the evidence of this
study unless separately measured.
