import { useEffect, useState } from "react";
import { useApi, versionPath } from "../api/client";
import type { Condition, Evidence, GraphEdge, Occurrence } from "../api/types";
import { NodeDetail, EdgeDetail } from "../components/EvidencePanel";
import { tr, useLang } from "../i18n/i18n";
import { fieldLabel } from "./fields";
import { EditableCell } from "./EditableCell";
import { useEditor } from "./EditorSessionProvider";
import { relationStatus } from "./RelationTable";
const CONDITION_KIND: Record<string, string> = {
  if: "Se",
  prerequisite: "Prerequisito",
  warning: "Avvertenza",
  expected: "Risultato atteso",
  order: "Sequenza",
};
function OccurrenceForm({
  edge,
  occurrence,
  manualId,
  versionId,
  onClose,
}: {
  edge: GraphEdge;
  occurrence?: Occurrence;
  manualId: string;
  versionId: string;
  onClose: () => void;
}) {
  const { state, dispatch } = useEditor();
  const [conditions, setConditions] = useState<Condition[]>(
    structuredClone(occurrence?.conditions ?? []),
  );
  const [segments, setSegments] = useState(
    occurrence?.evidence.map((e) => e.segment_id) ?? [],
  );
  const [annotation, setAnnotation] = useState(occurrence?.annotation ?? "");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState("");
  const [offset, setOffset] = useState(0);
  const source = useApi<{
    items: Evidence[];
    total: number;
    available: boolean;
  }>(
    state.document.source.segments_available
      ? `${versionPath(manualId, versionId)}/source-segments?q=${encodeURIComponent(query)}${page ? `&page=${page}` : ""}&offset=${offset}`
      : null,
  );
  const pending = () => dispatch({ type: "pending", value: true });
  const close = () => {
    dispatch({ type: "pending", value: false });
    onClose();
  };
  const selected = new Map(
    [...(occurrence?.evidence ?? []), ...(source.data?.items ?? [])].map(
      (e) => [e.segment_id, e],
    ),
  );
  return (
    <div className="editor-exit-overlay">
      <form
        className="card editor-occurrence-dialog"
        role="dialog"
        aria-label={tr("Modifica occorrenza")}
        onSubmit={(e) => {
          e.preventDefault();
          dispatch({
            type: "edit",
            operation: {
              op: occurrence ? "occurrence.update" : "occurrence.add",
              edge_id: edge.id,
              occurrence_id: occurrence?.id ?? `tmp_occ_${crypto.randomUUID()}`,
              conditions,
              segment_ids: segments,
              annotation,
            },
          });
          close();
        }}
      >
        <h2>
          {tr(occurrence ? "Modifica occorrenza" : "Aggiungi occorrenza")}
        </h2>
        <h3>{tr("Condizioni")}</h3>
        {conditions.map((c, i) => (
          <div className="editor-condition" key={i}>
            <select
              aria-label={tr("Tipo condizione")}
              value={c.kind}
              onChange={(e) => {
                setConditions((v) =>
                  v.map((x, j) =>
                    j === i ? { ...x, kind: e.target.value } : x,
                  ),
                );
                pending();
              }}
            >
              {Object.entries(CONDITION_KIND).map(([k, label]) => (
                <option key={k} value={k}>
                  {tr(label)}
                </option>
              ))}
            </select>
            <select
              aria-label={tr("Ambito condizione")}
              value={c.scope ?? "relation"}
              onChange={(e) => {
                setConditions((v) =>
                  v.map((x, j) =>
                    j === i
                      ? {
                          ...x,
                          scope: e.target.value as "relation" | "section",
                        }
                      : x,
                  ),
                );
                pending();
              }}
            >
              <option value="relation">{tr("Relazione")}</option>
              <option value="section">{tr("Sezione")}</option>
            </select>
            <textarea
              aria-label={tr("Testo condizione")}
              required
              value={c.text}
              onChange={(e) => {
                setConditions((v) =>
                  v.map((x, j) =>
                    j === i ? { ...x, text: e.target.value } : x,
                  ),
                );
                pending();
              }}
            />
            <label>
              {tr("Riferimenti della condizione")}
              <select
                multiple
                value={c.cite ?? []}
                onChange={(e) => {
                  const cite = Array.from(
                    e.target.selectedOptions,
                    (v) => v.value,
                  );
                  setConditions((v) =>
                    v.map((x, j) => (j === i ? { ...x, cite } : x)),
                  );
                  pending();
                }}
              >
                {[...selected.values()].map((s) => (
                  <option key={s.segment_id} value={s.segment_id}>
                    p. {s.page} · {s.text.slice(0, 80)}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={() => {
                setConditions((v) => v.filter((_, j) => j !== i));
                pending();
              }}
            >
              {tr("Elimina")}
            </button>
          </div>
        ))}
        <button
          type="button"
          className="button button-secondary"
          onClick={() => {
            setConditions((v) => [
              ...v,
              { kind: "if", text: "", cite: [], scope: "relation" },
            ]);
            pending();
          }}
        >
          {tr("Aggiungi condizione")}
        </button>
        <h3>{tr("Prove")}</h3>
        <p>
          {tr(
            "Il testo della fonte è in sola lettura. Seleziona i segmenti da associare.",
          )}
        </p>
        {!state.document.source.segments_available && (
          <p className="message">
            {tr(
              "Indice della fonte non verificabile: puoi conservare o rimuovere le citazioni incorporate.",
            )}
          </p>
        )}
        <div className="editor-toolbar">
          <label>
            {tr("Cerca nella fonte")}
            <input
              disabled={!state.document.source.segments_available}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label>
            {tr("Pagina")}
            <input
              disabled={!state.document.source.segments_available}
              type="number"
              min="1"
              value={page}
              onChange={(e) => {
                setPage(e.target.value);
                setOffset(0);
              }}
            />
          </label>
        </div>
        {source.error && <p role="alert">{source.error}</p>}
        {[...selected.values()].map((s) => (
          <label className="editor-source" key={s.segment_id}>
            <input
              type="checkbox"
              checked={segments.includes(s.segment_id)}
              onChange={(e) => {
                setSegments((v) =>
                  e.target.checked
                    ? [...v, s.segment_id]
                    : v.filter((id) => id !== s.segment_id),
                );
                pending();
              }}
            />
            <span>
              p. {s.page} · {s.text}
            </span>
          </label>
        ))}
        {source.data && (
          <div className="editor-toolbar">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset((v) => Math.max(0, v - 50))}
            >
              {tr("Indietro")}
            </button>
            <span>
              {source.data.total} {tr("segmenti")}
            </span>
            <button
              type="button"
              disabled={offset + 50 >= source.data.total}
              onClick={() => setOffset((v) => v + 50)}
            >
              {tr("Avanti")}
            </button>
          </div>
        )}
        <label>
          {tr("Annotazione personale")}
          <textarea
            value={annotation}
            onChange={(e) => {
              setAnnotation(e.target.value);
              pending();
            }}
          />
        </label>
        <button
          type="button"
          className="button button-secondary"
          onClick={close}
        >
          {tr("Annulla")}
        </button>
        <button className="button button-primary">
          {tr("Conferma modifica")}
        </button>
      </form>
    </div>
  );
}
export function EditorDetails({
  manualId,
  versionId,
  onPage,
  onNode,
  onGraph,
  readOnly = false,
}: {
  manualId: string;
  versionId: string;
  onPage: (page: number, evidence: Evidence[]) => void;
  onNode: (id: string) => void;
  onGraph: (kind: "node" | "edge", id: string) => void;
  readOnly?: boolean;
}) {
  useLang();
  const { state, dispatch, graph } = useEditor();
  const selection = state.selection;
  const nodes = new Map(graph.nodes.map((n) => [n.id, n]));
  const node = selection?.kind === "node" ? nodes.get(selection.id) : undefined;
  const edge =
    selection?.kind === "edge"
      ? graph.edges.find((e) => e.id === selection.id)
      : undefined;
  const [occ, setOcc] = useState<Occurrence | "new" | null>(null);
  const [reason, setReason] = useState("");
  const [removeOcc, setRemoveOcc] = useState<Occurrence | null>(null);
  useEffect(() => {
    if (selection?.field) {
      const inputs = document.querySelectorAll<HTMLInputElement>(
        ".editor-details input,.editor-details textarea",
      );
      for (const input of inputs)
        if (
          input.getAttribute("aria-label")?.endsWith(`: ${selection.field}`)
        ) {
          input.focus();
          break;
        }
    }
  }, [selection]);
  const close = () => dispatch({ type: "select", selection: null });
  if (!node && !edge) return null;
  return (
    <aside className="editor-details">
      <button
        className="button button-plain"
        onClick={() => onGraph(node ? "node" : "edge", (node ?? edge)!.id)}
      >
        {tr("Vedi nel grafo")}
      </button>
      {node && (
        <>
          <NodeDetail
            node={node}
            nodes={nodes}
            edges={graph.edges}
            onOpenPage={onPage}
            onSelectEdge={(id) =>
              dispatch({ type: "select", selection: { kind: "edge", id } })
            }
            onClose={close}
          />
          <section className="panel-section">
            <h3>{tr("Campi")}</h3>
            {state.document.ontology.nodes
              .find((t) => t.name === node.type)
              ?.properties.map((f) => (
                <label key={f.name}>
                  {fieldLabel(f.name)}
                  {f.required ? " *" : ""}
                  <EditableCell
                    field={f}
                    value={
                      f.name === "name" ? node.name : node.properties[f.name]
                    }
                    readOnly={readOnly || f.name.endsWith("_id")}
                    label={`${node.name}: ${f.name}`}
                    onChange={(value) =>
                      dispatch({
                        type: "edit",
                        operation:
                          f.name === "name"
                            ? {
                                op: "node.set_name",
                                node_id: node.id,
                                value: String(value),
                              }
                            : {
                                op: "node.set_property",
                                node_id: node.id,
                                field: f.name,
                                value,
                              },
                      })
                    }
                    onRemove={
                      !readOnly && !f.required
                        ? () =>
                            dispatch({
                              type: "edit",
                              operation: {
                                op: "node.remove_property",
                                node_id: node.id,
                                field: f.name,
                              },
                            })
                        : undefined
                    }
                  />
                </label>
              ))}
            <label>
              {tr("Altri nomi")}
              <EditableCell
                value={node.aliases ?? []}
                field={{ name: "aliases", type: "array", required: false }}
                label={`${node.name}: aliases`}
                readOnly={readOnly}
                onChange={(value) =>
                  dispatch({
                    type: "edit",
                    operation: {
                      op: "node.set_aliases",
                      node_id: node.id,
                      values: value as string[],
                    },
                  })
                }
              />
            </label>
            <details>
              <summary>{tr("Dati conservati")}</summary>
              <pre>{JSON.stringify(node, null, 2)}</pre>
            </details>
          </section>
        </>
      )}
      {edge && (
        <>
          <EdgeDetail
            edge={edge}
            nodes={nodes}
            onOpenPage={onPage}
            onSelectNode={onNode}
            onClose={close}
          />
          <section className="panel-section">
            <h3>{relationStatus(edge)}</h3>
            {!readOnly && !edge.derived && (
              <>
                <label>
                  {tr("Motivazione della decisione")}
                  <input
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                {edge.occurrences.map((o, i) => (
                  <div className="editor-occurrence" key={o.id ?? i}>
                    <h4>
                      {tr("Occorrenza")} {i + 1}
                    </h4>
                    <p>
                      {tr(
                        o.review?.status === "confirmed"
                          ? o.evidence.length
                            ? "Confermata da una persona"
                            : "Confermata da una persona, senza fonte collegata"
                          : o.review?.status === "rejected"
                            ? "Rifiutata"
                            : o.tier === "green"
                              ? "Verificata"
                              : "Da verificare",
                      )}
                    </p>
                    {o.annotation && <p>{o.annotation}</p>}
                    <button
                      className="button button-secondary"
                      onClick={() => setOcc(o)}
                    >
                      {tr("Modifica occorrenza")}
                    </button>
                    <button
                      className="button button-plain"
                      onClick={() => setRemoveOcc(o)}
                    >
                      {tr("Elimina")}
                    </button>
                    <button
                      className="button button-secondary"
                      disabled={!state.preview || !o.content_hash}
                      title={
                        !state.preview
                          ? tr("Esegui i controlli sul contenuto attuale")
                          : undefined
                      }
                      onClick={() =>
                        dispatch({
                          type: "edit",
                          operation: {
                            op: "occurrence.confirm",
                            edge_id: edge.id,
                            occurrence_id: o.id!,
                            content_hash: o.content_hash!,
                            reason,
                          },
                        })
                      }
                    >
                      {tr("Conferma contenuto")}
                    </button>
                    <button
                      className="button button-plain"
                      disabled={!state.preview || !o.content_hash}
                      onClick={() =>
                        dispatch({
                          type: "edit",
                          operation: {
                            op: "occurrence.reject",
                            edge_id: edge.id,
                            occurrence_id: o.id!,
                            content_hash: o.content_hash!,
                            reason,
                          },
                        })
                      }
                    >
                      {tr("Rifiuta contenuto")}
                    </button>
                  </div>
                ))}
                <button
                  className="button button-secondary"
                  onClick={() => setOcc("new")}
                >
                  {tr("Aggiungi occorrenza")}
                </button>
              </>
            )}
          </section>
        </>
      )}
      {edge && occ && (
        <OccurrenceForm
          edge={edge}
          occurrence={occ === "new" ? undefined : occ}
          manualId={manualId}
          versionId={versionId}
          onClose={() => setOcc(null)}
        />
      )}
      {edge && removeOcc && (
        <div className="editor-exit-overlay">
          <div className="card editor-dialog" role="alertdialog">
            <h2>{tr("Elimina occorrenza")}</h2>
            <p>
              {tr(
                edge.occurrences.length === 1
                  ? "Eliminando l’ultima occorrenza sarà eliminata anche la relazione."
                  : "La modifica può essere annullata nella sessione.",
              )}
            </p>
            <button
              className="button button-secondary"
              onClick={() => setRemoveOcc(null)}
            >
              {tr("Annulla")}
            </button>
            <button
              className="button button-primary"
              onClick={() => {
                dispatch({
                  type: "edit",
                  operation: {
                    op: "occurrence.delete",
                    edge_id: edge.id,
                    occurrence_id: removeOcc.id!,
                  },
                });
                setRemoveOcc(null);
              }}
            >
              {tr("Elimina")}
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
