import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApi } from "../api/client";
import type { RunRow } from "../api/types";
import { Monogram, SegmentedControl, StatusBadge } from "../components/Controls";
import { Loading, Problem } from "../components/Feedback";
import { Shell } from "../components/Shell";
import { type Column, nextSorting, type Sorting, Table } from "../components/Table";
import { nextStep } from "../flow/steps";
import { formatDate, formatDuration, formatNumber, formatShortDate, formatUsd, manualName, statusLabel, versionLabel } from "../text/it";
import { tr } from "../i18n/i18n";

type Origin = "all" | "workspace" | "campaign";

const COLUMNS: Column<RunRow>[] = [
  {
    key: "data",
    label: "Data",
    span: 2,
    sort: (row) => row.date,
    render: (row) => (
      <span className="mono" title={formatDate(row.date)}>
        {formatShortDate(row.date)}
      </span>
    ),
  },
  {
    key: "manuale",
    label: "Manuale",
    span: 3,
    sort: (row) => manualName(row.machine),
    render: (row) => (
      <span className="with-mark">
        <Monogram machine={row.machine} />
        <span>{manualName(row.machine)}</span>
      </span>
    ),
  },
  { key: "versione", label: "Versione", span: 2, sort: (row) => versionLabel(row), render: (row) => versionLabel(row) },
  {
    key: "esito",
    label: "Esito",
    span: 3,
    sort: (row) => statusLabel(row.status, row.decided_by),
    render: (row) => <StatusBadge status={row.status} decidedBy={row.decided_by} />,
  },
  {
    key: "durata",
    label: "Durata",
    span: 1,
    numeric: true,
    sort: (row) => row.seconds,
    render: (row) => (row.seconds ? <span className="mono">{formatDuration(row.seconds)}</span> : ""),
  },
  {
    key: "costo",
    label: "Costo (USD)",
    span: 1,
    numeric: true,
    sort: (row) => row.cost_usd,
    render: (row) => (row.cost_usd != null ? <span className="mono">{formatUsd(row.cost_usd).replace(" USD", "")}</span> : ""),
  },
];

/** Every run of every manual, newest first, with its time and cost. */
export function Runs() {
  const navigate = useNavigate();
  const { data, error, loading, reload } = useApi<RunRow[]>("/api/runs");
  const [origin, setOrigin] = useState<Origin>("all");
  const [sorting, setSorting] = useState<Sorting | null>(null);
  const rows = useMemo(() => (data ?? []).filter((row) => origin === "all" || row.origin === origin), [data, origin]);

  return (
    <Shell title={tr("Esecuzioni")}>
      <div className="stack">
        <section className="card">
          <header className="card-head">
            <h2 className="card-title">
              {tr("Esecuzioni")} {data && <span className="card-count">{formatNumber(rows.length)}</span>}
            </h2>
            <div className="row" style={{ gap: 16 }}>
              <SegmentedControl<Origin>
                label={tr("Quali esecuzioni mostrare")}
                value={origin}
                onChange={setOrigin}
                options={[
                  { value: "all", label: "Tutte" },
                  { value: "workspace", label: "Dall'interfaccia" },
                  { value: "campaign", label: "Campagna" },
                ]}
              />
            </div>
          </header>
          {error && <Problem message={`${tr("Non riesco a leggere le esecuzioni.")} ${error}`} onRetry={reload} />}
          {loading && !data && <Loading label={tr("Carico le esecuzioni")} />}
          {data && (
            <Table
              label={tr("Esecuzioni")}
              columns={COLUMNS}
              rows={rows}
              rowKey={(row) => `${row.manual_id}/${row.version_id}`}
              onOpen={(row) => navigate(nextStep(row.manual_id, row).to)}
              empty="Nessuna esecuzione in questo gruppo."
              sorting={sorting}
              onSort={(key) => setSorting(nextSorting(sorting, key))}
            />
          )}
        </section>
      </div>
    </Shell>
  );
}
