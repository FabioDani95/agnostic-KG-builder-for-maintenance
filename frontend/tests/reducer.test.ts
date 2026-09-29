import { describe, expect, it } from "vitest";
import type { UiEvent } from "../src/live/events";
import { counts, initialRun, runReducer } from "../src/live/reducer";
import { stationDetail } from "../src/screens/LiveRun";

let seq = 0;
const event = (kind: string, data: Record<string, unknown>, t = seq, cost = 0): UiEvent => ({
  seq: ++seq,
  t,
  cost_usd: cost,
  kind,
  data,
});

const node = (id: string, type = "Symptom") => ({ id, type, name: id, pages: [8] });
const edge = (id: string, from: string, to: string, tier: string | null = null) => ({
  id,
  type: "MAY_INDICATE",
  from,
  to,
  pages: [8],
  tier,
});

function play(events: UiEvent[]) {
  return events.reduce(runReducer, initialRun());
}

describe("run reducer", () => {
  it("builds stations, graph and counters from a recorded run", () => {
    seq = 0;
    const run = play([
      event("run_started", { mode: "replay", pages: 18 }),
      event("station", { station: "read", state: "running" }),
      event("station", { station: "read", state: "done" }),
      event("station", { station: "map", state: "running" }),
      event("pages_mapped", { pages: [{ label: "diagnostic" }, { label: "other" }] }),
      event("units_planned", { units: [{}, {}] }),
      event("station", { station: "extract", state: "running", done: 0, total: 2 }),
      event("unit_extracted", { index: 1, total: 2, nodes: [node("a"), node("b", "FailureMode")], edges: [edge("e1", "a", "b")] }, 10, 0.004),
      event("relations_checked", { nodes: [], edges: [edge("e1", "a", "b", "green")], removed: [] }, 20, 0.01),
    ]);
    expect(run.stations.read.phase).toBe("done");
    expect(run.stations.extract.phase).toBe("running");
    expect(run.units).toEqual({ done: 1, total: 2 });
    expect(run.readPages).toBe(1);
    expect(counts(run)).toEqual({ nodes: 2, relations: 1, verified: 1 });
    expect(run.cost).toBe(0.01);
    expect(stationDetail("extract", run)).toBe("Unità 1 di 2");
    expect(stationDetail("map", run)).toBe("1 pagina diagnostica su 18");
  });

  it("drops replaced edges, hides excluded ones and follows merges at the end", () => {
    seq = 0;
    const run = play([
      event("run_started", { mode: "live" }),
      event("unit_extracted", { index: 1, total: 1, nodes: [node("a"), node("a2"), node("b", "FailureMode")],
        edges: [edge("e1", "a", "b"), edge("e2", "a2", "b"), edge("e3", "b", "a")] }),
      event("relations_checked", { nodes: [], edges: [edge("e1", "a", "b", "yellow"), edge("e3", "b", "a", "red")], removed: ["e2"] }),
      event("graph_final", { nodes: [node("a"), node("b", "FailureMode")], edges: [{ ...edge("e1", "a", "b", "green"), pages: undefined }],
        merged_into: { a2: "a" }, edges_into: { e2: "e1" } }),
      event("run_finished", { status: "awaiting_approval", verified: 1, doubtful: 0, excluded: 1, open_questions: 3 }),
    ]);
    expect(Object.keys(run.nodes).sort()).toEqual(["a", "b"]);
    expect(run.edges.e1.tier).toBe("green");
    expect(run.edges.e1.pages).toEqual([8]); // kept from the provisional edge
    expect(run.recent).toEqual(["e1"]);
    expect(run.finished?.open_questions).toBe(3);
    expect(stationDetail("ask", run)).toBe("");
  });

  it("ignores events it has already seen", () => {
    seq = 0;
    const started = event("run_started", { mode: "replay" });
    const extracted = event("unit_extracted", { index: 1, total: 1, nodes: [node("a")], edges: [] });
    const once = play([started, extracted]);
    expect(runReducer(once, extracted)).toBe(once);
  });
});
