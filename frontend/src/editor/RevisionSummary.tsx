import type {
  EditPreview,
  Graph,
  GraphNode,
  GraphEdge,
  Issue,
} from "../api/types";
import { tr, useLang } from "../i18n/i18n";
import { RELATION_LABEL, TYPE_LABEL } from "../text/it";
import { fieldLabel } from "./fields";
import { issueText, targetLabel } from "./ReviewPanel";

/** A value as a person reads it: no JSON, no placeholders of the pipeline. */
function shown(value: unknown): string {
  if (value === undefined) return tr("Assente");
  if (value === null || value === "") return tr("Vuoto");
  if (Array.isArray(value))
    return value.length ? value.map(shown).join("; ") : tr("Lista vuota");
  if (typeof value === "boolean") return tr(value ? "Sì" : "No");
  if (
    typeof value === "string" &&
    ["not_stated", "unknown"].includes(value.toLowerCase())
  )
    return tr("Non dichiarato");
  return typeof value === "object" ? tr("Dato strutturato") : String(value);
}
function nodeChanges(before: GraphNode, after: GraphNode) {
  const rows: [string, unknown, unknown][] = [];
  if (before.name !== after.name) rows.push(["name", before.name, after.name]);
  const keys = new Set([
    ...Object.keys(before.properties),
    ...Object.keys(after.properties),
  ]);
  for (const key of keys)
    if (
      key !== "name" &&
      JSON.stringify(before.properties[key]) !==
        JSON.stringify(after.properties[key])
    )
      rows.push([key, before.properties[key], after.properties[key]]);
  if (
    JSON.stringify(before.aliases ?? []) !== JSON.stringify(after.aliases ?? [])
  )
    rows.push(["Nomi alternativi", before.aliases, after.aliases]);
  return rows;
}
function edgeName(graph: Graph, edge: GraphEdge) {
  const name = (id: string) =>
    graph.nodes.find((n) => n.id === id)?.name ?? "?";
  return `${name(edge.from)} → ${tr(RELATION_LABEL[edge.type] ?? edge.type)} → ${name(edge.to)}`;
}
function edgeChanges(before: GraphEdge, after: GraphEdge) {
  const changes: string[] = [];
  if (
    before.type !== after.type ||
    before.from !== after.from ||
    before.to !== after.to
  )
    changes.push("Relazione o estremi cambiati");
  if (
    JSON.stringify(
      before.occurrences.map((o) => [o.conditions, o.evidence, o.annotation]),
    ) !==
    JSON.stringify(
      after.occurrences.map((o) => [o.conditions, o.evidence, o.annotation]),
    )
  )
    changes.push("Condizioni, prove o note delle occorrenze modificate");
  if (
    JSON.stringify(before.occurrences.map((o) => o.review?.status)) !==
      JSON.stringify(after.occurrences.map((o) => o.review?.status)) ||
    before.trusted !== after.trusted
  )
    changes.push(after.trusted ? "Ora utilizzabile" : "Ora da verificare");
  return changes;
}
export function RevisionSummary({
  preview,
  base,
  baseGraph,
  note,
  onNote,
  acknowledged,
  onAck,
  onTarget,
}: {
  preview: EditPreview;
  base: string;
  baseGraph: Graph;
  note: string;
  onNote: (value: string) => void;
  acknowledged: boolean;
  onAck: (value: boolean) => void;
  onTarget: (kind: "node" | "edge", id: string, field?: string) => void;
}) {
  useLang();
  return (
    <section className="editor-summary">
      <h2>{tr("Riepilogo")}</h2>
      <p>{tr("Da {base}", { base })}</p>
      <p>
        {tr("Crea una nuova versione. Quella di partenza rimane invariata.")}
      </p>
      <p>
        {tr(
          "Accettare le modifiche non verifica automaticamente le relazioni.",
        )}
      </p>
      {!preview.has_changes && <p>{tr("Nessuna modifica da salvare")}</p>}
      {(
        [
          ["nodes", "Nodi", "node"],
          ["edges", "Relazioni", "edge"],
        ] as const
      ).map(([group, label, kind]) => (
        <div className="card editor-diff" key={group}>
          <h3>{tr(label)}</h3>
          {(
            [
              ["added", "Aggiunte"],
              ["removed", "Rimozioni"],
              ["updated", "Modifiche"],
            ] as const
          ).map(([key, label]) => (
            <section key={key}>
              <h4>
                {tr(label)} ({preview.diff[group][key].length})
              </h4>
              {preview.diff[group][key].map((item) => {
                const updated = "before" in item;
                const after = (updated ? item.after : item) as GraphNode &
                  GraphEdge;
                const graph = key === "removed" ? baseGraph : preview.graph;
                const label =
                  kind === "node"
                    ? `${after.name} (${tr(TYPE_LABEL[after.type] ?? after.type)})`
                    : edgeName(graph, after);
                return (
                  <div className="editor-diff-row" key={item.id}>
                    <button
                      className="button button-plain"
                      disabled={key === "removed"}
                      onClick={() => onTarget(kind, item.id)}
                    >
                      {key === "removed"
                        ? label
                        : `${tr("Torna a modificare")} · ${label}`}
                    </button>
                    {updated &&
                      kind === "node" &&
                      nodeChanges(
                        item.before as GraphNode,
                        item.after as GraphNode,
                      ).map(([field, b, a]) => (
                        <div key={field}>
                          <strong>{fieldLabel(field)}</strong>
                          <div className="editor-before-after">
                            <p>{shown(b)}</p>
                            <p>{shown(a)}</p>
                          </div>
                        </div>
                      ))}
                    {updated && kind === "edge" && (
                      <ul>
                        {edgeChanges(
                          item.before as GraphEdge,
                          item.after as GraphEdge,
                        ).map((c) => (
                          <li key={c}>{tr(c)}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                );
              })}
            </section>
          ))}
        </div>
      ))}
      <h3>{tr("Dubbi residui")}</h3>
      <ul>
        {preview.issues
          .filter((i) => preview.required_acknowledgements.includes(i.id))
          .map((i: Issue) => (
            <li key={i.id}>
              {issueText(i)} · {targetLabel(preview.graph, i)}
            </li>
          ))}
      </ul>
      {preview.required_acknowledgements.length > 0 && (
        <label className="editor-ack">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(e) => onAck(e.target.checked)}
          />
          {tr("Accetto la nuova versione con i dubbi residui elencati")}
        </label>
      )}
      <label>
        {tr("Nota facoltativa")}
        <textarea value={note} onChange={(e) => onNote(e.target.value)} />
      </label>
    </section>
  );
}
