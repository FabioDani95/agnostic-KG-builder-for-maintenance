import { Link, useNavigate, useParams } from "react-router-dom";
import { graphRoute, liveRoute, useApi, versionPath } from "../api/client";
import type { Manual, Version } from "../api/types";
import { StatusBadge } from "../components/Controls";
import { Loading, Problem } from "../components/Feedback";
import { Icon } from "../components/Icon";
import { Shell } from "../components/Shell";
import { type Column, Table } from "../components/Table";
import { lifecycle, nextStep, type Step } from "../flow/steps";
import { formatDate, formatDuration, formatNumber, formatShortDate, formatUsd, versionLabel } from "../text/it";

const COLUMNS: Column<Version>[] = [
  {
    key: "date",
    label: "Data",
    span: 2,
    render: (row) => (
      <span className="mono" title={formatDate(row.date)}>
        {formatShortDate(row.date)}
      </span>
    ),
  },
  { key: "version", label: "Versione", span: 2, render: (row) => versionLabel(row) },
  { key: "commit", label: "Codice", span: 1, render: (row) => <span className="mono">{row.commit}</span> },
  { key: "verified", label: "Verificate", span: 1, numeric: true, render: (row) => formatNumber(row.verified) },
  {
    key: "seconds",
    label: "Durata",
    span: 1,
    numeric: true,
    render: (row) => (row.seconds ? <span className="mono">{formatDuration(row.seconds)}</span> : ""),
  },
  { key: "questions", label: "Domande", span: 1, numeric: true, render: (row) => formatNumber(row.open_questions) },
  {
    key: "cost",
    label: "Costo (USD)",
    span: 1,
    numeric: true,
    render: (row) => (row.cost_usd != null ? <span className="mono">{formatUsd(row.cost_usd).replace(" USD", "")}</span> : ""),
  },
  { key: "status", label: "Esito", span: 3, render: (row) => <StatusBadge status={row.status} decidedBy={row.decided_by} /> },
];

export function Steps({ steps }: { steps: Step[] }) {
  return (
    <ol className="steps" aria-label="A che punto è il grafo">
      {steps.map((step) => (
        <li key={step.key} className="step" data-state={step.state}>
          <span className="step-lamp" aria-hidden="true">
            {step.state === "done" && <Icon name="check" size={12} />}
            {step.state === "failed" && <Icon name="x" size={12} />}
          </span>
          <span className="step-name">{step.label}</span>
          <span className="step-detail">{step.detail}</span>
        </li>
      ))}
    </ol>
  );
}

/** The latest version: where it stands, its figures, and the one thing to do next. */
function CurrentVersion({ manualId, version }: { manualId: string; version: Version }) {
  const next = nextStep(manualId, version);
  const opensGraph = next.to === graphRoute(manualId, version.version_id);
  const hasGraph = version.status !== "running" && version.status !== "failed";
  return (
    <section className="card">
      <header className="card-head">
        <h2 className="card-title">
          Versione attuale <span className="card-count">{versionLabel(version)}</span>
        </h2>
        <StatusBadge status={version.status} decidedBy={version.decided_by} />
      </header>
      <Steps steps={lifecycle(version)} />
      <dl className="figures">
        <div>
          <dt>Verificate</dt>
          <dd>{formatNumber(version.verified)}</dd>
        </div>
        <div>
          <dt>In dubbio</dt>
          <dd>{formatNumber(version.doubtful)}</dd>
        </div>
        <div>
          <dt>Escluse</dt>
          <dd>{formatNumber(version.excluded)}</dd>
        </div>
        <div>
          <dt>Domande</dt>
          <dd>{formatNumber(version.open_questions)}</dd>
        </div>
        <div>
          <dt>Durata</dt>
          <dd>{version.seconds ? formatDuration(version.seconds) : "–"}</dd>
        </div>
        <div>
          <dt>Costo</dt>
          <dd>{version.cost_usd != null ? formatUsd(version.cost_usd) : "–"}</dd>
        </div>
      </dl>
      <div className="card-actions">
        <Link to={next.to} className="button button-primary">
          {next.label}
          <Icon name="arrow-right" />
        </Link>
        {!opensGraph && hasGraph && (
          <Link to={graphRoute(manualId, version.version_id)} className="button button-secondary">
            <Icon name="graph" />
            Apri il grafo
          </Link>
        )}
        {version.replay && hasGraph && (
          <Link to={liveRoute(manualId, version.version_id)} className="button button-plain">
            <Icon name="play" />
            Rigioca l'esecuzione
          </Link>
        )}
        <span className="t-small secondary" style={{ marginLeft: "auto" }}>
          {formatDate(version.date)} · codice <span className="mono">{version.commit}</span>
        </span>
      </div>
    </section>
  );
}

export function ManualScreen() {
  const { manualId = "" } = useParams();
  const navigate = useNavigate();
  const { data: manual, error, loading, reload } = useApi<Manual>(`/api/manuals/${encodeURIComponent(manualId)}`);
  const current = manual?.versions[0];
  const open = (version: Version) =>
    navigate(
      version.status === "running" || version.status === "failed"
        ? liveRoute(manualId, version.version_id)
        : graphRoute(manualId, version.version_id),
    );

  return (
    <Shell
      trail={[{ to: "/", label: "Grafi" }]}
      title={manual?.machine.name ?? (error ? "Manuale" : "")}
      actions={
        manual && (
          <Link to={`/nuovo?manuale=${encodeURIComponent(manualId)}`} className="button button-bar">
            <Icon name="plus" />
            Nuova versione
          </Link>
        )
      }
    >
      {error && <Problem message={`Non trovo questo manuale. ${error}`} onRetry={reload} />}
      {loading && !manual && <Loading label="Carico il manuale" />}
      {manual && (
        <div className="stack">
          <section className="card">
            <header className="card-head">
              <h2 className="card-title">Macchina</h2>
            </header>
            <dl className="specs">
              <div>
                <dt>Marca</dt>
                <dd>{manual.machine.brand}</dd>
              </div>
              <div>
                <dt>Modello</dt>
                <dd>{manual.machine.model}</dd>
              </div>
              <div>
                <dt>Tipo</dt>
                <dd title={manual.machine.type}>{manual.machine.type}</dd>
              </div>
              <div>
                <dt>Pagine</dt>
                <dd className="mono">{formatNumber(manual.pages)}</dd>
              </div>
              <div>
                <dt>Origine</dt>
                <dd>{manual.origin === "campaign" ? "Campagna di valutazione" : "Caricato dall'interfaccia"}</dd>
              </div>
            </dl>
          </section>

          {current ? (
            <CurrentVersion manualId={manualId} version={current} />
          ) : (
            <section className="card">
              <div className="empty">
                <p>Questo manuale non ha ancora un grafo.</p>
                <Link to={`/nuovo?manuale=${encodeURIComponent(manualId)}`} className="button button-primary">
                  <Icon name="play" />
                  Avvia la prima esecuzione
                </Link>
              </div>
            </section>
          )}

          <section className="card">
            <header className="card-head">
              <h2 className="card-title">
                Versioni <span className="card-count">{formatNumber(manual.versions.length)}</span>
              </h2>
            </header>
            <Table
              label="Versioni"
              columns={COLUMNS}
              rows={manual.versions}
              rowKey={(row) => row.version_id}
              onOpen={open}
              empty="Nessuna versione: questo manuale non è ancora stato elaborato."
              actions={(row) =>
                row.replay &&
                row.status !== "running" && (
                  <Link
                    to={liveRoute(manualId, row.version_id)}
                    className="icon-button"
                    aria-label={`Rigioca l'esecuzione ${versionLabel(row)}`}
                    title="Rigioca l'esecuzione"
                  >
                    <Icon name="play" />
                  </Link>
                )
              }
            />
          </section>
        </div>
      )}
    </Shell>
  );
}

export const graphUrl = (manualId: string, versionId: string) => `${versionPath(manualId, versionId)}/graph`;
