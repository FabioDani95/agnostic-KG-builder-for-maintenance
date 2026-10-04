"""Review of what a reading missed; every proposal goes back through the checker.

Two reviewers share this module:

- ``review_omissions`` (base profile, off by default): one bounded pass over incomplete units.
- ``review_quality`` (quality profile): requests from the coverage ledger, grouped into one call
  per reading unit; the reviewer sees the rendered passage, the facts already held and the items
  still missing, and answers in the extraction format. ``apply_review_delta`` checks and adds them.
"""

from __future__ import annotations

from backend.kg_v3.checker import (
    CheckedRelation,
    Checker,
    context_key,
    group_candidates,
    normalize_name,
    same_relation,
    statement,
)
from backend.kg_v3.contracts import ReviewerKind, Tier
from backend.kg_v3.coverage import CoverageLedger, queue_requests, update_coverage
from backend.kg_v3.extractor import parse_read, quality_part_ids, translate_cites
from backend.kg_v3.llm import call_metadata
from backend.kg_v3.ontology import extraction_schema
from backend.kg_v3.reader import render_segments
from backend.kg_v3.run_state import digest, stable_id
from backend.kg_v3.source_index import SourceIndex, bind_proposal

# Base profile -------------------------------------------------------------


def incomplete_units(relations) -> set[str]:
    units = set()
    by_unit = {}
    for relation in relations:
        for p in relation.proposals:
            by_unit.setdefault(p.unit_id, []).append(p)
        if relation.assertion.tier is not Tier.GREEN:
            units.add(relation.proposals[0].unit_id)
    for unit, proposals in by_unit.items():
        indicators = {p.target.name for p in proposals if p.relation_type in {"MAY_INDICATE", "INDICATES"}}
        remedies = {p.source.name for p in proposals if p.relation_type == "RESOLVED_BY"}
        if indicators - remedies or any(not c.agreement for c in group_candidates(proposals)):
            units.add(unit)
    return units


async def review_omissions(llm, doc, units, relations, spec, *, limit=3):
    selected = incomplete_units(relations)
    # An entirely failed diagnostic unit is incomplete too.
    represented = {p.unit_id for r in relations for p in r.proposals}
    selected.update(u.unit_id for u in units if u.unit_id not in represented)
    additions, attempted = [], []
    checker = Checker(llm, spec, extractor_id="experimental:omissions")
    for unit in [u for u in units if u.unit_id in selected][: max(0, limit)]:
        attempted.append(unit.unit_id)
        existing = [p for r in relations for p in r.proposals if p.unit_id == unit.unit_id]
        allowed = set(unit.segment_ids + unit.context_segment_ids)
        source = render_segments(doc.segments(sorted(allowed, key=lambda c: doc.position(c) or 0)), doc=doc)
        branch = "\n".join(dict.fromkeys(statement(spec, p) for p in existing))
        data = await llm.json(
            name="kg_v3_omissions",
            max_output_tokens=6000,
            schema=extraction_schema(spec, sorted(allowed)),
            system="""Review this incomplete or disagreeing diagnostic branch against its source.
Return only missing relations, entities and typed conditions explicitly supported by that entry.
Preserve warnings, prerequisites, conditional service and ordering. Never invent a cause or remedy.
The supplied context is read-only. Do not repeat present relations. Use the extraction schema
and cite only supplied segment IDs. If nothing is missing, return empty lists.""",
            user=f"SOURCE:\n{source}\nCURRENT BRANCH:\n{branch}",
        )
        proposed, _, _ = parse_read(data, unit=unit, read="O", spec=spec, allowed=allowed)
        proposed = [p for p in proposed if not any(same_relation(p, other) for other in existing)]
        checked = await checker.check(doc, proposed)
        additions.extend(
            r.model_copy(
                update={
                    "assertion": r.assertion.model_copy(update={"assertion_id": "omission." + r.assertion.assertion_id})
                }
            )
            for r in checked
        )
    return additions, attempted


# Quality profile -------------------------------------------------------------

REVIEW_INSTRUCTIONS = """
REVIEW TASK: this passage was already read. CURRENT FACTS lists what the graph holds for it;
MISSING ITEMS lists passage elements no accepted fact represents yet. Return, with the rules
above, only facts the passage states that CURRENT FACTS lacks: first the missing items, then any
other remedy, check, condition or problem-cause link of this passage that is missing. A fact
listed as rejected stays rejected unless the passage clearly states it. Do not repeat current
facts. If nothing is missing, return empty lists.
"""


def _same_fact(a, b) -> bool:
    return all(
        (x.type, normalize_name(x.name), x.code, x.kind, x.denotation_status)
        == (y.type, normalize_name(y.name), y.code, y.kind, y.denotation_status)
        for x, y in [(a.source, b.source), (a.target, b.target)]
    )


async def apply_review_delta(
    delta,
    *,
    doc,
    index,
    unit,
    checker,
    relations,
    spec,
    method="COMPLETENESS_REVIEW",
    request_id="",
    trigger="",
    origin_metadata=None,
):
    """Check the reviewer's additions like any extraction and add the new ones.

    A fact a person rejected stays rejected on the same evidence; on new evidence it waits for a
    person. An addition equal to an accepted fact is dropped.
    """

    allowed = {
        *unit.owned_evidence_ref_ids,
        *unit.context_evidence_ref_ids,
        *unit.segment_ids,
        *unit.context_segment_ids,
    }
    origin = origin_metadata or {}
    human_rejected = [
        r.proposals[0]
        for r in relations
        if r.assertion.certificate.rejected_by and r.assertion.certificate.rejected_by.kind is ReviewerKind.HUMAN
    ]
    accepted = [r.proposals[0] for r in relations if r.assertion.tier is Tier.GREEN]
    proposals = []
    for read in delta.get("additions", []):
        parsed, _, _ = parse_read(read, unit=unit, read="review", spec=spec, allowed=allowed)
        for p in parsed:
            p = bind_proposal(
                index,
                doc,
                p.model_copy(
                    update={
                        "extraction_method": method,
                        "origin_request_id": request_id,
                        "review_trigger": trigger,
                        "origin_metadata": origin,
                        "origin_call_id": origin.get("call_id", ""),
                    }
                ),
                unit,
            )
            rejected = [
                o
                for o in human_rejected
                if p.branch_id == o.branch_id
                and p.relation_type == o.relation_type
                and context_key(p) == context_key(o)
                and _same_fact(p, o)
            ]
            if any(set(p.all_cites) == set(o.all_cites) for o in rejected):
                index.dispositions.append({"proposal_id": p.proposal_id, "reason": "HUMAN_REJECT_STANDS"})
                continue
            if rejected:
                p = p.model_copy(
                    update={
                        "validation_issues": sorted({*p.validation_issues, "HUMAN_REVIEW_REQUIRED"}),
                        "notes": [
                            *p.notes,
                            "New evidence for a previously human-rejected fact: exact human review required.",
                        ],
                    }
                )
            # No duplicate facts even when the model changes the record number.
            if any(same_relation(p, other) for other in accepted):
                continue
            proposals.append(p)
    checked = await checker.check(doc, proposals)
    known = {r.assertion.assertion_id for r in relations}
    output = [*relations, *(r for r in checked if r.assertion.assertion_id not in known)]
    return output, {
        "accepted": [r.assertion.assertion_id for r in checked if r.assertion.tier is Tier.GREEN],
        "candidates": [r.model_dump(mode="json") for r in checked],
    }


def request_unit(request, ledger, index, unit_of_ref):
    """The reading unit that owns the request's items or branch."""
    items = {i.item_id: i for i in ledger.items}
    refs = [r for item_id in request.target_item_ids if item_id in items for r in items[item_id].evidence_ref_ids]
    branch = index.branches.get(request.branch_id)
    if branch is not None:
        entry = index.entries.get(branch.entry_id)
        refs += [*branch.branch_anchor_refs, *(entry.member_refs if entry else [])]
    return next((unit_of_ref[r] for r in refs if r in unit_of_ref), None)


def choose_units(groups, room, audit_slots):
    """Units to review now: ordinary work by priority, plus reserved slots for the audit sample."""
    ranked = sorted(groups, key=lambda u: (-max(r.priority for r in groups[u]), u))
    audit = [u for u in ranked if all(r.audit for r in groups[u])][: min(room, audit_slots)]
    ordinary = [u for u in ranked if not all(r.audit for r in groups[u])]
    return ordinary[: max(0, room - len(audit))] + audit


def review_text(pipeline, unit, relations, items):
    """The passage as the extractor read it, the facts held for it and the items missing."""
    doc, index = pipeline.doc, pipeline.source_index
    segment_ids = [*unit.context_segment_ids, *unit.segment_ids]
    ordered = sorted(doc.segments(segment_ids), key=lambda item: doc.position(item.segment_id) or 0)
    images, marks = pipeline.page_images.for_segments(segment_ids) if pipeline.page_images is not None else ([], {})
    extra, aliases = quality_part_ids(index, ordered, unit)
    if not unit.segment_ids and unit.owned_region_ids and pipeline.images is not None:
        images = [*images, *pipeline.images.crops(unit.owned_region_ids)]
    tiers = {"green": "accepted", "yellow": "uncertain", "red": "rejected"}
    facts = sorted(
        {
            f"- [{tiers[r.assertion.tier.value]}] {statement(pipeline.spec, r.proposals[0])}"
            for r in relations
            if r.proposals and r.proposals[0].unit_id == unit.unit_id
        }
    )
    missing = []
    for item in items:
        where = sorted({index.evidence[r].segment_id or "image" for r in item.evidence_ref_ids})
        missing.append(f"- {item.kind.lower()}: {item.text} ({', '.join(where)})")
    text = "\n".join(
        [
            render_segments(ordered, context=set(unit.context_segment_ids), doc=doc, marks=marks),
            extra,
            "",
            "CURRENT FACTS:",
            "\n".join(facts) or "(none)",
            "",
            "MISSING ITEMS:",
            "\n".join(missing) or "(none listed: look for anything missing)",
        ]
    )
    return text, images, aliases, [*segment_ids, *aliases]


async def _review_unit(pipeline, unit, requests, items, relations, checker, system, attempt_id):
    """One reviewer call for one unit, saved before parsing; the checked delta is saved too."""
    state, index = pipeline.run_state, pipeline.source_index
    response = state.load("review_response_" + attempt_id)
    text, images, aliases, allowed = review_text(pipeline, unit, relations, items)
    if response is None:
        response = await pipeline.role_clients["review"].json(
            name="kg_quality_review",
            system=system,
            user=text,
            schema=extraction_schema(pipeline.spec, allowed, branches=[]),
            max_output_tokens=16000,
            images=images or None,
        )
        state.save("review_response_" + attempt_id, response, calls=[call_metadata(pipeline.role_clients["review"])])
    call_refs = state.call_refs("review_response_" + attempt_id)
    trigger = max(requests, key=lambda r: r.priority).trigger
    method = (
        "CROSS_REFERENCE_RECOVERY"
        if trigger == "UNRESOLVED_REFERENCE"
        else "GRAPH_REPAIR"
        if trigger in {"ORPHAN_CAUSE", "PROBLEM_WITHOUT_ACTION"}
        else "COMPLETENESS_REVIEW"
    )
    relations, delta = await apply_review_delta(
        {"additions": [translate_cites(response, aliases)]},
        doc=pipeline.doc,
        index=index,
        unit=unit,
        checker=checker,
        relations=relations,
        spec=pipeline.spec,
        request_id=requests[0].request_id,
        trigger=trigger,
        origin_metadata=call_refs[0] if call_refs else {},
        method=method,
    )
    saved = {
        "relations": [r.model_dump(mode="json") for r in relations],
        "delta": delta,
        "index": index.model_dump(mode="json"),
    }
    state.save("review_delta_" + attempt_id, saved)
    return saved


def _use_index(pipeline, checker, index):
    pipeline.source_index = pipeline.doc.source_index = checker.source_index = index
    return index


async def review_quality(pipeline, units, relations, ledger, checker):
    """Bounded, resumable completeness review: one call per reading unit with open requests."""
    cfg, index, state = pipeline.config.quality, pipeline.source_index, pipeline.run_state
    checkpoint = state.load("quality_review_checkpoint")
    if checkpoint:
        relations = [CheckedRelation.model_validate(r) for r in checkpoint["relations"]]
        ledger = CoverageLedger.model_validate(checkpoint["coverage"])
        index = _use_index(pipeline, checker, SourceIndex.model_validate(checkpoint["index"]))
    unit_of_ref = {r: u for u in units for r in [*u.owned_evidence_ref_ids, *u.owned_region_ids]}
    units_by_id = {u.unit_id: u for u in units}
    calls = {a["attempt_id"] for r in ledger.requests for a in r.attempts if a.get("status") == "PROCESSED"}
    system = pipeline.extraction_system + REVIEW_INSTRUCTIONS
    for round_ in range(cfg.max_review_rounds):
        ledger = update_coverage(ledger, index, relations)
        ledger = queue_requests(
            ledger,
            index,
            relations,
            completeness=cfg.completeness_review,
            graph_review=cfg.graph_review,
            reference_retrieval=cfg.reference_retrieval,
            audit_count=cfg.audit_requests_per_document,
        )
        by_id = {r.request_id: r for r in ledger.requests}
        groups: dict[str, list] = {}
        for request in ledger.requests:
            if request.status not in {"PENDING", "UNRESOLVED"}:
                continue
            unit = request_unit(request, ledger, index, unit_of_ref)
            if unit is None:
                by_id[request.request_id] = request.model_copy(
                    update={"status": "DEFERRED", "result_reason": "NO_READING_UNIT"}
                )
            else:
                groups.setdefault(unit.unit_id, []).append(request)
        room = max(0, cfg.max_review_requests_per_document - len(calls))
        selected = choose_units(groups, room, cfg.audit_requests_per_document)
        for unit_id in set(groups) - set(selected):
            for request in groups[unit_id]:
                by_id[request.request_id] = request.model_copy(
                    update={"status": "DEFERRED", "result_reason": "REQUEST_CAP"}
                )
        for unit_id in selected:
            requests = groups[unit_id]
            targets = {t for r in requests for t in r.target_item_ids}
            items = [i for i in ledger.items if i.item_id in targets]
            local = [r for r in relations if r.proposals and r.proposals[0].unit_id == unit_id]
            local_digest = digest(sorted((r.assertion.assertion_id, r.assertion.tier.value) for r in local))
            attempt_id = stable_id(
                "attempt",
                [
                    unit_id,
                    sorted(r.request_id for r in requests),
                    local_digest,
                    pipeline.role_profiles["review"],
                    pipeline.role_profiles["verify"],
                ],
            )
            try:
                saved = state.load("review_delta_" + attempt_id) or await _review_unit(
                    pipeline, units_by_id[unit_id], requests, items, relations, checker, system, attempt_id
                )
                relations = [CheckedRelation.model_validate(r) for r in saved["relations"]]
                index = _use_index(pipeline, checker, SourceIndex.model_validate(saved["index"]))
                if attempt_id not in index.applied_delta_ids:
                    index.applied_delta_ids.append(attempt_id)
                state.revise_index(index, {"attempt_id": attempt_id})
                attempt = {
                    "attempt_id": attempt_id,
                    "status": "PROCESSED",
                    "unit_id": unit_id,
                    "reason": "SUPPORTED_DELTA" if saved["delta"]["accepted"] else "NO_SUPPORTED_DELTA",
                }
                calls.add(attempt_id)
            except Exception as exc:
                attempt = {
                    "attempt_id": attempt_id,
                    "unit_id": unit_id,
                    "reason": type(exc).__name__,
                    "status": "DEFERRED" if "budget" in str(exc).casefold() else "FAILED",
                    "message": str(exc)[:300],
                }
            for request in requests:
                by_id[request.request_id] = request.model_copy(
                    update={
                        "status": attempt["status"],
                        "attempts": [*request.attempts, attempt],
                        "round": round_ + 1,
                        "result_reason": attempt["reason"],
                    }
                )
            ledger = update_coverage(ledger.model_copy(update={"requests": list(by_id.values())}), index, relations)
            state.save(
                "quality_review_checkpoint",
                {
                    "relations": [r.model_dump(mode="json") for r in relations],
                    "coverage": ledger.model_dump(mode="json"),
                    "index": index.model_dump(mode="json"),
                },
            )
        ledger = ledger.model_copy(update={"requests": list(by_id.values())})
        if not selected:
            break
    return relations, update_coverage(ledger, index, relations)
