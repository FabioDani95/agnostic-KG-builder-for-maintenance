import { describe, expect, it } from "vitest";
import type { ManualRow, Version } from "../src/api/types";
import { monogram } from "../src/components/Controls";
import { nextSorting, sortRows, type Column } from "../src/components/Table";
import { activeVersion, inbox, lifecycle, nextStep } from "../src/flow/steps";
import { blocker } from "../src/screens/NewGraph";
import { schemaLayout } from "../src/screens/OntologyScreen";

const version = (overrides: Partial<Version>): Version => ({
  version_id: "workspace~v3_r1",
  origin: "workspace",
  iteration: "",
  run: "v3_r1",
  repetition: 1,
  date: "2026-09-29T10:00:00+00:00",
  commit: "abc1234",
  verified: 60,
  doubtful: 4,
  excluded: 1,
  open_questions: 0,
  status: "approved",
  decided_by: "auto",
  cost_usd: 0.02,
  seconds: 99,
  pages: 18,
  replay: true,
  copied_from: null,
  ...overrides,
});

const row = (id: string, latest: Partial<Version> | null): ManualRow => ({
  id,
  origin: "campaign",
  machine: { name: `${id} pump`, brand: "Acme", model: id, type: "pump" },
  pages: 18,
  versions: 1,
  latest: latest ? version(latest) : null,
});

describe("the steps of a graph", () => {
  it("puts a person's questions before the approval", () => {
    const steps = lifecycle(version({ status: "awaiting_approval", open_questions: 10 }));
    expect(steps.map((step) => step.state)).toEqual(["done", "current", "waiting"]);
    expect(steps[1].detail).toBe("10 domande per te");
    expect(steps[0].detail).toBe("01:39 · 0,020 USD");
  });

  it("marks doubts left in an approved graph as optional, and who approved", () => {
    const steps = lifecycle(version({ open_questions: 3 }));
    expect(steps.map((step) => step.state)).toEqual(["done", "optional", "done"]);
    expect(steps[2].detail).toBe("Approvato dal sistema");
  });

  it("waits for the extraction while it runs, and stops at a failure", () => {
    expect(lifecycle(version({ status: "running" })).map((step) => step.state)).toEqual(["current", "waiting", "waiting"]);
    expect(lifecycle(version({ status: "failed" })).map((step) => step.state)).toEqual(["failed", "waiting", "waiting"]);
  });

  it("names the one next step and where it leads", () => {
    const base = "/manuali/m1/versioni/workspace~v3_r1";
    expect(nextStep("m1", version({ status: "awaiting_approval", open_questions: 2 }))).toEqual({
      label: "Rispondi alle 2 domande",
      to: `${base}/domande`,
      urgent: true,
    });
    expect(nextStep("m1", version({ status: "awaiting_approval", open_questions: 1 })).label).toBe("Rispondi alla domanda");
    expect(nextStep("m1", version({ status: "awaiting_approval" }))).toMatchObject({ to: base, urgent: true });
    expect(nextStep("m1", version({}))).toMatchObject({ label: "Apri il grafo", to: base, urgent: false });
    expect(nextStep("m1", version({ status: "running" })).to).toBe(`${base}/esecuzione`);
  });
});

describe("what waits for a person", () => {
  it("separates what blocks a run from doubts in approved graphs", () => {
    const box = inbox([
      row("a", { status: "awaiting_approval", open_questions: 4 }),
      row("b", { open_questions: 2 }),
      row("c", { open_questions: 7 }),
      row("d", {}),
      row("e", { status: "running" }),
      row("f", { status: "failed", open_questions: 3 }),
      row("g", null),
    ]);
    expect(box.waiting.map((item) => item.id)).toEqual(["a"]);
    expect(box.running.map((item) => item.id)).toEqual(["e"]);
    expect(box.doubts.map((item) => item.id)).toEqual(["c", "b"]);
  });

  it("reads the active run from the job path", () => {
    expect(activeVersion("graco/runs/v3_r2")).toEqual({ manualId: "graco", versionId: "workspace~v3_r2" });
    expect(activeVersion(null)).toBeNull();
    expect(activeVersion("odd")).toBeNull();
  });
});

describe("tables and small helpers", () => {
  const columns: Column<{ n: number | null; s: string }>[] = [
    { key: "n", label: "N", span: 6, sort: (item) => item.n, render: (item) => String(item.n) },
    { key: "s", label: "S", span: 6, sort: (item) => item.s, render: (item) => item.s },
  ];
  const items = [
    { n: 10, s: "b" },
    { n: null, s: "a10" },
    { n: 2, s: "a9" },
  ];

  it("sorts numbers and words, empty values last, and flips on a second click", () => {
    expect(sortRows(items, columns, { key: "n", direction: "asc" }).map((item) => item.n)).toEqual([2, 10, null]);
    expect(sortRows(items, columns, { key: "n", direction: "desc" }).map((item) => item.n)).toEqual([10, 2, null]);
    expect(sortRows(items, columns, { key: "s", direction: "asc" }).map((item) => item.s)).toEqual(["a9", "a10", "b"]);
    expect(nextSorting(null, "n")).toEqual({ key: "n", direction: "asc" });
    expect(nextSorting({ key: "n", direction: "asc" }, "n")).toEqual({ key: "n", direction: "desc" });
  });

  it("makes a maker's initials", () => {
    expect(monogram("ABB")).toBe("ABB");
    expect(monogram("Atlas Copco")).toBe("AC");
    expect(monogram("Grundfos")).toBe("GRU");
    expect(monogram("not_stated", "Pompa sommersa")).toBe("PS");
  });

  it("says why a run cannot start, in the order to fix it", () => {
    const ready = { running: null, hasManual: true, name: "Pump", worst: 0.05, estimated: true };
    expect(blocker(ready)).toBeNull();
    expect(blocker({ ...ready, running: "Graco" })).toMatch(/già un'esecuzione in corso/);
    expect(blocker({ ...ready, hasManual: false, name: "" })).toMatch(/Carica il manuale/);
    expect(blocker({ ...ready, name: " " })).toBe("Scrivi il nome della macchina.");
    expect(blocker({ ...ready, worst: null })).toMatch(/Non ho esecuzioni passate/);
  });
});

describe("the schema drawing", () => {
  it("puts each type in the column of its longest path", () => {
    const relations = [
      { domain: "Asset", range: "Component" },
      { domain: "Symptom", range: "FailureMode" },
      { domain: "FailureMode", range: "Component" },
      { domain: "FailureMode", range: "CorrectiveAction" },
      { domain: "Asset", range: "ErrorCode" },
      { domain: "ErrorCode", range: "FailureMode" },
    ];
    const names = ["Asset", "Component", "Symptom", "FailureMode", "CorrectiveAction", "ErrorCode"];
    const { position } = schemaLayout(names, relations);
    const column = (name: string) => position.get(name)!.x;
    expect(column("Asset")).toBe(column("Symptom"));
    expect(column("Asset")).toBeLessThan(column("ErrorCode"));
    expect(column("ErrorCode")).toBeLessThan(column("FailureMode"));
    expect(column("CorrectiveAction")).toBe(column("Component"));
    expect(position.get("Asset")!.y).toBeLessThan(position.get("Symptom")!.y);
  });
});
