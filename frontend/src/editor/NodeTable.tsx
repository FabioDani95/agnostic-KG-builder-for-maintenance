import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { GraphNode } from "../api/types";
import { tr, useLang } from "../i18n/i18n";
import { TYPE_LABEL } from "../text/it";
import { fieldLabel } from "./fields";
import { EditableCell } from "./EditableCell";
import { useEditor } from "./EditorSessionProvider";
import { filterNodes, indices } from "./selectors";
export function NodeTable({
  onGraph,
  readOnly = false,
}: {
  onGraph: (id: string) => void;
  readOnly?: boolean;
}) {
  useLang();
  const { state, dispatch, graph } = useEditor();
  const [params, setParams] = useSearchParams();
  const ontology = state.document.ontology;
  const type = params.get("tipo") ?? "all";
  const query = params.get("cerca") ?? "";
  const [sort, setSort] = useState({ field: "name", direction: 1 });
  const [showAll, setShowAll] = useState(false);
  const [deleting, setDeleting] = useState<GraphNode | null>(null);
  const [adding, setAdding] = useState(false);
  const [newType, setNewType] = useState(
    type === "all"
      ? ontology.nodes.find((n) => n.name !== ontology.root)!.name
      : type,
  );
  const [name, setName] = useState("");
  const indexed = useMemo(() => indices(graph, ontology), [graph, ontology]);
  const change = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };
  const [columns, setColumns] = useState<
    Record<string, { state: string; exact: string }>
  >({});
  const f = {
    columns,
    query,
    type,
    field: params.get("campo") ?? "description",
    state: params.get("valore") ?? "",
    exact: params.get("esatto") ?? "",
    links: params.get("collegamenti") ?? "",
    source: params.get("fonte") ?? "",
    modified: params.get("modificati") ?? "",
  };
  const selected =
    state.selection?.kind === "node" ? state.selection.id : undefined;
  const filtered = filterNodes(graph, state.document.graph, f, selected);
  const fields =
    type === "all"
      ? ["name"]
      : (indexed.fields.get(type) ?? ["name"]).filter(
          (f) => !f.endsWith("_id"),
        );
  const shown = showAll ? fields : fields.slice(0, 4);
  const rows = [...filtered.rows].sort(
    (a, b) =>
      String(
        sort.field === "name" ? a.name : (a.properties[sort.field] ?? ""),
      ).localeCompare(
        String(
          sort.field === "name" ? b.name : (b.properties[sort.field] ?? ""),
        ),
        undefined,
        { numeric: true },
      ) * sort.direction,
  );
  const modify = (node: GraphNode, field: string, value: unknown) =>
    dispatch({
      type: "edit",
      operation:
        field === "name"
          ? { op: "node.set_name", node_id: node.id, value: String(value) }
          : { op: "node.set_property", node_id: node.id, field, value },
    });
  return (
    <div className="editor-table-view">
      <div className="editor-toolbar">
        <label>
          {tr("Tipo")}
          <select
            aria-label={tr("Tipo di nodo")}
            value={type}
            onChange={(e) => change("tipo", e.target.value)}
          >
            <option value="all">{tr("Tutti")}</option>
            {ontology.nodes.map((t) => (
              <option key={t.name} value={t.name}>
                {TYPE_LABEL[t.name] ?? t.name} (
                {graph.nodes.filter((n) => n.type === t.name).length})
              </option>
            ))}
          </select>
        </label>
        <label>
          {tr("Cerca")}
          <input
            aria-label={tr("Cerca nei nodi")}
            value={query}
            onChange={(e) => change("cerca", e.target.value)}
          />
        </label>
        <label>
          {tr("Collegamenti")}
          <select
            value={f.links}
            onChange={(e) => change("collegamenti", e.target.value)}
          >
            <option value="">{tr("Tutti")}</option>
            {["0", "1", "2+"].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          {tr("Fonti")}
          <select
            value={f.source}
            onChange={(e) => change("fonte", e.target.value)}
          >
            <option value="">{tr("Tutti")}</option>
            <option value="yes">{tr("Con fonte")}</option>
            <option value="no">{tr("Senza fonte")}</option>
          </select>
        </label>
        <label>
          {tr("Modifiche")}
          <select
            value={f.modified}
            onChange={(e) => change("modificati", e.target.value)}
          >
            <option value="">{tr("Tutti")}</option>
            <option value="yes">{tr("Modificati")}</option>
            <option value="no">{tr("Non modificati")}</option>
          </select>
        </label>
        <button
          className="button button-secondary"
          onClick={() => setShowAll((v) => !v)}
        >
          {tr("Mostra campi")}
        </button>
        {!readOnly && (
          <button
            className="button button-secondary"
            onClick={() => setAdding(true)}
          >
            {tr("Aggiungi nodo")}
          </button>
        )}
      </div>
      <div className="editor-toolbar">
        <label>
          {tr("Campo")}
          <select
            value={f.field}
            onChange={(e) => change("campo", e.target.value)}
          >
            {[...new Set([...fields, f.field])].map((f) => (
              <option key={f} value={f}>
                {fieldLabel(f)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {tr("Stato del valore")}
          <select
            value={f.state}
            onChange={(e) => change("valore", e.target.value)}
          >
            <option value="">{tr("Tutti")}</option>
            {[
              ["missing", "Assente"],
              ["empty", "Vuoto"],
              ["not_stated", "Non dichiarato"],
              ["filled", "Compilato"],
            ].map(([v, l]) => (
              <option key={v} value={v}>
                {tr(l)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {tr("Valore esatto")}
          <input
            value={f.exact}
            onChange={(e) => change("esatto", e.target.value)}
          />
        </label>
        <button
          className="button button-secondary"
          disabled={!f.state && !f.exact}
          onClick={() => {
            setColumns((current) => ({
              ...current,
              [f.field]: { state: f.state, exact: f.exact },
            }));
            const next = new URLSearchParams(params);
            next.delete("valore");
            next.delete("esatto");
            setParams(next, { replace: true });
          }}
        >
          {tr("Aggiungi filtro del campo")}
        </button>
        {Object.entries(columns).map(([field, filter]) => (
          <button
            key={field}
            className="button button-plain"
            aria-label={tr("Rimuovi filtro {field}", { field })}
            onClick={() =>
              setColumns((current) => {
                const next = { ...current };
                delete next[field];
                return next;
              })
            }
          >
            {fieldLabel(field)}:{" "}
            {filter.exact ||
              tr(
                (
                  {
                    missing: "Assente",
                    empty: "Vuoto",
                    filled: "Compilato",
                    not_stated: "Non dichiarato",
                  } as Record<string, string>
                )[filter.state],
              )}{" "}
            ×
          </button>
        ))}
        <button
          className="button button-plain"
          onClick={() => {
            setColumns({});
            const next = new URLSearchParams(params);
            [
              "cerca",
              "campo",
              "valore",
              "esatto",
              "collegamenti",
              "fonte",
              "modificati",
            ].forEach((k) => next.delete(k));
            setParams(next, { replace: true });
          }}
        >
          {tr("Rimuovi filtri")}
        </button>
        <span>
          {rows.length} {tr("Nodi")}
        </span>
      </div>
      {filtered.exception && (
        <p className="message">
          {tr(
            "L’elemento selezionato è mostrato anche se escluso dai filtri attivi.",
          )}
        </p>
      )}
      <div className="editor-table-scroll">
        <table className="editor-table" aria-label={tr("Nodi")}>
          <thead>
            <tr>
              <th>{tr("Tipo")}</th>
              {shown.map((f) => (
                <th key={f}>
                  <button
                    onClick={() =>
                      setSort({
                        field: f,
                        direction: sort.field === f ? -sort.direction : 1,
                      })
                    }
                  >
                    {fieldLabel(f)}{" "}
                    {sort.field === f ? (sort.direction > 0 ? "↑" : "↓") : ""}
                  </button>
                </th>
              ))}
              <th>
                {tr("Collegamenti")}
                <small>{tr("Diagnostica / Sistema")}</small>
              </th>
              <th>{tr("Prove")}</th>
              <th>{tr("Azioni")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((node) => (
              <tr
                key={node.id}
                data-selected={selected === node.id}
                id={`row-${node.id}`}
              >
                <td>
                  {TYPE_LABEL[node.type] ?? node.type}
                  <small className="mono">{node.id}</small>
                </td>
                {shown.map((f) => {
                  const descriptor = ontology.nodes
                    .find((n) => n.name === node.type)
                    ?.properties.find((p) => p.name === f);
                  return (
                    <td key={f}>
                      <EditableCell
                        value={f === "name" ? node.name : node.properties[f]}
                        field={descriptor ?? { name: f, required: false }}
                        label={`${node.name}: ${f}`}
                        readOnly={readOnly || !descriptor}
                        onChange={(value) => modify(node, f, value)}
                        onRemove={
                          !readOnly &&
                          descriptor &&
                          !descriptor.required &&
                          f !== "name"
                            ? () =>
                                dispatch({
                                  type: "edit",
                                  operation: {
                                    op: "node.remove_property",
                                    node_id: node.id,
                                    field: f,
                                  },
                                })
                            : undefined
                        }
                      />
                    </td>
                  );
                })}
                <td className="mono">
                  <button
                    onClick={() =>
                      dispatch({
                        type: "select",
                        selection: { kind: "node", id: node.id },
                      })
                    }
                  >
                    {filtered.counts.get(node.id) ?? 0} /{" "}
                    {indexed.edges.get(node.id)?.filter((e) => e.derived)
                      .length ?? 0}
                  </button>
                </td>
                <td>
                  <button
                    className="button button-plain"
                    onClick={() =>
                      dispatch({
                        type: "select",
                        selection: { kind: "node", id: node.id },
                      })
                    }
                  >
                    {tr("Prove")} ({node.evidence.length})
                  </button>
                </td>
                <td>
                  <button
                    className="button button-plain"
                    onClick={() => onGraph(node.id)}
                  >
                    {tr("Vedi nel grafo")}
                  </button>
                  {!readOnly && node.type !== ontology.root && (
                    <button
                      className="button button-plain"
                      onClick={() => setDeleting(node)}
                    >
                      {tr("Elimina")}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && (
          <p className="empty">{tr("Nessun risultato con questi filtri.")}</p>
        )}
      </div>
      {adding && (
        <div className="editor-exit-overlay">
          <form
            className="card editor-dialog"
            role="dialog"
            aria-label={tr("Aggiungi nodo")}
            onSubmit={(e) => {
              e.preventDefault();
              const id = `tmp_node_${crypto.randomUUID()}`;
              dispatch({
                type: "edit",
                operation: {
                  op: "node.add",
                  temp_id: id,
                  node_type: newType,
                  name,
                  properties: {},
                },
              });
              dispatch({ type: "select", selection: { kind: "node", id } });
              change("tipo", newType);
              setAdding(false);
              setName("");
              dispatch({ type: "pending", value: false });
            }}
          >
            <h2>{tr("Aggiungi nodo")}</h2>
            <label>
              {tr("Tipo")}
              <select
                value={newType}
                onChange={(e) => setNewType(e.target.value)}
              >
                {ontology.nodes
                  .filter((n) => n.name !== ontology.root)
                  .map((n) => (
                    <option key={n.name}>{n.name}</option>
                  ))}
              </select>
            </label>
            <label>
              {tr("Nome")}
              <input
                autoFocus
                required
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  dispatch({ type: "pending", value: true });
                }}
              />
            </label>
            <p>{tr("Compila i campi obbligatori prima dell’accettazione.")}</p>
            <button
              type="button"
              className="button button-secondary"
              onClick={() => {
                setAdding(false);
                setName("");
                dispatch({ type: "pending", value: false });
              }}
            >
              {tr("Annulla")}
            </button>
            <button className="button button-primary">{tr("Aggiungi")}</button>
          </form>
        </div>
      )}
      {deleting && (
        <div className="editor-exit-overlay">
          <div
            className="card editor-dialog"
            role="alertdialog"
            aria-label={tr("Elimina nodo")}
          >
            <h2>
              {tr("Elimina nodo")}: {deleting.name}
            </h2>
            <p>
              {tr("Saranno eliminate anche {n} relazioni.", {
                n: indexed.edges.get(deleting.id)?.length ?? 0,
              })}
            </p>
            <ul>
              {indexed.edges.get(deleting.id)?.map((e) => (
                <li key={e.id}>
                  {indexed.nodes.get(e.from)?.name} → {e.type} →{" "}
                  {indexed.nodes.get(e.to)?.name}
                </li>
              ))}
            </ul>
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
                  operation: { op: "node.delete", node_id: deleting.id },
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
