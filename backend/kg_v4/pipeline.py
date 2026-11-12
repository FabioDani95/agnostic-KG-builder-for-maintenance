"""One autonomous run, from a read PDF to a connected graph, with state saved after every step.

    read -> survey -> extract -> verify -> resolve -> gaps -> enrich -> export

No person is asked anything during a run. A work directory makes the run resumable: finished
steps and passages are loaded, not called again, as long as the PDF, the prompts, the model and
the settings that change facts are the same.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import subprocess
import time
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from backend.kg_v3.contracts import ReadingUnit
from backend.kg_v3.ontology import ONTOLOGY_PATH, load_ontology
from backend.kg_v3.reader import DocumentText
from backend.kg_v3.run_state import atomic_json, digest, file_hash
from backend.kg_v4 import PIPELINE_VERSION
from backend.kg_v4.enrich import Enricher
from backend.kg_v4.export import graph_counts, graph_json
from backend.kg_v4.extract import Extractor
from backend.kg_v4.gaps import GapRepair, find_gaps, follow_entry_pointers, link_named_parts, resolve_references
from backend.kg_v4.metrics import scorecard
from backend.kg_v4.model import DocumentSurvey, Fact, Graph, Mention, Reference, UnitRecords
from backend.kg_v4.prompts import (
    ENRICH_PROMPT,
    EXTRACT_PROMPT,
    GAP_PROMPT,
    RESOLVE_PROMPT,
    SURVEY_PROMPT,
    VERIFY_PROMPT,
)
from backend.kg_v4.resolve import Resolution, assemble, catalogue_mentions, judge, summary
from backend.kg_v4.sections import SectionIndex, build_sections
from backend.kg_v4.survey import reading_units, survey_document
from backend.kg_v4.verify import Verifier

logger = logging.getLogger(__name__)

EventSink = Callable[[str, dict[str, Any]], None]
ROOT = Path(__file__).resolve().parents[2]


class BuildConfig(BaseModel):
    model: str = "gpt-6-luna"
    reasoning_effort: str = "low"
    unit_max_chars: int = 9000
    concurrency: int = 6
    # Stop with a clear error instead of spending on an unexpectedly large reading.
    max_units: int = 150
    page_images: bool = True
    reread_rows: bool = True
    verify: bool = True
    resolve_with_model: bool = True
    link_named_parts: bool = True
    gap_rounds: int = 2
    gap_max_calls: int = 24
    enrich: bool = True
    enrich_max_calls: int = 40
    # Pages read whatever the survey says (for example chosen by a person).
    extra_pages: list[int] = Field(default_factory=list)


class BuildResult(BaseModel):
    status: str
    graph: Graph
    document: dict[str, Any]
    report: dict[str, Any]
    survey: DocumentSurvey


def prompt_ids() -> dict[str, str]:
    prompts = {"survey": SURVEY_PROMPT, "extract": EXTRACT_PROMPT, "verify": VERIFY_PROMPT,
               "resolve": RESOLVE_PROMPT, "gap": GAP_PROMPT, "enrich": ENRICH_PROMPT}
    return {name: hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] for name, text in prompts.items()}


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              timeout=5, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def input_manifest(doc: DocumentText, config: BuildConfig, asset: dict[str, Any], pdf_path: Path | None) -> dict[str, Any]:
    """What the facts of a run depend on; worker counts and budgets of later steps are left out."""

    settings = config.model_dump(mode="json")
    for key in ("concurrency", "max_units", "gap_max_calls", "enrich_max_calls"):
        settings.pop(key, None)
    segments = digest([[segment.segment_id, segment.text] for segment in doc.segments()])
    return {"pipeline": PIPELINE_VERSION, "pdf_sha256": file_hash(pdf_path) if pdf_path else segments,
            "segments_sha256": segments, "pages": doc.page_count, "asset": asset.get("name", ""),
            "prompts": prompt_ids(), "ontology_sha256": file_hash(ONTOLOGY_PATH), "config": settings}


class _State:
    """Results of finished steps in ``<workdir>/state``, bound to the inputs that produced them."""

    def __init__(self, workdir: Path | None, manifest: dict[str, Any]) -> None:
        self.dir = workdir / "state" if workdir else None
        if self.dir is None:
            return
        path = self.dir / "manifest.json"
        if path.exists():
            saved = json.loads(path.read_text(encoding="utf-8"))
            if saved != json.loads(json.dumps(manifest)):
                changed = sorted(key for key in {*saved, *manifest} if saved.get(key) != manifest.get(key))
                raise ValueError(f"this run directory was made with different inputs ({', '.join(changed)}); "
                                 "use a new directory")
        else:
            atomic_json(path, manifest)

    def load(self, name: str) -> Any | None:
        if self.dir is None or not (self.dir / f"{name}.json").exists():
            return None
        return json.loads((self.dir / f"{name}.json").read_text(encoding="utf-8"))

    def save(self, name: str, value: Any) -> None:
        if self.dir is not None:
            atomic_json(self.dir / f"{name}.json", value)


class Builder:
    def __init__(self, *, doc: DocumentText, asset: dict[str, Any], llm, config: BuildConfig | None = None,
                 pdf_path: Path | None = None, workdir: Path | None = None, sections: SectionIndex | None = None,
                 source_title: str = "", on_event: EventSink | None = None) -> None:
        self.doc, self.asset, self.llm = doc, asset, llm
        self.config = config or BuildConfig()
        self.pdf_path, self.workdir, self.on_event = pdf_path, workdir, on_event
        self.sections = sections or (build_sections(pdf_path, doc) if pdf_path else SectionIndex(page_count=doc.page_count))
        self.source_title = source_title or (pdf_path.name if pdf_path else str(asset.get("name", "")))
        self.timings: dict[str, float] = {}
        self.manifest = input_manifest(doc, self.config, asset, pdf_path)
        self.state = _State(workdir, self.manifest)

    # Progress -------------------------------------------------------------

    def _emit(self, kind: str, **data: Any) -> None:
        if self.on_event is None:
            return
        try:
            self.on_event(kind, {**data, "cost_usd": round(self.llm.usage.estimated_cost_usd, 6)})
        except Exception:
            logger.exception("event listener failed on %s", kind)

    async def _timed(self, name: str, coroutine):
        started = time.perf_counter()
        self._emit("step_started", step=name)
        try:
            return await coroutine
        finally:
            elapsed = time.perf_counter() - started
            self.timings[name] = round(self.timings.get(name, 0) + elapsed, 3)
            self._emit("step_finished", step=name, seconds=round(elapsed, 3))

    def _save(self, name: str, value: Any) -> None:
        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")
        self.state.save(name, value)
        self._emit("state_saved", name=name, value=value)

    # Steps ----------------------------------------------------------------

    async def _survey(self) -> DocumentSurvey:
        saved = self.state.load("survey")
        if saved is not None:
            return DocumentSurvey.model_validate(saved)
        survey = await self._timed("survey", survey_document(self.llm, self.doc, asset_name=self.asset["name"]))
        self._save("survey", survey)
        return survey

    async def _extract(self, units: list[ReadingUnit], extractor: Extractor) -> list[UnitRecords]:
        async def one(unit: ReadingUnit) -> UnitRecords:
            saved = self.state.load(f"records_{unit.unit_id}")
            if saved is not None:
                return UnitRecords.model_validate(saved)
            records = await extractor.extract(unit)
            # A failed read is not saved: running again reads the passage again.
            if not records.failed_reads:
                self._save(f"records_{unit.unit_id}", records)
            return records

        return list(await self._timed("extract", asyncio.gather(*(one(unit) for unit in units))))

    async def _verify(self, units: list[ReadingUnit], records: list[UnitRecords], verifier: Verifier,
                      by_key: dict[str, Mention]) -> list[Fact]:
        async def one(unit: ReadingUnit, item: UnitRecords) -> list[Fact]:
            saved = self.state.load(f"verified_{unit.unit_id}")
            if saved is not None:
                return [Fact.model_validate(fact) for fact in saved]
            facts = await verifier.check_unit(unit, item.facts, by_key)
            if not item.failed_reads:
                self._save(f"verified_{unit.unit_id}", [fact.model_dump(mode="json") for fact in facts])
            return facts

        if not self.config.verify:
            return [fact for item in records for fact in item.facts]
        checked = await self._timed("verify", asyncio.gather(*(one(unit, item) for unit, item in zip(units, records))))
        return [fact for facts in checked for fact in facts]

    async def _resolve(self, name: str, mentions: list[Mention], facts: list[Fact],
                       known: Resolution | None) -> tuple[Resolution, list]:
        saved = self.state.load(name)
        if saved is not None:
            resolution = Resolution.model_validate(saved)
            _, apart = await judge(None, mentions, facts, resolution)
            return resolution, apart
        llm = self.llm if self.config.resolve_with_model else None
        resolution, apart = await self._timed("resolve", judge(llm, mentions, facts, known))
        self._save(name, resolution)
        return resolution, apart

    async def run(self) -> BuildResult:
        started = time.perf_counter()
        config = self.config
        survey = await self._survey()
        units = reading_units(self.doc, survey, self.sections, max_chars=config.unit_max_chars,
                              extra_pages=set(config.extra_pages))
        if len(units) > config.max_units:
            raise ValueError(f"{len(units)} reading units exceed max_units={config.max_units}; "
                             "check the survey or raise the limit explicitly")
        self._save("units", [unit.model_dump(mode="json") for unit in units])

        images = None
        if config.page_images and self.pdf_path is not None:
            from backend.kg_v3.vision import PageImages

            images = PageImages(self.pdf_path, self.doc)
        extractor = Extractor(self.llm, self.doc, self.sections, asset_name=self.asset["name"],
                              catalogue=survey.catalogue, images=images, concurrency=config.concurrency,
                              reread_rows=config.reread_rows)
        records = await self._extract(units, extractor)
        mentions = [mention for item in records for mention in item.mentions]
        extra_mentions, extra_facts = catalogue_mentions(survey.catalogue, self.sections)
        mentions.extend(extra_mentions)
        by_key = {mention.key: mention for mention in mentions}
        verifier = Verifier(self.llm, self.doc, images=images, concurrency=config.concurrency)
        facts = await self._verify(units, records, verifier, by_key) + extra_facts
        references = resolve_references([ref for item in records for ref in item.references], self.sections)
        # What the gap search establishes; an entry that gives no remedy is searched for elsewhere first.
        statuses: dict[str, dict[str, str]] = {}
        in_entry = {key: {"remedy_status": "not_in_entry"} for item in records for key in item.no_remedy}

        resolution, apart = await self._resolve("resolution_1", mentions, facts, None)
        graph, of_mention = assemble(mentions, facts, resolution, statuses=statuses)

        # Repairs that need no model: pointers between entries, then parts named by an item's own name.
        pointed = follow_entry_pointers(graph, references, of_mention, by_key)
        if pointed:
            facts.extend(pointed)
            graph, of_mention = assemble(mentions, facts, resolution, statuses=statuses)
        gap_rounds: list[dict[str, Any]] = []
        repair = GapRepair(self.llm, self.doc, self.sections, asset_name=self.asset["name"],
                           verifier=verifier if config.verify else None, references=references,
                           max_calls=config.gap_max_calls, concurrency=config.concurrency)
        for round_number in range(1, config.gap_rounds + 1):
            if not find_gaps(graph):
                break
            saved = self.state.load(f"gaps_{round_number}")
            if saved is None:
                found_mentions, found_facts, stats = await self._timed("gaps", repair.repair(graph, by_key, statuses))
                saved = {"mentions": [item.model_dump(mode="json") for item in found_mentions],
                         "facts": [item.model_dump(mode="json") for item in found_facts],
                         "statuses": statuses, "asked": sorted(repair.asked), "stats": stats}
                self._save(f"gaps_{round_number}", saved)
            else:
                statuses.update(saved["statuses"])
                repair.asked.update(saved["asked"])
                repair.calls += saved["stats"]["calls"]
            mentions.extend(Mention.model_validate(item) for item in saved["mentions"])
            facts.extend(Fact.model_validate(item) for item in saved["facts"])
            by_key = {mention.key: mention for mention in mentions}
            gap_rounds.append(saved["stats"])
            if saved["mentions"]:
                resolution, apart = await self._resolve(f"resolution_{round_number + 1}", mentions, facts, resolution)
            graph, of_mention = assemble(mentions, facts, resolution, statuses=statuses)
            if not saved["stats"]["asked"]:
                break
        named = link_named_parts(graph, mentions) if config.link_named_parts else []
        # A cause the search never reached keeps what its own entry says.
        statuses = {**in_entry, **statuses}
        facts.extend(named)
        graph, of_mention = assemble(mentions, facts, resolution, statuses=statuses)

        enrichment: dict[str, Any] = {}
        if config.enrich:
            saved = self.state.load("enrichment")
            if saved is None:
                enricher = Enricher(self.llm, self.doc, asset_name=self.asset["name"], references=references,
                                    max_calls=config.enrich_max_calls, concurrency=config.concurrency)
                stats = await self._timed("enrich", enricher.enrich(graph))
                saved = {"stats": stats, "nodes": {key: {"description": node.description, "inferred": node.inferred,
                                                         "properties": node.properties}
                                                   for key, node in graph.nodes.items()}}
                self._save("enrichment", saved)
            for key, values in saved["nodes"].items():
                if key in graph.nodes:
                    node = graph.nodes[key]
                    node.description, node.inferred = values["description"], values["inferred"]
                    node.properties = {**node.properties, **values["properties"]}
            enrichment = saved["stats"]

        report = self._report(survey, units, records, facts, references, graph, resolution, apart, gap_rounds,
                              enrichment, verifier, started)
        status = "incomplete" if report["incomplete_reasons"] else "approved"
        report["status"] = status
        document = graph_json(graph, self.doc, asset=self.asset, source_title=self.source_title, status=status,
                              report=report, spec=load_ontology(full=True), survey_asset=survey.asset)
        report["graph"] = graph_counts(document)
        report["scorecard"] = {key: value for key, value in scorecard(document).items() if key != "cost"}
        document["report"] = report
        self._save("report", report)
        return BuildResult(status=status, graph=graph, document=document, report=report, survey=survey)

    # Reporting ------------------------------------------------------------

    def _report(self, survey: DocumentSurvey, units: list[ReadingUnit], records: list[UnitRecords], facts: list[Fact],
                references: list[Reference], graph: Graph, resolution: Resolution, apart: list,
                gap_rounds: list[dict[str, Any]], enrichment: dict[str, Any], verifier: Verifier,
                started: float) -> dict[str, Any]:
        failed = [item.unit_id for item in records if item.failed_reads]
        reasons = []
        if failed:
            reasons.append("failed_extraction_reads")
        if survey.failed_batches:
            reasons.append("failed_survey_batches")
        if not graph.edges:
            reasons.append("empty_diagnostic_graph")
        open_gaps = Counter(gap.kind for gap in find_gaps(graph))
        usage = self.llm.usage.as_dict()
        return {
            "pipeline": PIPELINE_VERSION, "status": "", "approval": "automatic", "quality_measured": False,
            "incomplete_reasons": reasons, "pages": self.doc.page_count,
            "unreadable_pages": self.doc.unreadable_pages,
            "diagnostic_pages": survey.diagnostic_pages(),
            "read_pages": sorted({page for unit in units for page in unit.pages}),
            "page_kinds": dict(Counter(kind for page in survey.pages for kind in page.kinds)),
            "sections": {"headings": len(self.sections.headings), "printed_page_offset": self.sections.page_offset},
            "catalogue": dict(Counter(entry.type for entry in survey.catalogue)),
            "units": len(units), "failed_reads": sum(item.failed_reads for item in records), "failed_units": failed,
            "extraction": {"mentions": sum(len(item.mentions) for item in records),
                           "facts": sum(len(item.facts) for item in records),
                           "reread_units": sum(any("read again" in note for note in item.notes) for item in records),
                           "unclear_passages": sum(len(item.unclear) for item in records),
                           "notes": [note for item in records for note in item.notes][:100]},
            "facts_by_verdict": dict(Counter(fact.verdict for fact in facts)),
            "facts_by_origin": dict(Counter(fact.origin for fact in facts)),
            "failed_verification_batches": verifier.failed_batches,
            "references": {"printed": len(references), "resolved": sum(item.resolved for item in references)},
            "resolution": summary(graph, resolution, apart),
            "false_friends": [pair.model_dump(mode="json") for pair in apart][:60],
            "gap_rounds": gap_rounds, "open_gaps": dict(open_gaps), "enrichment": enrichment,
            "rejected_facts": len(graph.rejected),
            "usage": usage, "usage_total": {key: usage[key] for key in (
                "calls", "failed_calls", "prompt_tokens", "completion_tokens", "estimated_cost_usd")},
            "seconds": {**self.timings, "total": round(time.perf_counter() - started, 3)},
            "prompt_ids": prompt_ids(), "input_manifest_sha256": digest(self.manifest),
            "provenance": {"commit": _commit(), "config": self.config.model_dump(mode="json"),
                           "model": self.config.model, "reasoning_effort": self.config.reasoning_effort},
        }
