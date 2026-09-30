import { useMemo, useState } from "react";
import type { EditPreview, Issue, Ontology } from "../api/types";
import { tr, useLang } from "../i18n/i18n";
import { valueState } from "./selectors";
export const ISSUE_TEXT: Record<string, string> = {
  DUPLICATE_ID: "ID duplicato",
  ROOT_COUNT: "Serve una sola macchina radice",
  NODE_TYPE: "Tipo di nodo non ammesso",
  REQUIRED_FIELD: "Campo obbligatorio assente o vuoto",
  NOT_STATED: "Valore non dichiarato",
  CANONICAL_ID: "ID della proprietà non coerente",
  CANONICAL_NAME: "Nome della proprietà non coerente",
  VALUE_TYPE: "Tipo del valore non valido",
  ISOLATED_NODE: "Nodo senza collegamenti diagnostici",
  CAUSE_WITHOUT_ACTION: "Causa senza azioni",
  PROBLEM_WITHOUT_CAUSE: "Sintomo o codice senza cause",
  NO_COMPATIBLE_ACTION_PATH:
    "Nessun percorso verso un’azione con condizioni compatibili",
  ORPHAN_EDGE: "Estremo della relazione mancante",
  ENDPOINT_TYPE: "Estremi incompatibili con la relazione",
  DUPLICATE_EDGE: "Relazione duplicata: aggiungi un’occorrenza",
  DERIVED_READ_ONLY: "Relazione aggiunta dal sistema: sola lettura",
  NO_OCCURRENCES: "Relazione senza occorrenze",
  UNVERIFIED_CONTENT: "Contenuto da verificare",
  NO_EVIDENCE: "Contenuto senza fonte collegata",
  SOURCE_QUESTION: "Domanda della fonte ancora aperta",
  SIMILAR_NAME: "Nomi simili: controlla senza unire automaticamente",
};
export function issueText(issue: Issue) {
  return `${tr(ISSUE_TEXT[issue.code] ?? issue.message_key)}${issue.target.field ? ` · ${issue.target.field}` : ""}`;
}
const GROUPS: Record<string, string[]> = {
  integrity: [
    "DUPLICATE_ID",
    "ROOT_COUNT",
    "NODE_TYPE",
    "CANONICAL_ID",
    "CANONICAL_NAME",
    "VALUE_TYPE",
    "ORPHAN_EDGE",
    "ENDPOINT_TYPE",
    "DERIVED_READ_ONLY",
    "NO_OCCURRENCES",
  ],
  links: [
    "ISOLATED_NODE",
    "CAUSE_WITHOUT_ACTION",
    "PROBLEM_WITHOUT_CAUSE",
    "NO_COMPATIBLE_ACTION_PATH",
  ],
  sources: ["UNVERIFIED_CONTENT", "NO_EVIDENCE", "SOURCE_QUESTION"],
  duplicates: ["DUPLICATE_EDGE", "SIMILAR_NAME"],
};
export function ReviewPanel({
  preview,
  ontology,
  onTarget,
  onRetry,
  checking,
}: {
  preview: EditPreview | null;
  ontology: Ontology;
  onTarget: (issue: Issue) => void;
  onRetry: () => void;
  checking: boolean;
}) {
  useLang();
  const [filter, setFilter] = useState("all");
  const fields = useMemo(
    () =>
      preview?.graph.nodes.flatMap((node) =>
        (
          ontology.nodes.find((t) => t.name === node.type)?.properties ?? []
        ).map((field) => ({
          node,
          field,
          state: valueState(node.properties, field.name),
        })),
      ) ?? [],
    [preview, ontology],
  );
  const [category, state] = filter.split(":");
  const fieldItems =
    category === "required" || category === "optional"
      ? fields.filter(
          (f) =>
            f.field.required === (category === "required") &&
            (!state || f.state === state),
        )
      : null;
  const shownIssues =
    preview?.issues.filter(
      (i) =>
        filter === "all" ||
        filter === i.severity ||
        GROUPS[filter]?.includes(i.code),
    ) ?? [];
  return (
    <section className="editor-review">
      <h2>{tr("Controlla")}</h2>
      <p>
        {tr(
          "I controlli descrivono il contenuto del grafo, non la sua correttezza tecnica.",
        )}
      </p>
      <button
        className="button button-secondary"
        disabled={checking}
        onClick={onRetry}
      >
        {tr(checking ? "Controllo in corso…" : "Ripeti i controlli")}
      </button>
      {!preview && (
        <p role="status">
          {tr(
            checking
              ? "Controllo in corso…"
              : "Esegui i controlli sul contenuto attuale",
          )}
        </p>
      )}
      {preview && (
        <>
          <div className="editor-metrics">
            {[
              ["required", "Campi obbligatori"],
              ["optional", "Campi facoltativi"],
            ].map(([group, label]) => {
              const items = fields.filter(
                (f) => f.field.required === (group === "required"),
              );
              return (
                <div className="card" key={group}>
                  <h3>{tr(label)}</h3>
                  <button
                    className="button button-plain"
                    onClick={() => setFilter(group + ":filled")}
                  >
                    {items.length
                      ? tr("Compilati: {filled} / {total}", {
                          filled: items.filter((f) => f.state === "filled")
                            .length,
                          total: items.length,
                        })
                      : tr("Non applicabile")}
                  </button>
                  {[
                    ["missing", "Assenti: {n}"],
                    ["empty", "Vuoti: {n}"],
                    ["not_stated", "Non dichiarati: {n}"],
                  ].map(([state, label]) => (
                    <button
                      key={state}
                      className="button button-plain"
                      onClick={() => setFilter(group + ":" + state)}
                    >
                      {tr(label, {
                        n: items.filter((f) => f.state === state).length,
                      })}
                    </button>
                  ))}
                </div>
              );
            })}
            <div className="card">
              <h3>{tr("Filtra i controlli")}</h3>
              {[
                ["all", "Tutti i controlli"],
                ["error", "Errori"],
                ["warning", "Avvisi"],
                ["integrity", "Integrità"],
                ["links", "Collegamenti e percorsi"],
                ["sources", "Fonti e verifiche"],
                ["duplicates", "Duplicati e nomi simili"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  className="button button-plain"
                  aria-pressed={filter === key}
                  onClick={() => setFilter(key)}
                >
                  {tr(label)} (
                  {
                    preview.issues.filter(
                      (i) =>
                        key === "all" ||
                        i.severity === key ||
                        GROUPS[key]?.includes(i.code),
                    ).length
                  }
                  )
                </button>
              ))}
            </div>
            <div className="card">
              <h3>{tr("Relazioni")}</h3>
              <p>
                {tr("Diagnostiche: {n}", {
                  n: preview.graph.edges.filter((e) => !e.derived).length,
                })}
              </p>
              <p>
                {tr("Aggiunte dal sistema: {n}", {
                  n: preview.graph.edges.filter((e) => e.derived).length,
                })}
              </p>
              <p>
                {tr("Occorrenze con prove: {n}", {
                  n: preview.graph.edges
                    .filter((e) => !e.derived)
                    .flatMap((e) => e.occurrences)
                    .filter((o) => o.evidence.length).length,
                })}
              </p>
              <p>
                {tr("Contributi umani senza prove: {n}", {
                  n: preview.graph.edges
                    .flatMap((e) => e.occurrences)
                    .filter((o) => o.record === "human" && !o.evidence.length)
                    .length,
                })}
              </p>
            </div>
          </div>
          <ul className="editor-issues">
            {fieldItems
              ? fieldItems.map(({ node, field, state }) => (
                  <li key={node.id + field.name}>
                    <button
                      className="button button-plain"
                      onClick={() =>
                        onTarget({
                          id: node.id + field.name,
                          code: "REQUIRED_FIELD",
                          severity: "warning",
                          target: {
                            kind: "node",
                            id: node.id,
                            field: field.name,
                          },
                          introduced: false,
                          message_key: "REQUIRED_FIELD",
                          message_params: {},
                        })
                      }
                    >
                      {node.name} · {field.name} ·{" "}
                      {tr(
                        {
                          missing: "Assente",
                          empty: "Vuoto",
                          not_stated: "Non dichiarato",
                          filled: "Compilato",
                        }[state],
                      )}
                    </button>
                  </li>
                ))
              : shownIssues.map((i) => (
                  <li key={i.id} data-severity={i.severity}>
                    <span>
                      {tr(i.severity === "error" ? "Errore" : "Avviso")}
                    </span>
                    <button
                      className="button button-plain"
                      onClick={() => onTarget(i)}
                    >
                      {issueText(i)} ·{" "}
                      {i.target.id ??
                        i.message_params.question_id ??
                        tr("Grafo")}
                    </button>
                    <small>
                      {tr(
                        i.introduced
                          ? "Introdotto dalla modifica"
                          : "Già presente nella fonte",
                      )}
                    </small>
                  </li>
                ))}
          </ul>
          {!(fieldItems ?? shownIssues).length && (
            <p>{tr("Nessun problema rilevato.")}</p>
          )}
        </>
      )}
    </section>
  );
}
