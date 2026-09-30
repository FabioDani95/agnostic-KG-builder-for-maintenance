import { useEffect, useMemo, useRef, useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  ApiError,
  getJson,
  graphRoute,
  manualRoute,
  postJson,
  useApi,
  versionPath,
} from "../api/client";
import type {
  AcceptRevision,
  EditorDocument,
  EditPreview,
  Evidence,
  Manual,
  RevisionCreated,
  RevisionRequest,
  Issue,
} from "../api/types";
import { Shell } from "../components/Shell";
import { Loading, Problem } from "../components/Feedback";
import { PageDialog } from "../components/PageDialog";
import { Graph3D, type GraphHandle } from "../graph/Graph3D";
import { useLang, tr } from "../i18n/i18n";
import { edgeReview } from "../graph/style";
import { versionLabel } from "../text/it";
import { useStatus } from "../status/StatusProvider";
import { EditorSessionProvider, useEditor } from "./EditorSessionProvider";
import { EditorDetails } from "./EditorDetails";
import { dirty } from "./reducer";
import { NodeTable } from "./NodeTable";
import { RelationTable } from "./RelationTable";
import { ReviewPanel } from "./ReviewPanel";
import { RevisionSummary } from "./RevisionSummary";
import { useEditorExitGuard } from "./useEditorExitGuard";

export function EditorFlow() {
  useLang();
  const { manualId = "", versionId = "" } = useParams();
  const loaded = useApi<EditorDocument>(
    `${versionPath(manualId, versionId)}/editor`,
  );
  if (!loaded.data)
    return (
      <Shell title={tr("Modifica grafo")}>
        {loaded.error ? (
          <Problem message={loaded.error} onRetry={loaded.reload} />
        ) : (
          <Loading label="Carico il grafo" />
        )}
      </Shell>
    );
  if (!loaded.data.capabilities.can_edit)
    return (
      <Shell title={tr("Modifica grafo")}>
        <Problem
          message={tr(
            loaded.data.capabilities.edit_reason ?? "Grafo non disponibile",
          )}
        />
        <Link to={graphRoute(manualId, versionId)}>{tr("Apri il grafo")}</Link>
      </Shell>
    );
  return (
    <EditorSessionProvider
      key={`${manualId}/${versionId}`}
      document={loaded.data}
    >
      <Flow manualId={manualId} versionId={versionId} />
    </EditorSessionProvider>
  );
}
function Flow({
  manualId,
  versionId,
}: {
  manualId: string;
  versionId: string;
}) {
  const { state, dispatch, graph } = useEditor();
  const navigate = useNavigate();
  const location = useLocation();
  const [params, setParams] = useSearchParams();
  const { refresh } = useStatus();
  useLang();
  const manual = useApi<Manual>(`/api/manuals/${encodeURIComponent(manualId)}`);
  const base = manual.data?.versions.find((v) => v.version_id === versionId);
  const baseLabel = base ? versionLabel(base) : versionId;
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [unknown, setUnknown] = useState(false);
  const [requestState, setRequestState] = useState("");
  const [page, setPage] = useState<{
    page: number;
    evidence: Evidence[];
  } | null>(null);
  const current = useRef(state);
  current.current = state;
  const frozen = useRef<AcceptRevision | null>(null);
  const bypass = useRef(false);
  const reached = useRef(1);
  const backTarget = useRef<string | null>(null);
  const graphHandle = useRef<GraphHandle>(null);
  const [initialized, setInitialized] = useState(false);
  const step = initialized ? (params.get("passo") ?? "modifica") : "modifica";
  const tab = params.get("vista") ?? "nodi";
  const path = location.pathname;
  const exitDialog = useEditorExitGuard(path, bypass);
  const endpoint = versionPath(manualId, versionId);
  useEffect(() => {
    if (initialized) return;
    if (params.get("passo") !== "modifica" || params.get("vista") !== "nodi") {
      const next = new URLSearchParams(params);
      next.set("passo", "modifica");
      next.set("vista", "nodi");
      setParams(next, { replace: true });
      return;
    }
    setInitialized(true);
  }, [params, initialized]); // A URL is never a stored draft.
  useEffect(() => {
    const restore = (event: PageTransitionEvent) => {
      if (event.persisted) {
        setInitialized(false);
        reached.current = 1;
        frozen.current = null;
        backTarget.current = null;
        setNote("");
        setUnknown(false);
        setError("");
        move("modifica", "nodi", true);
      }
    };
    window.addEventListener("pageshow", restore);
    return () => window.removeEventListener("pageshow", restore);
  }, [params]);
  const move = (nextStep: string, view?: string, replace = false) => {
    const next = new URLSearchParams(params);
    next.set("passo", nextStep);
    if (view) next.set("vista", view);
    setParams(next, { replace });
  };
  const inputReady = () => {
    const active = document.activeElement as HTMLElement | null;
    active?.blur();
    const invalid = document.querySelector<HTMLElement>(
      '[aria-invalid="true"]',
    );
    if (invalid) {
      invalid.focus();
      return false;
    }
    return !document.querySelector('[role="dialog"]');
  };
  const check = async () => {
    if (checking || state.saving || !inputReady()) return;
    setChecking(true);
    setError("");
    const generation = current.current.generation;
    try {
      const preview = await postJson<EditPreview>(
        `${endpoint}/validate-edits`,
        {
          preconditions: state.document.preconditions,
          operations: current.current.operations,
          draft_generation: generation,
        },
      );
      dispatch({ type: "preview", preview });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setChecking(false);
    }
  };
  useEffect(() => {
    if (step === "controlla" && !state.preview && !checking && !error)
      void check();
  }, [step, state.generation, checking, error, state.preview]);
  useEffect(() => {
    if (
      step === "riepilogo" &&
      (!state.preview || !state.preview.can_accept || reached.current < 3)
    )
      move("controlla", undefined, true);
    if (step !== "modifica" && state.pending) move("modifica", undefined, true);
  }, [step, state.preview, state.pending]);
  const go = (next: string) => {
    if (!inputReady() || state.saving) return;
    if (next === "controlla") reached.current = Math.max(2, reached.current);
    if (next === "riepilogo") {
      if (!state.preview?.can_accept || state.pending) {
        move("controlla");
        return;
      }
      reached.current = 3;
    }
    move(next);
  };
  const target = (kind: "node" | "edge", id: string, field?: string) => {
    backTarget.current = step !== "modifica" ? step : backTarget.current;
    dispatch({ type: "select", selection: { kind, id, field } });
    move("modifica", kind === "node" ? "nodi" : "relazioni");
    window.setTimeout(
      () =>
        document
          .getElementById(`row-${id}`)
          ?.scrollIntoView({ block: "nearest" }),
      0,
    );
  };
  const issueTarget = (issue: Issue) => {
    if (
      issue.target.id &&
      (issue.target.kind === "node" || issue.target.kind === "edge")
    )
      target(issue.target.kind, issue.target.id, issue.target.field);
  };
  const success = (result: RevisionCreated) => {
    bypass.current = true;
    dispatch({ type: "reset" });
    refresh();
    navigate(graphRoute(manualId, result.version.version_id) + "?salvato=1", {
      replace: true,
    });
  };
  const send = async (payload: AcceptRevision) => {
    setError("");
    setUnknown(false);
    dispatch({ type: "saving", value: true });
    try {
      success(
        await postJson<RevisionCreated>(`${endpoint}/revisions`, payload),
      );
    } catch (e) {
      if (
        e instanceof ApiError &&
        (e.status === 409 || e.status === 422 || e.status === 404)
      ) {
        dispatch({ type: "saving", value: false });
        frozen.current = null;
        setError(e.message);
        move("controlla");
      } else {
        setUnknown(true);
        setError(tr("Verifica il salvataggio"));
      }
    }
  };
  const accept = () => {
    if (
      frozen.current ||
      state.saving ||
      !state.preview?.can_accept ||
      !state.preview.has_changes ||
      state.pending ||
      (state.preview.required_acknowledgements.length && !state.acknowledged)
    )
      return;
    const payload: AcceptRevision = {
      preconditions: state.document.preconditions,
      operations: state.operations,
      draft_generation: state.generation,
      request_id: crypto.randomUUID(),
      preview_hash: state.preview.preview_hash,
      note,
      acceptance: {
        decision: "accept_changes",
        acknowledged_issue_ids: state.acknowledged
          ? state.preview.required_acknowledgements
          : [],
      },
    };
    frozen.current = payload;
    void send(payload);
  };
  const resolve = async () => {
    if (!frozen.current) return;
    setRequestState("checking");
    try {
      const result = await getJson<RevisionRequest>(
        `/api/manuals/${encodeURIComponent(manualId)}/revision-requests/${frozen.current.request_id}`,
      );
      if (result.status === "saved") success(result.result);
      else setRequestState(result.status);
    } catch (e) {
      setError((e as Error).message);
      setRequestState("");
    }
  };
  const visible = useMemo(
    () => ({
      nodes: graph.nodes.map((n) => ({ id: n.id, type: n.type, name: n.name })),
      links: graph.edges.map((e) => ({
        id: e.id,
        type: e.type,
        from: e.from,
        to: e.to,
        tier: e.tier,
        derived: e.derived,
        review: edgeReview(e),
      })),
    }),
    [graph],
  );
  const toGraph = (kind: "node" | "edge", id: string) => {
    if (!inputReady()) return;
    dispatch({ type: "select", selection: { kind, id } });
    move("modifica", "grafo");
    window.setTimeout(() => graphHandle.current?.focus(id), 0);
  };
  return (
    <Shell
      workspace
      title={tr("Modifica grafo")}
      trail={[
        { to: "/", label: "Grafi" },
        {
          to: manualRoute(manualId),
          label: manual.data?.machine.name ?? manualId,
        },
        { to: graphRoute(manualId, versionId), label: baseLabel },
      ]}
      actions={
        <>
          {!state.saving && (
            <button
              className="button button-bar"
              onClick={() => navigate(graphRoute(manualId, versionId))}
            >
              {tr("Esci senza salvare")}
            </button>
          )}
          <button
            className="button button-secondary"
            disabled={step === "modifica" || state.saving}
            onClick={() => go(step === "riepilogo" ? "controlla" : "modifica")}
          >
            {tr("Indietro")}
          </button>
          {step !== "riepilogo" ? (
            <button
              className="button button-primary"
              disabled={
                state.saving ||
                (step === "controlla" &&
                  (!state.preview?.can_accept || checking))
              }
              onClick={() =>
                go(step === "modifica" ? "controlla" : "riepilogo")
              }
            >
              {tr(
                step === "modifica" ? "Avanti: controlla" : "Avanti: riepilogo",
              )}
            </button>
          ) : (
            <button
              className="button button-primary"
              disabled={
                state.saving ||
                !state.preview?.has_changes ||
                !state.preview.can_accept ||
                state.pending ||
                Boolean(
                  state.preview.required_acknowledgements.length &&
                    !state.acknowledged,
                )
              }
              onClick={accept}
            >
              {tr(
                state.saving
                  ? "Creazione della nuova versione…"
                  : "Accetta modifiche e crea nuova versione",
              )}
            </button>
          )}
        </>
      }
    >
      <div className="editor-workspace" aria-busy={state.saving}>
        <div className="editor-stepbar">
          <ol>
            {["modifica", "controlla", "riepilogo"].map((s, i) => (
              <li key={s}>
                <button
                  aria-current={step === s ? "step" : undefined}
                  disabled={state.saving || i + 1 > reached.current}
                  onClick={() => go(s)}
                >
                  {i + 1}. {tr(["Modifica", "Controlla", "Riepilogo"][i])}
                </button>
              </li>
            ))}
          </ol>
          <span>
            {tr(
              dirty(state) ? "{n} modifiche non salvate" : "Nessuna modifica",
              { n: state.operations.length },
            )}
          </span>
          <span>{tr("Da {base}", { base: baseLabel })}</span>
        </div>
        <p className="editor-notice">
          {tr(
            "Le modifiche saranno salvate solo quando le accetti. Se esci prima, vengono perse.",
          )}
        </p>
        {!!state.document.source_review.questions?.length && (
          <p className="editor-notice">
            {tr("Domande della fonte ancora aperte: {n}", {
              n: state.document.source_review.questions.length,
            })}{" "}
            ·{" "}
            <Link
              to={
                graphRoute(manualId, state.document.source_review.version_id) +
                "/domande"
              }
            >
              {tr("Consulta le domande della fonte")}
            </Link>
          </p>
        )}
        {error && (
          <Problem message={error} onRetry={unknown ? resolve : check} />
        )}
        {unknown && (
          <div className="editor-notice">
            <p>
              {tr(
                "L’esito della richiesta è incerto. Verifica la stessa richiesta prima di continuare.",
              )}
            </p>
            <button
              disabled={requestState === "checking"}
              className="button button-secondary"
              onClick={resolve}
            >
              {tr("Verifica il salvataggio")}
            </button>
            {requestState === "not_found" && (
              <button
                className="button button-secondary"
                onClick={() => void send(frozen.current!)}
              >
                {tr("Riprova")}
              </button>
            )}
            {requestState === "in_progress" && (
              <p>{tr("Creazione della nuova versione…")}</p>
            )}
          </div>
        )}
        <fieldset disabled={state.saving} className="editor-body">
          <div hidden={step !== "modifica"} className="editor-editing">
            <div className="editor-toolbar">
              <nav aria-label={tr("Viste del grafo")}>
                {["nodi", "relazioni", "grafo"].map((v) => (
                  <button
                    key={v}
                    className="button button-secondary"
                    aria-pressed={tab === v}
                    onClick={() => {
                      if (inputReady()) move("modifica", v);
                    }}
                  >
                    {tr(
                      { nodi: "Nodi", relazioni: "Relazioni", grafo: "Grafo" }[
                        v
                      ]!,
                    )}
                  </button>
                ))}
              </nav>
              <button
                className="button button-secondary"
                disabled={!state.past.length || state.pending}
                onClick={() => dispatch({ type: "undo" })}
              >
                {tr("Annulla modifica")}
              </button>
              <button
                className="button button-secondary"
                disabled={!state.future.length || state.pending}
                onClick={() => dispatch({ type: "redo" })}
              >
                {tr("Ripeti modifica")}
              </button>
              <button
                className="button button-plain"
                onClick={check}
                disabled={checking}
              >
                {tr("Controlla contenuto")}
              </button>
              {backTarget.current && (
                <button
                  className="button button-plain"
                  onClick={() => go(backTarget.current!)}
                >
                  {tr("Torna ai controlli o al riepilogo")}
                </button>
              )}
            </div>
            <div className="editor-content">
              <div className="editor-main">
                <div hidden={tab !== "nodi"}>
                  <NodeTable onGraph={(id) => toGraph("node", id)} />
                </div>
                <div hidden={tab !== "relazioni"}>
                  <RelationTable
                    onNode={(id) => target("node", id)}
                    onGraph={(id) => toGraph("edge", id)}
                  />
                </div>
                <div hidden={tab !== "grafo"} className="editor-graph">
                  <Graph3D
                    handle={graphHandle}
                    nodes={visible.nodes}
                    links={visible.links}
                    onNodeClick={(id) =>
                      dispatch({
                        type: "select",
                        selection: { kind: "node", id },
                      })
                    }
                    onLinkClick={(id) =>
                      dispatch({
                        type: "select",
                        selection: { kind: "edge", id },
                      })
                    }
                    onBackgroundClick={() =>
                      dispatch({ type: "select", selection: null })
                    }
                  />
                  <button
                    className="button button-secondary editor-graph-table"
                    disabled={!state.selection}
                    onClick={() =>
                      state.selection &&
                      target(state.selection.kind, state.selection.id)
                    }
                  >
                    {tr("Vedi in tabella")}
                  </button>
                </div>
              </div>
              <EditorDetails
                manualId={manualId}
                versionId={versionId}
                onPage={(number, evidence) => {
                  if (state.document.source.pdf_available)
                    setPage({ page: number, evidence });
                  else
                    setError(
                      tr(
                        "PDF non disponibile; le citazioni incorporate restano consultabili.",
                      ),
                    );
                }}
                onNode={(id) => target("node", id)}
                onGraph={toGraph}
              />
            </div>
          </div>
          {step === "controlla" && (
            <ReviewPanel
              ontology={state.document.ontology}
              preview={state.preview}
              onTarget={issueTarget}
              onRetry={check}
              checking={checking}
            />
          )}
          {step === "riepilogo" && state.preview && (
            <RevisionSummary
              preview={state.preview}
              base={baseLabel}
              note={note}
              onNote={setNote}
              acknowledged={state.acknowledged}
              onAck={(value) => dispatch({ type: "ack", value })}
              onTarget={target}
            />
          )}
        </fieldset>
      </div>
      {exitDialog}
      {page && (
        <PageDialog
          manualId={manualId}
          versionId={versionId}
          page={page.page}
          marks={page.evidence
            .filter((e) => e.bbox)
            .map((e) => ({ bbox: e.bbox! }))}
          onClose={() => setPage(null)}
        />
      )}
    </Shell>
  );
}
