from scripts.kg_v3_robustness_report import branch_strata


def test_branch_strata_require_every_action_and_exclude_indication_only():
    claims = [
        {'branch_id': 'a', 'claim_id': 'a1', 'failure': 'fault', 'action': 'repair'},
        {'branch_id': 'a', 'claim_id': 'a2', 'failure': 'fault', 'action': 'inspect'},
        {'branch_id': 'b', 'claim_id': 'b1', 'failure': 'another cause', 'action': ''},
        {'branch_id': 'c', 'claim_id': 'c1', 'failure': '', 'action': ''},
    ]
    assert branch_strata(claims, ['a2']) == {'with_actions': [0, 1], 'cause_only': [1, 1]}
