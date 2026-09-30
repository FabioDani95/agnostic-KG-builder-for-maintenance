import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { graphRoute, manualRoute, postJson, useApi, versionPath } from "../api/client";
import type { Manual, RunStatus } from "../api/types";
import { ProgressBar, SegmentedControl, typing } from "../components/Controls";
import { Icon } from "../components/Icon";
import { Legend } from "../components/Legend";
import { PageDialog } from "../components/PageDialog";
import { Shell } from "../components/Shell";
import { useStatus } from "../status/StatusProvider";
import { Graph3D, type ViewLink, type ViewNode } from "../graph/Graph3D";
import { nextStep } from "../flow/steps";
import { STATIONS, type Station } from "../live/events";
import { counts, type RunState } from "../live/reducer";
import { useRunStream } from "../live/useRunStream";
import {
  formatDuration,
  formatNumber,
  formatUsd,
  plural,
  RELATION_LABEL,
  STATION_LABEL,
  TIER_LABEL,
  TYPE_LABEL,
} from "../text/it";

type Speed = "1" | "4" | "16";

const PHASE_LABEL = { waiting: "In attesa", running: "In corso", done: "Fatta" } as const;

export function stationDetail(station: Station, run: RunState): string {
  const phase = run.stations[station].phase;
  if (phase === "waiting") return "";
  switch (station) {
    case "read":
      return run.pages ? plural(run.pages, "pagina", "pagine") : "Lettura del PDF";
    case "map":
      return run.readPages === null
        ? "Etichetta di ogni pagina"
        : `${plural(run.readPages, "pagina diagnostica", "pagine diagnostiche")} su ${formatNumber(run.pages)}`;
    case "extract":
      return `Unità ${formatNumber(run.units.done)} di ${formatNumber(run.units.total)}`;
    case "check": {
      const { relations, verified } = counts(run);
      if (run.stations.check.step === "split_recheck" && phase === "running") return "Nuova verifica dopo l'unione";
      if (phase === "running" && verified === 0) return "Testimoni per ogni relazione";
      return `${formatNumber(verified)} verificate su ${formatNumber(relations)}`;
    }
    case "merge":
      return phase === "done" ? `${formatNumber(run.merges)} coppie di nomi unite` : "Un nodo per ogni cosa";
    case "ask":
      if (run.finished) return `${formatNumber(run.finished.open_questions)} domande per te`;
      return run.agentAnswers ? `${formatNumber(run.agentAnswers)} risposte dell'agente` : "Domande sui dubbi";
  }
}

function edgeText(run: RunState, id: string): string {
  const edge = run.edges[id];
  const from = run.nodes[edge.from]?.name ?? "";
  const to = run.nodes[edge.to]?.name ?? "";
  return `«${from}» ${RELATION_LABEL[edge.type] ?? edge.type} «${to}»`;
}

export function LiveRun() {
  const { manualId = "", versionId = "" } = useParams();
  const manual = useApi<Manual>(`/api/manuals/${encodeURIComponent(manualId)}`);
  const version = manual.data?.versions.find((item) => item.version_id === versionId);
  const live = version?.status === "running";
  const [speed, setSpeed] = useState<Speed>("4");
  const [paused, setPaused] = useState(false);
  const url = version ? `${versionPath(manualId, versionId)}/events` : null;
  const { state: run, arrivedAt, unavailable } = useRunStream(url, live ? 1 : Number(speed), paused);
  const [selected, setSelected] = useState<string | null>(null);
  const [page, setPage] = useState<number | null>(null);
  const [now, setNow] = useState(() => performance.now());
  const [stopping, setStopping] = useState(false);
  const [handoffClosed, setHandoffClosed] = useState(false);
  const ended = Boolean(run.finished || run.failed);

  // Esc closes the node panel, unless a page of the manual is open on top.
  useEffect(() => {
    const press = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !typing(event.target) && !document.querySelector("dialog[open]")) setSelected(null);
    };
    window.addEventListener("keydown", press);
    return () => window.removeEventListener("keydown", press);
  }, []);

  // The clock moves between events, at the replay speed; it stops when the run ends or pauses.
  useEffect(() => {
    if (ended || paused || run.seq === 0) return;
    const timer = window.setInterval(() => setNow(performance.now()), 1000);
    return () => window.clearInterval(timer);
  }, [ended, paused, run.seq]);
  const elapsed = ended || paused ? run.t : run.t + (Math.max(0, now - arrivedAt) / 1000) * (live ? 1 : Number(speed));

  const nodes = useMemo<ViewNode[]>(() => Object.values(run.nodes), [run.nodes]);
  const { settings } = useStatus();
  const showCode = settings?.show_code_relations ?? true;
  const links = useMemo<ViewLink[]>(
    () => Object.values(run.edges).filter((edge) => showCode || !edge.derived),
    [run.edges, showCode],
  );
  const typeCounts = useMemo(() => {
    const byType: Record<string, number> = {};
    for (const node of nodes) byType[node.type] = (byType[node.type] ?? 0) + 1;
    return byType;
  }, [nodes]);
  const total = counts(run);
  const node = selected ? run.nodes[selected] : undefined;
  const base = `/manuali/${encodeURIComponent(manualId)}/versioni/${encodeURIComponent(versionId)}`;
  const openQuestions = run.finished?.open_questions ?? 0;

  const stop = async () => {
    setStopping(true);
    try {
      await postJson(`${versionPath(manualId, versionId)}/stop`);
    } finally {
      setStopping(false);
    }
  };

  const latest = run.recent.find((id) => run.edges[id]);
  const next = run.finished
    ? nextStep(manualId, { version_id: versionId, status: run.finished.status as RunStatus, open_questions: openQuestions })
    : null;

  return (
    <Shell
      workspace
      trail={[
        { to: "/", label: "Grafi" },
        { to: manualRoute(manualId), label: manual.data?.machine.name ?? "Manuale" },
      ]}
      title={live ? "Esecuzione" : "Replay"}
      actions={
        <>
          <dl className="readouts">
            <div>
              <dt>{live ? "Tempo" : `Replay ×${speed}`}</dt>
              <dd>{formatDuration(elapsed)}</dd>
            </div>
            <div>
              <dt>{run.costEstimated ? "Costo stimato" : "Costo"}</dt>
              <dd>{formatUsd(run.cost)}</dd>
            </div>
          </dl>
          {!live && !ended && (
            <>
              <SegmentedControl<Speed>
                label="Velocità del replay"
                value={speed}
                onChange={setSpeed}
                options={[
                  { value: "1", label: "1×" },
                  { value: "4", label: "4×" },
                  { value: "16", label: "16×" },
                ]}
              />
              <button type="button" className="button button-bar" onClick={() => setPaused((value) => !value)}>
                <Icon name={paused ? "play" : "pause"} />
                {paused ? "Riprendi" : "Pausa"}
              </button>
            </>
          )}
          {live && !ended && (
            <button type="button" className="button button-bar" disabled={stopping} onClick={stop}>
              <Icon name="stop" />
              Ferma
            </button>
          )}
          {openQuestions > 0 && (
            <Link to={`${base}/domande`} className="button button-bar">
              <Icon name="question" />
              {openQuestions === 1 ? "1 domanda per te" : `${formatNumber(openQuestions)} domande per te`}
            </Link>
          )}
          {run.finished && (
            <Link to={base} className="button button-bar">
              <Icon name="graph" />
              Apri il grafo
            </Link>
          )}
        </>
      }
    >
      <div className="workspace">
        <aside className="dock dock-left" aria-label="Stazioni">
          {unavailable && (
            <section className="panel-section">
              <p className="alert t-small">Questa esecuzione non si può rigiocare su questo computer: manca il suo stato salvato.</p>
            </section>
          )}
          <section className="panel-section">
            <h2 className="panel-title">Stazioni</h2>
            <ol className="stations">
              {STATIONS.map((station) => {
                const phase = run.stations[station].phase;
                return (
                  <li key={station}>
                    <span className="lamp" data-phase={phase} aria-hidden="true" />
                    <span className={phase === "running" ? "strong" : undefined}>{STATION_LABEL[station]}</span>
                    <span className="t-small secondary">{PHASE_LABEL[phase]}</span>
                    <span className="station-detail">{stationDetail(station, run)}</span>
                    {station === "extract" && phase !== "waiting" && (
                      <span className="station-progress">
                        <ProgressBar value={run.units.done} total={run.units.total} label="Unità lette" />
                      </span>
                    )}
                  </li>
                );
              })}
            </ol>
          </section>
          <section className="panel-section">
            <h2 className="panel-title">Legenda</h2>
            <Legend counts={typeCounts} />
          </section>
        </aside>

        <div className="canvas">
          <Graph3D
            nodes={nodes}
            links={links}
            labels={settings?.node_labels ?? false}
            onNodeClick={setSelected}
            onBackgroundClick={() => setSelected(null)}
          />
          {ended && !handoffClosed && (
            <div className="handoff" role="status">
              <button type="button" className="icon-button handoff-close" aria-label="Chiudi" onClick={() => setHandoffClosed(true)}>
                <Icon name="x" />
              </button>
              {run.finished && next ? (
                <>
                  <p className="handoff-title">
                    <span className="lamp" data-phase="done" aria-hidden="true" />
                    Estrazione finita
                    <span className="mono secondary">
                      {formatDuration(run.t)} · {formatUsd(run.cost)}
                    </span>
                  </p>
                  <p className="secondary">
                    {formatNumber(run.finished.verified)} relazioni verificate, {formatNumber(run.finished.doubtful)} in dubbio.{" "}
                    {openQuestions > 0
                      ? `${openQuestions === 1 ? "Una domanda aspetta" : `${formatNumber(openQuestions)} domande aspettano`} te: il grafo non si approva prima.`
                      : next.urgent
                        ? "Il grafo aspetta la tua approvazione."
                        : "Nessuna domanda per te."}
                  </p>
                  <div className="row">
                    <Link to={next.to} className="button button-primary">
                      {next.label}
                      <Icon name="arrow-right" />
                    </Link>
                    {next.to !== graphRoute(manualId, versionId) && (
                      <Link to={graphRoute(manualId, versionId)} className="button button-secondary">
                        Apri il grafo
                      </Link>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <p className="handoff-title">
                    <span className="lamp" data-phase="failed" aria-hidden="true" />
                    L'esecuzione si è fermata
                  </p>
                  <p className="secondary">{run.failed || "Senza un messaggio."}</p>
                  <div className="row">
                    <Link to={manualRoute(manualId)} className="button button-secondary">
                      Torna al manuale
                    </Link>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {node && (
          <aside className="dock dock-right" aria-label="Nodo">
            <section className="panel-section">
              <div className="panel-head">
                <h2 className="panel-title">{TYPE_LABEL[node.type] ?? node.type}</h2>
                <button type="button" className="button button-secondary button-icon" aria-label="Chiudi" onClick={() => setSelected(null)}>
                  <Icon name="x" />
                </button>
              </div>
              <p className="panel-name">{node.name}</p>
              {(node.pages ?? []).length > 0 && (
                <dl className="data-list" style={{ gridTemplateColumns: "72px 1fr" }}>
                  <dt>Pagine</dt>
                  <dd className="mono">{node.pages!.join(", ")}</dd>
                </dl>
              )}
              {(node.pages ?? []).map((number) => (
                <button key={number} type="button" className="button button-plain" style={{ paddingLeft: 0 }} onClick={() => setPage(number)}>
                  <Icon name="external-link" size={14} />
                  Apri la pagina {number}
                </button>
              ))}
            </section>
          </aside>
        )}

        <footer className="statusbar">
          <dl>
            <div>
              <dt>Nodi</dt>
              <dd>{formatNumber(total.nodes)}</dd>
            </div>
            <div>
              <dt>Relazioni</dt>
              <dd>{formatNumber(total.relations)}</dd>
            </div>
            <div>
              <dt>Verificate</dt>
              <dd>{formatNumber(total.verified)}</dd>
            </div>
          </dl>
          <p className="statusbar-log">
            {latest && (
              <>
                Ultima relazione: <strong>{edgeText(run, latest)}</strong>
                {run.edges[latest].pages?.length ? ` · p. ${run.edges[latest].pages!.join(", ")}` : ""}
                {" · "}
                {run.edges[latest].derived ? "Aggiunta dal sistema" : TIER_LABEL[run.edges[latest].tier ?? "proposed"]}
              </>
            )}
          </p>
        </footer>
      </div>

      {page !== null && <PageDialog manualId={manualId} page={page} marks={[]} onClose={() => setPage(null)} />}
    </Shell>
  );
}
