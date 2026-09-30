import type {
  EditorDocument,
  Graph,
  EditPreview,
  EditInput,
  Version,
} from "../src/api/types";
import { project } from "../src/editor/reducer";
export const version: Version = {
  version_id: "runs~v3_r1",
  origin: "campaign",
  kind: "run",
  iteration: "",
  run: "v3_r1",
  repetition: 1,
  date: "2026-09-30",
  commit: "abc",
  verified: 1,
  doubtful: 0,
  excluded: 0,
  open_questions: 0,
  status: "approved",
  decided_by: "auto",
  cost_usd: 0,
  seconds: 1,
  pages: 1,
  replay: true,
  copied_from: null,
  can_edit: true,
};
export const graph: Graph = {
  version: "kg-v3-graph-2",
  status: "approved",
  source_title: "Fixture",
  nodes: [
    {
      id: "asset",
      type: "Asset",
      name: "Pump",
      properties: { name: "Pump", asset_id: "asset" },
      evidence: [],
    },
    {
      id: "sym",
      type: "Symptom",
      name: "Noise",
      properties: {
        name: "Noise",
        description: "Loud noise",
        count: 0,
        enabled: false,
        list: [],
      },
      evidence: [],
    },
    {
      id: "cause",
      type: "FailureMode",
      name: "Wear",
      properties: { name: "Wear", description: "Wear" },
      evidence: [],
    },
  ],
  edges: [
    {
      id: "edge",
      type: "MAY_INDICATE",
      from: "sym",
      to: "cause",
      tier: "green",
      trusted: true,
      conditions: [],
      occurrences: [
        {
          id: "occ",
          record: "r",
          content_hash: "content",
          tier: "green",
          trusted: true,
          evidence: [
            {
              segment_id: "seg",
              page: 1,
              bbox: null,
              text: "Noise means wear",
            },
          ],
        },
      ],
    },
  ],
  excluded_relations: [],
};
export const document: EditorDocument = {
  graph,
  preconditions: {
    base_hash: "base",
    ontology_hash: "schema",
    source_token: "source",
    source_review_hash: "review",
  },
  ontology: {
    root: "Asset",
    nodes: [
      {
        name: "Asset",
        description: "",
        properties: [
          { name: "asset_id", type: "string", required: true },
          { name: "name", type: "string", required: true },
        ],
      },
      {
        name: "Symptom",
        description: "",
        properties: [
          { name: "name", type: "string", required: true },
          { name: "description", type: "string", required: true },
          { name: "count", type: "number", required: false },
          { name: "enabled", type: "boolean", required: false },
          { name: "list", type: "array", items: "string", required: false },
        ],
      },
      {
        name: "FailureMode",
        description: "",
        properties: [
          { name: "name", type: "string", required: true },
          { name: "description", type: "string", required: true },
        ],
      },
    ],
    relations: [
      {
        name: "MAY_INDICATE",
        domain: "Symptom",
        range: "FailureMode",
        description: "",
        added_by_code: false,
      },
    ],
  },
  capabilities: { can_edit: true, edit_reason: null },
  source: { pdf_available: false, segments_available: false },
  source_review: { version_id: version.version_id, questions: [] },
};
export function preview(body: EditInput): EditPreview {
  const current = project(graph, body.operations);
  const old = new Map(graph.nodes.map((n) => [n.id, n]));
  return {
    draft_generation: body.draft_generation,
    preview_hash: `hash_${body.draft_generation}`,
    has_changes: JSON.stringify(current) !== JSON.stringify(graph),
    can_accept: true,
    graph: current,
    diff: {
      nodes: {
        added: current.nodes.filter((n) => !old.has(n.id)),
        removed: graph.nodes.filter(
          (n) => !current.nodes.some((v) => v.id === n.id),
        ),
        updated: current.nodes
          .filter(
            (n) =>
              old.has(n.id) &&
              JSON.stringify(old.get(n.id)) !== JSON.stringify(n),
          )
          .map((n) => ({
            id: n.id,
            before: old.get(n.id)!,
            after: n,
            fields: ["name", "properties"],
          })),
      },
      edges: { added: [], removed: [], updated: [] },
    },
    issues: [
      {
        id: "doubt",
        code: "UNVERIFIED_CONTENT",
        severity: "warning",
        target: { kind: "edge", id: "edge" },
        introduced: true,
        message_key: "UNVERIFIED_CONTENT",
        message_params: {},
      },
    ],
    required_acknowledgements: ["doubt"],
  };
}
