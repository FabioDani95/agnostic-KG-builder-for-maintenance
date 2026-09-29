// Shapes of the local API (backend/ui/api.py). Written by hand, kept small.

export interface Machine {
  name: string;
  brand: string;
  model: string;
  type: string;
}

export type RunStatus =
  | "approved"
  | "awaiting_approval"
  | "incomplete"
  | "rejected"
  | "failed"
  | "running";

export interface Version {
  version_id: string;
  origin: "campaign" | "workspace";
  iteration: string;
  run: string;
  repetition: number | null;
  date: string | null;
  commit: string;
  verified: number;
  doubtful: number;
  excluded: number;
  open_questions: number;
  status: RunStatus;
  decided_by: string | null;
  cost_usd: number | null;
  seconds: number | null;
  pages: number | null;
  replay: boolean;
  copied_from: string | null;
}

export interface ManualRow {
  id: string;
  origin: "campaign" | "workspace";
  machine: Machine;
  pages: number | null;
  versions: number;
  latest: Version | null;
}

export interface Manual {
  id: string;
  origin: "campaign" | "workspace";
  machine: Machine;
  pages: number | null;
  versions: Version[];
}

export type Tier = "green" | "yellow" | "red";

export interface Evidence {
  segment_id: string;
  page: number;
  evidence_id?: string;
  bbox: [number, number, number, number] | null;
  text: string;
}

export interface Reviewer {
  kind: string;
  name: string;
}

export interface Certificate {
  segment_ids: string[];
  witnesses: string[];
  verifier_verdict: string | null;
  confirmed_by: Reviewer | null;
  rejected_by: Reviewer | null;
  notes: string[];
}

export interface Condition {
  kind: string;
  text: string;
}

export interface Occurrence {
  record: string;
  tier?: Tier;
  conditions?: Condition[];
  certificate?: Certificate;
  evidence: Evidence[];
}

export interface GraphNode {
  id: string;
  type: string;
  name: string;
  aliases?: string[];
  stated_in_source?: boolean;
  properties: Record<string, unknown>;
  evidence: Evidence[];
}

export interface GraphEdge {
  id: string;
  type: string;
  from: string;
  to: string;
  tier: Tier;
  trusted: boolean;
  derived?: boolean;
  conditions: Condition[];
  occurrences: Occurrence[];
}

export interface Graph {
  version: string;
  status: RunStatus;
  source_title: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  excluded_relations: unknown[];
}

export interface Budget {
  committed_usd: number;
  reserved_usd: number;
  ceiling_usd: number;
  budget_usd: number;
  ui_limit_usd: number;
  ui_spent_usd: number;
}

export interface Estimate {
  seconds: [number, number] | null;
  cost_usd: [number, number] | null;
  based_on: string[];
  note: string;
}

export interface Segment {
  segment_id: string;
  page: number;
  bbox: [number, number, number, number] | null;
  text: string;
}

export interface Upload {
  upload_id: string;
  file_name: string;
  pages: number;
  size_bytes: number;
  duplicate_of: string | null;
  machine: Machine | null;
}

export interface QuestionOption {
  option_id: string;
  label_it: string;
  needs_statements: boolean;
  needs_text: boolean;
}

export interface QuestionView {
  question_id: string;
  kind: string;
  title_it: string;
  source: { segment_id: string; page: number; text: string }[];
  claims_it: string[];
  proposal: string[];
  options: QuestionOption[];
  default_option_id: string;
  priority: number;
  answer?: { option_id: string; text: string; keep: number[] };
}

export interface Questions {
  budget: number;
  editable: boolean;
  copy_needed: boolean;
  open: QuestionView[];
  answered: QuestionView[];
  unverified: QuestionView[];
  unapplied: number;
  awaiting_approval: boolean;
  can_approve: boolean;
}
