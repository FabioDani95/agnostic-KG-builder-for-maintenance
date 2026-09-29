// State of a run built from its events: a pure function, tested with recorded sequences.
import type { Tier } from "../api/types";
import { type LiveEdge, type LiveNode, STATIONS, type Station, type UiEvent } from "./events";

export type StationPhase = "waiting" | "running" | "done";

export interface RunSummary {
  status: string;
  verified: number;
  doubtful: number;
  excluded: number;
  open_questions: number;
}

export interface RunState {
  seq: number;
  t: number;
  cost: number;
  costEstimated: boolean;
  mode: string | null;
  pages: number | null;
  stations: Record<Station, { phase: StationPhase; step: string | null }>;
  readPages: number | null; // pages the map sends to reading
  units: { done: number; total: number };
  merges: number;
  agentAnswers: number;
  nodes: Record<string, LiveNode>;
  edges: Record<string, LiveEdge>;
  recent: string[]; // edge IDs, latest change first
  finished: RunSummary | null;
  failed: string | null;
}

export const RECENT_LIMIT = 200;

export function initialRun(): RunState {
  return {
    seq: 0,
    t: 0,
    cost: 0,
    costEstimated: false,
    mode: null,
    pages: null,
    stations: Object.fromEntries(STATIONS.map((station) => [station, { phase: "waiting", step: null }])) as RunState["stations"],
    readPages: null,
    units: { done: 0, total: 0 },
    merges: 0,
    agentAnswers: 0,
    nodes: {},
    edges: {},
    recent: [],
    finished: null,
    failed: null,
  };
}

function touch(recent: string[], ids: string[]): string[] {
  const moved = new Set(ids);
  return [...ids.slice().reverse(), ...recent.filter((id) => !moved.has(id))].slice(0, RECENT_LIMIT);
}

function addNodes(nodes: Record<string, LiveNode>, added: unknown): Record<string, LiveNode> {
  const list = (added as LiveNode[] | undefined) ?? [];
  if (!list.length) return nodes;
  const next = { ...nodes };
  for (const node of list) next[node.id] = { ...next[node.id], ...node };
  return next;
}

export function runReducer(state: RunState, event: UiEvent): RunState {
  if (event.seq <= state.seq && event.kind !== "run_started") return state;
  const base = { ...state, seq: Math.max(state.seq, event.seq), t: Math.max(state.t, event.t), cost: Math.max(state.cost, event.cost_usd) };
  const data = event.data;
  switch (event.kind) {
    case "run_started": {
      const fresh = data.mode === "resume" ? base : { ...initialRun(), seq: event.seq, t: event.t };
      return {
        ...fresh,
        mode: (data.mode as string) ?? null,
        pages: (data.pages as number | null) ?? fresh.pages,
        costEstimated: Boolean(data.cost_estimated),
        finished: null,
        failed: null,
      };
    }
    case "station": {
      const station = data.station as Station;
      const phase = data.state === "running" ? "running" : "done";
      const units =
        station === "extract" && typeof data.total === "number"
          ? { done: (data.done as number) ?? 0, total: data.total as number }
          : base.units;
      return {
        ...base,
        units,
        stations: { ...base.stations, [station]: { phase, step: (data.step as string) ?? base.stations[station].step } },
      };
    }
    case "pages_mapped": {
      const pages = (data.pages as { label: string }[]) ?? [];
      return {
        ...base,
        pages: base.pages ?? pages.length,
        readPages: pages.filter((page) => page.label === "diagnostic").length,
      };
    }
    case "units_planned":
      return { ...base, units: { done: 0, total: ((data.units as unknown[]) ?? []).length } };
    case "unit_extracted": {
      const edges = { ...base.edges };
      const added = (data.edges as LiveEdge[]) ?? [];
      for (const edge of added) edges[edge.id] = { ...edge, tier: edge.tier ?? null };
      return {
        ...base,
        units: { done: data.index as number, total: data.total as number },
        nodes: addNodes(base.nodes, data.nodes),
        edges,
        recent: touch(base.recent, added.map((edge) => edge.id)),
      };
    }
    case "relations_checked": {
      const edges = { ...base.edges };
      const removed = new Set((data.removed as string[]) ?? []);
      for (const id of removed) delete edges[id];
      const changed: string[] = [];
      for (const edge of (data.edges as LiveEdge[]) ?? []) {
        const before = edges[edge.id];
        if (!before || before.tier !== edge.tier) changed.push(edge.id);
        edges[edge.id] = { ...before, ...edge };
      }
      return {
        ...base,
        nodes: addNodes(base.nodes, data.nodes),
        edges,
        recent: touch(base.recent.filter((id) => !removed.has(id)), changed),
      };
    }
    case "merged":
      return { ...base, merges: ((data.same as unknown[]) ?? []).length };
    case "questions": {
      const answered = (data.answered as { by: string }[]) ?? [];
      const agent = answered.filter((answer) => answer.by === "agent").length;
      return data.gate === "map" ? base : { ...base, agentAnswers: Math.max(base.agentAnswers, agent) };
    }
    case "graph_final": {
      const previous = base.nodes;
      const nodes: Record<string, LiveNode> = {};
      for (const node of (data.nodes as LiveNode[]) ?? []) nodes[node.id] = { ...previous[node.id], ...node };
      const into = (data.edges_into as Record<string, string>) ?? {};
      // Final edges keep the pages their provisional edges were found on.
      const pages: Record<string, number[]> = {};
      for (const [id, edge] of Object.entries(base.edges)) {
        const target = into[id] ?? id;
        pages[target] = [...new Set([...(pages[target] ?? []), ...(edge.pages ?? [])])].sort((a, b) => a - b);
      }
      const edges: Record<string, LiveEdge> = {};
      for (const edge of (data.edges as LiveEdge[]) ?? []) edges[edge.id] = { ...edge, pages: pages[edge.id] ?? [] };
      const recent = [...new Set(base.recent.map((id) => into[id] ?? id))].filter((id) => id in edges);
      return { ...base, nodes, edges, recent };
    }
    case "run_finished": {
      const stations = Object.fromEntries(
        STATIONS.map((station) => [
          station,
          { ...base.stations[station], phase: base.stations[station].phase === "waiting" ? "waiting" : "done" },
        ]),
      ) as RunState["stations"];
      return { ...base, stations, finished: data as unknown as RunSummary };
    }
    case "run_failed":
      return { ...base, failed: String(data.message ?? "") };
    default:
      return base;
  }
}

export function counts(state: RunState): { nodes: number; relations: number; verified: number } {
  const edges = Object.values(state.edges).filter((edge) => !edge.derived && edge.tier !== "red");
  return {
    nodes: Object.keys(state.nodes).length,
    relations: edges.length,
    verified: edges.filter((edge) => edge.tier === ("green" as Tier)).length,
  };
}
