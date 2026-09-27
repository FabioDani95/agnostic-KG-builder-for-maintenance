"""Offline before/after summary, including action-bearing versus cause-only gold branches."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def branch_strata(claims: list[dict], missing: list[str]) -> dict:
    branches = defaultdict(list)
    for claim in claims:
        if claim.get('failure') or claim.get('action'):
            branches[claim['branch_id']].append(claim)
    result = {'with_actions': [0, 0], 'cause_only': [0, 0]}
    absent = set(missing)
    for members in branches.values():
        kind = 'with_actions' if any(c.get('action') for c in members) else 'cause_only'
        result[kind][1] += 1
        result[kind][0] += all(c['claim_id'] not in absent for c in members)
    return result


def summarize(root: Path, before: dict, after: dict, quality_before: dict, quality_after: dict) -> dict:
    rows = {}
    strata = {version: {kind: [0, 0] for kind in ('with_actions', 'cause_only')} for version in ('before', 'after')}
    macro = defaultdict(list)
    for manual in sorted(after['manuals']):
        claims = json.loads((root / manual / 'gold/gold.json').read_text())['claims']
        row = {}
        for version, kpi, quality, runs_dir in (('before', before, quality_before, 'runs_C'),
                                               ('after', after, quality_after, 'runs')):
            systems = {name: data for name, data in kpi['manuals'][manual]['systems'].items() if name.startswith('v3_')}
            q = quality['manuals'][manual]
            branches = [data['branch_recall'] for data in systems.values()]
            assertions = [data['claim_recall'] for data in systems.values()]
            row[version] = {
                'branches': branches, 'claims': assertions,
                'fusion_violations': sum(data['fusion_violations'] for data in q['runs'].values()),
                'orphan_causes': sum(data['orphan_causes'] for data in q['runs'].values()),
                'problems_without_action': sum(data['problems_without_action'] for data in q['runs'].values()),
                'jaccard': q['mean_jaccard'],
                'human_questions': [data['person_questions'] for data in systems.values()],
                'unresolved_questions': [data.get('unresolved_questions', data['person_questions']) for data in systems.values()],
                'build_cost_usd': round(sum(data['cost_usd'] for data in systems.values()), 6),
                'mean_pipeline_seconds': round(mean(data['seconds'] for data in systems.values()), 1),
                'contrastive_pairs_kept': [data['contrastive_pairs_kept'] for data in systems.values()],
            }
            complete_times = [json.loads((root / manual / runs_dir / name / 'report.json').read_text())['seconds'].get('end_to_end')
                              for name in systems]
            row[version]['mean_pdf_plus_pipeline_seconds'] = round(mean(complete_times), 1) if all(complete_times) else None
            macro[version].append(sum(b[0] for b in branches) / sum(b[1] for b in branches))
            for data in systems.values():
                parts = branch_strata(claims, data['missing_claims'])
                assert [sum(p[i] for p in parts.values()) for i in (0, 1)] == data['branch_recall']
                for kind, pair in parts.items():
                    for i in (0, 1):
                        strata[version][kind][i] += pair[i]
        rows[manual] = row
    return {'manuals': rows, 'branch_strata': strata,
            'macro_branch_recall': {version: round(mean(values), 4) for version, values in macro.items()},
            'note': 'Counts sum three repetitions; Jaccard averages the three pairs. Strata reuse existing semantic judgements; no new model calls.'}


def fraction_total(pairs):
    return f'{sum(p[0] for p in pairs)}/{sum(p[1] for p in pairs)}'


def markdown(data: dict) -> str:
    lines = ['# Confronto prima/dopo della robustezza', '',
             'Conteggi cumulati su tre esecuzioni, confrontate con lo stesso giudice aggiornato. C → D.', '',
             '| Manuale | Rami | Asserzioni | Fusioni vietate | Cause orfane | Problemi senza azioni | Jaccard | Domande a persona (r1/r2/r3) |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for manual, row in data['manuals'].items():
        a, b = row['before'], row['after']
        values = [f'{fraction_total(a[k])} → {fraction_total(b[k])}' for k in ('branches', 'claims')]
        values += [f'{a[k]} → {b[k]}' for k in ('fusion_violations', 'orphan_causes', 'problems_without_action', 'jaccard')]
        values += [f"{'/'.join(map(str, a['human_questions']))} → {'/'.join(map(str, b['human_questions']))}"]
        lines.append('| ' + manual + ' | ' + ' | '.join(values) + ' |')
    lines += ['', '| Manuale | USD costruzione, 3 run C → D | Secondi pipeline, media C → D | Secondi PDF + pipeline, media D |',
              '| --- | --- | --- | --- |']
    for manual, row in data['manuals'].items():
        a, b = row['before'], row['after']
        lines.append(f"| {manual} | {a['build_cost_usd']:.4f} → {b['build_cost_usd']:.4f} | "
                     f"{a['mean_pipeline_seconds']} → {b['mean_pipeline_seconds']} | {b['mean_pdf_plus_pipeline_seconds']} |")
    lines += ['', 'Il costo di costruzione esclude la valutazione dei KPI e il lavoro umano. Il tempo PDF non era registrato in C.', '',
              f"Recall macro (media dei sei manuali): {data['macro_branch_recall']}.", '',
              f"Rami separati per presenza di azioni: {data['branch_strata']}.", '',
              'Le coppie contrastive sono provvisorie fino alla revisione di Fabio. Nessuno di questi numeri stima la precisione semantica del grafo.']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('campaign'))
    args = parser.parse_args()
    out = args.root / 'results'
    load = lambda name: json.loads((out / name).read_text())  # noqa: E731
    data = summarize(args.root, load('kpi_C_context.json'), load('kpi.json'), load('quality_C.json'), load('quality.json'))
    (out / 'robustness_comparison.json').write_text(json.dumps(data, indent=2) + '\n')
    (out / 'robustness_comparison.md').write_text(markdown(data))
    print(markdown(data))


if __name__ == '__main__':
    main()
