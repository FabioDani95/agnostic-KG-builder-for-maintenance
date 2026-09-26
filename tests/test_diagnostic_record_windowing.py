from __future__ import annotations

from backend.domain.evidence import (
    EvidenceContent,
    EvidenceUnit,
    IngestionInfo,
    LanguageInfo,
    LanguageQualification,
    ProvenanceRef,
    RawReference,
    RecordRole,
)
from backend.domain.locators import PdfLocator
from backend.domain.sources import SourceAuthority, SourceKind
from backend.services.diagnostic_record_windowing import build_diagnostic_record_windows


def _evidence(
    evidence_id: str,
    *,
    page: int,
    text: str,
    block_index: int | None = None,
    table_index: int | None = None,
    row_index: int | None = None,
) -> EvidenceUnit:
    locator = PdfLocator(
        page=page,
        quote=text,
        extraction_method="table" if table_index is not None else "native_text",
        block_index=block_index,
        table_index=table_index,
        row_index=row_index,
    )
    raw_id = f"raw_{evidence_id.removeprefix('ev_')}"
    return EvidenceUnit(
        evidence_id=evidence_id,
        workspace_id="ws_windowfixture0001",
        asset_id="asset_windowfixture01",
        source_id="src_windowfixture001",
        source_kind=SourceKind.PDF,
        authority=SourceAuthority.NORMATIVE,
        locator=locator,
        provenance_refs=[
            ProvenanceRef(
                role="primary",
                raw_unit_id=raw_id,
                source_id="src_windowfixture001",
                locator=locator,
                raw_hash="a" * 64,
                structure_id=(
                    f"page:{page}:table:{table_index}"
                    if table_index is not None
                    else f"page:{page}"
                ),
            )
        ],
        language=LanguageInfo(
            detected="en",
            confidence=1.0,
            qualification=LanguageQualification.QUALIFIED_EN,
        ),
        record_role=RecordRole.GENERIC_EVIDENCE,
        content=EvidenceContent(
            observation=text,
            semantic_texts={"observation": text},
        ),
        raw_ref=RawReference(
            source_id="src_windowfixture001",
            raw_unit_id=raw_id,
            locator_hash="b" * 64,
        ),
        ingestion=IngestionInfo(adapter_version="pdf-layout-v4"),
    )


def _titled_table(*, cause="The inlet filter is blocked.", solution="Replace the inlet filter."):
    cells = [["The pressure alarm illuminates.", ""], ["Possible causes", "Possible solutions"], [cause, solution]]
    units = []
    for index, values in enumerate(cells, 1):
        unit = _evidence(f"ev_titledtable{index:03d}", page=7, table_index=1, row_index=index, text=" | ".join(values))
        unit.attributes["table_layout"] = {
            "cells": values, "table_bbox": [10, 10, 210, 110],
            "cell_bboxes": [[10, 10, 210, 30], None] if index == 1 else [[10, 30, 110, 60], [110, 30, 210, 60]],
        }
        units.append(unit)
    return units


def test_spanning_symptom_title_is_root_above_plural_cause_solution_header():
    units = _titled_table()
    windows = build_diagnostic_record_windows(units)
    assert len(windows) == 1
    window = windows[0]
    assert window.structure_status == "atomic"
    assert window.record_anchor == units[0].evidence_id
    assert window.branch_anchor == units[2].evidence_id
    assert window.allowed_source_anchors == [units[0].evidence_id, units[2].evidence_id]
    assert window.allowed_evidence_spans[units[0].evidence_id] == ["The pressure alarm illuminates."]
    assert units[1].evidence_id not in window.allowed_source_anchors
    assert build_diagnostic_record_windows(list(reversed(units))) == windows


def test_spanning_title_needs_geometry_and_diagnostic_column_roles():
    units = _titled_table()
    units[0].attributes["table_layout"]["cell_bboxes"][0][2] = 110
    assert build_diagnostic_record_windows(units) == []
    units = _titled_table()
    units[1].attributes["table_layout"]["cells"] = ["Part number", "Description"]
    assert build_diagnostic_record_windows(units) == []


def test_unnumbered_alternatives_are_not_paired_by_bullet_count():
    units = _titled_table(cause="□ The inlet is blocked. □ The outlet is blocked.", solution="□ Clean the outlet. □ Clean the inlet.")
    windows = build_diagnostic_record_windows(units)
    assert len(windows) == 1
    assert windows[0].structure_status == "ambiguous_pairing"
    assert "Clean the inlet" in windows[0].text_with_pages


def _base_table() -> list[EvidenceUnit]:
    return [
        _evidence(
            "ev_tableheader00001",
            page=3,
            text="Problem | Possible cause | Remedy",
            table_index=1,
            row_index=1,
        ),
        _evidence(
            "ev_tablebranch00001",
            page=3,
            text="Motor does not start | Fuse is open | Replace the fuse",
            table_index=1,
            row_index=2,
        ),
        _evidence(
            "ev_tablebranch00002",
            page=3,
            text=" | Supply cable is loose | Tighten the cable",
            table_index=1,
            row_index=3,
        ),
        _evidence(
            "ev_tablebranch00003",
            page=3,
            text="Motor overheats | Vent is blocked | Clear the vent",
            table_index=1,
            row_index=4,
        ),
    ]


def test_blank_first_cell_inherits_only_root_cell_within_table() -> None:
    windows = build_diagnostic_record_windows(_base_table())

    assert len(windows) == 3
    first, continuation, new_root = windows
    assert first.record_anchor == first.branch_anchor == "ev_tablebranch00001"
    assert not first.inherited_root

    assert continuation.record_anchor == continuation.root_anchor == "ev_tablebranch00001"
    assert continuation.branch_anchor == "ev_tablebranch00002"
    assert continuation.allowed_source_anchors == [
        "ev_tablebranch00001",
        "ev_tablebranch00002",
    ]
    assert continuation.inherited_root
    assert "ROOT CELL (CONTEXT ONLY): Motor does not start" in continuation.text_with_pages
    assert "Fuse is open" not in continuation.text_with_pages
    assert "Replace the fuse" not in continuation.text_with_pages
    assert "Supply cable is loose" in continuation.text_with_pages

    assert new_root.record_anchor == new_root.branch_anchor == "ev_tablebranch00003"
    assert new_root.allowed_source_anchors == ["ev_tablebranch00003"]
    assert not new_root.inherited_root


def test_new_physical_table_resets_root_even_with_blank_first_cell() -> None:
    units = [
        *_base_table()[:3],
        _evidence(
            "ev_secondheader0001",
            page=3,
            text="Problem | Possible cause | Remedy",
            table_index=2,
            row_index=1,
        ),
        _evidence(
            "ev_secondbranch0001",
            page=3,
            text=" | Connector is dirty | Clean the connector",
            table_index=2,
            row_index=2,
        ),
    ]

    second = next(
        window
        for window in build_diagnostic_record_windows(units)
        if window.branch_anchor == "ev_secondbranch0001"
    )
    assert second.root_anchor == second.branch_anchor == "ev_secondbranch0001"
    assert second.allowed_source_anchors == ["ev_secondbranch0001"]
    assert not second.inherited_root
    assert "Motor does not start" not in second.text_with_pages


def test_repeated_header_can_continue_one_logical_table_across_adjacent_pages() -> None:
    units = [
        _evidence(
            "ev_crossheader00001",
            page=5,
            text="Symptom | Cause | Action",
            table_index=3,
            row_index=1,
        ),
        _evidence(
            "ev_crossbranch00001",
            page=5,
            text="Pressure is low | Inlet is blocked | Clean the inlet",
            table_index=3,
            row_index=2,
        ),
        _evidence(
            "ev_crossheader00002",
            page=6,
            text="Symptom | Cause | Action",
            table_index=4,
            row_index=1,
        ),
        _evidence(
            "ev_crossbranch00002",
            page=6,
            text=" | Hose is leaking | Replace the hose",
            table_index=4,
            row_index=2,
        ),
    ]

    continued = next(
        window
        for window in build_diagnostic_record_windows(units)
        if window.branch_anchor == "ev_crossbranch00002"
    )
    assert continued.root_anchor == "ev_crossbranch00001"
    assert continued.allowed_source_anchors == [
        "ev_crossbranch00001",
        "ev_crossbranch00002",
    ]
    assert continued.page_numbers == [5, 6]
    assert continued.inherited_root


def test_explicit_block_record_keeps_contiguous_support_across_page_break() -> None:
    units = [
        _evidence(
            "ev_blockheading0001",
            page=10,
            block_index=4,
            text="TROUBLE SHOOTING GUIDE",
        ),
        _evidence(
            "ev_blockproblem0001",
            page=10,
            block_index=5,
            text="Problem: Drive stops unexpectedly",
        ),
        _evidence(
            "ev_blockcause00001",
            page=10,
            block_index=6,
            text="Cause: Cooling path is obstructed",
        ),
        _evidence(
            "ev_blockaction0001",
            page=11,
            block_index=0,
            text="Remedy: Clear the cooling path and restart the drive",
        ),
    ]

    windows = build_diagnostic_record_windows(units)
    assert len(windows) == 1
    window = windows[0]
    assert window.window_kind == "contiguous_blocks"
    assert window.record_anchor == "ev_blockproblem0001"
    assert window.allowed_source_anchors == [
        "ev_blockproblem0001",
        "ev_blockcause00001",
        "ev_blockaction0001",
    ]
    assert window.page_numbers == [10, 11]
    assert "--- PAGE 10 ---" in window.text_with_pages
    assert "--- PAGE 11 ---" in window.text_with_pages


def test_numbered_prose_alternatives_are_atomized_with_alpha_substeps() -> None:
    units = [
        _evidence(
            "ev_proseroot00001",
            page=10,
            block_index=1,
            text="Problem: Output is low",
        ),
        _evidence(
            "ev_prosestep00001",
            page=10,
            block_index=2,
            text="Troubleshooting:\n1. Replace the inlet filter.",
        ),
        _evidence(
            "ev_prosestep00002",
            page=10,
            block_index=3,
            text="2. Correct tool mapping.",
        ),
        _evidence(
            "ev_prosesubstep001",
            page=10,
            block_index=4,
            text="a) Open the tool menu.",
        ),
        _evidence(
            "ev_prosesubstep002",
            page=10,
            block_index=5,
            text="b) Map the tool to the spindle.",
        ),
    ]

    windows = build_diagnostic_record_windows(units)

    assert len(windows) == 2
    assert all(window.edge_policy == "prose_structural_endpoint_union" for window in windows)
    assert windows[0].allowed_source_anchors == [
        "ev_proseroot00001",
        "ev_prosestep00001",
    ]
    assert windows[1].allowed_source_anchors == [
        "ev_proseroot00001",
        "ev_prosestep00002",
        "ev_prosesubstep001",
        "ev_prosesubstep002",
    ]


def test_numbered_procedure_remains_one_sequential_record() -> None:
    units = [
        _evidence(
            "ev_procedureroot1",
            page=11,
            block_index=1,
            text="Problem: Controls are out of alignment",
        ),
        _evidence(
            "ev_procedurestep1",
            page=11,
            block_index=2,
            text="Troubleshooting: Calibration required. Proceed as follows.\n1. Power down.",
        ),
        _evidence(
            "ev_procedurestep2",
            page=11,
            block_index=3,
            text="2. Start calibration.",
        ),
        _evidence(
            "ev_procedurestep3",
            page=11,
            block_index=4,
            text="3. Save and exit.",
        ),
    ]

    windows = build_diagnostic_record_windows(units)

    assert len(windows) == 1
    assert windows[0].edge_policy == "prose_structural_endpoint_union"
    assert len(windows[0].allowed_source_anchors) == 4


def test_embedded_new_section_heading_stops_current_prose_record() -> None:
    units = [
        _evidence(
            "ev_boundaryroot001",
            page=12,
            block_index=1,
            text="Problem: Path is too wide",
        ),
        _evidence(
            "ev_boundarystep001",
            page=12,
            block_index=2,
            text="Troubleshooting:\n1. Replace the damaged nozzle.",
        ),
        _evidence(
            "ev_boundarysection1",
            page=12,
            block_index=3,
            text="RF/EMI Interference\nSome environments generate electrical noise.",
        ),
        _evidence(
            "ev_boundarystep002",
            page=12,
            block_index=4,
            text="Step 1) Install an earth ground.",
        ),
    ]

    window = build_diagnostic_record_windows(units)[0]

    assert "ev_boundarysection1" not in window.allowed_source_anchors
    assert "ev_boundarystep002" not in window.allowed_source_anchors


def test_window_ids_and_physical_order_do_not_depend_on_input_order() -> None:
    units = _base_table()
    forward = build_diagnostic_record_windows(units)
    reverse = build_diagnostic_record_windows(list(reversed(units)))

    assert [window.window_id for window in forward] == [window.window_id for window in reverse]
    assert [window.branch_anchor for window in forward] == [
        "ev_tablebranch00001",
        "ev_tablebranch00002",
        "ev_tablebranch00003",
    ]
    assert [window.model_dump(mode="json") for window in forward] == [
        window.model_dump(mode="json") for window in reverse
    ]


def test_long_block_record_is_exhaustively_split_without_support_overlap() -> None:
    units = [
        _evidence(
            "ev_longroot0000001",
            page=20,
            block_index=0,
            text="Problem: Output pressure is low",
        ),
        *[
            _evidence(
                f"ev_longstep{index:07d}",
                page=20,
                block_index=index,
                text=f"Troubleshooting step {index}: inspect branch {index}",
            )
            for index in range(1, 8)
        ],
    ]

    windows = build_diagnostic_record_windows(units, max_block_units=4)

    assert len(windows) == 3
    assert all(window.record_anchor == "ev_longroot0000001" for window in windows)
    non_root_anchors = [
        anchor
        for window in windows
        for anchor in window.allowed_source_anchors
        if anchor != "ev_longroot0000001"
    ]
    assert non_root_anchors == [f"ev_longstep{index:07d}" for index in range(1, 8)]
    assert len(non_root_anchors) == len(set(non_root_anchors))


def test_numbered_table_row_is_atomized_and_scoped_per_branch() -> None:
    units = [
        _evidence(
            "ev_numberedheader01",
            page=12,
            text="Fault number | Fault name | Possible fault | Troubleshooting",
            table_index=7,
            row_index=1,
        ),
        _evidence(
            "ev_numberedbranch1",
            page=12,
            text=(
                "3 | Ambient OTP | 1 The air vents are blocked. "
                "2 The fans do not work. | Contact service personnel."
            ),
            table_index=7,
            row_index=2,
        ),
    ]

    windows = build_diagnostic_record_windows(units)

    assert len(windows) == 2
    assert {window.branch_ordinal for window in windows} == {1, 2}
    assert all(window.branch_count == 2 for window in windows)
    assert len({window.window_id for window in windows}) == 2
    scoped = [
        window.allowed_evidence_spans["ev_numberedbranch1"] for window in windows
    ]
    assert all("Ambient OTP" in spans for spans in scoped)
    assert sum("1 The air vents are blocked." in spans for spans in scoped) == 1
    assert sum("2 The fans do not work." in spans for spans in scoped) == 1
    assert all("Contact service personnel." in spans for spans in scoped)


def test_equal_numbered_cause_and_action_lists_pair_positionally() -> None:
    units = [
        _evidence(
            "ev_pairedheader0001",
            page=13,
            text="Problem | Cause | Remedy",
            table_index=8,
            row_index=1,
        ),
        _evidence(
            "ev_pairedbranch001",
            page=13,
            text=(
                "Link down | 1 Cable is loose. 2 Module IDs repeat. | "
                "1 Tighten the cable. 2 Set unique IDs."
            ),
            table_index=8,
            row_index=2,
        ),
    ]

    windows = sorted(
        build_diagnostic_record_windows(units), key=lambda item: item.branch_ordinal
    )

    assert len(windows) == 2
    assert "1 Cable is loose." in windows[0].text_with_pages
    assert "1 Tighten the cable." in windows[0].text_with_pages
    assert "2 Set unique IDs." not in windows[0].text_with_pages
    assert "2 Module IDs repeat." in windows[1].text_with_pages
    assert "2 Set unique IDs." in windows[1].text_with_pages
    assert "1 Tighten the cable." not in windows[1].text_with_pages


def test_incompatible_numbered_cardinalities_are_not_guessed() -> None:
    units = [
        _evidence(
            "ev_ambiguousheader1",
            page=14,
            text="Problem | Cause | Remedy",
            table_index=9,
            row_index=1,
        ),
        _evidence(
            "ev_ambiguousrow001",
            page=14,
            text=(
                "Output low | 1 Filter blocked. 2 Valve closed. | "
                "1 Clean filter. 2 Open valve. 3 Contact service."
            ),
            table_index=9,
            row_index=2,
        ),
    ]

    windows = build_diagnostic_record_windows(units)

    assert len(windows) == 1
    assert windows[0].structure_status == "ambiguous_pairing"
    assert windows[0].branch_count == 1


def test_lowercase_wrapped_heading_and_procedure_continue_across_pages():
    units = [
        _evidence("ev_wrappedroot01", page=12, block_index=1, text="Problem: Controls are out of"),
        _evidence("ev_wrappedtail01", page=12, block_index=2, text="alignment\nDescription of Problem: Controls do not align."),
        _evidence("ev_wrappedstep01", page=12, block_index=3, text="Troubleshooting:\nCalibration is required. Proceed as follows.\n1) Start calibration."),
        _evidence("ev_wrappedstep02", page=13, block_index=0, text="2) Save and exit."),
    ]
    windows = build_diagnostic_record_windows(units)
    assert len(windows) == 1
    assert windows[0].page_numbers == [12, 13]
    assert windows[0].edge_policy == "prose_structural_endpoint_union"
    assert set(windows[0].allowed_source_anchors) == {unit.evidence_id for unit in units}


def test_table_rendering_deduplicates_only_literal_geometric_overlap():
    from backend.adapters.pdf import _semantic_page_units
    row = _evidence("ev_tableliteral01", page=1, table_index=1, row_index=1, text="Low pressure | Valve closed | Open valve")
    row = row.model_copy(update={"attributes": {"table_layout": {"table_bbox": [0, 0, 200, 100], "cells": ["Low pressure", "Valve closed", "Open valve"]}}})
    block = _evidence("ev_blockliteral01", page=1, block_index=1, text="Valve closed")
    block = block.model_copy(update={"locator": block.locator.model_copy(update={"bbox": [10, 10, 100, 20]})})
    outside = block.model_copy(update={"evidence_id": "ev_outsideliteral1", "locator": block.locator.model_copy(update={"bbox": [10, 200, 100, 220]})})
    negated = block.model_copy(update={"evidence_id": "ev_negativeliteral", "locator": block.locator.model_copy(update={"quote": "Valve not closed"})})
    inventory = [row, block, outside, negated]
    selected, _ = _semantic_page_units(inventory)
    assert block not in selected
    assert row in selected and outside in selected and negated in selected
    assert len(inventory) == 4


def test_only_complete_check_cell_is_an_informational_source_gap():
    from backend.services.diagnostic_bundle_compiler import compile_diagnostic_bundles

    def run(cell, quote):
        anchor = 'ev_checkedrow00001'
        cells = ['Motor stops', 'Drive overheating', cell]
        unit = _evidence(anchor, page=7, text=' | '.join(cells), table_index=1, row_index=1).model_copy(update={'attributes': {'table_layout': {'cells': cells, 'column_headers': ['Problem', 'Cause', 'Solution']}}})
        def span(text):
            return {'source_anchor': anchor, 'source_page': 7, 'quote': text}
        window = {'window_id': 'diagwin_check_cell', 'record_anchor': anchor, 'branch_anchor': anchor, 'structure_status': 'atomic', 'edge_policy': 'table_atomic_endpoint_union', 'branch_count': 1, 'allowed_source_anchors': [anchor], 'allowed_evidence_spans': {anchor: cells}}
        candidate = {'record_window_id': window['window_id'], 'record_anchor': anchor, 'branch_anchor': anchor, 'allowed_source_anchors': [anchor], 'indicators': [{'kind': 'symptom', 'name': 'Motor stops', 'description': 'Motor stops', 'severity': 'Unknown', 'claim_evidence': [span('Motor stops')], 'failure_link_evidence': [span('Motor stops'), span('Drive overheating')]}], 'failure': {'name': 'Drive overheating', 'description': 'Drive overheating', 'material_context': None, 'claim_evidence': [span('Drive overheating')]}, 'actions': [], 'inspection_steps': [{'instruction_text': quote, 'claim_evidence': [span(quote)]}], 'conditions': [], 'affected_component': None, 'resolution_status': 'check_only'}
        result = compile_diagnostic_bundles([candidate], source_type='manual', source_title='Synthetic source', evidence_units=[unit], record_windows=[window])
        assert not result.ontology.relations
        return result.report.entries[0]
    clear = run('Check the temperature.', 'Check the temperature.')
    assert clear.source_gap_verified and clear.disposition == 'gap'
    assert not run('Check the temperature. Replace the sensor.', 'Check the temperature.').source_gap_verified
    assert not run('Check the temperature.', 'temperature').source_gap_verified
