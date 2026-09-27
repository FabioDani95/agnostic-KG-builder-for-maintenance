"""Resolve structural numeric cross-references within a reading unit, without language rules."""
from __future__ import annotations

import re
from collections import defaultdict

from backend.kg_v3.extractor import Endpoint, Proposal

_ENTRY = re.compile(r"^\s*(\d+)[.)]\s+(.+)", re.S)
_REFS = re.compile(r"\b\d+(?:\s*[*;,|]\s*\d+){2,}\b")


def reference_index(doc, unit):
    definitions = defaultdict(list)
    matrices = []
    for segment in doc.segments([*unit.segment_ids, *unit.context_segment_ids]):
        entry = _ENTRY.match(segment.text)
        if entry:
            definitions[entry[1]].append((segment.segment_id, entry[2].strip()))
        for match in _REFS.finditer(segment.text):
            numbers = re.findall(r"\d+", match[0])
            label = segment.text[:match.start()].strip(" |\n")
            if label:
                matrices.append((segment.segment_id, label, numbers))
    # A matrix must refer to a list actually present, not merely contain numbers.
    matrices = [row for row in matrices if len(set(row[2]) & definitions.keys()) >= 2]
    definitions = {number: entries[0] for number, entries in definitions.items() if len(entries) == 1}
    return definitions, matrices


def resolve_references(doc, unit, proposals: list[Proposal]):
    definitions, matrices = reference_index(doc, unit)
    unresolved = [{"unit_id": unit.unit_id, "segment_id": cite, "reference": number,
                   "reason": "missing or ambiguous numbered entry"}
                  for cite, _, numbers in matrices for number in dict.fromkeys(numbers) if number not in definitions]
    output = []
    for proposal in proposals:
        code = proposal.source
        number = code.code.strip() or code.name.strip()
        rows = [row for row in matrices if number in row[2]]
        origins = {row[0] for row in rows}
        if number in definitions:
            origins.add(definitions[number][0])
        if (code.type != "ErrorCode" or not rows or not (set(code.cites + proposal.cites) & origins)):
            output.append(proposal)
            continue
        if number not in definitions:
            continue  # unresolved references never become invented codes or causes
        cite, text = definitions[number]
        cause = (proposal.target if proposal.target.type == "FailureMode" and cite in proposal.target.cites
                 else Endpoint(type="FailureMode", name=text, cites=[cite]))
        for matrix_cite, label, _ in rows:
            symptoms = {item.source.name: item.source for item in proposals
                        if item.source.type == "Symptom" and matrix_cite in item.source.cites}
            symptom = (next(iter(symptoms.values())) if len(symptoms) == 1 else
                       Endpoint(type="Symptom", name=label, cites=[matrix_cite]))
            output.append(proposal.model_copy(update={
                "relation_type": "MAY_INDICATE", "source": symptom, "target": cause,
                "cites": [matrix_cite, cite], "record": f"reference:{matrix_cite}:{number}",
                "notes": [*proposal.notes, "number resolves to a cited list entry, not an error code"]}))
    return output, unresolved
