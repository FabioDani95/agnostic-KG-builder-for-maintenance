import unittest

from backend.services.ontology_semantics import (
    corrective_actions_match,
    infer_asset_type,
    is_operational_state_failure_mode,
    normalize_asset_node,
)


class OperationalStateFailureModeTests(unittest.TestCase):
    def test_flags_reversible_operational_states(self):
        cases = [
            ("Machine in Emergency Stop state", "The machine is in an emergency stop state."),
            ("Door in open state", "The safety door is open."),
            ("Door not cycled since power up", "The door has not been cycled since power up."),
            ("Pallet Pool operation in interrupted state", "Pallet pool operation was interrupted."),
            ("Emergency Stop button activated", "The e-stop button is pressed."),
            ("Fixture clamp incomplete input state", "Fixture clamp input incomplete."),
        ]
        for name, description in cases:
            self.assertTrue(
                is_operational_state_failure_mode(name, description),
                msg=f"expected operational-state flag for {name!r}",
            )

    def test_does_not_flag_degraded_component_conditions(self):
        # A degradation/cause token means it is a real failure that merely names
        # an operational element — must NOT be flagged.
        cases = [
            ("Door interlock key bent", "The door interlock key is bent."),
            ("Door interlock switch faulty", "The door interlock switch is faulty."),
            ("Safety door switch disconnected", "The door switch wiring is disconnected."),
            ("Cover latch broken", "The cover latch is broken."),
            ("Spindle motor seized", "The spindle motor bearing has seized."),
        ]
        for name, description in cases:
            self.assertFalse(
                is_operational_state_failure_mode(name, description),
                msg=f"did not expect operational-state flag for {name!r}",
            )

    def test_does_not_flag_programming_or_generic_failures(self):
        cases = [
            ("DO-END statement uses zero instead of letter O", "Programming syntax error."),
            ("Macro statements improperly structured", "Macro placed incorrectly."),
            ("Clogged inlet filter", "The inlet filter is clogged."),
        ]
        for name, description in cases:
            self.assertFalse(is_operational_state_failure_mode(name, description))


class OntologySemanticsTests(unittest.TestCase):
    def test_infer_asset_type_prefers_specific_scope_from_title(self):
        asset_type = infer_asset_type(
            source_title="UR Series Control box 5.5/5.6",
            source_type="Service Manual",
            current_value="robot system",
        )
        self.assertEqual(asset_type, "control box")

    def test_normalize_asset_node_keeps_source_scope(self):
        node = normalize_asset_node(
            {
                "asset_id": "ASSET-001",
                "name": "UR-Series",
                "description": "",
                "brand": "",
                "model": "",
                "asset_type": "robot system",
            },
            source_title="UR Series Control box 5.5/5.6",
            source_type="Service Manual",
        )
        self.assertEqual(node["name"], "UR Series Control box 5.5/5.6")
        self.assertEqual(node["asset_type"], "control box")

    def test_corrective_actions_match_ignores_low_signal_verification_tail(self):
        self.assertTrue(corrective_actions_match(
            "Reconnect USB cable",
            "Reconnect the USB cable to DSQC 662.",
            "1. Reconnect the USB cable to DSQC 662. 2. Verify that the fault has been fixed.",
            "Reconnect the USB cable",
            "Reconnect the USB cable to DSQC 662.",
            "1. Reconnect the USB cable to DSQC 662.",
        ))


if __name__ == "__main__":
    unittest.main()
