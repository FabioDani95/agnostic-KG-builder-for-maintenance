import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = new URL(".", import.meta.url).pathname;
const csvPath = `${outputDir}hydraulic_press_7_maintenance_log.csv`;
const xlsxPath = `${outputDir}hydraulic_press_7_maintenance_log.xlsx`;
const previewPath = `${outputDir}hydraulic_press_7_maintenance_log_preview.png`;
const verificationPath = `${outputDir}verification.json`;

const rows = [
  [
    "record_id",
    "event_timestamp",
    "machine_serial",
    "machine_model",
    "component",
    "event_type",
    "severity",
    "error_code",
    "observation",
    "action_taken",
    "downtime_minutes",
    "technician",
    "status",
  ],
  [
    "LOG-0001",
    "2026-07-01T07:45:00+02:00",
    "HP7-000042",
    "HP-700",
    "hydraulic_pump",
    "inspection",
    "low",
    "",
    "Pressure stable at 208 bar; no visible leaks.",
    "No action required.",
    0,
    "Marco R.",
    "closed",
  ],
  [
    "LOG-0002",
    "2026-07-03T14:12:00+02:00",
    "HP7-000042",
    "HP-700",
    "oil_cooling_loop",
    "alarm",
    "medium",
    "HYD-TEMP-042",
    "Hydraulic oil temperature reached 78 C during a long forming cycle.",
    "Cleaned heat-exchanger fins and verified fan rotation.",
    18,
    "Elena P.",
    "closed",
  ],
  [
    "LOG-0003",
    "2026-07-06T09:25:00+02:00",
    "HP7-000042",
    "HP-700",
    "return_line_filter",
    "corrective_maintenance",
    "high",
    "FILTER-DP-017",
    "Differential pressure indicator remained in the red zone after warm-up.",
    "Replaced return-line filter and recorded the removed element for inspection.",
    35,
    "Luca B.",
    "closed",
  ],
  [
    "LOG-0004",
    "2026-07-09T11:05:00+02:00",
    "HP7-000042",
    "HP-700",
    "main_cylinder",
    "fault",
    "medium",
    "RAM-DRIFT-008",
    "Ram drift measured at 1.8 mm over five minutes with the machine stopped.",
    "Adjusted counterbalance valve and repeated the holding test.",
    45,
    "Marco R.",
    "closed",
  ],
  [
    "LOG-0005",
    "2026-07-12T08:00:00+02:00",
    "HP7-000042",
    "HP-700",
    "emergency_stop_circuit",
    "safety_test",
    "low",
    "",
    "All emergency-stop stations interrupted motion and removed hydraulic enable.",
    "Signed the weekly safety-test checklist.",
    0,
    "Sara T.",
    "closed",
  ],
  [
    "LOG-0006",
    "2026-07-14T16:40:00+02:00",
    "HP7-000042",
    "HP-700",
    "high_pressure_hose_H17",
    "leak",
    "high",
    "LEAK-H17-003",
    "Oil mist observed at the crimp fitting during pressure build-up.",
    "Depressurized the circuit, replaced hose H17, cleaned the area, and leak-tested at 220 bar.",
    75,
    "Luca B.",
    "closed",
  ],
  [
    "LOG-0007",
    "2026-07-17T10:18:00+02:00",
    "HP7-000042",
    "HP-700",
    "pressure_transducer_PT2",
    "sensor_fault",
    "medium",
    "PT2-SIGNAL-011",
    "PT2 reading differed from the calibrated reference gauge by 9 bar.",
    "Recalibrated the transducer and verified readings at 50, 150, and 210 bar.",
    25,
    "Elena P.",
    "closed",
  ],
  [
    "LOG-0008",
    "2026-07-20T13:35:00+02:00",
    "HP7-000042",
    "HP-700",
    "hydraulic_pump",
    "inspection",
    "medium",
    "",
    "Intermittent cavitation noise heard for two seconds after cold start.",
    "Checked reservoir level and suction line; scheduled follow-up trend inspection.",
    10,
    "Marco R.",
    "monitoring",
  ],
  [
    "LOG-0009",
    "2026-07-22T15:08:00+02:00",
    "HP7-000042",
    "HP-700",
    "directional_valve_V4",
    "fault",
    "high",
    "PRESS-DROP-026",
    "System pressure dropped to 172 bar when V4 was energized.",
    "Replaced worn V4 spool seals and completed ten loaded cycles.",
    90,
    "Luca B.",
    "closed",
  ],
  [
    "LOG-0010",
    "2026-07-24T07:30:00+02:00",
    "HP7-000042",
    "HP-700",
    "slide_guides",
    "preventive_maintenance",
    "low",
    "",
    "Lubrication interval reached 500 operating hours.",
    "Cleaned guide surfaces and applied the approved EP2 lubricant.",
    20,
    "Sara T.",
    "closed",
  ],
  [
    "LOG-0011",
    "2026-07-26T12:55:00+02:00",
    "HP7-000042",
    "HP-700",
    "electrical_cabinet",
    "thermal_inspection",
    "low",
    "",
    "Highest terminal temperature was 41 C; no abnormal thermal pattern found.",
    "Stored thermal images with the monthly inspection record.",
    0,
    "Elena P.",
    "closed",
  ],
  [
    "LOG-0012",
    "2026-07-28T17:10:00+02:00",
    "HP7-000042",
    "HP-700",
    "hydraulic_system",
    "verification",
    "low",
    "",
    "Final pressure, temperature, leakage, and emergency-stop checks passed.",
    "Released the machine for production and closed the maintenance window.",
    0,
    "Marco R.",
    "closed",
  ],
];

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const csvText = `${rows.map((row) => row.map(csvCell).join(",")).join("\n")}\n`;
await fs.writeFile(csvPath, csvText, "utf8");

const workbook = await Workbook.fromCSV(csvText, { sheetName: "Maintenance Log" });
const sheet = workbook.worksheets.getItem("Maintenance Log");
sheet.showGridLines = false;
sheet.freezePanes.freezeRows(1);
sheet.getRange(`B2:B${rows.length}`).values = rows.slice(1).map((row) => {
  const wallClock = String(row[1]).slice(0, 16);
  return [new Date(`${wallClock}:00Z`)];
});

const used = sheet.getRange(`A1:M${rows.length}`);
used.format = {
  font: { name: "Aptos", size: 10, color: "#22211D" },
  verticalAlignment: "center",
};
sheet.getRange("A1:M1").format = {
  fill: "#355E4A",
  font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" },
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "outside", style: "thin", color: "#294839" },
};
sheet.getRange(`A2:M${rows.length}`).format.borders = {
  insideHorizontal: { style: "thin", color: "#E4E1D9" },
};
sheet.getRange(`B2:B${rows.length}`).format.numberFormat = "yyyy-mm-dd hh:mm";
sheet.getRange(`K2:K${rows.length}`).format.numberFormat = "0";
sheet.getRange(`A1:M${rows.length}`).format.rowHeight = 34;
sheet.getRange("A1:M1").format.rowHeight = 38;

const widths = {
  A: 86,
  B: 154,
  C: 112,
  D: 82,
  E: 160,
  F: 170,
  G: 78,
  H: 116,
  I: 310,
  J: 340,
  K: 96,
  L: 88,
  M: 82,
};
for (const [column, widthPx] of Object.entries(widths)) {
  sheet.getRange(`${column}1:${column}${rows.length}`).format.columnWidthPx = widthPx;
}
sheet.getRange(`I2:J${rows.length}`).format.wrapText = true;
sheet.getRange(`E2:F${rows.length}`).format.wrapText = true;

sheet.getRange(`G2:G${rows.length}`).conditionalFormats.add("containsText", {
  text: "high",
  format: { fill: "#FCE8E5", font: { color: "#9B3424", bold: true } },
});
sheet.getRange(`G2:G${rows.length}`).conditionalFormats.add("containsText", {
  text: "medium",
  format: { fill: "#FFF2D9", font: { color: "#805D19", bold: true } },
});
sheet.getRange(`M2:M${rows.length}`).conditionalFormats.add("containsText", {
  text: "closed",
  format: { fill: "#E7F2E9", font: { color: "#3F6747", bold: true } },
});

const table = sheet.tables.add(`A1:M${rows.length}`, true, "MaintenanceLogTable");
table.style = "TableStyleMedium4";
table.showBandedRows = true;
table.showFilterButton = true;

const inspection = await workbook.inspect({
  kind: "table",
  range: `Maintenance Log!A1:M${rows.length}`,
  include: "values,formulas",
  tableMaxRows: rows.length,
  tableMaxCols: 13,
  maxChars: 12000,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});

const preview = await workbook.render({
  sheetName: "Maintenance Log",
  range: `A1:M${rows.length}`,
  scale: 1,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(xlsxPath);

await fs.writeFile(
  verificationPath,
  JSON.stringify(
    {
      csvPath,
      xlsxPath,
      previewPath,
      rowCount: rows.length - 1,
      columnCount: rows[0].length,
      serial: "HP7-000042",
      inspection: inspection.ndjson,
      formulaErrorScan: errors.ndjson,
    },
    null,
    2,
  ),
  "utf8",
);

console.log(JSON.stringify({ csvPath, xlsxPath, previewPath, rowCount: rows.length - 1 }));
