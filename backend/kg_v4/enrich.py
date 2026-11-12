"""Stage 6, enrich: every node gets a description and its attributes from the places it is written.

It runs after resolution, once per entity and not per relation, so it is cheap: the model sees
the node, the passages around all its occurrences and the passages its printed pointers lead to,
and writes what the manual says. A value it cannot read stays empty and is exported as a
declared placeholder; a value it deduces is listed as inferred.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.kg_v3.reader import DocumentText, render_segments
from backend.kg_v4.gaps import Retriever
from backend.kg_v4.model import Graph, Node, Reference
from backend.kg_v4.names import canonical
from backend.kg_v4.prompts import ENRICH_PROMPT
from backend.kg_v4.survey import CATEGORIES

logger = logging.getLogger(__name__)

NODES_PER_CALL = 10
NODE_PASSAGE_CHARS = 1400
ENRICH_OUTPUT_TOKENS = 8000
MIN_DESCRIPTION_CHARS = 25
SEVERITIES = ("critical", "high", "medium", "low")
# The attribute each node type must have beyond name and description.
REQUIRED_ATTRIBUTE = {"Symptom": "severity", "Component": "category", "FailureMode": "material_context",
                      "CorrectiveAction": "instruction_text"}


def real_description(node: Node) -> bool:
    """A description that says more than the name."""

    text = " ".join(node.description.split())
    return len(text) >= MIN_DESCRIPTION_CHARS and canonical(text) != canonical(node.name)


def missing(node: Node) -> list[str]:
    lacks = [] if real_description(node) else ["description"]
    required = REQUIRED_ATTRIBUTE.get(node.type)
    if required and not node.properties.get(required):
        lacks.append(required)
    return lacks


def _schema(ids: list[str]) -> dict[str, Any]:
    text = {"type": "string"}
    answer = {"type": "object", "additionalProperties": False,
              "required": ["id", "description", "severity", "category", "material_context", "instruction_text",
                           "expected_result", "inferred"],
              "properties": {"id": {"type": "string", "enum": ids}, "description": text,
                             "severity": {"type": "string", "enum": ["", *SEVERITIES]},
                             "category": {"type": "string", "enum": ["", *CATEGORIES]},
                             "material_context": text, "instruction_text": text, "expected_result": text,
                             "inferred": {"type": "array", "items": {"type": "string", "enum": [
                                 "severity", "category", "material_context"]}}}}
    return {"type": "object", "additionalProperties": False, "required": ["nodes"],
            "properties": {"nodes": {"type": "array", "items": answer}}}


class Enricher:
    def __init__(self, llm, doc: DocumentText, *, asset_name: str, references: list[Reference] = (),
                 max_calls: int = 40, concurrency: int = 6) -> None:
        self.llm, self.doc = llm, doc
        self.system = ENRICH_PROMPT.format(asset=asset_name)
        self.retriever = Retriever(doc)
        self.targets: dict[str, list[int]] = {}
        for reference in references:
            self.targets.setdefault(reference.mention, []).extend(reference.target_pages)
        self.max_calls = max_calls
        self._limit = asyncio.Semaphore(max(1, concurrency))

    def passage(self, node: Node) -> str:
        cited = [cite for item in node.evidence for cite in item.segment_ids]
        ids = self.retriever.window(cited, radius=1) if cited else []
        if not ids:
            # Known only by page: the segments of that page that name it.
            found = self.retriever.search(node.name, limit=3)
            pages = {item.page for item in node.evidence}
            ids = [cite for cite in found if self.doc.segment(cite).page in pages] or found[:2]
        segments = self.doc.segments(list(dict.fromkeys(ids)))
        text = render_segments(sorted(segments, key=lambda item: self.doc.position(item.segment_id) or 0),
                               doc=self.doc)[:NODE_PASSAGE_CHARS]
        pages = sorted({page for key in node.mention_keys for page in self.targets.get(key, [])})[:2]
        if pages:
            pointed = [segment for page in pages for segment in self.doc.pages.get(page, [])]
            text += "\nThe manual points to:\n" + render_segments(pointed, doc=self.doc)[:NODE_PASSAGE_CHARS]
        return text

    async def _one(self, nodes: list[Node]) -> dict[str, dict[str, Any]]:
        ids = [f"N{index}" for index in range(1, len(nodes) + 1)]
        blocks = []
        for label, node in zip(ids, nodes):
            known = "; ".join(f"{key}: {value}" for key, value in node.properties.items()
                              if key in {"instruction_text", "expected_result"} and value)
            blocks.append(f"{label} [{node.type}{' ' + node.kind if node.kind else ''}] '{node.name}'"
                          + (f" (code {node.code})" if node.code else "")
                          + (f"\nAlready read: {known[:400]}" if known else "")
                          + (f"\nDraft description: {node.description}" if node.description else "")
                          + f"\nPassages:\n{self.passage(node)}")
        try:
            async with self._limit:
                data = await self.llm.json(system=self.system, user="\n\n".join(blocks), schema=_schema(ids),
                                           name="kg_v4_enrich", max_output_tokens=ENRICH_OUTPUT_TOKENS)
        except Exception as exc:
            logger.warning("Enrichment call failed: %s", exc)
            return {}
        answers = {}
        for item in data.get("nodes") or []:
            if isinstance(item, dict) and item.get("id") in ids:
                answers[nodes[ids.index(item["id"])].node_id] = item
        return answers

    async def enrich(self, graph: Graph) -> dict[str, int]:
        """Fill what nodes lack, in place; nodes that lack nothing cost nothing."""

        todo = sorted((node for node in graph.nodes.values() if missing(node)),
                      key=lambda node: (node.evidence[0].page if node.evidence else 0, node.node_id))
        batches = [todo[index:index + NODES_PER_CALL] for index in range(0, len(todo), NODES_PER_CALL)]
        results = await asyncio.gather(*(self._one(batch) for batch in batches[:self.max_calls]))
        filled = 0
        for answers in results:
            for node_id, answer in answers.items():
                node = graph.nodes[node_id]
                before = len(missing(node))
                description = " ".join(str(answer.get("description") or "").split())
                if description and canonical(description) != canonical(node.name) and (
                        not real_description(node) or len(description) > len(node.description)):
                    node.description = description
                required = REQUIRED_ATTRIBUTE.get(node.type)
                for key in filter(None, (required, "expected_result" if node.kind == "inspection" else "")):
                    value = " ".join(str(answer.get(key) or "").split())
                    if value and not node.properties.get(key):
                        node.properties[key] = value
                        if key in (answer.get("inferred") or []):
                            node.inferred = sorted({*node.inferred, key})
                filled += before > len(missing(node))
        return {"nodes_lacking": len(todo), "calls": min(len(batches), self.max_calls), "nodes_improved": filled,
                "nodes_deferred": sum(len(batch) for batch in batches[self.max_calls:])}
