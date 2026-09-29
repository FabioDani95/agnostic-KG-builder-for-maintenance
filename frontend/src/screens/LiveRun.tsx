import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { postJson, useApi, versionPath } from "../api/client";
import type { Manual } from "../api/types";
import { BackLink, ProgressBar, SegmentedControl } from "../components/Controls";
import { Icon } from "../components/Icon";
import { Legend } from "../components/Legend";
import { PageDialog } from "../components/PageDialog";
import { Graph3D, type ViewLink, type ViewNode } from "../graph/Graph3D";
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
      return relations ? `${formatNumber(verified)} verificate su ${formatNumber(relations)}` : "Testimoni per ogni relazione";
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
  const ended = Boolean(run.finished || run.failed);

  // The clock moves between events, at the replay speed; it stops when the run ends or pauses.
  useEffect(() => {
    if (ended || paused || run.seq === 0) return;
    const timer = window.setInterval(() => setNow(performance.now()), 1000);
    return () => window.clearInterval(timer);
  }, [ended, paused, run.seq]);
  const elapsed = ended || paused ? run.t : run.t + (Math.max(0, now - arrivedAt) / 1000) * (live ? 1 : Number(speed));

  const nodes = useMemo<ViewNode[]>(() => Object.values(run.nodes), [run.nodes]);
  const links = useMemo<ViewLink[]>(() => Object.values(run.edges), [run.edges]);
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

  return (
    <div className="stage">
      <Graph3D nodes={nodes} links={links} onNodeClick={setSelected} onBackgroundClick={() => setSelected(null)} />

      <header className="stage-bar glass">
        <BackLink to={`/manuali/${encodeURIComponent(manualId)}`}>{manual.data?.machine.name ?? "Manuale"}</BackLink>
        <span className="stage-bar-title" />
        <dl className="row">
          <div className="row" style={{ gap: 8 }}>
            <dt className="secondary">{live ? "Tempo" : `Replay ×${speed}`}</dt>
            <dd className="num" style={{ minWidth: 48 }}>{formatDuration(elapsed)}</dd>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <dt className="secondary">{run.costEstimated ? "Costo stimato" : "Costo"}</dt>
            <dd className="num" style={{ minWidth: 96 }}>{formatUsd(run.cost)}</dd>
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
            <button type="button" className="button button-secondary" onClick={() => setPaused((value) => !value)}>
              <Icon name={paused ? "play" : "pause"} size={16} />
              {paused ? "Riprendi" : "Pausa"}
            </button>
          </>
        )}
        {live && !ended && (
          <button type="button" className="button button-secondary" disabled={stopping} onClick={stop}>
            Ferma
          </button>
        )}
        {openQuestions > 0 && (
          <Link to={`${base}/domande`} className="button button-secondary">
            {openQuestions === 1 ? "1 domanda per te" : `${formatNumber(openQuestions)} domande per te`}
          </Link>
        )}
        {run.finished && (
          <Link to={base} className="button button-primary">
            Apri il grafo
          </Link>
        )}
      </header>

      <aside className="stage-left glass" aria-label="Stazioni">
        <section className="panel-section">
          <h2 className="panel-title">Stazioni</h2>
          <ol className="stage-list">
            {STATIONS.map((station) => {
              const phase = run.stations[station].phase;
              return (
                <li key={station} style={{ minHeight: 72 }}>
                  <div className="row" style={{ justifyContent: "space-between" }}>
                    <span className={phase === "running" ? "strong" : undefined}>{STATION_LABEL[station]}</span>
                    <span className="secondary">{PHASE_LABEL[phase]}</span>
                  </div>
                  <p className="t-small secondary">{stationDetail(station, run)}</p>
                  {station === "extract" && phase !== "waiting" && (
                    <div style={{ marginTop: 8 }}>
                      <ProgressBar value={run.units.done} total={run.units.total} label="Unità lette" />
                    </div>
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

      <aside className="stage-right glass" aria-label={node ? "Nodo" : "Relazioni trovate"}>
        {unavailable && <p className="message">Questa esecuzione non si può rigiocare su questo computer: manca il suo stato salvato.</p>}
        {run.failed && (
          <section className="panel-section">
            <h2 className="panel-title">L'esecuzione si è fermata</h2>
            <p className="t-small secondary">{run.failed}</p>
          </section>
        )}
        {node ? (
          <section className="panel-section">
            <button type="button" className="button button-plain" style={{ paddingLeft: 0 }} onClick={() => setSelected(null)}>
              <Icon name="chevron-left" size={16} />
              Relazioni trovate
            </button>
            <h2 className="panel-title">{node.name}</h2>
            <dl className="data-list" style={{ gridTemplateColumns: "96px 1fr" }}>
              <dt>Tipo</dt>
              <dd>{TYPE_LABEL[node.type] ?? node.type}</dd>
              {(node.pages ?? []).length > 0 && (
                <>
                  <dt>Pagine</dt>
                  <dd>{node.pages!.join(", ")}</dd>
                </>
              )}
            </dl>
            {(node.pages ?? []).map((number) => (
              <button key={number} type="button" className="button button-plain" style={{ paddingLeft: 0 }} onClick={() => setPage(number)}>
                Apri la pagina {number}
              </button>
            ))}
          </section>
        ) : (
          <section className="panel-section">
            <h2 className="panel-title">Relazioni trovate</h2>
            {run.recent.length === 0 && !unavailable && <p className="message">Le relazioni compaiono qui appena il sistema le trova.</p>}
            <ol className="stage-list">
              {run.recent
                .filter((id) => run.edges[id])
                .slice(0, 60)
                .map((id) => {
                  const edge = run.edges[id];
                  return (
                    <li key={id}>
                      <p>{edgeText(run, id)}</p>
                      <p className="row t-small secondary" style={{ justifyContent: "space-between" }}>
                        <span>{edge.pages?.length ? `Pagina ${edge.pages.join(", ")}` : ""}</span>
                        <span>{edge.derived ? "Aggiunta dal sistema" : TIER_LABEL[edge.tier ?? "proposed"]}</span>
                      </p>
                    </li>
                  );
                })}
            </ol>
          </section>
        )}
      </aside>

      <div className="stage-counters">
        <dl className="glass">
          <div>
            <dt>Nodi</dt>
            <dd className="num">{formatNumber(total.nodes)}</dd>
          </div>
          <div>
            <dt>Relazioni</dt>
            <dd className="num">{formatNumber(total.relations)}</dd>
          </div>
          <div>
            <dt>Verificate</dt>
            <dd className="num">{formatNumber(total.verified)}</dd>
          </div>
        </dl>
      </div>

      {page !== null && <PageDialog manualId={manualId} page={page} marks={[]} onClose={() => setPage(null)} />}
    </div>
  );
}
