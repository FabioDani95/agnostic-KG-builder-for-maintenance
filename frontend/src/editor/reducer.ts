import type {
  EditorDocument,
  EditOperation,
  EditPreview,
  Graph,
} from "../api/types";
export type Selection = {
  kind: "node" | "edge";
  id: string;
  field?: string;
} | null;
export interface EditorState {
  epoch: number;
  document: EditorDocument;
  operations: EditOperation[];
  past: { operations: EditOperation[]; selection: Selection }[];
  future: { operations: EditOperation[]; selection: Selection }[];
  generation: number;
  preview: EditPreview | null;
  selection: Selection;
  acknowledged: boolean;
  pending: boolean;
  saving: boolean;
}
export const initialState = (document: EditorDocument): EditorState => ({
  epoch: 0,
  document,
  operations: [],
  past: [],
  future: [],
  generation: 0,
  preview: null,
  selection: null,
  acknowledged: false,
  pending: false,
  saving: false,
});
export type Action =
  | { type: "edit"; operation: EditOperation }
  | { type: "undo" | "redo" | "reset" | "stale" }
  | { type: "preview"; preview: EditPreview }
  | { type: "select"; selection: Selection }
  | { type: "ack" | "pending" | "saving"; value: boolean };
export function reducer(state: EditorState, action: Action): EditorState {
  if (action.type === "reset")
    return {
      ...initialState(state.document),
      epoch: state.epoch + 1,
      generation: state.generation + 1,
    };
  if (action.type === "stale")
    // A rejected acceptance makes the preview unusable: checks must run again.
    return {
      ...state,
      generation: state.generation + 1,
      preview: null,
      acknowledged: false,
    };
  if (action.type === "select")
    return { ...state, selection: action.selection };
  if (action.type === "preview")
    return action.preview.draft_generation === state.generation
      ? { ...state, preview: action.preview }
      : state;
  if (action.type === "ack") return { ...state, acknowledged: action.value };
  if (action.type === "pending") return { ...state, pending: action.value };
  if (action.type === "saving") return { ...state, saving: action.value };
  if (state.saving) return state;
  const invalidated = {
    ...state,
    generation: state.generation + 1,
    preview: null,
    acknowledged: false,
  };
  if (action.type === "edit")
    return {
      ...invalidated,
      past: [
        ...state.past,
        { operations: state.operations, selection: state.selection },
      ],
      future: [],
      operations: [...state.operations, action.operation],
    };
  const source = action.type === "undo" ? state.past : state.future;
  if (!source.length) return state;
  const snapshot = source[source.length - 1];
  const current = { operations: state.operations, selection: state.selection };
  return {
    ...invalidated,
    ...snapshot,
    past:
      action.type === "undo" ? source.slice(0, -1) : [...state.past, current],
    future:
      action.type === "redo" ? source.slice(0, -1) : [...state.future, current],
  };
}
function lastIndex<T>(values: T[], predicate: (value: T) => boolean) {
  for (let index = values.length - 1; index >= 0; index--)
    if (predicate(values[index])) return index;
  return -1;
}
/** Projection for immediate editing feedback. Server alone calculates certificates, trust and final diff. */
export function project(base: Graph, operations: EditOperation[]): Graph {
  const graph: Graph = structuredClone(base);
  for (const o of operations) {
    const node =
      "node_id" in o ? graph.nodes.find((n) => n.id === o.node_id) : undefined;
    const edge =
      "edge_id" in o ? graph.edges.find((e) => e.id === o.edge_id) : undefined;
    switch (o.op) {
      case "node.add":
        graph.nodes.push({
          id: o.temp_id,
          type: o.node_type,
          name: o.name,
          properties: { ...o.properties, name: o.name },
          evidence: [],
        });
        break;
      case "node.set_name":
        if (node) node.name = String((node.properties.name = o.value));
        break;
      case "node.set_property":
        if (node) node.properties[o.field] = o.value;
        break;
      case "node.remove_property":
        if (node) delete node.properties[o.field];
        break;
      case "node.set_aliases":
        if (node) node.aliases = o.values;
        break;
      case "node.delete":
        graph.nodes = graph.nodes.filter((n) => n.id !== o.node_id);
        graph.edges = graph.edges.filter(
          (e) => e.from !== o.node_id && e.to !== o.node_id,
        );
        break;
      case "edge.add":
        graph.edges.push({
          id: o.temp_id,
          type: o.relation_type,
          from: o.from,
          to: o.to,
          tier: null,
          trusted: false,
          conditions: [],
          occurrences: o.occurrences.map((v, i) => ({
            id: `${o.temp_id}_${i}`,
            record: "human",
            ...v,
            evidence: [],
            review: { status: "pending" },
          })),
        });
        break;
      case "edge.replace_endpoints":
        if (edge) {
          edge.id = o.replacement_temp_id;
          edge.type = o.relation_type;
          edge.from = o.from;
          edge.to = o.to;
          edge.tier = null;
          edge.trusted = false;
          edge.occurrences.forEach((v) => {
            v.tier = null;
            delete v.certificate;
            v.review = { status: "pending" };
          });
        }
        break;
      case "edge.delete":
        graph.edges = graph.edges.filter((e) => e.id !== o.edge_id);
        break;
      case "occurrence.add":
        if (edge)
          edge.occurrences.push({
            id: o.occurrence_id,
            record: "human",
            conditions: o.conditions,
            annotation: o.annotation,
            evidence: [],
            tier: null,
            review: { status: "pending" },
          });
        break;
      case "occurrence.update":
        if (edge) {
          const occ = edge.occurrences.find((v) => v.id === o.occurrence_id);
          if (occ) {
            occ.conditions = o.conditions;
            occ.annotation = o.annotation;
            occ.evidence = occ.evidence.filter((e) =>
              o.segment_ids.includes(e.segment_id),
            );
            occ.tier = null;
            delete occ.certificate;
            occ.review = { status: "pending" };
          }
        }
        break;
      case "occurrence.delete":
        if (edge) {
          edge.occurrences = edge.occurrences.filter(
            (v) => v.id !== o.occurrence_id,
          );
          if (!edge.occurrences.length)
            graph.edges = graph.edges.filter((e) => e.id !== edge.id);
        }
        break;
      case "occurrence.confirm":
      case "occurrence.reject":
        if (edge) {
          const occ = edge.occurrences.find((v) => v.id === o.occurrence_id);
          if (occ)
            occ.review = {
              status: o.op === "occurrence.confirm" ? "confirmed" : "rejected",
              content_hash: o.content_hash,
            };
        }
        break;
    }
  }
  const old = new Map(base.nodes.map((n) => [n.id, n]));
  const changed = new Set(
    graph.nodes
      .filter((n) => JSON.stringify(n) !== JSON.stringify(old.get(n.id)))
      .map((n) => n.id),
  );
  // Only edges an operation touched are re-derived: untouched edges keep tier and trust as loaded.
  const touched = new Set<string>();
  for (const o of operations) {
    if ("edge_id" in o) touched.add(o.edge_id);
    if (o.op === "edge.add") touched.add(o.temp_id);
    if (o.op === "edge.replace_endpoints") touched.add(o.replacement_temp_id);
  }
  for (const e of graph.edges) {
    if (e.derived) continue;
    const incident = changed.has(e.from) || changed.has(e.to);
    if (!incident && !touched.has(e.id)) continue;
    if (incident) {
      e.tier = null;
      for (const v of e.occurrences) {
        v.tier = null;
        delete v.certificate;
        v.review = { status: "pending" };
        // A decision made after the last content edit remains visible until the server validates its hash.
        const decision = lastIndex(
          operations,
          (o) =>
            (o.op === "occurrence.confirm" || o.op === "occurrence.reject") &&
            o.edge_id === e.id &&
            o.occurrence_id === v.id,
        );
        const content = lastIndex(
          operations,
          (o) =>
            ("node_id" in o && [e.from, e.to].includes(o.node_id)) ||
            ("edge_id" in o &&
              o.edge_id === e.id &&
              (o.op === "edge.replace_endpoints" ||
                (o.op === "occurrence.update" && o.occurrence_id === v.id))),
        );
        if (decision > content) {
          const o = operations[decision];
          if (o.op === "occurrence.confirm" || o.op === "occurrence.reject")
            v.review = {
              status: o.op === "occurrence.confirm" ? "confirmed" : "rejected",
              content_hash: o.content_hash,
            };
        }
      }
    }
    e.occurrences.forEach((v) => {
      v.trusted =
        v.review?.status !== "rejected" &&
        (v.tier === "green" || v.review?.status === "confirmed");
    });
    e.trusted = e.occurrences.some((v) => v.trusted);
    const active = e.occurrences.filter((v) => v.review?.status !== "rejected");
    e.tier = active.some((v) => v.tier === "green")
      ? "green"
      : active.some((v) => v.tier === "yellow")
        ? "yellow"
        : null;
  }
  return graph;
}
export function dirty(state: EditorState) {
  if (state.preview) return state.preview.has_changes;
  return (
    JSON.stringify(project(state.document.graph, state.operations)) !==
    JSON.stringify(state.document.graph)
  );
}
