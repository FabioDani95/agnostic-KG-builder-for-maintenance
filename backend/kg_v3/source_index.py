"""System-owned document anchors, atomic evidence, scope and lexical lookup."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from pydantic import Field

from backend.kg_v3.contracts import ContextBinding
from backend.kg_v3.quality_contracts import (
    BranchScope,
    DocumentIdentity,
    EvidenceBinding,
    EvidenceRef,
    Mention,
    QualityContract,
    SourceEntry,
    SourceRegion,
)
from backend.kg_v3.run_state import digest, stable_id


class SourceIndex(QualityContract):
    identity: DocumentIdentity
    evidence: dict[str, EvidenceRef] = Field(default_factory=dict)
    regions: dict[str, SourceRegion] = Field(default_factory=dict)
    entries: dict[str, SourceEntry] = Field(default_factory=dict)
    branches: dict[str, BranchScope] = Field(default_factory=dict)
    mentions: dict[str, Mention] = Field(default_factory=dict)
    segment_refs: dict[str, list[str]] = Field(default_factory=dict)
    atomic_refs: dict[str, list[str]] = Field(default_factory=dict)
    ref_branch: dict[str, str] = Field(default_factory=dict)
    ref_branches: dict[str, list[str]] = Field(default_factory=dict)
    headings: dict[str, list[str]] = Field(default_factory=dict)
    printed_pages: dict[str, list[int]] = Field(default_factory=dict)
    applied_delta_ids: list[str] = Field(default_factory=list)
    dispositions: list[dict[str, Any]] = Field(default_factory=list)

    def put(self, registry: str, key: str, value):
        target = getattr(self, registry)
        if key in target and target[key] != value:
            raise ValueError(f"{registry}: ID collision {key}")
        target[key] = value

    def refs_for(self, cites: list[str], name: str = "") -> list[str]:
        refs = list(
            dict.fromkeys(
                ref for cite in cites for ref in ([cite] if cite in self.evidence else self.atomic_refs.get(cite, []))
            )
        )
        if not name:
            return refs
        needle = " ".join(name.casefold().split())
        exact = [ref for ref in refs if needle and needle in " ".join(self.evidence[ref].exact_text.casefold().split())]
        return exact or refs

    def resolve(self, ref_id: str, doc) -> bool:
        ref = self.evidence.get(ref_id)
        if ref is None or ref.locator_status != "EXACT" or ref.document_id != self.identity.document_id:
            return False
        if ref.kind == "VISUAL_REGION":
            region = self.regions.get(ref.region_id)
            return bool(
                region
                and region.page == ref.page
                and region.bbox == ref.bbox
                and region.render_fingerprint == ref.render_fingerprint
            )
        segment = doc.segment(ref.segment_id)
        return bool(
            segment
            and hashlib.sha256(segment.text.encode()).hexdigest() == ref.text_basis
            and segment.text[ref.char_start : ref.char_end] == ref.exact_text
            and hashlib.sha256(ref.exact_text.encode()).hexdigest() == ref.content_sha256
        )

    def packet_text(self, ref_ids: list[str]) -> str:
        lines = []
        for key in ref_ids:
            ref = self.evidence[key]
            if ref.kind == "VISUAL_REGION":
                region = self.regions[ref.region_id]
                lines.append(f"[{key}] VISUAL page={ref.page} bbox={region.bbox} render={ref.render_fingerprint}")
            else:
                lines.append(f"[{key}] {ref.segment_id} offsets={ref.char_start}:{ref.char_end}: {ref.exact_text}")
        return "\n".join(lines)


def _text_ref(index, segment, start, end, *, kind="TEXT_SPAN", column=None, item=None, inherited=()):
    text = segment.text[start:end]
    content = hashlib.sha256(text.encode()).hexdigest()
    basis = hashlib.sha256(segment.text.encode()).hexdigest()
    locator = {
        "document": index.identity.document_id,
        "format": index.contract_version,
        "kind": kind,
        "page": segment.page,
        "segment": segment.segment_id,
        "offsets": [start, end],
        "content": content,
        "column": column,
        "item": item,
    }
    ref_id = stable_id("evidence", locator)
    ref = EvidenceRef(
        evidence_ref_id=ref_id,
        document_id=index.identity.document_id,
        page=segment.page,
        kind=kind,
        locator_status="EXACT",
        content_sha256=content,
        segment_id=segment.segment_id,
        char_start=start,
        char_end=end,
        exact_text=text,
        text_basis=basis,
        raw_evidence_id=segment.evidence_id,
        bbox=segment.bbox,
        column=column,
        item_index=item,
        table=segment.table.table if segment.table else None,
        row=segment.table.row if segment.table else None,
        inherited_from=list(inherited),
        transcription_method="OCR" if segment.kind.value == "ocr_text" else "",
        transcription_status="UNCERTAIN" if segment.low_quality else "NONE",
    )
    index.put("evidence", ref_id, ref)
    index.segment_refs.setdefault(segment.segment_id, []).append(ref_id)
    return ref_id


def build_source_index(doc, geometry: dict | None, identity: DocumentIdentity) -> SourceIndex:
    index = SourceIndex(identity=identity)
    for segment in doc.segments():
        parent = _text_ref(index, segment, 0, len(segment.text))
        refs = []
        if segment.table:
            offset = 0
            for col, cell in enumerate(segment.text.split(" | ")):
                origin = segment.table.inherited_origins.get(col)
                inherited = index.atomic_refs.get(origin, []) if origin else []
                if cell.strip():
                    # Only printed numbering/bullets creates atomic sub-items.
                    # Wrapped lines are not automatically separate actions.
                    starts = [m.start() for m in re.finditer(r"(?:^|\s)(?:\d+[.)]\s+|[•●▪]\s*)", cell)]
                    # Action clauses also own disjoint exact spans. Their semantic
                    # pairing is still mandatory verifier work, never table proximity.
                    if not starts and re.search(
                        r"solution|remedy|action",
                        segment.table.headers[col] if col < len(segment.table.headers) else "",
                        re.I,
                    ):
                        starts = [
                            m.start()
                            for m in re.finditer(
                                r"\b(?:and|then)\s+(?=(?:inspect|check|replace|repair|clean|adjust|contact)\b)|;\s*(?=(?:inspect|check|replace|repair|clean|adjust|contact)\b)",
                                cell,
                                re.I,
                            )
                        ]
                    cuts = sorted(set([0, *starts, len(cell)])) if starts else [0, len(cell)]
                    for n, (a, b) in enumerate(zip(cuts, cuts[1:]), 1):
                        while a < b and cell[a].isspace():
                            a += 1
                        while b > a and cell[b - 1].isspace():
                            b -= 1
                        if a < b:
                            refs.append(
                                _text_ref(
                                    index,
                                    segment,
                                    offset + a,
                                    offset + b,
                                    kind="TABLE_ITEM" if starts else "TABLE_CELL",
                                    column=col,
                                    item=n if starts else None,
                                    inherited=inherited,
                                )
                            )
                offset += len(cell) + 3
        else:
            refs = [parent]
        index.atomic_refs[segment.segment_id] = refs
        kind = "TABLE_ROW" if segment.table else "NUMBERED_PROCEDURE" if segment.segment_id in doc.step else "PARAGRAPH"
        entry_id = stable_id("entry", [identity.document_id, kind, parent])
        headings = [r for h in doc.step_context(segment.segment_id) for r in index.atomic_refs.get(h, [])]
        verified = bool(segment.table or segment.segment_id in doc.step)
        entry = SourceEntry(
            entry_id=entry_id,
            document_id=identity.document_id,
            kind=kind,
            anchor_refs=[parent],
            member_refs=refs,
            heading_refs=headings,
            scope_status="VERIFIED_STRUCTURE" if verified else "PROVISIONAL",
            scope_evidence_refs=[parent],
        )
        index.put("entries", entry_id, entry)
        # An aligned numbered cause column is a branch anchor, never the model's R1.
        numbered_columns = {}
        for ref in refs:
            item = index.evidence[ref]
            if item.kind == "TABLE_ITEM":
                numbered_columns.setdefault(item.column, []).append(ref)
        cause_col = (
            next((i for i, h in enumerate(segment.table.headers) if re.search(r"cause|fault", h, re.I)), None)
            if segment.table
            else None
        )
        anchors = numbered_columns.get(cause_col, [])
        groups = []
        if anchors:
            counts = {len(v) for v in numbered_columns.values()}
            aligned = len(counts) == 1
            for n, anchor in enumerate(anchors):
                members = [r for col, values in numbered_columns.items() for r in values[n : n + 1]]
                members += [r for r in refs if index.evidence[r].column not in numbered_columns]
                groups.append(([anchor], members, verified and aligned))
        else:
            groups = [([parent], refs, verified)]
        for anchors_, members, certain in groups:
            branch_id = stable_id("branch", [entry_id, sorted(anchors_)])
            branch = BranchScope(
                branch_id=branch_id,
                entry_id=entry_id,
                branch_anchor_refs=anchors_,
                scope_status="VERIFIED_STRUCTURE" if certain else "PROVISIONAL",
                scope_evidence_refs=anchors_,
            )
            index.put("branches", branch_id, branch)
            for ref in members:
                # Shared indicator cells are context to multiple branch anchors.
                index.ref_branches.setdefault(ref, []).append(branch_id)
                if ref not in index.ref_branch:
                    index.ref_branch[ref] = branch_id
        title = doc.section_titles.get(segment.page, "")
        if title:
            index.headings.setdefault(title.casefold(), []).append(parent)
        if re.fullmatch(r"\s*\d+\s*", segment.text):
            index.printed_pages.setdefault(segment.text.strip(), []).append(segment.page)
    doc.source_index = index
    return index


def add_region(index: SourceIndex, region: SourceRegion) -> str:
    if region.document_id != index.identity.document_id:
        raise ValueError("foreign document region")
    index.put("regions", region.region_id, region)
    key = stable_id(
        "evidence",
        [
            index.identity.document_id,
            index.contract_version,
            "VISUAL_REGION",
            region.page,
            [round(v, 2) for v in region.bbox],
            region.render_fingerprint,
        ],
    )
    value = EvidenceRef(
        evidence_ref_id=key,
        document_id=region.document_id,
        page=region.page,
        kind="VISUAL_REGION",
        locator_status="EXACT",
        content_sha256=region.render_fingerprint,
        region_id=region.region_id,
        bbox=region.bbox,
        render_fingerprint=region.render_fingerprint,
    )
    existing = index.evidence.get(key)
    if existing and existing.model_dump(
        exclude={"transcription", "transcription_method", "transcription_status"}
    ) == value.model_dump(exclude={"transcription", "transcription_method", "transcription_status"}):
        return key
    index.put("evidence", key, value)
    return key


def add_visual_entry(
    index: SourceIndex,
    refs: list[str],
    *,
    heading_refs=(),
    path_steps=(),
    verified=False,
    diagram_id="",
    scope_evidence_refs=None,
):
    if not refs or any(r not in index.evidence for r in refs):
        raise ValueError("visual entry needs catalog anchors")
    entry_id = stable_id("entry", [index.identity.document_id, "FLOWCHART", sorted(refs)])
    scope = "VERIFIED_REVIEW" if verified else "PROVISIONAL"
    index.put(
        "entries",
        entry_id,
        SourceEntry(
            entry_id=entry_id,
            document_id=index.identity.document_id,
            kind="FLOWCHART",
            anchor_refs=refs,
            member_refs=refs,
            heading_refs=list(heading_refs),
            scope_status=scope,
            scope_evidence_refs=refs,
        ),
    )
    branch_id = stable_id("branch", [entry_id, sorted(refs), [p.model_dump(mode="json") for p in path_steps]])
    value = BranchScope(
        branch_id=branch_id,
        entry_id=entry_id,
        diagram_id=diagram_id or entry_id,
        branch_anchor_refs=refs,
        scope_status=scope,
        scope_evidence_refs=scope_evidence_refs or refs,
        path_steps=list(path_steps),
    )
    previous = index.branches.get(branch_id)
    if previous and previous.model_dump(exclude={"scope_status"}) == value.model_dump(exclude={"scope_status"}):
        value = previous
    index.put("branches", branch_id, value)
    index.ref_branch.update({r: branch_id for r in refs})
    for r in refs:
        index.ref_branches[r] = sorted(set(index.ref_branches.get(r, []) + [branch_id]))
    return branch_id


# Issues a semantic verification (verifier or reviewer) resolves: they flag work, not errors.
RESOLVABLE_ISSUES = frozenset(
    {
        "UNRESOLVED_SCOPE",
        "CONTEXT_ONLY_TARGET",
        "MISSING_INFERENCE_PREMISES",
        "INCOMPLETE_PATH_EVIDENCE",
        "MISSING_CONDITION_EVIDENCE",
        "INVALID_SCOPE",
        "AMBIGUOUS_ROW_ALIGNMENT",
    }
)
# Issues only a person may clear.
HUMAN_ISSUES = frozenset({"SOURCE_CONFLICT", "HUMAN_REVIEW_REQUIRED"})


def _mentions(text: str, name: str) -> bool:
    needle = " ".join(name.casefold().split())
    return bool(needle) and needle in " ".join(text.casefold().split())


def narrowed_refs(index: SourceIndex, cites: list[str], names: list[str]) -> list[str]:
    """Atomic refs of the cites. A cell listing several numbered items narrows to
    the items that name one of the relation's ends; otherwise every part is kept."""
    out = []
    for cite in cites:
        if cite in index.evidence:
            out.append(cite)
            continue
        parts = index.atomic_refs.get(cite, [])
        if len(parts) > 1:
            hits = [r for r in parts if any(_mentions(index.evidence[r].exact_text, n) for n in names)]
            out.extend(hits or parts)
        else:
            out.extend(parts)
    return list(dict.fromkeys(out))


def scope_branch(index: SourceIndex, doc, unit, anchor_refs) -> str:
    """One provisional scope per reading unit and section for prose, procedures and
    diagrams, where a diagnostic branch spans several text blocks. The verifier or a
    reviewer checks applicability; the scope only keeps causes of different units and
    sections apart."""
    pages = sorted({index.evidence[r].page for r in anchor_refs if r in index.evidence}) or (unit.pages if unit else [])
    title = doc.section_titles.get(pages[0], "") if pages and doc is not None else ""
    members = list(unit.owned_evidence_ref_ids or unit.owned_region_ids) if unit else list(anchor_refs)
    members = [r for r in members if r in index.evidence] or [r for r in anchor_refs if r in index.evidence]
    if not members:
        return ""
    key = [unit.unit_id if unit else "", title]
    entry_id = stable_id("entry", [index.identity.document_id, "UNRESOLVED", key])
    if entry_id not in index.entries:
        index.entries[entry_id] = SourceEntry(
            entry_id=entry_id,
            document_id=index.identity.document_id,
            kind="UNRESOLVED",
            anchor_refs=members[:1],
            member_refs=members,
            scope_status="PROVISIONAL",
            scope_evidence_refs=members[:1],
        )
    branch_id = stable_id("branch", [entry_id, "SCOPE"])
    if branch_id not in index.branches:
        index.branches[branch_id] = BranchScope(
            branch_id=branch_id,
            entry_id=entry_id,
            branch_anchor_refs=members[:1],
            scope_status="PROVISIONAL",
            scope_evidence_refs=members[:1],
        )
    return branch_id


def _fine_branch(index: SourceIndex, refs: list[str]) -> str:
    """A table row, a numbered cause item or a verified diagram path, when unique."""
    branches = {index.ref_branch[r] for r in refs if r in index.ref_branch}
    if len(branches) != 1:
        return ""
    branch = index.branches.get(next(iter(branches)))
    entry = index.entries.get(branch.entry_id) if branch else None
    return branch.branch_id if entry and entry.kind in {"TABLE_ROW", "TEST_TABLE", "FLOWCHART"} else ""


def bind_proposal(index: SourceIndex, doc, proposal, unit=None):
    """Resolve model hints against the allowed catalog. This does not grant support."""
    allowed = set(unit.owned_evidence_ref_ids + unit.context_evidence_ref_ids) if unit else set(index.evidence)
    names = [proposal.source.name, proposal.target.name]
    refs = narrowed_refs(index, proposal.all_cites, names)
    if unit:
        refs = [r for r in refs if r in allowed]
    subject_refs = [
        r for r in index.refs_for(proposal.source.cites or proposal.cites, proposal.source.name) if r in allowed
    ]
    object_refs = [
        r for r in index.refs_for(proposal.target.cites or proposal.cites, proposal.target.name) if r in allowed
    ]
    # The cause anchors the branch, so both relations of one chain share its cause.
    if proposal.source.type == "FailureMode":
        anchor = subject_refs
    elif proposal.target.type == "FailureMode":
        anchor = object_refs
    else:
        anchor = object_refs or refs
    branch_id = proposal.branch_id if proposal.branch_id in index.branches else _fine_branch(index, anchor)
    if not branch_id:
        branch_id = scope_branch(index, doc, unit, anchor or refs)
    branch = index.branches.get(branch_id)
    issues = list(proposal.validation_issues)
    if proposal.branch_id and proposal.branch_id not in index.branches:
        issues.append("INVALID_SCOPE")
    if not branch:
        issues.append("UNRESOLVED_SCOPE")
    if branch:
        owned = set(unit.owned_evidence_ref_ids + unit.owned_region_ids) if unit else set(index.evidence)
        owns_path = bool(branch.path_steps and owned & set(branch.branch_anchor_refs))
        if object_refs and not owned & set(object_refs) and not owns_path:
            issues.append("CONTEXT_ONLY_TARGET")
        # In a verified table a remedy belongs to its own row, and a numbered remedy to the cause
        # with its number. Prose, procedure and diagram combinations are verified, not rejected.
        entry = index.entries.get(branch.entry_id)
        foreign = [
            r
            for r in object_refs
            if r in index.ref_branch
            and index.ref_branch[r] != branch_id
            and branch_id not in index.ref_branches.get(r, [])
            and not index.evidence[r].inherited_from
        ]
        if (
            foreign
            and entry is not None
            and entry.kind == "TABLE_ROW"
            and not any(b.role == "branch_path" for b in proposal.evidence_bindings)
        ):
            other = [index.branches[index.ref_branch[r]] for r in foreign]
            same_row = [b for b in other if b.entry_id == branch.entry_id]
            other_rows = [
                b
                for b in other
                if b.entry_id != branch.entry_id
                and index.entries[b.entry_id].kind == "TABLE_ROW"
                and b.scope_status == "VERIFIED_STRUCTURE"
            ]
            aligned = branch.scope_status == "VERIFIED_STRUCTURE" and all(
                index.evidence[r].kind == "TABLE_ITEM" for r in foreign + subject_refs
            )
            if other_rows and branch.scope_status == "VERIFIED_STRUCTURE" or same_row and aligned:
                issues.append("CROSS_BRANCH_CONTAMINATION")
            elif same_row:
                issues.append("AMBIGUOUS_ROW_ALIGNMENT")
        # A printed contradiction quarantines the statements resting on it, not its page.
        conflict_refs = {
            r
            for d in index.dispositions
            if d.get("reason") == "SOURCE_CONFLICT"
            for r in d.get("evidence_ref_ids", [])
            if index.evidence.get(r) is not None
            and not (
                index.evidence[r].kind == "VISUAL_REGION" and index.regions[index.evidence[r].region_id].kind == "PAGE"
            )
        }
        if conflict_refs & set(refs):
            issues.append("SOURCE_CONFLICT")
    # An end cited only through the relation is bound to the relation's evidence.
    bindings = [
        EvidenceBinding(role=role, evidence_ref_ids=ids)
        for role, ids in [("subject", subject_refs or refs), ("predicate", refs), ("object", object_refs or refs)]
        if ids
    ]
    context_bindings = []
    for c in proposal.conditions:
        ids = [r for r in index.refs_for(list(c.cite)) if r in allowed]
        if ids:
            bindings.append(EvidenceBinding(role="condition", evidence_ref_ids=ids))
            origins = [origin for r in ids for origin in index.evidence[r].inherited_from]
            context_bindings.append(
                ContextBinding(
                    **c.model_dump(),
                    context_id=stable_id("context", [c.model_dump(mode="json"), branch_id, ids]),
                    applies_to_branch_ids=(branch_id,) if branch_id else (),
                    evidence_ref_ids=tuple(ids),
                    origin="inherited" if origins else "direct",
                    origin_ref=origins[0] if origins else "",
                ).model_dump(mode="json")
            )
        else:
            issues.append("MISSING_CONDITION_EVIDENCE")
    if branch and branch.path_steps:
        path_refs = sorted(
            {
                r
                for step in branch.path_steps
                for r in [step.question_ref, step.outcome_ref, step.transition_ref, step.destination_ref]
            }
        )
        if all(r in allowed for r in path_refs):
            bindings.append(EvidenceBinding(role="branch_path", evidence_ref_ids=path_refs))
        else:
            issues.append("INCOMPLETE_PATH_EVIDENCE")
    premises = [r for r in proposal.premise_refs if r in allowed]
    if premises:
        bindings.append(EvidenceBinding(role="premise", evidence_ref_ids=premises))
    for binding in proposal.evidence_bindings:
        if binding.role == "branch_path" and all(r in allowed for r in binding.evidence_ref_ids):
            bindings.append(binding.model_copy(update={"support_status": "UNCHECKED"}))
    if not refs:
        issues.append("MISSING_EVIDENCE")
    if any(not index.resolve(r, doc) for b in bindings for r in b.evidence_ref_ids):
        issues.append("INVALID_EVIDENCE")
    scoped = []
    for role, endpoint, endpoint_refs in [
        ("subject", proposal.source, subject_refs),
        ("object", proposal.target, object_refs),
    ]:
        status = endpoint.denotation_status
        if status == "LEGACY_UNCLASSIFIED":
            status = "PLACEHOLDER" if endpoint.placeholder else "STATED" if endpoint.stated else "INFERRED"
        mention_id = stable_id(
            "mention",
            [
                sorted(endpoint_refs),
                endpoint.type,
                endpoint.kind,
                status,
                endpoint.code,
                endpoint.name if not endpoint_refs or status in {"INFERRED", "UNRESOLVED"} else "",
            ],
        )
        mention = Mention(
            mention_id=mention_id,
            type=endpoint.type,
            original_name=endpoint.name,
            observed_names=[endpoint.name],
            code=endpoint.code,
            action_kind=endpoint.kind,
            denotation_status=status,
            evidence_ref_ids=endpoint_refs,
            entry_id=branch.entry_id if branch else "",
            branch_id=branch_id,
            reading_refs=[proposal.record_key],
        )
        existing = index.mentions.get(mention_id)
        if existing:
            mention = existing.model_copy(
                update={
                    "reading_refs": sorted(set(existing.reading_refs + mention.reading_refs)),
                    "observed_names": sorted(set(existing.observed_names + [endpoint.name])),
                    "original_name": min(existing.original_name, endpoint.name),
                }
            )
        index.mentions[mention_id] = mention
        scoped.append(
            endpoint.model_copy(
                update={
                    "mention_id": mention_id,
                    "branch_id": branch_id,
                    "entry_id": branch.entry_id if branch else "",
                    "document_id": index.identity.document_id,
                    "asset_scope_id": index.identity.asset_scope_id,
                    "denotation_status": status,
                    "evidence_ref_ids": endpoint_refs,
                }
            )
        )
    if any(e.denotation_status == "UNRESOLVED" for e in scoped):
        issues.append("UNRESOLVED_DENOTATION")
    if any(e.type == "FailureMode" and e.denotation_status == "TEST_CONTEXT" for e in scoped):
        issues.append("TEST_CONTEXT_NOT_A_FAULT")
    epistemic = (
        "STRUCTURAL_PLACEHOLDER"
        if any(e.denotation_status == "PLACEHOLDER" for e in scoped)
        else "INFERRED_FROM_TEXT"
        if any(e.denotation_status == "INFERRED" for e in scoped)
        else "UNRESOLVED"
        if any(e.denotation_status == "UNRESOLVED" for e in scoped)
        else "EXPLICIT"
    )
    if epistemic == "INFERRED_FROM_TEXT" and not premises:
        issues.append("MISSING_INFERENCE_PREMISES")
    fact = {
        "relation": proposal.relation_type,
        "branch": branch_id,
        "ends": [
            {"type": e.type, "name": e.name, "code": e.code, "kind": e.kind, "status": e.denotation_status}
            for e in scoped
        ],
        "conditions": sorted([c.model_dump(mode="json") for c in proposal.conditions], key=digest),
        "evidence": sorted(refs),
        "epistemic": epistemic,
    }
    return proposal.model_copy(
        update={
            "source": scoped[0],
            "target": scoped[1],
            "entry_id": branch.entry_id if branch else "",
            "branch_id": branch_id,
            "scope_status": branch.scope_status if branch else "PROVISIONAL",
            "proposal_id": stable_id("proposal", fact),
            "fact_fingerprint": digest(fact),
            "evidence_bindings": bindings,
            "context_bindings": context_bindings,
            "premise_refs": premises,
            "epistemic_status": epistemic,
            "evidence_modalities": sorted(
                {"VISUAL" if index.evidence[r].kind == "VISUAL_REGION" else "TEXT" for r in refs}
            ),
            "validation_issues": sorted(set(issues)),
        }
    )


def inventory_mentions(index, entities, unit, read):
    """Preserve isolated entity observations without promoting them to facts."""
    allowed = set(unit.owned_evidence_ref_ids + unit.context_evidence_ref_ids)
    for entity in entities:
        name, type_ = str(entity.get("name") or ""), str(entity.get("type") or "")
        refs = [r for r in index.refs_for(entity.get("cite") or [], name) if r in allowed]
        if not name or not type_ or not refs:
            continue
        status = entity.get("denotation_status", "STATED" if entity.get("stated", True) else "INFERRED")
        if status not in {"STATED", "INFERRED", "PLACEHOLDER", "TEST_CONTEXT", "UNRESOLVED"}:
            status = "UNRESOLVED"
        branches = {index.ref_branch[r] for r in refs if r in index.ref_branch}
        branch_id = next(iter(branches)) if len(branches) == 1 else ""
        branch = index.branches.get(branch_id)
        key = stable_id(
            "mention",
            [
                sorted(refs),
                type_,
                entity.get("kind", ""),
                status,
                entity.get("code", ""),
                name if status in {"INFERRED", "UNRESOLVED"} else "",
            ],
        )
        value = Mention(
            mention_id=key,
            type=type_,
            original_name=name,
            observed_names=[name],
            code=entity.get("code", ""),
            action_kind=entity.get("kind", ""),
            denotation_status=status,
            evidence_ref_ids=refs,
            entry_id=branch.entry_id if branch else "",
            branch_id=branch_id,
            reading_refs=[unit.unit_id + ":" + read],
        )
        old = index.mentions.get(key)
        index.mentions[key] = (
            old.model_copy(
                update={
                    "reading_refs": sorted(set(old.reading_refs + value.reading_refs)),
                    "observed_names": sorted(set(old.observed_names + [name])),
                    "original_name": min(old.original_name, name),
                }
            )
            if old
            else value
        )
