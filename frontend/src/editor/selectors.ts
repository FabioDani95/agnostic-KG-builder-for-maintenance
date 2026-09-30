// Adapted from kg-graph-editor_V1/app.js: indexed fields, adjacency and value states.
import type { Graph, GraphNode, Ontology } from "../api/types";
export type ValueState = "missing" | "empty" | "filled" | "not_stated";
export function valueState(
  properties: Record<string, unknown>,
  field: string,
): ValueState {
  if (!(field in properties)) return "missing";
  const value = properties[field];
  if (
    value == null ||
    value === "" ||
    (typeof value === "string" && !value.trim()) ||
    (Array.isArray(value) && !value.length)
  )
    return "empty";
  if (
    typeof value === "string" &&
    ["not_stated", "unknown"].includes(value.toLowerCase())
  )
    return "not_stated";
  return "filled";
}
export function indices(graph: Graph, ontology: Ontology) {
  const nodes = new Map(graph.nodes.map((n) => [n.id, n]));
  const fields = new Map(
    ontology.nodes.map((t) => [t.name, t.properties.map((p) => p.name)]),
  );
  const fieldSets = new Map(
    [...fields].map(([type, values]) => [type, new Set(values)]),
  );
  graph.nodes.forEach((n) => {
    const set = fieldSets.get(n.type);
    if (set) Object.keys(n.properties).forEach((f) => set.add(f));
  });
  fieldSets.forEach((set, type) => fields.set(type, [...set]));
  const edges = new Map(graph.nodes.map((n) => [n.id, [] as Graph["edges"]]));
  graph.edges.forEach((e) => {
    edges.get(e.from)?.push(e);
    if (e.from !== e.to) edges.get(e.to)?.push(e);
  });
  return { nodes, fields, edges };
}
export interface NodeFilters {
  query: string;
  type: string;
  field: string;
  state: string;
  exact: string;
  links: string;
  source: string;
  modified: string;
  columns?: Record<string, { state: string; exact: string }>;
}
export function filterNodes(
  graph: Graph,
  base: Graph,
  f: NodeFilters,
  selected?: string,
) {
  const old = new Map(base.nodes.map((n) => [n.id, JSON.stringify(n)]));
  const counts = new Map<string, number>();
  graph.edges
    .filter((e) => !e.derived)
    .forEach((e) => {
      counts.set(e.from, (counts.get(e.from) ?? 0) + 1);
      counts.set(e.to, (counts.get(e.to) ?? 0) + 1);
    });
  const matches = (n: GraphNode) => {
    const count = counts.get(n.id) ?? 0;
    return (
      (!f.type || f.type === "all" || n.type === f.type) &&
      JSON.stringify(n).toLowerCase().includes(f.query.toLowerCase()) &&
      (!f.state || valueState(n.properties, f.field) === f.state) &&
      (!f.exact || String(n.properties[f.field]) === f.exact) &&
      Object.entries(f.columns ?? {}).every(
        ([field, filter]) =>
          (!filter.state || valueState(n.properties, field) === filter.state) &&
          (!filter.exact || String(n.properties[field]) === filter.exact),
      ) &&
      (!f.links ||
        (f.links === "2+" ? count >= 2 : count === Number(f.links))) &&
      (!f.source || (f.source === "yes") === Boolean(n.evidence.length)) &&
      (!f.modified ||
        (f.modified === "yes") === (old.get(n.id) !== JSON.stringify(n)))
    );
  };
  const rows = graph.nodes.filter(matches);
  const exception = graph.nodes.find((n) => n.id === selected && !matches(n));
  return { rows: exception ? [exception, ...rows] : rows, exception, counts };
}
