"""Traceability entry point for the explicit n:1 JoinSpec contract."""

from tests.planned import test_g2_acceptance as scenarios


def test_ac_join_001(foundation_client, machine_payload):
    scenarios.test_g2_join_is_explicit_and_adds_lookup_lineage(
        foundation_client, machine_payload
    )
