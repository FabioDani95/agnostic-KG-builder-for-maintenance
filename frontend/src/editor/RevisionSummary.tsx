import type { EditPreview, GraphNode, GraphEdge, Issue } from "../api/types";
import { tr, useLang } from "../i18n/i18n";
import { issueText } from "./ReviewPanel";
export function RevisionSummary({
  preview,
  base,
  note,
  onNote,
  acknowledged,
  onAck,
  onTarget,
}: {
  preview: EditPreview;
  base: string;
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
                const before = updated ? item.before : null;
                const after = updated ? item.after : item;
                const id = item.id;
                return (
                  <div className="editor-diff-row" key={id}>
                    <button
                      className="button button-plain"
                      disabled={key === "removed"}
                      onClick={() => onTarget(kind, id)}
                    >
                      {tr("Torna a modificare")} ·{" "}
                      {(after as GraphNode).name ?? (after as GraphEdge).type} ·{" "}
                      {id}
                    </button>
                    {updated &&
                      item.fields.map((field) => (
                        <div key={field}>
                          <strong>{field}</strong>
                          <div className="editor-before-after">
                            <pre>
                              {JSON.stringify(
                                (before as unknown as Record<string, unknown>)[
                                  field
                                ],
                                null,
                                2,
                              ) ?? tr("Assente")}
                            </pre>
                            <pre>
                              {JSON.stringify(
                                (after as unknown as Record<string, unknown>)[
                                  field
                                ],
                                null,
                                2,
                              ) ?? tr("Assente")}
                            </pre>
                          </div>
                        </div>
                      ))}
                    {!updated && (
                      <details>
                        <summary>{tr("Dettagli")}</summary>
                        <pre>{JSON.stringify(after, null, 2)}</pre>
                      </details>
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
              {issueText(i)} · {i.target.id ?? i.message_params.question_id}
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
