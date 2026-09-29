// Interface events of a run (backend/ui/events.py), live or replayed.
import type { Tier } from "../api/types";

export interface UiEvent {
  seq: number;
  t: number;
  cost_usd: number;
  kind: string;
  data: Record<string, unknown>;
}

export interface LiveNode {
  id: string;
  type: string;
  name: string;
  pages?: number[];
}

export interface LiveEdge {
  id: string;
  type: string;
  from: string;
  to: string;
  pages?: number[];
  tier: Tier | null;
  derived?: boolean;
}

export const STATIONS = ["read", "map", "extract", "check", "merge", "ask"] as const;
export type Station = (typeof STATIONS)[number];
