"""Structural reachability and conservative source-entry reconnection."""
from collections import defaultdict

from backend.kg_v3.checker import normalize_name
from backend.kg_v3.contracts import Tier
from backend.kg_v3.extractor import Proposal


def graph_navigation(graph):
    edges = [e for e in graph.edges if e.tier is not Tier.RED]
    used = {x for e in edges for x in (e.source, e.target)}
    return navigation([{'id': n.node_id, 'type': n.type} for n in graph.nodes.values() if n.node_id in used],
                      [{'type': e.relation_type, 'from': e.source, 'to': e.target} for e in edges])


def reconnect_proposals(doc, graph, relations):
    """Propose a link only to one already known problem in the same source entry.

    This does not infer a problem from arbitrary prose. If the introducing block
    was not extracted as a problem, the orphan remains explicitly reported.
    New links still pass through the checker and the review gate.
    """
    orphan_ids = set(graph_navigation(graph)['orphan_cause_ids'])
    orphan_names = {normalize_name(name) for n in graph.nodes.values() if n.node_id in orphan_ids
                    for name in [n.name, *n.aliases]}

    def scopes(cites):
        found = set()
        for cite in cites:
            found.add(('segment', cite))
            if cite in doc.step:
                found.add(('sequence', doc.step[cite][0]))
            for sequence, head in doc.sequence_head.items():
                if head == cite:
                    found.add(('sequence', sequence))
        return found

    problems = {}
    for relation in relations:
        if relation.assertion.tier is Tier.RED:
            continue
        for p in relation.proposals:
            for end in (p.source, p.target):
                if end.type in {'Symptom', 'ErrorCode'}:
                    key = (end.type, normalize_name(end.code or end.name))
                    problems.setdefault(key, []).append(end)
    added, seen = [], set()
    for relation in relations:
        if relation.assertion.tier is Tier.RED:
            continue
        for p in relation.proposals:
            if p.relation_type != 'RESOLVED_BY' or normalize_name(p.source.name) not in orphan_names:
                continue
            origin = scopes(p.source.cites or p.cites)
            matches = [(key, end) for key, ends in problems.items() for end in ends if scopes(end.cites) & origin]
            if len({key for key, _ in matches}) != 1:
                continue
            key, problem = matches[0]
            signature = (key, normalize_name(p.source.name))
            if signature in seen:
                continue
            seen.add(signature)
            added.append(Proposal(unit_id=p.unit_id, read='N', record=p.record,
                                  relation_type='INDICATES' if problem.type == 'ErrorCode' else 'MAY_INDICATE',
                                  source=problem, target=p.source,
                                  cites=sorted({*problem.cites, *(p.source.cites or p.cites)}),
                                  notes=['navigation: unique known problem in the same source entry']))
    return added

def navigation(nodes: list[dict], edges: list[dict]) -> dict:
    """Reachability in the exported diagnostic graph; root links do not count."""
    by_id = {n['id']: n for n in nodes}
    outgoing = defaultdict(set)
    incoming = defaultdict(set)
    for e in edges:
        if e.get('derived') or e.get('tier') == 'red':
            continue
        outgoing[e['from']].add(e['to'])
        if e['type'] in {'MAY_INDICATE', 'INDICATES'}:
            incoming[e['to']].add(e['from'])

    def reaches_action(start):
        todo, seen = [start], set()
        while todo:
            current = todo.pop()
            if current in seen:
                continue
            seen.add(current)
            if by_id.get(current, {}).get('type') == 'CorrectiveAction':
                return True
            todo.extend(outgoing[current] - seen)
        return False

    orphan = [n['id'] for n in nodes if n['type'] == 'FailureMode'
              and reaches_action(n['id']) and not incoming[n['id']]]
    no_action = [n['id'] for n in nodes if n['type'] in {'Symptom', 'ErrorCode'}
                 and not reaches_action(n['id'])]
    return {'orphan_causes': len(orphan), 'problems_without_action': len(no_action),
            'orphan_cause_ids': sorted(orphan), 'problem_without_action_ids': sorted(no_action)}
