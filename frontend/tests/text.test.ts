import { describe, expect, it } from "vitest";
import type { Version } from "../src/api/types";
import { formatCost, formatDuration, formatMinutes, formatRange, formatUsd, iterationLabel, statusLabel, versionLabel } from "../src/text/it";

const version = (overrides: Partial<Version>): Version => ({
  version_id: "runs~v3_r1",
  origin: "campaign",
  iteration: "",
  run: "v3_r1",
  repetition: 1,
  date: null,
  commit: "3ed84f5",
  verified: 0,
  doubtful: 0,
  excluded: 0,
  open_questions: 0,
  status: "approved",
  decided_by: null,
  cost_usd: null,
  seconds: null,
  pages: null,
  replay: true,
  copied_from: null,
  ...overrides,
});

describe("Italian labels", () => {
  it("says who approved", () => {
    expect(statusLabel("approved", "auto")).toBe("Approvato dal sistema");
    expect(statusLabel("approved", "human")).toBe("Approvato");
    expect(statusLabel("awaiting_approval")).toBe("Da approvare");
    expect(statusLabel("failed")).toBe("Non riuscita");
  });

  it("names versions by iteration and repetition", () => {
    expect(versionLabel(version({}))).toBe("Attuale r1");
    expect(versionLabel(version({ iteration: "E", repetition: 3 }))).toBe("E r3");
    expect(iterationLabel(version({ origin: "workspace" }))).toBe("Interfaccia");
    expect(iterationLabel(version({ origin: "workspace", copied_from: "campaign/x" }))).toBe("Risposte");
    expect(
      versionLabel(version({ origin: "workspace", copied_from: "campaign/x", run: "risposte-1", repetition: null })),
    ).toBe("Risposte 1");
  });

  it("formats money and time", () => {
    expect(formatUsd(0.0243)).toBe("0,024 USD");
    expect(formatDuration(137.8)).toBe("02:18");
    expect(formatRange(281, 295, formatMinutes, "min")).toBe("~5 min");
    expect(formatRange(250, 370, formatMinutes, "min")).toBe("4–6 min");
    expect(formatRange(0.106, 0.134, formatCost, "USD")).toBe("0,106–0,134 USD");
  });
});
