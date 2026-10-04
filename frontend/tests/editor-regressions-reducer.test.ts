// Regressions found by the independent review of 2afd41c.
import { describe, expect, it } from "vitest";
import { dirty, initialState, project, reducer } from "../src/editor/reducer";
import { document, graph } from "./editor-fixture";
import type { EditorDocument, Graph } from "../src/api/types";

// Real exported graphs contain yellow (doubtful) edges; the shared fixture only has green ones.
function withYellow(): EditorDocument {
  const g: Graph = structuredClone(graph);
  g.edges[0].tier = "yellow";
  g.edges[0].trusted = false;
  g.edges[0].occurrences[0].tier = "yellow";
  g.edges[0].occurrences[0].trusted = false;
  return { ...document, graph: g };
}

describe("review: dirty state on untouched graphs", () => {
  it("a freshly opened session with a yellow edge is not dirty", () => {
    const state = initialState(withYellow());
    expect(state.operations).toHaveLength(0);
    expect(dirty(state)).toBe(false);
  });
  it("edit + full undo on a yellow-edge graph is not dirty", () => {
    let state = initialState(withYellow());
    state = reducer(state, { type: "edit", operation: { op: "node.set_name", node_id: "sym", value: "X" } });
    state = reducer(state, { type: "undo" });
    expect(state.operations).toHaveLength(0);
    expect(dirty(state)).toBe(false);
  });
  it("project() keeps the yellow tier of untouched edges", () => {
    const g = withYellow().graph;
    expect(project(g, []).edges[0].tier).toBe("yellow");
  });
});
