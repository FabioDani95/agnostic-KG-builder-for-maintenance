"""Replay only graph assembly from frozen checked relations, without any model call.

This measures identity changes only, not extraction quality or new-run recall.
Original checked witnesses and reviewer decisions are retained.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.kg_v3.checker import CheckedRelation  # noqa: E402
from backend.kg_v3.contracts import Answer, Question, Tier  # noqa: E402
from backend.kg_v3.merger import MergePlan, assemble  # noqa: E402
from backend.kg_v3.questions import apply_relation_answers, merge_decisions  # noqa: E402
from scripts.kg_v3_quality import graph_metrics  # noqa: E402


def replay(run: Path) -> dict:
    paths = list((run / 'state').glob('checked_*.json'))
    if len(paths) != 1:
        raise ValueError(f'{run}: expected one frozen checked state, found {len(paths)}')
    checked = [CheckedRelation.model_validate(item) for item in json.loads(paths[0].read_text())]
    plan_path = paths[0].with_name(paths[0].name.replace('checked_', 'merge_plan_'))
    plan = MergePlan.model_validate_json(plan_path.read_text())
    gate = json.loads((run / 'state/gate_doubts.json').read_text())
    questions = [Question.model_validate(q) for q in gate['questions']]
    answers = [Answer.model_validate(a) for a in gate['answers']]
    checked = apply_relation_answers(checked, questions, answers)
    rejected = {a.question_id for a in answers if a.option_id == 'different'}
    different = [*plan.different, *(p for p in plan.unsure if f'merge:{p.left}|{p.right}' in rejected)]
    graph = assemble(checked, [*plan.same, *merge_decisions(questions, answers, plan.unsure)], different)
    edges = [e for e in graph.edges if e.tier is not Tier.RED]
    used = {x for e in edges for x in (e.source, e.target)}
    exported = {'nodes': [{'id': n.node_id, 'name': n.name, 'type': n.type, 'aliases': n.aliases,
                           'stated_in_source': n.stated} for n in graph.nodes.values() if n.node_id in used],
                'edges': [{'type': e.relation_type, 'from': e.source, 'to': e.target,
                           'occurrences': [{'evidence': a.certificate.segment_ids} for a in e.assertions]}
                          for e in edges]}
    old = json.loads((run / 'graph.json').read_text())
    return {'before': graph_metrics(old, [p.model_dump() for p in different]),
            'after': graph_metrics(exported, [p.model_dump() for p in different]),
            'blocked_merges': graph.blocked_merges,
            'nodes_after': exported['nodes']}


if __name__ == '__main__':
    result = {str(run.relative_to(ROOT)): replay(run) for run in sorted((ROOT / 'campaign').glob('*/runs/v3_r*'))}
    out = ROOT / 'campaign/results/merge_replay_F1_F2.json'
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'runs': len(result), 'violations_before': sum(r['before']['fusion_violations'] for r in result.values()),
                      'violations_after': sum(r['after']['fusion_violations'] for r in result.values())}))
