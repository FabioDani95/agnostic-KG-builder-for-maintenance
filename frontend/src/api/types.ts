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

interface VersionFields {
  parent_version_id?: string | null;
  root_run_id?: string | null;
  revision_number?: number | null;
  can_edit?: boolean;
  edit_reason?: string | null;
  can_approve?: boolean;
  can_replay?: boolean;
  can_resume?: boolean;
  version_id: string;
  origin: "campaign" | "workspace";
  iteration: string;
  run: string;
  repetition: number | null;
  date: string | null;
  commit: string;
  verified: number;
  human_confirmed?: number;
  rejected?: number;
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

export interface RunVersion extends VersionFields { kind?: "run" }
export interface RevisionVersion extends VersionFields {
  kind: "revision"; parent_version_id: string; root_run_id: string; revision_number: number;
  status: "approved"; decided_by: "human"; cost_usd: 0; seconds: null; replay: false;
  can_approve: false; can_replay: false; can_resume: false;
}
export type Version = RunVersion | RevisionVersion;

export interface ManualRow {
  id: string;
  origin: "campaign" | "workspace";
  machine: Machine;
  pages: number | null;
  versions: number;
  latest: Version | null;
  activities?: Version[];
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
  cite?: string[];
  scope?: "relation" | "section";
}

export interface Occurrence {
  record: string;
  id?: string;
  content_hash?: string;
  annotation?: string;
  trusted?: boolean;
  review?: HumanReview;
  tier?: Tier | null;
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
  tier: Tier | null;
  review?: HumanReview;
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

/** One row of the run log (/api/runs): a version with the manual it belongs to. */
export interface RunRow extends RunVersion {
  manual_id: string;
  machine: Machine;
}

export interface ActiveJob {
  run: string | null; // "<manual>/runs/<run>", relative to the workspace
}

export interface OntologyNode {
  name: string;
  description: string;
  properties: FieldDescriptor[];
}

export interface OntologyRelation {
  name: string;
  domain: string;
  range: string;
  description: string;
  added_by_code: boolean;
}

export interface Ontology {
  root: string;
  nodes: OntologyNode[];
  relations: OntologyRelation[];
}

/** The machine read from the first pages of an upload (/api/uploads/{id}/machine). */
export interface Identified {
  machine: Machine;
  model: string;
  seconds: number;
  cost_usd: number;
  read: "text" | "cover";
  cached: boolean;
}

export type Reasoning = "none" | "low" | "medium" | "high";

/** Settings of the interface (/api/settings); the key itself never comes back, only where it is from. */
export interface Preferences {
  reasoning: Reasoning;
  reads: number;
  agent_model: string;
  agent_reasoning: Reasoning;
  human_questions: number;
  show_code_relations: boolean;
  node_labels: boolean;
  key: { source: "custom" | "env" | "none"; hint: string | null };
  choices: { reasoning: Reasoning[]; agent_models: string[] };
}

export interface FieldDescriptor { name: string; required: boolean; type?: string; items?: string | {type: string}; unique?: boolean }
export interface HumanReview { status: "pending" | "confirmed" | "rejected"; author?: string; date?: string; reason?: string; content_hash?: string }
export interface Preconditions { base_hash: string; ontology_hash: string; source_token: string; source_review_hash: string }
export type OccurrenceInput = { conditions: Condition[]; segment_ids: string[]; annotation: string };
export type EditOperation =
  | {op: "node.add"; temp_id: string; node_type: string; name: string; properties: Record<string, unknown>}
  | {op: "node.set_name"; node_id: string; value: string}
  | {op: "node.set_property"; node_id: string; field: string; value: unknown}
  | {op: "node.remove_property"; node_id: string; field: string}
  | {op: "node.set_aliases"; node_id: string; values: string[]}
  | {op: "node.delete"; node_id: string}
  | {op: "edge.add"; temp_id: string; relation_type: string; from: string; to: string; occurrences: OccurrenceInput[]}
  | {op: "edge.replace_endpoints"; edge_id: string; replacement_temp_id: string; relation_type: string; from: string; to: string}
  | {op: "edge.delete"; edge_id: string}
  | ({op: "occurrence.add" | "occurrence.update"; edge_id: string; occurrence_id: string} & OccurrenceInput)
  | {op: "occurrence.delete"; edge_id: string; occurrence_id: string}
  | {op: "occurrence.confirm" | "occurrence.reject"; edge_id: string; occurrence_id: string; content_hash: string; reason: string};
export interface Issue { id: string; code: string; severity: "error" | "warning"; target: {kind: string; id?: string; field?: string}; introduced: boolean; message_key: string; message_params: Record<string, string | number> }
export interface DiffGroup<T> { added: T[]; removed: T[]; updated: {id: string; before: T; after: T; fields: string[]}[] }
export interface GraphDiff { nodes: DiffGroup<GraphNode>; edges: DiffGroup<GraphEdge> }
export interface EditInput { preconditions: Preconditions; operations: EditOperation[]; draft_generation: number }
export interface EditPreview { draft_generation: number; preview_hash: string; has_changes: boolean; can_accept: boolean; diff: GraphDiff; issues: Issue[]; required_acknowledgements: string[]; graph: Graph }
export interface EditorDocument { graph: Graph; preconditions: Preconditions; ontology: Ontology; capabilities: {can_edit: boolean; edit_reason: string | null}; source: {pdf_available: boolean; segments_available: boolean}; source_review: {version_id: string; questions?: {question_id: string}[]} }
export interface AcceptRevision extends EditInput { request_id: string; preview_hash: string; note: string; acceptance: {decision: "accept_changes"; acknowledged_issue_ids: string[]} }
export interface RevisionCreated { version: RevisionVersion; parent_version_id: string; graph_hash: string; request_id: string; id_map: Record<string, string> }
export type RevisionRequest = {status: "saved"; result: RevisionCreated} | {status: "not_found" | "in_progress"};
