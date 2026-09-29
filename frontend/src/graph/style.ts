// Meaning carried by color, only inside the graph (docs/DESIGN.md, section 4).
import type { Tier } from "../api/types";

export const NODE_TYPES = ["Asset", "Symptom", "ErrorCode", "FailureMode", "CorrectiveAction", "Component"] as const;

export const NODE_STYLE: Record<string, { color: string; radius: number }> = {
  Asset: { color: "#f5f5f7", radius: 3 },
  Symptom: { color: "#ff9f0a", radius: 2 },
  ErrorCode: { color: "#ff6482", radius: 2 },
  FailureMode: { color: "#bf5af2", radius: 1.5 },
  CorrectiveAction: { color: "#64d2ff", radius: 1.5 },
  Component: { color: "#8e8e93", radius: 1 },
};

export type EdgeLook = "proposed" | "green" | "yellow" | "derived";

export const EDGE_STYLE: Record<EdgeLook, { color: string; opacity: number; dashed: boolean }> = {
  proposed: { color: "#636366", opacity: 0.5, dashed: false },
  green: { color: "#30d158", opacity: 0.9, dashed: false },
  yellow: { color: "#ffd60a", opacity: 0.9, dashed: true },
  derived: { color: "#636366", opacity: 0.35, dashed: false },
};

export const DIMMED = 0.15;

export function edgeLook(tier: Tier | null | undefined, derived = false): EdgeLook | null {
  if (derived) return "derived";
  if (tier === "red") return null; // excluded relations are not drawn
  return tier ?? "proposed";
}
