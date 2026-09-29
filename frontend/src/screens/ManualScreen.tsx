import { useNavigate, useParams } from "react-router-dom";
import { versionPath, useApi } from "../api/client";
import type { Manual, Version } from "../api/types";
import { BackLink, TopBar } from "../components/Controls";
import { type Column, Table } from "../components/Table";
import { formatDate, formatNumber, iterationLabel, statusLabel } from "../text/it";

const COLUMNS: Column<Version>[] = [
  { key: "date", label: "Data", span: 3, render: (row) => formatDate(row.date) },
  { key: "iteration", label: "Iterazione", span: 3, render: (row) => iterationLabel(row) },
  { key: "run", label: "Ripetizione", span: 1, numeric: true, render: (row) => formatNumber(row.repetition) },
  { key: "commit", label: "Codice", span: 1, render: (row) => row.commit },
  { key: "verified", label: "Relazioni verificate", span: 1, numeric: true, render: (row) => formatNumber(row.verified) },
  {
    key: "questions",
    label: "Domande aperte",
    span: 1,
    numeric: true,
    render: (row) => formatNumber(row.open_questions),
  },
  { key: "status", label: "Esito", span: 2, render: (row) => statusLabel(row.status, row.decided_by) },
];

export function ManualScreen() {
  const { manualId = "" } = useParams();
  const navigate = useNavigate();
  const { data: manual, error } = useApi<Manual>(`/api/manuals/${encodeURIComponent(manualId)}`);
  const replayable = manual?.versions.find((version) => version.replay && version.status !== "running");
  const open = (version: Version) => {
    const base = `/manuali/${encodeURIComponent(manualId)}/versioni/${encodeURIComponent(version.version_id)}`;
    navigate(version.status === "running" || version.status === "failed" ? `${base}/esecuzione` : base);
  };

  return (
    <div className="page">
      <TopBar back={<BackLink to="/">Grafi</BackLink>} />
      <main className="container">
        {error && <p className="message page-head">Non trovo questo manuale: {error}</p>}
        {manual && (
          <>
            <div className="page-head">
              <h1 className="t-title">{manual.machine.name}</h1>
              {replayable && (
                <button
                  type="button"
                  className="button button-primary"
                  onClick={() =>
                    navigate(
                      `/manuali/${encodeURIComponent(manualId)}/versioni/${encodeURIComponent(replayable.version_id)}/esecuzione`,
                    )
                  }
                >
                  Rigioca l'esecuzione
                </button>
              )}
            </div>
            <div className="stack">
              <dl className="data-list">
                <dt>Marca</dt>
                <dd>{manual.machine.brand}</dd>
                <dt>Modello</dt>
                <dd>{manual.machine.model}</dd>
                <dt>Tipo</dt>
                <dd>{manual.machine.type}</dd>
                <dt>Pagine</dt>
                <dd>{formatNumber(manual.pages)}</dd>
                <dt>Origine</dt>
                <dd>{manual.origin === "campaign" ? "Campagna di valutazione" : "Caricato dall'interfaccia"}</dd>
              </dl>
              <h2 className="t-heading">Versioni</h2>
              <Table
                label="Versioni"
                columns={COLUMNS}
                rows={manual.versions}
                rowKey={(row) => row.version_id}
                onOpen={open}
                empty="Nessuna versione: questo manuale non è ancora stato elaborato."
              />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export const graphUrl = (manualId: string, versionId: string) => `${versionPath(manualId, versionId)}/graph`;
