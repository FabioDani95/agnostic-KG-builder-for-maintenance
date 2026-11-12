"""Stage 3, verify: one reading of the passage decides what each fact means against it.

The check can reject a fact only for its meaning (an opposite value, a remedy of another entry,
a prerequisite taken for the remedy, something the passage never names). Wording, a missing
citation or an incomplete name never count against a fact. Unclear facts stay in the graph with
low confidence; rejected ones are listed with the reason.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.kg_v3.contracts import ReadingUnit, context_text
from backend.kg_v3.llm import TruncatedResponse
from backend.kg_v3.reader import DocumentText, render_segments
from backend.kg_v4.model import Fact, Mention
from backend.kg_v4.prompts import VERIFY_PROMPT

logger = logging.getLogger(__name__)

VERIFY_BATCH = 40
VERIFY_OUTPUT_TOKENS = 8000
PROBLEMS = ("", "opposite", "other_entry", "prerequisite", "invented", "wrong_part")


def statement(fact: Fact, mentions: dict[str, Mention]) -> str:
    """One fact as a sentence a reader can check against the passage."""

    source, target = mentions[fact.source], mentions[fact.target]
    context = f" Context: {context_text(fact.conditions)}." if fact.conditions else ""
    mark = " [inspection]" if target.kind == "inspection" else " [contact service]" if target.kind == "escalation" else ""
    code = f" (code {source.code})" if source.code else ""
    detail = target.attributes.get("instruction_text", "")
    detail = f" Steps: {detail[:300]}." if detail else ""
    if fact.relation in {"MAY_INDICATE", "INDICATES"}:
        return f"The problem '{source.name}'{code} may be caused by '{target.name}'.{context}"
    if fact.relation == "RESOLVED_BY":
        return f"For the cause '{source.name}' the manual prescribes{mark}: '{target.name}'.{detail}{context}"
    if fact.relation in {"ADDRESSED_BY", "CLEARED_BY"}:
        return (f"'{target.name}'{mark} is given directly for the problem '{source.name}'{code}, "
                f"without a named cause.{detail}{context}")
    if fact.relation == "AFFECTS":
        return f"The fault '{source.name}' concerns the part '{target.name}'."
    if fact.relation == "ACTS_ON":
        return f"The action '{source.name}' is performed on the part '{target.name}'."
    if fact.relation == "OBSERVED_ON":
        return f"The problem '{source.name}' shows on the part '{target.name}'."
    if fact.relation == "PART_OF":
        return f"The part '{source.name}' belongs to '{target.name}'."
    return f"{source.name} -[{fact.relation}]-> {target.name}.{context}"


def _schema(ids: list[str]) -> dict[str, Any]:
    item = {"type": "object", "additionalProperties": False, "required": ["id", "verdict", "problem", "reason"],
            "properties": {"id": {"type": "string", "enum": ids},
                           "verdict": {"type": "string", "enum": ["supported", "contradicted", "unclear"]},
                           "problem": {"type": "string", "enum": list(PROBLEMS)},
                           "reason": {"type": "string"}}}
    return {"type": "object", "additionalProperties": False, "required": ["answers"],
            "properties": {"answers": {"type": "array", "items": item}}}


class Verifier:
    def __init__(self, llm, doc: DocumentText, *, images: Any | None = None, concurrency: int = 6,
                 batch: int = VERIFY_BATCH) -> None:
        self.llm, self.doc, self.images, self.batch = llm, doc, images, batch
        self._limit = asyncio.Semaphore(max(1, concurrency))
        self.failed_batches = 0

    def passage(self, segment_ids: list[str], context: list[str] = ()) -> tuple[str, list[str]]:
        ids = list(dict.fromkeys([*context, *segment_ids]))
        ordered = sorted(self.doc.segments(ids), key=lambda item: self.doc.position(item.segment_id) or 0)
        images, marks = self.images.for_segments(ids) if self.images is not None else ([], {})
        return render_segments(ordered, doc=self.doc, marks=marks), images

    async def _judge(self, text: str, images: list[str], facts: list[Fact], mentions: dict[str, Mention],
                     depth: int = 0) -> dict[str, tuple[str, str]]:
        ids = [f"S{index}" for index in range(1, len(facts) + 1)]
        lines = [f"{label}: {statement(fact, mentions)}" for label, fact in zip(ids, facts)]
        try:
            async with self._limit:
                data = await self.llm.json(system=VERIFY_PROMPT, schema=_schema(ids), name="kg_v4_verify",
                                           user=f"Passage:\n{text}\n\nStatements:\n" + "\n".join(lines),
                                           max_output_tokens=VERIFY_OUTPUT_TOKENS, images=images or None)
        except TruncatedResponse:
            if len(facts) < 2 or depth >= 3:
                self.failed_batches += 1
                return {}
            half = len(facts) // 2
            left, right = await asyncio.gather(self._judge(text, images, facts[:half], mentions, depth + 1),
                                               self._judge(text, images, facts[half:], mentions, depth + 1))
            return {**left, **right}
        except Exception as exc:
            logger.warning("Verification failed: %s", exc)
            self.failed_batches += 1
            return {}
        verdicts = {}
        for item in data.get("answers") or []:
            label = str(item.get("id"))
            if label in ids and item.get("verdict") in {"supported", "contradicted", "unclear"}:
                reason = " ".join(str(item.get("reason") or "").split())
                problem = item.get("problem") if item.get("problem") in PROBLEMS else ""
                # A rejection must say what in the meaning is wrong; without that the fact is only unclear.
                verdict = item["verdict"]
                if verdict == "contradicted" and not problem:
                    verdict = "unclear"
                verdicts[facts[ids.index(label)].fact_id] = (verdict, ": ".join(part for part in (problem, reason) if part))
        return verdicts

    async def check(self, facts: list[Fact], mentions: dict[str, Mention], segment_ids: list[str],
                    context: list[str] = ()) -> list[Fact]:
        """The facts with their verdicts; a fact the model did not answer for stays unchecked."""

        if not facts:
            return []
        text, images = self.passage(segment_ids, list(context))
        groups = [facts[start:start + self.batch] for start in range(0, len(facts), self.batch)]
        results = await asyncio.gather(*(self._judge(text, images, group, mentions) for group in groups))
        verdicts = {key: value for result in results for key, value in result.items()}
        return [fact.model_copy(update={"verdict": verdicts[fact.fact_id][0], "reason": verdicts[fact.fact_id][1]})
                if fact.fact_id in verdicts else fact for fact in facts]

    async def check_unit(self, unit: ReadingUnit, facts: list[Fact], mentions: dict[str, Mention]) -> list[Fact]:
        return await self.check(facts, mentions, unit.segment_ids, unit.context_segment_ids)
