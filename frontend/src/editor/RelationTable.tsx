import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { GraphEdge } from "../api/types";
import { tr, useLang } from "../i18n/i18n";
import { RELATION_LABEL } from "../text/it";
import { useEditor } from "./EditorSessionProvider";
const STATUS_LABELS: Record<string, string> = {
  system: "Aggiunta dal sistema",
  rejected: "Rifiutata",
  human: "Confermata da una persona",
  green: "Verificata",
  pending: "Da verificare",
};
export function relationState(edge: GraphEdge) {
  if (edge.derived) return "system";
  if (
    edge.occurrences.length &&
    edge.occurrences.every((o) => o.review?.status === "rejected")
  )
    return "rejected";
  if (edge.tier === "green") return "green";
  if (edge.occurrences.some((o) => o.review?.status === "confirmed"))
    return "human";
  return "pending";
}
export function relationStatus(edge: GraphEdge) {
  return tr(STATUS_LABELS[relationState(edge)]);
}
function relationOrigin(edge: GraphEdge) {
  return edge.derived
    ? "system"
    : edge.occurrences.some(
          (o) =>
            o.record === "human" ||
            o.review?.status === "confirmed" ||
            o.review?.status === "rejected",
        )
      ? "human"
      : "extraction";
}
export function RelationTable({
  onNode,
  onGraph,
  readOnly = false,
}: {
  onNode: (id: string) => void;
  onGraph: (id: string) => void;
  readOnly?: boolean;
}) {
  useLang();
  const { state, dispatch, graph } = useEditor();
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [origin, setOrigin] = useState("");
  const [source, setSource] = useState("");
  const [page, setPage] = useState("");
  const [modified, setModified] = useState("");
  const [sort, setSort] = useState(1);
  const [editing, setEditing] = useState<GraphEdge | "new" | null>(null);
  const [relation, setRelation] = useState(
    state.document.ontology.relations.find((r) => !r.added_by_code)!.name,
  );
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [nodeQuery, setNodeQuery] = useState("");
  const [deleting, setDeleting] = useState<GraphEdge | null>(null);
  const type = params.get("relazione") ?? "";
  const nodes = new Map(graph.nodes.map((n) => [n.id, n]));
  const selected =
    state.selection?.kind === "edge" ? state.selection.id : undefined;
  const old = new Map(
    state.document.graph.edges.map((e) => [e.id, JSON.stringify(e)]),
  );
  const matches = (e: GraphEdge) =>
    (!type || e.type === type) &&
    [e.id, e.type, nodes.get(e.from)?.name, nodes.get(e.to)?.name]
      .join(" ")
      .toLowerCase()
      .includes(query.toLowerCase()) &&
    (!status || relationState(e) === status) &&
    (!origin ||
      (origin === "diagnostic" ? !e.derived : relationOrigin(e) === origin)) &&
    (!source ||
      (source === "yes") ===
        e.occurrences.some((o) => o.evidence.length > 0)) &&
    (!page ||
      e.occurrences.some((o) =>
        o.evidence.some((v) => v.page === Number(page)),
      )) &&
    (!modified ||
      (modified === "yes") === (old.get(e.id) !== JSON.stringify(e)));
  const exception = graph.edges.find((e) => e.id === selected && !matches(e));
  const shown = graph.edges
    .filter(matches)
    .sort((a, b) => a.type.localeCompare(b.type) * sort);
  if (exception) shown.unshift(exception);
  const openEditor = (edge: GraphEdge | "new") => {
    setEditing(edge);
    if (edge !== "new") {
      setRelation(edge.type);
      setFrom(edge.from);
      setTo(edge.to);
    } else {
      setFrom("");
      setTo("");
    }
    setNodeQuery("");
  };
  const spec = state.document.ontology.relations.find(
    (r) => r.name === relation,
  )!;
  const eligible = (type: string) =>
    graph.nodes.filter(
      (n) =>
        n.type === type &&
        (n.id === from ||
          n.id === to ||
          `${n.name} ${n.id}`.toLowerCase().includes(nodeQuery.toLowerCase())),
    );
  const editingDuplicate =
    editing && editing !== "new"
      ? graph.edges.find(
          (e) =>
            e.id !== editing.id &&
            e.type === relation &&
            e.from === from &&
            e.to === to,
        )
      : undefined;
  const save = () => {
    if (editingDuplicate) return;
    const duplicate = graph.edges.find(
      (e) =>
        e.type === relation &&
        e.from === from &&
        e.to === to &&
        (editing === "new" || e.id !== editing?.id),
    );
    if (duplicate) {
      dispatch({
        type: "edit",
        operation: {
          op: "occurrence.add",
          edge_id: duplicate.id,
          occurrence_id: `tmp_occ_${crypto.randomUUID()}`,
          conditions: [],
          segment_ids: [],
          annotation: "",
        },
      });
      dispatch({
        type: "select",
        selection: { kind: "edge", id: duplicate.id },
      });
    } else {
      const id = `tmp_edge_${crypto.randomUUID()}`;
      if (editing === "new")
        dispatch({
          type: "edit",
          operation: {
            op: "edge.add",
            temp_id: id,
            relation_type: relation,
            from,
            to,
            occurrences: [{ conditions: [], segment_ids: [], annotation: "" }],
          },
        });
      else if (
        editing &&
        (editing.type !== relation ||
          editing.from !== from ||
          editing.to !== to)
      )
        dispatch({
          type: "edit",
          operation: {
            op: "edge.replace_endpoints",
            edge_id: editing.id,
            replacement_temp_id: id,
            relation_type: relation,
            from,
            to,
          },
        });
      dispatch({
        type: "select",
        selection: {
          kind: "edge",
          id:
            editing !== "new" &&
            editing?.type === relation &&
            editing?.from === from &&
            editing?.to === to
              ? editing.id
              : id,
        },
      });
    }
    setEditing(null);
    dispatch({ type: "pending", value: false });
  };
  return (
    <div className="editor-table-view">
      <div className="editor-toolbar">
        <label>
          {tr("Cerca")}
          <input
            aria-label={tr("Cerca nelle relazioni")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <label>
          {tr("Relazione")}
          <select
            value={type}
            onChange={(e) => {
              const next = new URLSearchParams(params);
              next.set("relazione", e.target.value);
              setParams(next, { replace: true });
            }}
          >
            <option value="">{tr("Tutte")}</option>
            {state.document.ontology.relations.map((r) => (
              <option key={r.name} value={r.name}>
                {RELATION_LABEL[r.name] ?? r.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          {tr("Stato")}
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">{tr("Tutti")}</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {tr(label)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {tr("Origine")}
          <select value={origin} onChange={(e) => setOrigin(e.target.value)}>
            <option value="">{tr("Tutte")}</option>
            <option value="system">{tr("Sistema")}</option>
            <option value="diagnostic">{tr("Diagnostica")}</option>
            <option value="human">{tr("Contributo umano")}</option>
            <option value="extraction">{tr("Estrazione")}</option>
          </select>
        </label>
        <label>
          {tr("Prove")}
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">{tr("Tutte")}</option>
            <option value="yes">{tr("Con fonte")}</option>
            <option value="no">{tr("Senza fonte")}</option>
          </select>
        </label>
        <label>
          {tr("Pagina")}
          <input
            aria-label={tr("Filtra per pagina")}
            type="number"
            min="1"
            value={page}
            onChange={(e) => setPage(e.target.value)}
          />
        </label>
        <label>
          {tr("Modifiche")}
          <select
            value={modified}
            onChange={(e) => setModified(e.target.value)}
          >
            <option value="">{tr("Tutte")}</option>
            <option value="yes">{tr("Modificati")}</option>
            <option value="no">{tr("Non modificati")}</option>
          </select>
        </label>
        {!readOnly && (
          <button
            className="button button-secondary"
            onClick={() => openEditor("new")}
          >
            {tr("Aggiungi relazione")}
          </button>
        )}
        <button
          className="button button-plain"
          onClick={() => {
            setQuery("");
            setStatus("");
            setOrigin("");
            setSource("");
            setPage("");
            setModified("");
            const next = new URLSearchParams(params);
            next.delete("relazione");
            setParams(next, { replace: true });
          }}
        >
          {tr("Rimuovi filtri")}
        </button>
      </div>
      {exception && (
        <p className="message">
          {tr(
            "L’elemento selezionato è mostrato anche se escluso dai filtri attivi.",
          )}
        </p>
      )}
      <div className="editor-table-scroll">
        <table className="editor-table" aria-label={tr("Relazioni")}>
          <thead>
            <tr>
              <th>{tr("Da")}</th>
              <th>
                <button onClick={() => setSort((v) => -v)}>
                  {tr("Relazione")} ↕
                </button>
              </th>
              <th>{tr("A")}</th>
              <th>{tr("Verifica/revisione")}</th>
              <th>{tr("Condizioni")}</th>
              <th>{tr("Prove")}</th>
              <th>{tr("Origine")}</th>
              <th>{tr("Azioni")}</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((edge) => (
              <tr
                key={edge.id}
                id={`row-${edge.id}`}
                data-selected={selected === edge.id}
              >
                <td>
                  <button
                    className="button button-plain"
                    onClick={() => onNode(edge.from)}
                  >
                    {nodes.get(edge.from)?.name ?? edge.from}
                  </button>
                </td>
                <td>
                  {RELATION_LABEL[edge.type] ?? edge.type}
                  <small className="mono">{edge.id}</small>
                </td>
                <td>
                  <button
                    className="button button-plain"
                    onClick={() => onNode(edge.to)}
                  >
                    {nodes.get(edge.to)?.name ?? edge.to}
                  </button>
                </td>
                <td>
                  {relationStatus(edge)}
                  {edge.trusted &&
                    edge.occurrences.some(
                      (o) => !o.trusted && o.review?.status !== "confirmed",
                    ) && <small>{tr("Altre occorrenze da verificare")}</small>}
                </td>
                <td>
                  {edge.occurrences
                    .flatMap((o) => o.conditions ?? [])
                    .map((c) => c.text)
                    .join(" · ") || "–"}
                </td>
                <td>
                  <button
                    className="button button-plain"
                    onClick={() =>
                      dispatch({
                        type: "select",
                        selection: { kind: "edge", id: edge.id },
                      })
                    }
                  >
                    {tr("Prove")} ({edge.occurrences.length})
                  </button>
                </td>
                <td>
                  {tr(
                    edge.derived
                      ? "Sistema"
                      : edge.occurrences.some(
                            (o) => o.record === "human" || o.review,
                          )
                        ? "Contributo umano"
                        : "Estrazione",
                  )}
                </td>
                <td>
                  <button
                    className="button button-plain"
                    onClick={() => onGraph(edge.id)}
                  >
                    {tr("Vedi nel grafo")}
                  </button>
                  {!readOnly && !edge.derived && (
                    <>
                      <button
                        className="button button-plain"
                        onClick={() => openEditor(edge)}
                      >
                        {tr("Modifica")}
                      </button>
                      <button
                        className="button button-plain"
                        onClick={() => setDeleting(edge)}
                      >
                        {tr("Elimina")}
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!shown.length && (
          <p className="empty">{tr("Nessun risultato con questi filtri.")}</p>
        )}
      </div>
      <details className="editor-history">
        <summary>
          {tr("Relazioni escluse della fonte")} (
          {graph.excluded_relations.length})
        </summary>
        <pre>{JSON.stringify(graph.excluded_relations, null, 2)}</pre>
        <p>{tr("Una nuova proposta umana conserva l’esclusione originale.")}</p>
      </details>
      {editing && (
        <div className="editor-exit-overlay">
          <form
            role="dialog"
            aria-label={tr("Modifica relazione")}
            className="card editor-dialog"
            onSubmit={(e) => {
              e.preventDefault();
              save();
            }}
          >
            <h2>
              {tr(
                editing === "new" ? "Aggiungi relazione" : "Modifica relazione",
              )}
            </h2>
            <label>
              {tr("Relazione")}
              <select
                value={relation}
                onChange={(e) => {
                  setRelation(e.target.value);
                  setFrom("");
                  setTo("");
                  dispatch({ type: "pending", value: true });
                }}
              >
                {state.document.ontology.relations
                  .filter((r) => !r.added_by_code)
                  .map((r) => (
                    <option key={r.name}>{r.name}</option>
                  ))}
              </select>
            </label>
            <label>
              {tr("Cerca estremi")}
              <input
                value={nodeQuery}
                onChange={(e) => setNodeQuery(e.target.value)}
              />
            </label>
            {(
              [
                ["Da", from, setFrom, spec.domain],
                ["A", to, setTo, spec.range],
              ] as const
            ).map(([label, value, change, type]) => (
              <label key={label}>
                {tr(label)} ({type})
                <select
                  required
                  value={value}
                  onChange={(e) => {
                    change(e.target.value);
                    dispatch({ type: "pending", value: true });
                  }}
                >
                  <option value="">{tr("Seleziona nodo")}</option>
                  {eligible(type).map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.name} · {n.id}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <p>
              {tr(
                "Cambiare tipo o estremi crea una nuova identità e invalida le verifiche.",
              )}
            </p>
            <button
              type="button"
              className="button button-secondary"
              onClick={() => {
                setEditing(null);
                dispatch({ type: "pending", value: false });
              }}
            >
              {tr("Annulla")}
            </button>
            {editingDuplicate && (
              <p className="message">
                {tr(
                  "La relazione esiste già. Aggiungi un’occorrenza alla relazione esistente.",
                )}
              </p>
            )}
            <button
              className="button button-primary"
              disabled={!from || !to || Boolean(editingDuplicate)}
            >
              {tr("Conferma modifica")}
            </button>
          </form>
        </div>
      )}
      {deleting && (
        <div className="editor-exit-overlay">
          <div
            className="card editor-dialog"
            role="alertdialog"
            aria-label={tr("Elimina relazione")}
          >
            <h2>{tr("Elimina relazione")}</h2>
            <p>
              {nodes.get(deleting.from)?.name} → {deleting.type} →{" "}
              {nodes.get(deleting.to)?.name}
            </p>
            <button
              className="button button-secondary"
              onClick={() => setDeleting(null)}
            >
              {tr("Annulla")}
            </button>
            <button
              className="button button-primary"
              onClick={() => {
                dispatch({
                  type: "edit",
                  operation: { op: "edge.delete", edge_id: deleting.id },
                });
                setDeleting(null);
              }}
            >
              {tr("Elimina")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
