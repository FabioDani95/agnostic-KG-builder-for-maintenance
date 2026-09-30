import { useMemo } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { graphRoute, liveRoute, manualRoute, useApi } from "../api/client";
import type { ManualRow } from "../api/types";
import { Problem, Loading } from "../components/Feedback";
import { Monogram, SearchField, SegmentedControl, StatusBadge } from "../components/Controls";
import { Icon } from "../components/Icon";
import { Shell } from "../components/Shell";
import { type Column, nextSorting, type Sorting, Table } from "../components/Table";
import { formatDuration, formatNumber, formatUsd, manualName, statusLabel, versionLabel } from "../text/it";
import { tr } from "../i18n/i18n";

type Filter = "all" | "review" | "approved";

// The filter as it reads in the address, so a view can be shared and survives «back».
const FILTER_PARAM: Record<Filter, string | null> = { all: null, review: "da-rivedere", approved: "approvati" };

export function needsReview(row: ManualRow): boolean {
  const latest = row.latest;
  return !!latest && (latest.status === "awaiting_approval" || latest.open_questions > 0);
}

export function matches(row: ManualRow, query: string): boolean {
  const text = query.trim().toLowerCase();
  if (!text) return true;
  const { name, brand, model, type } = row.machine;
  return [row.id, name, brand, model, type].some((value) => value.toLowerCase().includes(text));
}

const COLUMNS: Column<ManualRow>[] = [
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
  { key: "pagine", label: "Pagine", span: 1, numeric: true, sort: (row) => row.pages, render: (row) => formatNumber(row.pages) },
  {
    key: "versione",
    label: "Versione",
    span: 2,
    sort: (row) => row.latest?.date,
    render: (row) => (row.latest ? versionLabel(row.latest) : ""),
  },
  {
    key: "verificate",
    label: "Relazioni verificate",
    span: 1,
    numeric: true,
    sort: (row) => row.latest?.verified,
    render: (row) => formatNumber(row.latest?.verified),
  },
  {
    key: "domande",
    label: "Domande aperte",
    span: 1,
    numeric: true,
    sort: (row) => row.latest?.open_questions,
    render: (row) => formatNumber(row.latest?.open_questions),
  },
  {
    key: "durata",
    label: "Durata",
    span: 1,
    numeric: true,
    sort: (row) => row.latest?.seconds,
    render: (row) => (row.latest?.seconds ? <span className="mono">{formatDuration(row.latest.seconds)}</span> : ""),
  },
  {
    key: "costo",
    label: "Costo (USD)",
    span: 1,
    numeric: true,
    sort: (row) => row.latest?.cost_usd,
    render: (row) =>
      row.latest?.cost_usd != null ? <span className="mono">{formatUsd(row.latest.cost_usd).replace(" USD", "")}</span> : "",
  },
  {
    key: "stato",
    label: "Stato",
    span: 2,
    sort: (row) => (row.latest ? statusLabel(row.latest.status, row.latest.decided_by) : null),
    render: (row) =>
      row.latest ? <StatusBadge status={row.latest.status} decidedBy={row.latest.decided_by} /> : tr("Nessuna versione"),
  },
];

function RowActions({ row }: { row: ManualRow }) {
  const latest = row.latest;
  if (!latest) return null;
  const live = latest.status === "running" || latest.status === "failed";
  const label = tr(latest.status === "running" ? "Segui l'esecuzione" : live ? "Vedi dove si è fermata" : "Apri il grafo");
  return (
    <Link
      to={live ? liveRoute(row.id, latest.version_id) : graphRoute(row.id, latest.version_id)}
      className="icon-button"
      aria-label={`${label}: ${row.machine.name}`}
      title={label}
    >
      <Icon name={live ? "activity" : "graph"} />
    </Link>
  );
}

export function Library() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const { data, error, loading, reload } = useApi<ManualRow[]>("/api/manuals");
  const query = params.get("cerca") ?? "";
  const filter = (Object.keys(FILTER_PARAM) as Filter[]).find((key) => FILTER_PARAM[key] === params.get("mostra")) ?? "all";
  const sorting: Sorting | null = params.get("ordina")
    ? { key: params.get("ordina")!, direction: params.get("verso") === "giu" ? "desc" : "asc" }
    : null;
  const update = (changes: Record<string, string | null>) =>
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        for (const [key, value] of Object.entries(changes)) {
          if (value) next.set(key, value);
          else next.delete(key);
        }
        return next;
      },
      { replace: true },
    );

  const rows = useMemo(
    () =>
      (data ?? [])
        .filter((row) => matches(row, query))
        .filter((row) =>
          filter === "all" ? true : filter === "review" ? needsReview(row) : row.latest?.status === "approved",
        ),
    [data, query, filter],
  );
  const empty = query.trim()
    ? tr("Nessun manuale corrisponde a «{query}».", { query: query.trim() })
    : filter === "all"
      ? "Nessun manuale. Carica il primo con «Nuovo grafo»."
      : "Nessun manuale in questo gruppo.";

  return (
    <Shell
      title={tr("Grafi")}
      actions={
        <Link to="/nuovo" className="button button-primary">
          <Icon name="plus" />
          {tr("Nuovo grafo")}
        </Link>
      }
    >
      <section className="card">
        <header className="card-head">
          <h2 className="card-title">
            {tr("Manuali")} {data && <span className="card-count">{formatNumber(rows.length)}</span>}
          </h2>
          <div className="row">
            <SegmentedControl<Filter>
              label={tr("Quali manuali mostrare")}
              value={filter}
              onChange={(value) => update({ mostra: FILTER_PARAM[value] })}
              options={[
                { value: "all", label: "Tutti" },
                { value: "review", label: "Da rivedere" },
                { value: "approved", label: "Approvati" },
              ]}
            />
            <SearchField
              label={tr("Cerca un manuale o una macchina")}
              value={query}
              onChange={(value) => update({ cerca: value || null })}
              hotkey
            />
          </div>
        </header>
        {error && <Problem message={`${tr("Non riesco a leggere la libreria.")} ${error}`} onRetry={reload} />}
        {loading && !data && <Loading label={tr("Carico i manuali")} />}
        {data && (
          <Table
            label={tr("Manuali")}
            columns={COLUMNS}
            rows={rows}
            rowKey={(row) => row.id}
            onOpen={(row) => navigate(manualRoute(row.id))}
            empty={empty}
            sorting={sorting}
            onSort={(key) => {
              const next = nextSorting(sorting, key);
              update({ ordina: next.key, verso: next.direction === "desc" ? "giu" : null });
            }}
            actions={(row) => <RowActions row={row} />}
          />
        )}
      </section>
    </Shell>
  );
}
