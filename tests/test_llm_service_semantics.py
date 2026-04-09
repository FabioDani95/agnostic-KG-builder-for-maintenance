import unittest

from backend.models import (
    CorrectiveAction,
    ExtractionResult,
    FailureMode,
    Severity,
    Symptom,
    Triplet,
)
from backend.services.llm_service import (
    _filter_extraction_result_by_source_support,
    _merge_extraction_results,
)


def _result_from_triplets(*triplets: Triplet) -> ExtractionResult:
    return ExtractionResult(
        triplets=list(triplets),
        raw_symptom_table="",
        raw_failure_mode_table="",
        raw_corrective_action_table="",
    )


class LlmServiceSemanticMergeTests(unittest.TestCase):
    def test_merge_extraction_results_deduplicates_semantic_duplicates(self):
        result_one = _result_from_triplets(Triplet(
            symptom=Symptom(
                symptom_id="SYM-001",
                name="System does not start",
                description="The control box has no power and the system does not start.",
                severity=Severity.HIGH,
            ),
            failure_modes=[
                FailureMode(
                    failure_mode_id="FM-001",
                    name="Loose power connector",
                    description="The power connector is loose.",
                    material_context="Control box",
                    linked_symptom_id="SYM-001",
                ),
            ],
            corrective_actions=[
                CorrectiveAction(
                    action_id="CA-001",
                    name="Reconnect power connector",
                    description="Reconnect the loose power connector.",
                    instruction_text="1. Power off the system\n2. Reconnect the power connector",
                    source_type="Service Manual",
                    source_title="UR Series Control box 5.5/5.6",
                    source_page=10,
                    linked_failure_mode_id="FM-001",
                ),
            ],
        ))
        result_two = _result_from_triplets(Triplet(
            symptom=Symptom(
                symptom_id="SYM-009",
                name="System will not start",
                description="No power from the control box prevents startup.",
                severity=Severity.CRITICAL,
            ),
            failure_modes=[
                FailureMode(
                    failure_mode_id="FM-011",
                    name="Power connector loose",
                    description="Loose connector at the control box power input.",
                    material_context="Controller",
                    linked_symptom_id="SYM-009",
                ),
            ],
            corrective_actions=[
                CorrectiveAction(
                    action_id="CA-014",
                    name="Reconnect the power connector",
                    description="Reconnect the power connector at the control box.",
                    instruction_text="1. Power off the system\n2. Reconnect the power connector",
                    source_type="Service Manual",
                    source_title="UR Series Control box 5.5/5.6",
                    source_page=11,
                    linked_failure_mode_id="FM-011",
                ),
            ],
        ))

        merged = _merge_extraction_results([result_one, result_two])

        self.assertEqual(len(merged.triplets), 1)
        self.assertEqual(len(merged.triplets[0].failure_modes), 1)
        self.assertEqual(len(merged.triplets[0].corrective_actions), 1)
        self.assertEqual(merged.triplets[0].symptom.severity, Severity.CRITICAL)

    def test_merge_extraction_results_filters_verification_only_noise(self):
        noisy = _result_from_triplets(Triplet(
            symptom=Symptom(
                symptom_id="SYM-001",
                name="Joint verification failed",
                description="Joint verification failed during inspection.",
                severity=Severity.MEDIUM,
            ),
            failure_modes=[
                FailureMode(
                    failure_mode_id="FM-001",
                    name="Joint verification failed",
                    description="Verification failed during test.",
                    material_context="",
                    linked_symptom_id="SYM-001",
                ),
            ],
            corrective_actions=[
                CorrectiveAction(
                    action_id="CA-001",
                    name="Verify joint connection",
                    description="Verify the joint connection.",
                    instruction_text="1. Verify the joint connection\n2. Confirm the test result",
                    source_type="Service Manual",
                    source_title="UR Series Control box 5.5/5.6",
                    source_page=10,
                    linked_failure_mode_id="FM-001",
                ),
            ],
        ))

        merged = _merge_extraction_results([noisy])
        self.assertEqual(merged.triplets, [])

    def test_merge_extraction_results_drops_incomplete_triads(self):
        incomplete = _result_from_triplets(Triplet(
            symptom=Symptom(
                symptom_id="SYM-001",
                name="System does not start",
                description="The control box has no power and the system does not start.",
                severity=Severity.HIGH,
            ),
            failure_modes=[
                FailureMode(
                    failure_mode_id="FM-001",
                    name="Loose power connector",
                    description="The power connector is loose.",
                    material_context="Control box",
                    linked_symptom_id="SYM-001",
                ),
            ],
            corrective_actions=[],
        ))

        merged = _merge_extraction_results([incomplete])
        self.assertEqual(merged.triplets, [])

    def test_filter_extraction_result_by_source_support_trims_unsupported_steps(self):
        result = _result_from_triplets(Triplet(
            symptom=Symptom(
                symptom_id="SYM-001",
                name="USB communication error",
                description="USB communication error has occurred.",
                severity=Severity.MEDIUM,
            ),
            failure_modes=[
                FailureMode(
                    failure_mode_id="FM-001",
                    name="USB cable connection fault",
                    description="USB cable connection is not properly connected.",
                    material_context="DSQC 662 USB connection",
                    linked_symptom_id="SYM-001",
                ),
            ],
            corrective_actions=[
                CorrectiveAction(
                    action_id="CA-001",
                    name="Reconnect USB cable",
                    description="Reconnect the USB cable to DSQC 662.",
                    instruction_text=(
                        "1. Reconnect the USB cable to DSQC 662. "
                        "2. Verify that the fault has been fixed."
                    ),
                    source_type="Operating manual",
                    source_title="IRC5",
                    source_page=65,
                    linked_failure_mode_id="FM-001",
                ),
            ],
        ))

        filtered = _filter_extraction_result_by_source_support(result, {
            65: "Reconnect the USB cable to DSQC 662. Make sure the USB cable is properly connected on both ends.",
        })

        self.assertEqual(len(filtered.triplets), 1)
        self.assertEqual(len(filtered.triplets[0].corrective_actions), 1)
        self.assertEqual(
            filtered.triplets[0].corrective_actions[0].instruction_text,
            "1. Reconnect the USB cable to DSQC 662.",
        )

    def test_filter_extraction_result_by_source_support_drops_unbacked_actions(self):
        result = _result_from_triplets(Triplet(
            symptom=Symptom(
                symptom_id="SYM-001",
                name="USB communication error",
                description="USB communication error has occurred.",
                severity=Severity.MEDIUM,
            ),
            failure_modes=[
                FailureMode(
                    failure_mode_id="FM-001",
                    name="USB cable connection fault",
                    description="USB cable connection is not properly connected.",
                    material_context="DSQC 662 USB connection",
                    linked_symptom_id="SYM-001",
                ),
            ],
            corrective_actions=[
                CorrectiveAction(
                    action_id="CA-001",
                    name="Reconnect USB cable",
                    description="Reconnect the USB cable to DSQC 662.",
                    instruction_text="1. Reconnect the USB cable to DSQC 662.",
                    source_type="Operating manual",
                    source_title="IRC5",
                    source_page=65,
                    linked_failure_mode_id="FM-001",
                ),
            ],
        ))

        filtered = _filter_extraction_result_by_source_support(result, {
            65: "Inspect the event log and review the power supply status.",
        })

        self.assertEqual(filtered.triplets, [])


if __name__ == "__main__":
    unittest.main()
