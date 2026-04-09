import unittest

from backend.services.ontology_semantics import (
    corrective_actions_match,
    infer_asset_type,
    normalize_asset_node,
)


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
