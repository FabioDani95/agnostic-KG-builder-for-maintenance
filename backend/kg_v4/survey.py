"""Stage 1, survey: the whole manual is read once, before any relation is extracted.

The result is the global picture the old pipeline lacked: which pages hold troubleshooting
knowledge (decided on their full text, not on an outline) and one catalogue of the machine's
components, with their hierarchy, and of its codes. Extraction then names parts from this
catalogue, so the same pump is one node wherever it is mentioned.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections import Counter, defaultdict
from typing import Any

from backend.kg_v3.contracts import DocumentMap, PageLabel, PageMapEntry, ReadingUnit
from backend.kg_v3.mapper import build_units, scan_batches
from backend.kg_v3.reader import DocumentText, render_segments
from backend.kg_v4.model import CatalogueEntry, DocumentSurvey, PageSurvey
from backend.kg_v4.names import canonical, code_key, distinguishing_difference, name_defects
from backend.kg_v4.prompts import SURVEY_PROMPT
from backend.kg_v4.sections import SectionIndex

logger = logging.getLogger(__name__)

PAGE_KINDS = ("troubleshooting", "error_codes", "diagnostic_test", "maintenance", "repair_procedure",
              "parts_list", "specifications", "safety", "operation", "other")
DIAGNOSTIC_KINDS = {"troubleshooting", "error_codes", "diagnostic_test"}
CATEGORIES = ("mechanical", "electrical", "electronic", "hydraulic", "pneumatic", "optical", "software",
              "sensor", "safety", "consumable", "structural", "other")
SURVEY_BATCH_CHARS = 24000
SURVEY_CONCURRENCY = 8
SURVEY_OUTPUT_TOKENS = 12000
# Words that name what a machine handles or the machine itself: never a component on their own.
NOT_A_COMPONENT = {"machine", "unit", "system", "equipment", "device", "product", "appliance", "water", "oil",
                   "air", "gas", "fluid", "material", "dust", "workpiece", "power", "electricity", "part",
                   "component", "tool", "operator", "manual", "coolant", "grease", "lubricant", "steam"}


def _schema(pages: list[int], segment_ids: list[str]) -> dict[str, Any]:
    def obj(properties: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": False, "required": list(properties),
                "properties": properties}

    text = {"type": "string"}
    return obj({
        "pages": {"type": "array", "items": obj({
            "page": {"type": "integer", "enum": pages},
            "kinds": {"type": "array", "items": {"type": "string", "enum": list(PAGE_KINDS)}},
            "evidence": {"type": "array", "items": {"type": "string", "enum": segment_ids}},
        })},
        "components": {"type": "array", "items": obj({
            "name": text, "part_of": text, "category": {"type": "string", "enum": ["", *CATEGORIES]},
            "part_number": text, "description": text, "page": {"type": "integer", "enum": pages},
        })},
        "codes": {"type": "array", "items": obj({"code": text, "meaning": text,
                                                 "page": {"type": "integer", "enum": pages}})},
        "machine": obj({"description": text, "brand": text, "model": text, "type": text}),
    })


def usable_component(name: str) -> bool:
    words = canonical(name).split()
    if not words or len(" ".join(words)) < 3 or "generic" in name_defects(name):
        return False
    return not (len(words) == 1 and words[0] in NOT_A_COMPONENT)


def machine_words(asset: dict[str, Any]) -> set[str]:
    """Words that name the machine itself ("pump" for a booster pump): alone, they are no part of it."""

    return set(canonical(f"{asset.get('name', '')} {asset.get('asset_type', '')}").split())


def is_the_machine(name: str, words: set[str]) -> bool:
    own = canonical(name).split()
    return len(own) == 1 and own[0] in words


def split_listed_parts(name: str) -> list[str]:
    """"Air pump, water chiller or exhaust fan" names three parts; "nuts and bolts" style pairs stay."""

    pieces = [piece.strip() for piece in re.split(r",\s*(?:or\s+|and\s+)?|\s+or\s+", name) if piece.strip()]
    return pieces if len(pieces) >= 2 and all(len(piece.split()) >= 2 for piece in pieces) else [name]


def build_catalogue(raw_components: list[dict[str, Any]], raw_codes: list[dict[str, Any]],
                    machine: set[str] | frozenset[str] = frozenset()) -> list[CatalogueEntry]:
    """One entry per part and per code; names equal in canonical form are one part."""

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in raw_components:
        for name in split_listed_parts(" ".join(str(item.get("name") or "").split())):
            if usable_component(name) and not is_the_machine(name, machine):
                groups[canonical(name)].append({**item, "name": name})
    entries: list[CatalogueEntry] = []
    for key in sorted(groups):
        items = groups[key]
        names = Counter(item["name"] for item in items)
        name = sorted(names, key=lambda value: (-names[value], len(value), value))[0]
        parents = Counter(canonical(str(item.get("part_of") or "")) for item in items
                          if usable_component(str(item.get("part_of") or "")))
        parents.pop(key, None)
        parent_key = parents.most_common(1)[0][0] if parents else ""
        parent = next((str(item["part_of"]).strip() for item in items
                       if canonical(str(item.get("part_of") or "")) == parent_key), "") if parent_key else ""
        categories = Counter(str(item.get("category") or "") for item in items if item.get("category"))
        descriptions = sorted({" ".join(str(item.get("description") or "").split()) for item in items} - {""},
                              key=len, reverse=True)
        entries.append(CatalogueEntry(
            type="Component", name=name, aliases=sorted(set(names) - {name}), part_of=parent,
            category=categories.most_common(1)[0][0] if categories else "",
            part_number=next((str(item["part_number"]).strip() for item in items if item.get("part_number")), ""),
            description=descriptions[0] if descriptions else "",
            pages=sorted({int(item["page"]) for item in items if item.get("page")}),
        ))
    # A parent the survey named only as "part_of" is a part too.
    known = {canonical(entry.name) for entry in entries}
    for entry in list(entries):
        if entry.part_of and canonical(entry.part_of) not in known:
            known.add(canonical(entry.part_of))
            entries.append(CatalogueEntry(type="Component", name=entry.part_of, pages=entry.pages))
    codes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in raw_codes:
        if code_key(str(item.get("code") or "")):
            codes[code_key(str(item["code"]))].append(item)
    for key in sorted(codes):
        items = codes[key]
        meanings = Counter(" ".join(str(item.get("meaning") or "").split()) for item in items)
        meanings.pop("", None)
        # One printed code with two meanings that differ in kind is two codes: keep both visible.
        distinct: list[str] = []
        for meaning, _ in meanings.most_common():
            if not any(not distinguishing_difference(meaning, other) for other in distinct):
                distinct.append(meaning)
        for meaning in distinct or [""]:
            entries.append(CatalogueEntry(
                type="ErrorCode", name=meaning or str(items[0]["code"]).strip(), code=str(items[0]["code"]).strip(),
                pages=sorted({int(item["page"]) for item in items if item.get("page")})))
    return entries


async def survey_document(llm, doc: DocumentText, *, asset_name: str, batch_chars: int = SURVEY_BATCH_CHARS,
                          machine: set[str] | frozenset[str] = frozenset()) -> DocumentSurvey:
    """Read the full text of every page once."""

    limit = asyncio.Semaphore(SURVEY_CONCURRENCY)
    system = SURVEY_PROMPT.format(asset=asset_name)

    async def one(batch: list[int], depth: int = 0) -> dict[str, Any] | None:
        from backend.kg_v3.llm import TruncatedResponse

        segments = [segment for page in batch for segment in doc.pages[page]]
        try:
            async with limit:
                return await llm.json(system=system, user=render_segments(segments),
                                      schema=_schema(batch, [segment.segment_id for segment in segments]),
                                      name="kg_v4_survey", max_output_tokens=SURVEY_OUTPUT_TOKENS)
        except TruncatedResponse:
            if len(batch) < 2 or depth >= 3:
                logger.warning("Survey of pages %s truncated", batch)
                return None
            half = len(batch) // 2
            parts = await asyncio.gather(one(batch[:half], depth + 1), one(batch[half:], depth + 1))
            if any(part is None for part in parts):
                return None
            return {**{key: [item for part in parts for item in part.get(key) or []]
                       for key in ("pages", "components", "codes")}, "machine": parts[0].get("machine") or {}}
        except Exception as exc:
            logger.warning("Survey of pages %s-%s failed: %s", batch[0], batch[-1], exc)
            return None

    batches = scan_batches(doc, batch_chars)
    results = await asyncio.gather(*(one(batch) for batch in batches))
    survey = DocumentSurvey()
    components: list[dict[str, Any]] = []
    codes: list[dict[str, Any]] = []
    seen: dict[int, PageSurvey] = {}
    for batch, data in zip(batches, results):
        if data is None:
            survey.failed_batches.append(batch)
            # A page whose survey failed is read anyway: an extra page costs little, a lost one its facts.
            for page in batch:
                seen[page] = PageSurvey(page=page, kinds=["other"], diagnostic=True)
            continue
        for item in data.get("pages") or []:
            page = int(item.get("page") or 0)
            if page not in batch:
                continue
            evidence = [cite for cite in item.get("evidence") or [] if cite.startswith(f"p{page}.")]
            kinds = [kind for kind in item.get("kinds") or [] if kind in PAGE_KINDS]
            seen[page] = PageSurvey(page=page, kinds=kinds, evidence=evidence,
                                    diagnostic=bool(evidence) or bool(set(kinds) & DIAGNOSTIC_KINDS))
        machine = data.get("machine") if isinstance(data.get("machine"), dict) else {}
        for key in ("description", "brand", "model", "type"):
            value = " ".join(str(machine.get(key) or "").split())
            if value:  # the first pages that say it are the ones that introduce the machine
                survey.asset.setdefault(key, value)
        components.extend(item for item in data.get("components") or [] if isinstance(item, dict))
        codes.extend(item for item in data.get("codes") or [] if isinstance(item, dict))
    for page in sorted(doc.pages):
        survey.pages.append(seen.get(page) or PageSurvey(page=page, kinds=["other"]))
    survey.catalogue = build_catalogue(components, codes, machine)
    return survey


def reading_units(doc: DocumentText, survey: DocumentSurvey, sections: SectionIndex, *,
                  max_chars: int = 9000, extra_pages: set[int] | None = None) -> list[ReadingUnit]:
    """Diagnostic pages cut into passages; packing, title trail and context are the proven V3 ones."""

    chosen = set(survey.diagnostic_pages()) | set(extra_pages or ())
    entries = []
    for page in range(1, doc.page_count + 1):
        if page not in doc.pages:
            entries.append(PageMapEntry(page=page, label=PageLabel.UNREADABLE))
            continue
        # The first two heading levels decide where a unit may be cut; deeper ones change too often.
        section = " > ".join(sections.by_page.get(page, "").split(" > ")[:2])
        entries.append(PageMapEntry(page=page, section=section,
                                    label=PageLabel.DIAGNOSTIC if page in chosen else PageLabel.OTHER))
    if not entries:
        return []
    return build_units(doc, DocumentMap(entries=entries), max_chars=max_chars)


def catalogue_brief(catalogue: list[CatalogueEntry], pages: list[int], *, limit: int = 120) -> str:
    """The parts and codes shown to an extraction call: those of nearby pages first."""

    def distance(entry: CatalogueEntry) -> int:
        return min((abs(page - own) for page in entry.pages for own in pages), default=10_000)

    parts = sorted((entry for entry in catalogue if entry.type == "Component"),
                   key=lambda entry: (distance(entry), -len(entry.pages), entry.name))[:limit]
    codes = sorted((entry for entry in catalogue if entry.type == "ErrorCode" and distance(entry) <= 2),
                   key=lambda entry: entry.code)[:80]
    lines = []
    if parts:
        lines.append("Known components of this machine (use these names for the same part): "
                     + "; ".join(f"{entry.name} (part of {entry.part_of})" if entry.part_of else entry.name
                                 for entry in sorted(parts, key=lambda entry: entry.name)))
    if codes:
        lines.append("Known codes on these pages: " + "; ".join(f"{entry.code} = {entry.name}" for entry in codes))
    return "\n".join(lines)
