import { Link, useNavigate } from "react-router-dom";
import { questionsRoute } from "../api/client";
import type { ManualRow } from "../api/types";
import { Monogram, StatusBadge } from "../components/Controls";
import { Loading, Problem } from "../components/Feedback";
import { Icon } from "../components/Icon";
import { Shell } from "../components/Shell";
import { type Column, Table } from "../components/Table";
import { nextStep } from "../flow/steps";
import { useStatus } from "../status/StatusProvider";
import { formatNumber, manualName, versionLabel } from "../text/it";

const manualColumn: Column<ManualRow> = {
  key: "manuale",
  label: "Manuale",
  span: 4,
  render: (row) => (
    <span className="with-mark">
      <Monogram machine={row.machine} />
      <span>{manualName(row.machine)}</span>
    </span>
  ),
};

const versionColumn: Column<ManualRow> = {
  key: "versione",
  label: "Versione",
  span: 2,
  render: (row) => (row.latest ? versionLabel(row.latest) : ""),
};

const STEP_COLUMNS: Column<ManualRow>[] = [
  manualColumn,
  versionColumn,
  {
    key: "stato",
    label: "Stato",
    span: 2,
    render: (row) => row.latest && <StatusBadge status={row.latest.status} decidedBy={row.latest.decided_by} />,
  },
  {
    key: "passo",
    label: "Prossimo passo",
    span: 4,
    render: (row) => {
      const step = nextStep(row.id, row.latest!);
      return (
        <span className="next" data-urgent={step.urgent}>
          {step.label}
          <Icon name="arrow-right" size={14} />
        </span>
      );
    },
  },
];

const DOUBT_COLUMNS: Column<ManualRow>[] = [
  manualColumn,
  versionColumn,
  {
    key: "domande",
    label: "Domande senza risposta",
    span: 2,
    numeric: true,
    render: (row) => formatNumber(row.latest?.open_questions),
  },
  {
    key: "passo",
    label: "",
    span: 4,
    render: () => (
      <span className="next">
        Rivedi i dubbi
        <Icon name="arrow-right" size={14} />
      </span>
    ),
  },
];

/**
 * What waits for a person, across all the graphs: first what holds a run up (questions to answer,
 * a graph to approve), then the run in progress, then approved graphs that still carry doubts.
 */
export function Inbox() {
  const navigate = useNavigate();
  const { inbox, manuals, error, refresh } = useStatus();
  const open = (row: ManualRow) => navigate(nextStep(row.id, row.latest!).to);

  return (
    <Shell title="Tocca a te">
      {error && <Problem message={`Non riesco a leggere i grafi. ${error}`} onRetry={refresh} />}
      {!inbox && !manuals && !error && <Loading label="Cerco quello che aspetta te" />}
      {inbox && (
        <div className="stack">
          <section className="card">
            <header className="card-head">
              <h2 className="card-title">
                Aspettano te <span className="card-count">{formatNumber(inbox.waiting.length)}</span>
              </h2>
              <span className="t-small secondary">L'esecuzione resta ferma finché non rispondi o approvi.</span>
            </header>
            {inbox.waiting.length === 0 ? (
              <div className="empty">
                <p>Nessun grafo aspetta te.</p>
                <Link to="/nuovo" className="button button-secondary">
                  <Icon name="plus" />
                  Nuovo grafo
                </Link>
              </div>
            ) : (
              <Table label="Aspettano te" columns={STEP_COLUMNS} rows={inbox.waiting} rowKey={(row) => row.id} onOpen={open} empty="" />
            )}
          </section>

          {inbox.running.length > 0 && (
            <section className="card">
              <header className="card-head">
                <h2 className="card-title">
                  In corso <span className="card-count">{formatNumber(inbox.running.length)}</span>
                </h2>
              </header>
              <Table label="In corso" columns={STEP_COLUMNS} rows={inbox.running} rowKey={(row) => row.id} onOpen={open} empty="" />
            </section>
          )}

          <section className="card">
            <header className="card-head">
              <h2 className="card-title">
                Dubbi nei grafi approvati <span className="card-count">{formatNumber(inbox.doubts.length)}</span>
              </h2>
              <span className="t-small secondary">
                Non bloccano nulla. In un grafo della campagna la prima risposta ne crea una copia.
              </span>
            </header>
            <Table
              label="Dubbi nei grafi approvati"
              columns={DOUBT_COLUMNS}
              rows={inbox.doubts}
              rowKey={(row) => row.id}
              onOpen={(row) => navigate(questionsRoute(row.id, row.latest!.version_id))}
              empty="Nessun dubbio aperto nei grafi approvati."
            />
          </section>
        </div>
      )}
    </Shell>
  );
}
