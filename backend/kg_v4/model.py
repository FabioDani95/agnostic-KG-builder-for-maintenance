"""Data exchanged by the stages: mentions and facts read from the manual, then nodes and edges.

Design rules:

* A fact always carries a page and a section. Segment IDs point to the exact place when the
  model cites them; their absence never removes the fact.
* A verdict about meaning is the only reason a fact leaves the graph (``contradicted``).
  Everything else is a confidence level a consumer may filter on.
* Mentions keep the manual's own words (description, instruction, expected result); nodes are
  built from them, so merging never loses text or provenance.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.kg_v3.contracts import ContextItem

ACTION_KINDS = ("repair", "inspection", "escalation")
Verdict = Literal["supported", "unclear", "contradicted", "unchecked"]
# extract/reread: read from a passage; gap_repair: found by a targeted search for a gap; reference: the
# manual points from one entry to another; catalogue: the survey's hierarchy; name_mention: the item's
# own name names the part; import: converted from a run of the previous pipeline.
Origin = Literal["extract", "reread", "gap_repair", "reference", "catalogue", "name_mention", "import"]
CONFIDENCE = {"supported": "high", "unchecked": "medium", "unclear": "low", "contradicted": "rejected"}


class Evidence(BaseModel):
    """Where a fact is written: page and section always, segments when known."""

    page: int = Field(ge=1)
    section: str = ""
    segment_ids: list[str] = Field(default_factory=list)
    # cited: the model named the segments; matched: found by the code on that page;
    # unit: only the passage that was read is known.
    anchor: Literal["cited", "matched", "unit"] = "unit"


class Mention(BaseModel):
    """One entity as one passage names it."""

    key: str
    type: str
    name: str
    code: str = ""
    kind: str = ""  # action kind
    stated: bool = True
    description: str = ""
    # Ontology properties read from the passage: instruction_text, expected_result, severity,
    # category, material_context, part_number.
    attributes: dict[str, str] = Field(default_factory=dict)
    evidence: Evidence
    unit_id: str = ""
    record: str = ""


class Fact(BaseModel):
    """One relation between two mentions, as one passage states it."""

    fact_id: str
    relation: str
    source: str  # mention key
    target: str  # mention key
    # Source entry (table row, list item, flowchart branch): facts of one record form one branch.
    record: str
    conditions: list[ContextItem] = Field(default_factory=list)
    evidence: Evidence
    origin: Origin = "extract"
    verdict: Verdict = "unchecked"
    reason: str = ""

    @property
    def confidence(self) -> str:
        return CONFIDENCE[self.verdict]


class Reference(BaseModel):
    """A pointer the manual prints ("see page 63", "like 'Pump gets too hot'")."""

    text: str
    mention: str = ""  # mention key it was written for
    unit_id: str = ""
    page: int = 0
    target_pages: list[int] = Field(default_factory=list)
    target_section: str = ""
    resolved: bool = False


class UnitRecords(BaseModel):
    """Everything one reading unit yielded."""

    unit_id: str
    pages: list[int] = Field(default_factory=list)
    mentions: list[Mention] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    # Causes the passage lists while saying nothing about a remedy (mention keys).
    no_remedy: list[str] = Field(default_factory=list)
    unclear: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    failed_reads: int = 0
    reads: int = 0


class CatalogueEntry(BaseModel):
    """A component or code of the machine, named once for the whole manual."""

    type: Literal["Component", "ErrorCode"]
    name: str
    code: str = ""
    aliases: list[str] = Field(default_factory=list)
    part_of: str = ""
    category: str = ""
    part_number: str = ""
    description: str = ""
    pages: list[int] = Field(default_factory=list)


class PageSurvey(BaseModel):
    page: int
    kinds: list[str] = Field(default_factory=list)
    diagnostic: bool = False
    evidence: list[str] = Field(default_factory=list)


class DocumentSurvey(BaseModel):
    """The whole manual seen once: what each page holds and which parts and codes exist."""

    pages: list[PageSurvey] = Field(default_factory=list)
    catalogue: list[CatalogueEntry] = Field(default_factory=list)
    asset: dict[str, str] = Field(default_factory=dict)
    failed_batches: list[list[int]] = Field(default_factory=list)

    def diagnostic_pages(self) -> list[int]:
        return sorted(item.page for item in self.pages if item.diagnostic)


class Node(BaseModel):
    node_id: str
    type: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    code: str = ""
    kind: str = ""
    stated: bool = True
    description: str = ""
    properties: dict[str, Any] = Field(default_factory=dict)
    # Properties deduced rather than read; reported as such.
    inferred: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    mention_keys: list[str] = Field(default_factory=list)


class Edge(BaseModel):
    edge_id: str
    relation: str
    source: str
    target: str
    facts: list[Fact] = Field(default_factory=list)

    @property
    def verdict(self) -> str:
        order = ("supported", "unchecked", "unclear", "contradicted")
        return min((fact.verdict for fact in self.facts), key=order.index)


class Graph(BaseModel):
    nodes: dict[str, Node] = Field(default_factory=dict)
    edges: list[Edge] = Field(default_factory=list)
    # Facts a meaning check rejected, with the reason; never silently dropped.
    rejected: list[dict[str, Any]] = Field(default_factory=list)
    merges: list[dict[str, Any]] = Field(default_factory=list)
    kept_apart: list[dict[str, Any]] = Field(default_factory=list)

    def out_edges(self, node_id: str, *relations: str) -> list[Edge]:
        return [edge for edge in self.edges if edge.source == node_id and (not relations or edge.relation in relations)]

    def in_edges(self, node_id: str, *relations: str) -> list[Edge]:
        return [edge for edge in self.edges if edge.target == node_id and (not relations or edge.relation in relations)]
