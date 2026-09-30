import { describe, it, expect } from "vitest";
import { document, preview } from "./editor-fixture";
import { dirty, initialState, project, reducer } from "../src/editor/reducer";
import { filterNodes, indices, valueState } from "../src/editor/selectors";
import { parseValue } from "../src/editor/EditableCell";
describe("graph document editing", () => {
  it("preserves the base, invalidates incident assertions, restores cascade deletions with undo", () => {
    let state = initialState(document);
    state = reducer(state, {
      type: "select",
      selection: { kind: "node", id: "sym" },
    });
    state = reducer(state, {
      type: "edit",
      operation: { op: "node.set_name", node_id: "sym", value: "Edited" },
    });
    const current = project(document.graph, state.operations);
    expect(current.nodes[1].properties.name).toBe("Edited");
    expect(current.edges[0].trusted).toBe(false);
    expect(document.graph.nodes[1].name).toBe("Noise");
    state = reducer(state, {
      type: "edit",
      operation: { op: "node.delete", node_id: "sym" },
    });
    expect(project(document.graph, state.operations).edges).toHaveLength(0);
    state = reducer(state, { type: "undo" });
    expect(project(document.graph, state.operations).edges).toHaveLength(1);
    expect(state.selection?.id).toBe("sym");
    state = reducer(state, { type: "undo" });
    expect(dirty(state)).toBe(false);
    expect(state.future).toHaveLength(2);
    state = reducer(state, { type: "redo" });
    expect(dirty(state)).toBe(true);
  });
  it("ignores old validation generations and invalidates acknowledgements", () => {
    let s = initialState(document);
    s = reducer(s, {
      type: "edit",
      operation: { op: "node.set_name", node_id: "sym", value: "Changed" },
    });
    const p = preview({
      preconditions: document.preconditions,
      operations: s.operations,
      draft_generation: s.generation,
    });
    s = reducer(s, { type: "preview", preview: p });
    s = reducer(s, { type: "ack", value: true });
    s = reducer(s, {
      type: "edit",
      operation: { op: "node.set_name", node_id: "sym", value: "Again" },
    });
    s = reducer(s, { type: "preview", preview: p });
    expect(s.preview).toBeNull();
    expect(s.acknowledged).toBe(false);
  });
  it("keeps false, zero, lists, null, absence and multiline text distinct", () => {
    expect(valueState({ v: 0 }, "v")).toBe("filled");
    expect(valueState({ v: false }, "v")).toBe("filled");
    expect(valueState({ v: [] }, "v")).toBe("empty");
    expect(valueState({ v: null }, "v")).toBe("empty");
    expect(valueState({}, "v")).toBe("missing");
    expect(valueState({ v: "Unknown" }, "v")).toBe("not_stated");
    expect(parseValue("0", "number")).toBe(0);
    expect(() => parseValue("oops", "number")).toThrow();
    expect(parseValue('["a,b","c"]', "array")).toEqual(["a,b", "c"]);
    expect(parseValue("[]", "array")).toEqual([]);
    expect(parseValue("a\nb", "string")).toBe("a\nb");
  });
  it("combines filters and retains a visible selection exception", () => {
    const f = {
      type: "Symptom",
      query: "noise",
      field: "count",
      state: "filled",
      exact: "0",
      links: "1",
      source: "no",
      modified: "no",
    };
    expect(
      filterNodes(document.graph, document.graph, f).rows.map((n) => n.id),
    ).toEqual(["sym"]);
    const result = filterNodes(
      document.graph,
      document.graph,
      { ...f, query: "no result" },
      "sym",
    );
    expect(result.exception?.id).toBe("sym");
    expect(result.rows).toHaveLength(1);
    expect(
      indices(document.graph, document.ontology).edges.get("sym"),
    ).toHaveLength(1);
  });
  it("has no persistent draft and cannot mutate while saving", () => {
    let s = initialState(document);
    s = reducer(s, { type: "saving", value: true });
    expect(
      reducer(s, {
        type: "edit",
        operation: { op: "node.delete", node_id: "sym" },
      }),
    ).toBe(s);
    expect(reducer(s, { type: "reset" }).operations).toEqual([]);
  });
});

it("combines several column filters and expires validation across discarded sessions", () => {
  const f = {
    query: "",
    type: "Symptom",
    field: "name",
    state: "",
    exact: "",
    links: "",
    source: "",
    modified: "",
    columns: {
      count: { state: "filled", exact: "0" },
      enabled: { state: "filled", exact: "false" },
    },
  };
  expect(
    filterNodes(document.graph, document.graph, f).rows.map((n) => n.id),
  ).toEqual(["sym"]);
  expect(
    filterNodes(document.graph, document.graph, {
      ...f,
      columns: { ...f.columns, description: { state: "empty", exact: "" } },
    }).rows,
  ).toEqual([]);
  const old = preview({
    preconditions: document.preconditions,
    operations: [],
    draft_generation: 0,
  });
  const s = reducer(initialState(document), { type: "reset" });
  expect(reducer(s, { type: "preview", preview: old }).preview).toBeNull();
});
it("shows an explicit human decision after editing while expiring it on a later edit", () => {
  const edit = {
    op: "node.set_name",
    node_id: "sym",
    value: "Changed",
  } as const;
  const confirm = {
    op: "occurrence.confirm",
    edge_id: "edge",
    occurrence_id: "occ",
    content_hash: "new_hash",
    reason: "checked",
  } as const;
  let current = project(document.graph, [edit, confirm]);
  expect(current.edges[0].trusted).toBe(true);
  expect(current.edges[0].tier).toBeNull();
  expect(current.edges[0].occurrences[0].certificate).toBeUndefined();
  current = project(document.graph, [
    edit,
    confirm,
    { ...edit, value: "Again" },
  ]);
  expect(current.edges[0].trusted).toBe(false);
  expect(current.edges[0].occurrences[0].review?.status).toBe("pending");
});
