import { describe, expect, it } from "vitest";
import type { GraphEdge, GraphNode } from "../src/api/types";
import { edgeLook } from "../src/graph/style";
import { diagnosticPath, searchStarts } from "../src/screens/FinishedGraph";

const edge = (from: string, to: string, type: string, derived = false): GraphEdge => ({
  id: `${from}-${to}`, type, from, to, tier: "green", trusted: true, derived, conditions: [], occurrences: [],
});
const node = (id: string, type: string, name: string, code = ""): GraphNode => ({
  id, type, name, properties: code ? { code } : {}, evidence: [],
});

describe("graph", () => {
  it("follows symptom, causes, actions and components", () => {
    const edges = [
      edge("s", "f", "MAY_INDICATE"),
      edge("f", "a", "RESOLVED_BY"),
      edge("f", "c", "AFFECTS"),
      edge("asset", "c", "HAS_COMPONENT", true),
      edge("s2", "f2", "MAY_INDICATE"),
    ];
    expect([...diagnosticPath("s", edges)].sort()).toEqual(["a", "c", "f", "s"]);
  });

  it("finds symptoms and codes by name or code", () => {
    const nodes = [node("1", "Symptom", "Pump stops"), node("2", "ErrorCode", "Overcurrent", "E-01"),
      node("3", "FailureMode", "Pump worn")];
    expect(searchStarts(nodes, "pump").map((item) => item.id)).toEqual(["1"]);
    expect(searchStarts(nodes, "e-01").map((item) => item.id)).toEqual(["2"]);
  });

  it("hides excluded relations and marks the rest by tier", () => {
    expect(edgeLook("red")).toBeNull();
    expect(edgeLook("yellow")).toBe("yellow");
    expect(edgeLook(null)).toBe("proposed");
    expect(edgeLook("green", true)).toBe("derived");
  });
});
