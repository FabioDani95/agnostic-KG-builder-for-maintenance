"""Offline graph diagnostics, independent of gold and model calls.

These are structural indicators, not estimates of semantic precision. Jaccard
compares normalised named relations (and is consequently sensitive to paraphrase).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.kg_v3.checker import normalize_name  # noqa: E402
from backend.kg_v3.extractor import UNSPECIFIED_CAUSE  # noqa: E402
from backend.kg_v3.navigation import navigation  # noqa: E402


def graph_metrics(graph: dict, different: list[dict] = ()) -> dict:
    nodes = graph['nodes']
    edges = [e for e in graph['edges'] if not e.get('derived')]
    violations = []
    duplicates = Counter()
    for n in nodes:
        names = {normalize_name(name) for name in [n['name'], *n.get('aliases', [])]}
        duplicates[(n['type'], normalize_name(n['name']))] += 1
        reasons = []
        if len({tuple(sorted(set(re.findall(r'\d+', name)))) for name in names}) > 1:
            reasons.append('different_numbers')
        for pair in different:
            if (n['type'] == pair['type'] and normalize_name(pair['left_name']) in names
                    and normalize_name(pair['right_name']) in names):
                reasons.append({'different': [pair['left_name'], pair['right_name']]})
        if reasons:
            violations.append({'node_id': n['id'], 'name': n['name'], 'reasons': reasons})
    return {
        'nodes': len(nodes), 'diagnostic_edges': len(edges),
        'fusion_violations': len(violations), 'fusion_violation_details': violations,
        **navigation(nodes, edges),
        'duplicate_nodes': sum(count - 1 for count in duplicates.values()),
        'edges_without_evidence': sum(not any(o.get('evidence') for o in e.get('occurrences', [])) for e in edges),
        'derived_causes': sum(n['type'] == 'FailureMode' and not n.get('stated_in_source', True)
                              and not n['name'].startswith(UNSPECIFIED_CAUSE) for n in nodes),
    }


def relations(graph: dict) -> set[tuple]:
    names = {n['id']: (n['type'], normalize_name(n['name']),
                       normalize_name(str(n.get('properties', {}).get('code', '')))) for n in graph['nodes']}
    return {(e['type'], names[e['from']], names[e['to']]) for e in graph['edges'] if not e.get('derived')}


def measure(root: Path, runs_name: str = 'runs') -> dict:
    result = {'definition': 'Offline structural diagnostics; no gold, no semantic precision estimate.',
              'runs_directory': runs_name, 'manuals': {}}
    for directory in sorted(root.glob('*/' + runs_name)):
        runs, signatures = {}, {}
        for run in sorted(directory.glob('v3_r*')):
            path = run / 'graph.json'
            if not path.exists():
                runs[run.name] = {'status': 'missing_graph'}
                continue
            graph = json.loads(path.read_text())
            different = [pair for plan in sorted((run / 'state').glob('merge_plan_*.json'))
                         for pair in json.loads(plan.read_text()).get('different', [])]
            runs[run.name] = {'status': graph.get('status'), 'graph_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                              **graph_metrics(graph, different)}
            signatures[run.name] = relations(graph)
        if not runs:
            continue
        stability = {}
        for a, b in combinations(signatures, 2):
            union = signatures[a] | signatures[b]
            stability[f'{a}/{b}'] = round(len(signatures[a] & signatures[b]) / len(union), 4) if union else 1.0
        result['manuals'][directory.parent.name] = {'runs': runs, 'relation_jaccard': stability,
                                                    'mean_jaccard': round(sum(stability.values()) / len(stability), 4)
                                                    if stability else None}
    return result


def markdown(result: dict) -> str:
    lines = ['# Qualità strutturale (senza gold e senza modello)', '',
             'I problemi senza azioni possono essere fedeli a una fonte che non prescrive rimedi.',
             'Jaccard confronta relazioni con nomi normalizzati: risente anche delle parafrasi.', '',
             '| Manuale | Run | Fusioni vietate | Cause orfane | Problemi senza azione | Doppioni | Senza prove | Dedotte |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for manual, data in result['manuals'].items():
        for run, row in data['runs'].items():
            values = [row.get(k, 'n/d') for k in ('fusion_violations', 'orphan_causes', 'problems_without_action',
                                                'duplicate_nodes', 'edges_without_evidence', 'derived_causes')]
            lines.append(f'| {manual} | {run} | ' + ' | '.join(map(str, values)) + ' |')
    for manual, data in result['manuals'].items():
        lines.append(f"\nJaccard {manual}: {data['relation_jaccard']}; media {data['mean_jaccard']}.\n")
    return '\n'.join(lines) + '\n'


def write_results(root: Path, out: Path, runs_name: str = 'runs') -> dict:
    result = measure(root, runs_name)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    out.with_suffix('.md').write_text(markdown(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT / 'campaign')
    parser.add_argument('--runs-name', default='runs')
    parser.add_argument('--out', type=Path, default=ROOT / 'campaign/results/quality.json')
    args = parser.parse_args()
    print(markdown(write_results(args.root, args.out, args.runs_name)))


if __name__ == '__main__':
    main()
