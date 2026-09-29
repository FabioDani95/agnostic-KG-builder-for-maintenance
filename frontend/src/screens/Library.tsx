import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApi } from "../api/client";
import type { ManualRow } from "../api/types";
import { SearchField, SegmentedControl, TopBar } from "../components/Controls";
import { type Column, Table } from "../components/Table";
import { formatNumber, statusLabel, versionLabel } from "../text/it";

type Filter = "all" | "review" | "approved";

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
  { key: "manual", label: "Manuale", span: 3, render: (row) => `${row.machine.brand} ${row.machine.model}` },
  { key: "machine", label: "Macchina", span: 2, render: (row) => row.machine.type },
  { key: "pages", label: "Pagine", span: 1, numeric: true, render: (row) => formatNumber(row.pages) },
  { key: "version", label: "Versione", span: 2, render: (row) => (row.latest ? versionLabel(row.latest) : "") },
  {
    key: "verified",
    label: "Relazioni verificate",
    span: 1,
    numeric: true,
    render: (row) => formatNumber(row.latest?.verified),
  },
  {
    key: "questions",
    label: "Domande aperte",
    span: 1,
    numeric: true,
    render: (row) => formatNumber(row.latest?.open_questions),
  },
  {
    key: "status",
    label: "Stato",
    span: 2,
    render: (row) => (row.latest ? statusLabel(row.latest.status, row.latest.decided_by) : "Nessuna versione"),
  },
];

export function Library() {
  const navigate = useNavigate();
  const { data, error, loading } = useApi<ManualRow[]>("/api/manuals");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
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
    ? `Nessun manuale corrisponde a «${query.trim()}».`
    : filter === "all"
      ? "Nessun manuale. Carica il primo con «Nuovo grafo»."
      : "Nessun manuale in questo gruppo.";

  return (
    <div className="page">
      <TopBar>
        <SearchField label="Cerca un manuale o una macchina" value={query} onChange={setQuery} width={360} />
      </TopBar>
      <main className="container">
        <div className="page-head">
          <h1 className="t-title">Grafi</h1>
          <Link to="/nuovo" className="button button-primary">
            Nuovo grafo
          </Link>
        </div>
        <div className="stack">
          <div>
            <SegmentedControl<Filter>
              label="Quali manuali mostrare"
              value={filter}
              onChange={setFilter}
              options={[
                { value: "all", label: "Tutti" },
                { value: "review", label: "Da rivedere" },
                { value: "approved", label: "Approvati" },
              ]}
            />
          </div>
          {error && <p className="message">Non riesco a leggere la libreria: {error}</p>}
          {!error && !loading && (
            <Table
              label="Manuali"
              columns={COLUMNS}
              rows={rows}
              rowKey={(row) => row.id}
              onOpen={(row) => navigate(`/manuali/${encodeURIComponent(row.id)}`)}
              empty={empty}
            />
          )}
        </div>
      </main>
    </div>
  );
}
