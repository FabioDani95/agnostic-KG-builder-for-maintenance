"""Experimental bounded omission review; proposals always return through the checker."""

from __future__ import annotations

from backend.kg_v3.checker import Checker, group_candidates, same_relation, statement
from backend.kg_v3.contracts import Tier
from backend.kg_v3.extractor import parse_read
from backend.kg_v3.ontology import extraction_schema
from backend.kg_v3.reader import render_segments


def incomplete_units(relations) -> set[str]:
    units = set()
    by_unit = {}
    for relation in relations:
        for p in relation.proposals:
            by_unit.setdefault(p.unit_id, []).append(p)
        if relation.assertion.tier is not Tier.GREEN:
            units.add(relation.proposals[0].unit_id)
    for unit, proposals in by_unit.items():
        indicators = {p.target.name for p in proposals if p.relation_type in {'MAY_INDICATE', 'INDICATES'}}
        remedies = {p.source.name for p in proposals if p.relation_type == 'RESOLVED_BY'}
        if indicators - remedies or any(not c.agreement for c in group_candidates(proposals)):
            units.add(unit)
    return units


async def review_omissions(llm, doc, units, relations, spec, *, limit=3):
    selected = incomplete_units(relations)
    # An entirely failed diagnostic unit is incomplete too.
    represented = {p.unit_id for r in relations for p in r.proposals}
    selected.update(u.unit_id for u in units if u.unit_id not in represented)
    additions, attempted = [], []
    checker = Checker(llm, spec, extractor_id='experimental:omissions')
    for unit in [u for u in units if u.unit_id in selected][:max(0, limit)]:
        attempted.append(unit.unit_id)
        existing = [p for r in relations for p in r.proposals if p.unit_id == unit.unit_id]
        allowed = set(unit.segment_ids + unit.context_segment_ids)
        source = render_segments(doc.segments(sorted(allowed, key=lambda c: doc.position(c) or 0)), doc=doc)
        branch = '\n'.join(dict.fromkeys(statement(spec, p) for p in existing))
        data = await llm.json(name='kg_v3_omissions', max_output_tokens=6000,
            schema=extraction_schema(spec, sorted(allowed)),
            system='''Review this incomplete or disagreeing diagnostic branch against its source.
Return only missing relations, entities and typed conditions explicitly supported by that entry.
Preserve warnings, prerequisites, conditional service and ordering. Never invent a cause or remedy.
The supplied context is read-only. Do not repeat present relations. Use the extraction schema
and cite only supplied segment IDs. If nothing is missing, return empty lists.''',
            user=f'SOURCE:\n{source}\nCURRENT BRANCH:\n{branch}')
        proposed, _, _ = parse_read(data, unit=unit, read='O', spec=spec, allowed=allowed)
        proposed = [p for p in proposed if not any(same_relation(p, other) for other in existing)]
        checked = await checker.check(doc, proposed)
        additions.extend(r.model_copy(update={'assertion': r.assertion.model_copy(update={
            'assertion_id': 'omission.' + r.assertion.assertion_id})}) for r in checked)
    return additions, attempted
