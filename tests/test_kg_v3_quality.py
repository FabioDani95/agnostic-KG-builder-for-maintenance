from scripts.kg_v3_quality import graph_metrics, relations


def test_quality_detects_constraints_orphans_and_missing_evidence():
    graph = {'nodes': [
        {'id': 'f', 'type': 'FailureMode', 'name': 'state 1', 'aliases': ['state 2']},
        {'id': 'a', 'type': 'CorrectiveAction', 'name': 'inspect'},
        {'id': 's', 'type': 'Symptom', 'name': 'alert'},
    ], 'edges': [{'type': 'RESOLVED_BY', 'from': 'f', 'to': 'a', 'occurrences': []}]}
    row = graph_metrics(graph)
    assert row['fusion_violations'] == row['orphan_causes'] == row['problems_without_action'] == 1
    assert row['edges_without_evidence'] == 1
    renamed = {**graph, "nodes": [{**node, "name": " STATE 1 "} if node["id"] == "f" else node
                                  for node in graph["nodes"]]}
    assert relations(graph) == relations(renamed)


def test_quality_detects_judge_difference_and_ignores_root_navigation():
    graph = {'nodes': [{'id': 'f', 'type': 'FailureMode', 'name': 'alpha', 'aliases': ['beta']},
                       {'id': 'a', 'type': 'CorrectiveAction', 'name': 'inspect'},
                       {'id': 'r', 'type': 'Asset', 'name': 'machine'}],
             'edges': [{'type': 'RESOLVED_BY', 'from': 'f', 'to': 'a', 'occurrences': [{'evidence': [{'text': 'x'}]}]},
                       {'type': 'GENERATES_ERROR', 'from': 'r', 'to': 'f', 'derived': True}]}
    row = graph_metrics(graph, [{'type': 'FailureMode', 'left_name': 'alpha', 'right_name': 'beta'}])
    assert row['fusion_violations'] == 1
    assert row['orphan_causes'] == 1
    assert row['edges_without_evidence'] == 0
