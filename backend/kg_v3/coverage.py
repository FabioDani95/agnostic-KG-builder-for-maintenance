"""Processing and observed fact coverage have separate, explicit denominators."""

from __future__ import annotations

import re
from collections import Counter

from pydantic import Field

from backend.kg_v3.contracts import Tier
from backend.kg_v3.quality_contracts import CoverageItem, ProcessingItem, QualityContract, ReviewRequest
from backend.kg_v3.run_state import digest, stable_id


class CoverageLedger(QualityContract):
    processing: list[ProcessingItem] = Field(default_factory=list)
    items: list[CoverageItem] = Field(default_factory=list)
    requests: list[ReviewRequest] = Field(default_factory=list)
    inventory_exhaustiveness: str = "PARTIAL"

    def counts(self):
        return {
            "processing_denominator": len(self.processing),
            "processing_states": dict(Counter(p.status for p in self.processing)),
            "observed_items_denominator": len(self.items),
            "semantic_states": dict(Counter(i.status for i in self.items)),
            "inventory_exhaustiveness": self.inventory_exhaustiveness,
            "coverage_backlog": sum(i.status != "REPRESENTED" for i in self.items),
            "review_counts": dict(Counter(r.status for r in self.requests)),
        }


def inventory(index, doc, page_map, units, extractions=()) -> CoverageLedger:
    labels = {e.page: e for e in page_map.entries}
    processed_pages = {p for u in units for p in u.pages}
    failed = {e.unit_id for e in extractions if e.failed_reads}
    result = CoverageLedger()
    for page in range(1, doc.page_count + 1):
        label = labels[page]
        state = (
            "FAILED"
            if any(u.unit_id in failed and page in u.pages for u in units)
            else "PROCESSED"
            if page in processed_pages
            else "UNREADABLE"
            if label.label.value == "unreadable"
            else "OUT_OF_SCOPE"
        )
        route = doc.page_geometry.get(page, {})
        if route.get("route_unresolved"):
            state = "DEFERRED"
        result.processing.append(
            ProcessingItem(
                item_id=f"page:{page}",
                kind="PAGE",
                page=page,
                status=state,
                reason=route.get("route_reason", label.label.value),
                evidence_ref_ids=list(label.evidence),
                stage="extraction",
            )
        )
    # Observed items come from the pages the run read; other pages are outside the census.
    entries = [e for e in index.entries.values() if index.evidence[e.member_refs[0]].page in processed_pages]
    for entry in entries:
        for key in entry.member_refs:
            ref = index.evidence[key]
            if not ref.exact_text or (ref.row == 1 and ref.table is not None):
                continue
            segment = doc.segment(ref.segment_id)
            header = (
                segment.table.headers[ref.column].casefold()
                if segment and segment.table and ref.column is not None and ref.column < len(segment.table.headers)
                else ""
            )
            text = ref.exact_text
            if re.search(r"cause|fault", header):
                kind = "CAUSE"
            elif re.search(r"problem|symptom|alarm|code", header):
                kind = "INDICATOR"
            elif re.search(r"normal|expected", header):
                kind = "EXPECTED"
            elif re.search(r"contact|service|dealer", text, re.I):
                kind = "ESCALATION"
            elif re.search(r"\b(inspect|check|test|measure)\b", text, re.I):
                kind = "INSPECTION"
            elif re.search(r"\b(replace|repair|clean|tighten|adjust)\b", text, re.I):
                kind = "REPAIR"
            elif re.search(r"\b(see|refer to)\s+(page|section|figure|table|step)", text, re.I):
                kind = "REFERENCE"
            else:
                continue  # Observed structural inventory, never a complete semantic census.
            branch = index.ref_branch.get(key, "")
            result.items.append(
                CoverageItem(
                    item_id=stable_id("item", [key, kind]),
                    entry_id=entry.entry_id,
                    branch_id=branch,
                    kind=kind,
                    evidence_ref_ids=[key],
                    text=text,
                    inventory_exhaustiveness="STRUCTURAL" if segment and segment.table else "PARTIAL",
                )
            )
    # Typed context is an additional observed obligation even when its containing
    # action was extracted. No context is marked represented by a row cite alone.
    for entry in entries:
        for key in entry.member_refs:
            ref = index.evidence[key]
            text = ref.exact_text
            for kind, pattern in [
                ("CONDITION", r"\bif\s+"),
                ("EXPECTED", r"\b(?:normal|expected)\b"),
                ("WARNING", r"\b(?:warning|do not|never)\b"),
                ("PREREQUISITE", r"\b(?:before|disconnect|isolate)\b"),
                ("ORDER", r"\bthen\b"),
            ]:
                if re.search(pattern, text, re.I):
                    result.items.append(
                        CoverageItem(
                            item_id=stable_id("item", [key, kind]),
                            entry_id=entry.entry_id,
                            branch_id=index.ref_branch.get(key, ""),
                            kind=kind,
                            evidence_ref_ids=[key],
                            text=text,
                            inventory_exhaustiveness="PARTIAL",
                        )
                    )
    for branch in index.branches.values():
        for step in branch.path_steps:
            result.items.append(
                CoverageItem(
                    item_id=stable_id("item", [branch.branch_id, step.outcome_ref, "OUTCOME"]),
                    entry_id=branch.entry_id,
                    branch_id=branch.branch_id,
                    kind="OUTCOME",
                    evidence_ref_ids=[step.outcome_ref],
                    text=step.outcome_value,
                    inventory_exhaustiveness="PARTIAL",
                )
            )
    return result


def update_coverage(ledger, index, relations):
    updated = []
    for item in ledger.items:
        matches, rejected = [], []
        for relation in relations:
            a = relation.assertion
            # The item's own evidence ties it to a relation; a prose or diagram relation lives
            # in its unit scope, not in the block's branch.
            bindings = [
                b for b in a.certificate.verified_bindings if set(b.evidence_ref_ids) & set(item.evidence_ref_ids)
            ]
            if not bindings:
                continue
            lead = relation.proposals[0]
            valid_role = (
                "subject"
                if item.kind in {"INDICATOR", "CAUSE"} and lead.source.type in {"Symptom", "ErrorCode", "FailureMode"}
                else "object"
            )
            expected_type = {
                "INDICATOR": {"Symptom", "ErrorCode"},
                "CAUSE": {"FailureMode"},
                "INSPECTION": {"CorrectiveAction"},
                "REPAIR": {"CorrectiveAction"},
                "ESCALATION": {"CorrectiveAction"},
            }.get(item.kind)
            ends = [(lead.source, "subject"), (lead.target, "object")]
            # The item's text must itself match the represented denotation, not
            # merely share the row locator. Numbering is safely stripped for this check.
            text = re.sub(r"^\s*(?:\d+[.)]\s*|(?:and|then)\s+|;\s*)", "", item.text, flags=re.I).strip().casefold()
            # Meaning, not characters: a paraphrased name sharing most words represents the item.
            valid_role = any(
                role == b.role
                and (expected_type is None or end.type in expected_type)
                and (item.kind not in {"INSPECTION", "REPAIR", "ESCALATION"} or end.kind == item.kind.lower())
                and names_match(text, end.name)
                and end.denotation_status not in {"PLACEHOLDER", "UNRESOLVED"}
                for end, role in ends
                for b in bindings
            )
            if item.kind in {"CONDITION", "EXPECTED", "WARNING", "PREREQUISITE", "ORDER", "OUTCOME"}:
                context_kind = {
                    "CONDITION": "if",
                    "EXPECTED": "expected",
                    "WARNING": "warning",
                    "PREREQUISITE": "prerequisite",
                    "ORDER": "order",
                    "OUTCOME": "if",
                }[item.kind]
                valid_role = any(
                    c.kind == context_kind and names_match(text, c.text)
                    for c in a.context_bindings
                    if set(c.evidence_ref_ids) & set(item.evidence_ref_ids)
                )
            if valid_role and a.tier is Tier.GREEN and all(b.support_status == "SUPPORTED" for b in bindings):
                matches.append(a.assertion_id)
            elif valid_role and a.tier is Tier.RED:
                rejected.append(a.assertion_id)
        updated.append(
            item.model_copy(
                update={
                    "status": "REPRESENTED" if matches else "REJECTED_PROPOSAL" if rejected else "MISSING",
                    "assertion_ids": sorted(matches or rejected),
                }
            )
        )
    return ledger.model_copy(update={"items": updated})


_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "of", "to", "and", "or", "if", "is", "are", "for", "on", "in", "with", "be"}


def names_match(text: str, name: str) -> bool:
    words = [w for w in _WORD.findall(name.casefold()) if w not in _STOP]
    found = set(_WORD.findall(text.casefold()))
    return bool(words) and sum(w in found for w in words) >= max(1, round(0.7 * len(words)))


# Recall work first: a missed action or condition is what the reviewer can recover. Source
# conflicts go to a person and contaminated statements are rejected; neither is model work.
TRIGGER_PRIORITY = {
    "FAILED_READ": 100,
    "MISSING_ACTION": 90,
    "PROBLEM_WITHOUT_ACTION": 85,
    "UNRESOLVED_REFERENCE": 80,
    "ORPHAN_CAUSE": 75,
    "UNREADABLE_RELEVANT_PAGE": 70,
    "MISSING_CONDITION": 60,
    "COMPOUND_ACTION": 60,
    "MISSING_OUTCOME": 60,
    "MISSING_OR_APPROXIMATE_EVIDENCE": 40,
    "ALIAS_CANDIDATE": 30,
    "AUDIT": 10,
}


def request(index, trigger, branch_id="", *, items=(), assertions=(), query="", audit=False):
    branch = index.branches.get(branch_id)
    entry = index.entries.get(branch.entry_id) if branch else None
    source = (
        digest([index.evidence[r].model_dump(mode="json") for r in entry.member_refs])
        if entry
        else index.identity.inventory_fingerprint
    )
    local = digest({"branch": branch.model_dump(mode="json") if branch else None, "assertions": sorted(assertions)})
    value = [trigger, branch_id, sorted(items), [] if items or audit else sorted(assertions), source]
    return ReviewRequest(
        request_id=stable_id("request", value),
        trigger=trigger,
        branch_id=branch_id,
        entry_id=branch.entry_id if branch else "",
        source_fingerprint=source,
        local_scope_fingerprint=local,
        priority=TRIGGER_PRIORITY.get(trigger, 50),
        target_item_ids=sorted(items),
        target_assertion_ids=sorted(assertions),
        retrieval_query=query,
        audit=audit,
    )


def queue_requests(
    ledger, index, relations, *, completeness=True, graph_review=True, reference_retrieval=True, audit_count=2
):
    found = {r.request_id: r for r in ledger.requests}

    def remember(r):
        previous = found.get(r.request_id)
        if previous and previous.attempts and previous.local_scope_fingerprint != r.local_scope_fingerprint:
            found[r.request_id] = r.model_copy(update={"attempts": previous.attempts, "status": "UNRESOLVED"})
        elif previous is None:
            found[r.request_id] = r

    for item in ledger.items:
        if not completeness and not (reference_retrieval and item.kind == "REFERENCE"):
            continue
        if item.status == "REPRESENTED":
            continue
        trigger = (
            "UNRESOLVED_REFERENCE"
            if item.kind == "REFERENCE"
            else "MISSING_ACTION"
            if item.kind in {"REPAIR", "INSPECTION", "ESCALATION"}
            else "MISSING_CONDITION"
        )
        r = request(
            index,
            trigger,
            item.branch_id,
            items=[item.item_id],
            query=item.text,
            assertions=[a.assertion.assertion_id for a in relations if a.assertion.branch_id == item.branch_id],
        )
        remember(r)
    for processing in ledger.processing:
        if processing.status not in {"FAILED", "DEFERRED", "UNREADABLE"}:
            continue
        # Unreadable relevant routes are requests; ordinary non-diagnostic blank
        # pages stay in the processing denominator without semantic claims.
        if processing.status == "UNREADABLE" and not processing.evidence_ref_ids:
            continue
        trigger = "FAILED_READ" if processing.status == "FAILED" else "UNREADABLE_RELEVANT_PAGE"
        # One request per page: the reviewer reads the page's unit, not each block alone.
        branch = next(
            (
                b
                for b, scope in sorted(index.branches.items())
                if any(index.evidence[r].page == processing.page for r in scope.branch_anchor_refs)
            ),
            "",
        )
        remember(request(index, trigger, branch, query=f"physical page {processing.page}"))
    if graph_review:
        by_branch = {}
        for r in relations:
            if r.assertion.tier is Tier.GREEN:
                by_branch.setdefault(r.assertion.branch_id, []).append(r)
        for branch in index.branches:
            rs = by_branch.get(branch, [])
            indicators = {
                r.proposals[0].target.mention_id
                for r in rs
                if r.assertion.relation_type in {"INDICATES", "MAY_INDICATE"}
            }
            causes = {r.proposals[0].source.mention_id for r in rs if r.assertion.relation_type == "RESOLVED_BY"}
            for trigger in (["ORPHAN_CAUSE"] if causes - indicators else []) + (
                ["PROBLEM_WITHOUT_ACTION"] if indicators - causes else []
            ):
                r = request(index, trigger, branch, assertions=[r.assertion.assertion_id for r in rs])
                remember(r)
    # A deterministic hash sample includes apparently complete branches; its slots
    # are reserved independently of priority work.
    for branch in sorted(index.branches, key=lambda b: digest(b))[:audit_count]:
        r = request(
            index,
            "AUDIT",
            branch,
            audit=True,
            assertions=[a.assertion.assertion_id for a in relations if a.assertion.branch_id == branch],
        )
        remember(r)
    return ledger.model_copy(
        update={"requests": sorted(found.values(), key=lambda r: (-r.priority, -r.severity, r.branch_id, r.request_id))}
    )
