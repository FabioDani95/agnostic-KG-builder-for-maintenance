#!/usr/bin/env python3
"""Build the versioned, gold-blind G1 skeleton of DS-003."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import fitz

REPO_ROOT = Path(__file__).resolve().parent.parent
ROOT = REPO_ROOT / "tests" / "golden" / "workspaces" / "ds003"
RAW = ROOT / "raw"
INGESTION = ROOT / "ingestion"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_pdf(path: Path, title: str, lines: list[str]) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(
        fitz.Rect(54, 54, 540, 760),
        "\n".join([title, *lines]),
        fontsize=11,
    )
    document.set_metadata(
        {
            "title": title,
            "author": "DS-003 fixture builder",
            "creator": "log-kg-builder",
            "producer": "PyMuPDF",
            "creationDate": "D:20260729000000Z",
            "modDate": "D:20260729000000Z",
        }
    )
    document.save(path, garbage=4, deflate=True, no_new_id=True)
    document.close()


def _write_minimal_xlsx(path: Path) -> None:
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Maintenance" sheetId="1" r:id="rId1"/><sheet name="Components" sheetId="2" r:id="rId2"/></sheets>
</workbook>""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
</Relationships>""",
        "xl/worksheets/sheet1.xml": """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>alarm_code</t></is></c><c r="B1" t="inlineStr"><is><t>observation</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>0017</t></is></c><c r="B2" t="inlineStr"><is><t>Hydraulic pressure low</t></is></c></row>
</sheetData></worksheet>""",
        "xl/worksheets/sheet2.xml": """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>component_code</t></is></c><c r="B1" t="inlineStr"><is><t>component_name</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>P-01</t></is></c><c r="B2" t="inlineStr"><is><t>Main pump</t></is></c></row>
</sheetData></worksheet>""",
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(2026, 7, 29, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name])


def _evidence(source_id: str, quote: str) -> list[dict]:
    return [
        {
            "source_id": source_id,
            "unit_id": "raw_ds003_manual_a_p1_b1",
            "locator": {
                "kind": "pdf",
                "page": 1,
                "extraction_method": "native_text",
            },
            "quote": quote,
            "content_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest(),
        }
    ]


def main() -> int:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    RAW.mkdir(parents=True)
    INGESTION.mkdir(parents=True)

    quote = "Hydraulic pressure low"
    _write_pdf(
        RAW / "maintenance_manual.pdf",
        "HP-700 Maintenance Manual",
        ["SERIAL: HP7-000042", quote, "Inspect the main pump and tighten the coupling."],
    )
    _write_pdf(
        RAW / "service_bulletin.pdf",
        "HP-700 Service Bulletin",
        ["SERIAL: HP7-000042", "Alarm 0017 can indicate insufficient hydraulic pressure."],
    )
    (RAW / "events.csv").write_text(
        "timestamp,alarm_code,observation,action,outcome\n"
        "2026-01-02T08:00:00Z,0017,Hydraulic pressure low,Tighten coupling,resolved\n",
        encoding="utf-8",
    )
    _write_minimal_xlsx(RAW / "maintenance.xlsx")
    (RAW / "observations.jsonl").write_text(
        '{"timestamp":"2026-01-03T09:00:00Z","component":"Main pump","observation":"Hydraulic pressure low"}\n',
        encoding="utf-8",
    )

    (INGESTION / "maintenance_manual.txt").write_text(
        "HP-700 Maintenance Manual\nSERIAL: HP7-000042\nHydraulic pressure low\n"
        "Inspect the main pump and tighten the coupling.\n",
        encoding="utf-8",
    )
    (INGESTION / "service_bulletin.txt").write_text(
        "HP-700 Service Bulletin\nSERIAL: HP7-000042\n"
        "Alarm 0017 can indicate insufficient hydraulic pressure.\n",
        encoding="utf-8",
    )
    shutil.copyfile(RAW / "events.csv", INGESTION / "events.csv")
    (INGESTION / "maintenance.json").write_text(
        json.dumps(
            {
                "sheets": {
                    "Maintenance": [{"alarm_code": "0017", "observation": quote}],
                    "Components": [{"component_code": "P-01", "component_name": "Main pump"}],
                }
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    shutil.copyfile(RAW / "observations.jsonl", INGESTION / "observations.jsonl")

    source_specs = [
        ("src_ds003_pdf_manual", "pdf", "raw/maintenance_manual.pdf", "ingestion/maintenance_manual.txt", "calibration"),
        ("src_ds003_pdf_bulletin", "pdf", "raw/service_bulletin.pdf", "ingestion/service_bulletin.txt", "held_out"),
        ("src_ds003_csv_events", "csv", "raw/events.csv", "ingestion/events.csv", "calibration"),
        ("src_ds003_xlsx_maintenance", "xlsx", "raw/maintenance.xlsx", "ingestion/maintenance.json", "held_out"),
        ("src_ds003_jsonl_observations", "jsonl", "raw/observations.jsonl", "ingestion/observations.jsonl", "held_out"),
    ]
    sources = []
    for source_id, kind, raw_path, view_path, split in source_specs:
        item = {
            "source_id": source_id,
            "kind": kind,
            "sha256": _sha(ROOT / raw_path),
            "split": split,
            "raw_path": raw_path,
            "ingestion_view": {
                "path": view_path,
                "sha256": _sha(ROOT / view_path),
            },
        }
        if kind == "csv":
            item["ingestion_view"]["columns"] = [
                "timestamp",
                "alarm_code",
                "observation",
                "action",
                "outcome",
            ]
        if kind == "xlsx":
            item["sheet_count"] = 2
            item["ingestion_view"]["columns"] = [
                "alarm_code",
                "observation",
                "component_code",
                "component_name",
            ]
        if kind == "jsonl":
            item["ingestion_view"]["columns"] = ["timestamp", "component", "observation"]
        sources.append(item)

    evidence = _evidence("src_ds003_pdf_manual", quote)
    nodes = [
        {
            "claim_id": f"claim_node_{index:02d}",
            "node_type": "Component" if index else "Asset",
            "node_id": f"node_ds003_{index:02d}",
            "evidence": evidence,
        }
        for index in range(10)
    ]
    properties = [
        {
            "claim_id": f"claim_property_{index:02d}",
            "node_id": f"node_ds003_{index:02d}",
            "property": "name",
            "value": f"DS-003 placeholder entity {index:02d}",
            "evidence": evidence,
        }
        for index in range(10)
    ]
    relationships = [
        {
            "claim_id": f"claim_relationship_{index:02d}",
            "relationship": "HAS_COMPONENT",
            "from_id": "node_ds003_00",
            "to_id": f"node_ds003_{index:02d}",
            "evidence": evidence,
        }
        for index in range(10)
    ]
    expected = {
        "schema_ref": "tests/golden/workspaces/ds003_expected.schema.json",
        "contract_version": "1.0.0",
        "workspace_id": "ws_ds003_skeleton",
        "graph_id": "kg_ds003_single_graph",
        "asset": {
            "asset_id": "node_ds003_00",
            "name": "Hydraulic Press 7",
            "model": "HP-700",
        },
        "sources": sources,
        "claim_count": len(nodes) + len(properties) + len(relationships),
        "expected": {
            "nodes": nodes,
            "properties": properties,
            "relationships": relationships,
        },
        "negative_claims": [
            {
                "claim_id": "negative_missing_supported_action",
                "kind": "failure_mode_without_action",
                "matcher": {"failure_mode": "unsupported_placeholder_failure"},
                "prohibited": {"invented_action": True},
                "evidence": evidence,
            }
        ],
    }
    (ROOT / "expected.json").write_text(
        json.dumps(expected, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (ROOT / "SKELETON.json").write_text(
        json.dumps(
            {
                "status": "g1_skeleton",
                "quality_gate": "not_evaluated",
                "warning": "Placeholder expected claims are evaluator-only and do not certify AC-SEM-001.",
                "raw_source_count": len(sources),
                "pdf_source_count": 2,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    checksum_paths = sorted(
        [path for path in RAW.rglob("*") if path.is_file()]
        + [path for path in INGESTION.rglob("*") if path.is_file()]
    )
    (ROOT / "checksums.sha256").write_text(
        "".join(f"{_sha(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in checksum_paths),
        encoding="utf-8",
    )
    print(ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

