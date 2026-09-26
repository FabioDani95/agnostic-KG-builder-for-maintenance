"""One V3 run: six stations, three gates, state saved after every step.

A run with a work directory resumes where it stopped: finished stations and
units are loaded, not called again. Gates use a reviewer chain built from names
(agent, human, auto, script); people receive at most ``human_question_budget``
doubt questions, the most important first.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from backend.kg_v3.checker import CheckedRelation, Checker
from backend.kg_v3.contracts import Answer, DocumentMap, PageLabel, Question, ReadingUnit, Tier, Witness
from backend.kg_v3.extractor import Extractor, UnitExtraction, prompt_hash
from backend.kg_v3.llm import ModelClient
from backend.kg_v3.mapper import apply_map_answer, build_units, map_pages, map_question
from backend.kg_v3.merger import MergedGraph, MergePlan, assemble, judge_pairs, merge_candidates
from backend.kg_v3.ontology import OntologySpec, load_ontology
from backend.kg_v3.questions import (
    apply_relation_answers,
    approval_question,
    merge_decisions,
    merge_questions,
    relation_questions,
    unreadable_questions,
)
from backend.kg_v3.reader import DocumentText
from backend.kg_v3.reviewers import (
    AgentReviewer,
    AutoReviewer,
    HumanReviewer,
    InMemoryQuestionStore,
    QuestionStore,
    Reviewer,
    ReviewerChain,
    ScriptedReviewer,
)

GATE_NAMES = ("map", "doubts", "approval")


class RunConfig(BaseModel):
    model: str = "gpt-6-luna"
    reasoning_effort: str = "low"
    reads: int = 2
    unit_max_chars: int = 9000
    concurrency: int = 6
    human_question_budget: int = 15
    gates: dict[str, list[str]] = Field(default_factory=lambda: {
        "map": ["agent"], "doubts": ["agent", "human"], "approval": ["human"],
    })
    agent_model: str = "gpt-6-luna"
    agent_reasoning_effort: str = "medium"
    # Stop before extraction until the map is confirmed; otherwise the model's
    # map is used and its question stays open.
    wait_for_map: bool = False
    # Stop with a clear error instead of spending on an unexpectedly large reading.
    max_units: int = 150


class GateRecord(BaseModel):
    questions: list[Question] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)
    pending: list[str] = Field(default_factory=list)


class RunResult(BaseModel):
    status: str
    page_map: DocumentMap
    units: list[ReadingUnit]
    relations: list[CheckedRelation]
    graph: MergedGraph
    gates: dict[str, GateRecord]
    report: dict[str, Any]


class _HumanBudget:
    """Show a person only the most important questions, up to the budget."""

    def __init__(self, inner: Reviewer, budget: int) -> None:
        self.inner = inner
        self.identity = inner.identity
        self.budget = max(0, budget)

    async def review(self, questions: Sequence[Question]) -> list[Answer]:
        chosen = sorted(questions, key=lambda item: -item.priority)[: self.budget]
        return await self.inner.review(chosen)


class Pipeline:
    def __init__(
        self,
        *,
        doc: DocumentText,
        asset_name: str,
        llm: ModelClient,
        config: RunConfig | None = None,
        agent_llm: Any | None = None,
        human_store: QuestionStore | None = None,
        script: dict[str, Any] | None = None,
        workdir: Path | None = None,
        spec: OntologySpec | None = None,
    ) -> None:
        self.doc = doc
        self.asset_name = asset_name
        self.llm = llm
        self.config = config or RunConfig()
        self.agent_llm = agent_llm
        self.human_store = human_store or InMemoryQuestionStore()
        self.script = script or {}
        self.workdir = workdir
        self.spec = spec or load_ontology()
        self.timings: dict[str, float] = {}

    # Persistence ---------------------------------------------------------

    def _path(self, name: str) -> Path | None:
        return self.workdir / "state" / f"{name}.json" if self.workdir else None

    def _load(self, name: str) -> Any | None:
        path = self._path(name)
        return json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else None

    def _save(self, name: str, value: Any) -> None:
        path = self._path(name)
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")
        path.write_text(json.dumps(value, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # Gates ---------------------------------------------------------------

    def _reviewer(self, name: str) -> Reviewer:
        if name == "agent":
            if self.agent_llm is None:
                raise ValueError("an agent reviewer needs a model client")
            return AgentReviewer(self.agent_llm, model=self.config.agent_model)
        if name == "human":
            return _HumanBudget(HumanReviewer(self.human_store), self.config.human_question_budget)
        if name == "auto":
            return AutoReviewer()
        if name == "script":
            return ScriptedReviewer(self.script)
        raise ValueError(f"unknown reviewer {name!r}")

    async def _gate(self, gate: str, questions: list[Question]) -> GateRecord:
        saved = self._load(f"gate_{gate}")
        record = GateRecord.model_validate(saved) if saved else GateRecord()
        answered = {answer.question_id for answer in record.answers}
        todo = [question for question in questions if question.question_id not in answered]
        record.questions = questions
        names = list(self.config.gates.get(gate, ["auto"]))
        if todo and not names:
            # No reviewer configured: questions stay open (map: the model's map is used).
            record.pending = [question.question_id for question in todo]
        elif todo:
            # A resumed gate asks only the last reviewer, the one questions wait for.
            if saved and record.pending:
                names = names[-1:]
            outcome = await ReviewerChain([self._reviewer(name) for name in names]).review(todo)
            record.answers = [*record.answers, *outcome.answers]
            record.pending = [question.question_id for question in outcome.pending]
        else:
            record.pending = []
        self._save(f"gate_{gate}", record)
        return record

    # Stations ------------------------------------------------------------

    async def _timed(self, name: str, coroutine):
        started = time.perf_counter()
        try:
            return await coroutine
        finally:
            self.timings[name] = round(self.timings.get(name, 0) + time.perf_counter() - started, 3)

    async def _map(self) -> tuple[DocumentMap, GateRecord]:
        saved = self._load("map")
        page_map = DocumentMap.model_validate(saved) if saved else await self._timed("map", map_pages(self.llm, self.doc))
        self._save("map", page_map)
        record = await self._timed("gate_map", self._gate("map", [map_question(self.doc, page_map)]))
        for answer in record.answers:
            if answer.option_id == "correct":
                page_map = apply_map_answer(page_map, answer.edits)
        return page_map, record

    async def _extract(self, units: list[ReadingUnit], extractor: Extractor) -> list[UnitExtraction]:
        async def one(unit: ReadingUnit) -> UnitExtraction:
            saved = self._load(f"extract_{unit.unit_id}")
            if saved:
                return UnitExtraction.model_validate(saved)
            result = await extractor.extract(self.doc, unit)
            self._save(f"extract_{unit.unit_id}", result)
            return result

        return list(await self._timed("extract", asyncio.gather(*(one(unit) for unit in units))))

    async def run(self) -> RunResult:
        started = time.perf_counter()
        page_map, map_record = await self._map()
        if map_record.pending and self.config.wait_for_map:
            return self._result("waiting_for_map", page_map, [], [], MergedGraph(), {"map": map_record}, started, [])
        units = build_units(self.doc, page_map, max_chars=self.config.unit_max_chars)
        if len(units) > self.config.max_units:
            raise ValueError(f"{len(units)} reading units exceed max_units={self.config.max_units}; "
                             "check the page map or raise the limit explicitly")
        self._save("units", [unit.model_dump(mode="json") for unit in units])
        # Later steps depend on exactly these units: their saved state is keyed by them.
        stamp = hashlib.sha256("|".join(unit.unit_id for unit in units).encode("utf-8")).hexdigest()[:10]

        extractor = Extractor(self.llm, self.spec, asset_name=self.asset_name, reads=self.config.reads,
                              concurrency=self.config.concurrency)
        extractions = await self._extract(units, extractor)
        proposals = [proposal for item in extractions for proposal in item.proposals]

        saved = self._load(f"checked_{stamp}")
        if saved is not None:
            relations = [CheckedRelation.model_validate(item) for item in saved]
        else:
            checker = Checker(self.llm, self.spec, extractor_id=f"{self.config.model}:{extractor.prompt_id}",
                              concurrency=self.config.concurrency)
            relations = await self._timed("check", checker.check(self.doc, proposals))
            self._save(f"checked_{stamp}", [item.model_dump(mode="json") for item in relations])

        saved = self._load(f"merge_plan_{stamp}")
        if saved is not None:
            plan = MergePlan.model_validate(saved)
        else:
            plan = await self._timed("merge", judge_pairs(self.llm, merge_candidates(relations)))
            self._save(f"merge_plan_{stamp}", plan)

        doubts = [
            *relation_questions(self.doc, self.spec, relations),
            *merge_questions(self.doc, plan.unsure),
            *unreadable_questions(page_map),
        ]
        doubt_record = await self._timed("gate_doubts", self._gate("doubts", doubts))
        relations = apply_relation_answers(relations, doubts, doubt_record.answers)
        graph = assemble(relations, [*plan.same, *merge_decisions(doubts, doubt_record.answers, plan.unsure)])

        gates = {"map": map_record, "doubts": doubt_record}
        summary = self._summary(graph, relations, doubt_record)
        approval = await self._timed("gate_approval", self._gate("approval", [approval_question(summary)]))
        gates["approval"] = approval
        decision = next((answer.option_id for answer in approval.answers), None)
        status = {"approve": "approved", "reject": "rejected"}.get(decision, "awaiting_approval")
        return self._result(status, page_map, units, relations, graph, gates, started, extractions)

    # Reporting -----------------------------------------------------------

    def _summary(self, graph: MergedGraph, relations: list[CheckedRelation], doubts: GateRecord) -> list[str]:
        tiers = Counter(edge.tier.value for edge in graph.edges)
        return [
            f"{len(graph.nodes)} nodes and {len(graph.edges)} relations.",
            f"Relations by tier: green {tiers.get('green', 0)}, yellow {tiers.get('yellow', 0)}, red {tiers.get('red', 0)}.",
            f"Doubt questions: {len(doubts.questions)} asked, {len(doubts.answers)} answered, {len(doubts.pending)} unanswered.",
        ]

    def _result(self, status, page_map, units, relations, graph, gates, started, extractions) -> RunResult:
        tiers = Counter(item.assertion.tier.value for item in relations)
        witnesses = Counter(w.value for item in relations for w in item.assertion.certificate.witnesses)
        verdicts = Counter((item.assertion.certificate.verifier_verdict or "not_called") for item in relations)
        answered_by = Counter(answer.answered_by.kind.value for record in gates.values() for answer in record.answers)
        report = {
            "status": status,
            "pages": self.doc.page_count,
            "page_labels": dict(Counter(entry.label.value for entry in page_map.entries)),
            "diagnostic_pages": page_map.pages_with(PageLabel.DIAGNOSTIC),
            "units": len(units),
            "failed_reads": sum(item.failed_reads for item in extractions),
            "proposals": sum(len(item.proposals) for item in extractions),
            "unclear_passages": sum(len(item.unclear) for item in extractions),
            "extraction_notes": [note for item in extractions for note in item.notes][:200],
            "assertions_by_tier": dict(tiers),
            "witnesses": dict(witnesses),
            "verifier_verdicts": {str(key): value for key, value in verdicts.items()},
            "graph": {
                "nodes": len(graph.nodes),
                "nodes_by_type": dict(Counter(node.type for node in graph.nodes.values())),
                "edges": len(graph.edges),
                "edges_by_tier": dict(Counter(edge.tier.value for edge in graph.edges)),
                "merged_aliases": graph.merged_aliases,
            },
            "gates": {
                name: {"questions": len(record.questions), "answered": len(record.answers),
                       "pending": len(record.pending)}
                for name, record in gates.items()
            },
            "answers_by_reviewer": dict(answered_by),
            "human_questions": len(self.human_store.open_questions())
            if isinstance(self.human_store, InMemoryQuestionStore) else None,
            "reviewer_confirmed": witnesses.get(Witness.REVIEWER.value, 0),
            "usage": self.llm.usage.as_dict(),
            "agent_usage": self.agent_llm.usage.as_dict() if hasattr(self.agent_llm, "usage") else None,
            "seconds": {**self.timings, "total": round(time.perf_counter() - started, 3)},
            "prompt_ids": {"extraction": prompt_hash(Extractor(self.llm, self.spec, asset_name=self.asset_name).system)},
        }
        result = RunResult(status=status, page_map=page_map, units=units, relations=relations, graph=graph,
                           gates=gates, report=report)
        self._save("report", report)
        return result


def red_relations(result: RunResult) -> list[CheckedRelation]:
    return [item for item in result.relations if item.assertion.tier is Tier.RED]
