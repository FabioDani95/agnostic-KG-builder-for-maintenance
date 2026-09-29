import { type DragEvent, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, postJson, useApi } from "../api/client";
import type { Budget, Estimate, Machine, Upload } from "../api/types";
import { BackLink, SegmentedControl, TopBar } from "../components/Controls";
import { formatNumber, formatUsd } from "../text/it";

type Reviewers = "agent" | "agent_human" | "human";

export const REVIEWER_TEXT: Record<Reviewers, string> = {
  agent: "L'agente risponde a tutti i dubbi. Tu approvi il grafo alla fine.",
  agent_human: "L'agente risponde ai dubbi che sa risolvere; i restanti, al massimo 10, arrivano a te.",
  human: "I dubbi arrivano a te, al massimo 10; gli altri restano da verificare.",
};

const EMPTY: Machine = { name: "", brand: "", model: "", type: "" };

export function fileSize(bytes: number): string {
  if (bytes < 1_048_576) return `${formatNumber(Math.max(1, Math.round(bytes / 1024)))} KB`;
  return `${(bytes / 1_048_576).toLocaleString("it-IT", { maximumFractionDigits: 1 })} MB`;
}

function minutes(seconds: number): number {
  return Math.max(1, Math.round(seconds / 60));
}

async function send(file: File): Promise<Upload> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/api/uploads", { method: "POST", body });
  const data = await response.json();
  if (!response.ok) throw new ApiError(response.status, data.detail ?? response.statusText);
  return data as Upload;
}

export function NewGraph() {
  const navigate = useNavigate();
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [upload, setUpload] = useState<Upload | null>(null);
  const [machine, setMachine] = useState<Machine>(EMPTY);
  const [reviewers, setReviewers] = useState<Reviewers>("agent_human");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"upload" | "start" | null>(null);
  const budget = useApi<Budget>("/api/budget");
  const guess = useApi<Estimate>(upload ? `/api/estimate?pages=${upload.pages}` : null);

  const choose = async (file: File | undefined) => {
    if (!file) return;
    setError(null);
    setBusy("upload");
    try {
      const done = await send(file);
      setUpload(done);
      setMachine(done.machine ?? { ...EMPTY, name: file.name.replace(/\.pdf$/i, "") });
    } catch (failure) {
      setUpload(null);
      setError((failure as Error).message);
    } finally {
      setBusy(null);
    }
  };

  const drop = (event: DragEvent) => {
    event.preventDefault();
    setOver(false);
    void choose(event.dataTransfer.files[0]);
  };

  const start = async () => {
    if (!upload) return;
    setError(null);
    setBusy("start");
    try {
      const manual = await postJson<{ id: string }>("/api/manuals", { upload_id: upload.upload_id, ...machine });
      const run = await postJson<{ version_id: string }>(`/api/manuals/${encodeURIComponent(manual.id)}/runs`, {
        reviewers,
      });
      navigate(`/manuali/${encodeURIComponent(manual.id)}/versioni/${encodeURIComponent(run.version_id)}/esecuzione`);
    } catch (failure) {
      setError((failure as Error).message);
      setBusy(null);
    }
  };

  const worst = guess.data?.cost_usd?.[1] ?? null;
  const room = budget.data
    ? Math.min(
        budget.data.ceiling_usd - budget.data.committed_usd - budget.data.reserved_usd,
        budget.data.ui_limit_usd - budget.data.ui_spent_usd,
      )
    : null;
  const tooExpensive = worst !== null && room !== null && worst >= room;
  const missing = !upload ? "Carica prima il manuale." : !machine.name.trim() ? "Scrivi il nome della macchina." : null;
  const blocked = missing ?? (tooExpensive ? "La stima massima supera la spesa ancora possibile." : null);
  const field = (key: keyof Machine, label: string) => (
    <div className="field">
      <label htmlFor={`machine-${key}`}>{label}</label>
      <input
        id={`machine-${key}`}
        className="input"
        value={machine[key]}
        disabled={Boolean(upload?.duplicate_of)}
        onChange={(event) => setMachine({ ...machine, [key]: event.target.value })}
      />
    </div>
  );

  return (
    <div className="page">
      <TopBar back={<BackLink to="/">Grafi</BackLink>} />
      <main className="container">
        <div className="column-8">
          <div className="page-head">
            <h1 className="t-title">Nuovo grafo</h1>
          </div>
          <div className="stack">
            <div
              className="dropzone"
              data-over={over}
              onDragOver={(event) => {
                event.preventDefault();
                setOver(true);
              }}
              onDragLeave={() => setOver(false)}
              onDrop={drop}
            >
              <p className="t-large strong">{busy === "upload" ? "Lettura del PDF in corso" : "Trascina qui il manuale in PDF"}</p>
              <button type="button" className="button button-plain" onClick={() => input.current?.click()}>
                Scegli un file
              </button>
              <input
                ref={input}
                type="file"
                accept="application/pdf,.pdf"
                className="visually-hidden"
                tabIndex={-1}
                onChange={(event) => void choose(event.target.files?.[0])}
              />
            </div>

            {upload && (
              <>
                <div className="file-row">
                  <span className="strong" title={upload.file_name} style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {upload.file_name}
                  </span>
                  <span className="num">{upload.pages === 1 ? "1 pagina" : `${formatNumber(upload.pages)} pagine`}</span>
                  <span className="num">{fileSize(upload.size_bytes)}</span>
                </div>
                {upload.duplicate_of && (
                  <p className="message">
                    È il manuale di «{upload.machine?.name}», già nella libreria: l'esecuzione sarà una sua nuova versione.
                  </p>
                )}
              </>
            )}

            <div className="fields-2">
              {field("name", "Macchina")}
              {field("brand", "Marca")}
              {field("model", "Modello")}
              {field("type", "Tipo")}
            </div>

            <div className="field">
              <span className="field-label" id="reviewers-label">
                Chi risponde ai dubbi
              </span>
              <SegmentedControl<Reviewers>
                label="Chi risponde ai dubbi"
                value={reviewers}
                onChange={setReviewers}
                options={[
                  { value: "agent", label: "Solo agente" },
                  { value: "agent_human", label: "Agente, poi io" },
                  { value: "human", label: "Solo io" },
                ]}
              />
              <p className="secondary">{REVIEWER_TEXT[reviewers]}</p>
            </div>

            <dl className="facts">
              {guess.data?.seconds && guess.data.cost_usd && (
                <>
                  <dt>Tempo stimato</dt>
                  <dd>
                    da {minutes(guess.data.seconds[0])} a {minutes(guess.data.seconds[1])} minuti
                  </dd>
                  <dt>Costo stimato</dt>
                  <dd>
                    da {formatUsd(guess.data.cost_usd[0])} a {formatUsd(guess.data.cost_usd[1])}
                  </dd>
                </>
              )}
              {budget.data && (
                <>
                  <dt>Speso finora sul registro</dt>
                  <dd>
                    {formatUsd(budget.data.committed_usd, 2)} di {formatUsd(budget.data.ceiling_usd, 2)}
                  </dd>
                  <dt>Speso dall'interfaccia</dt>
                  <dd>
                    {formatUsd(budget.data.ui_spent_usd, 2)} di {formatUsd(budget.data.ui_limit_usd, 2)}
                  </dd>
                </>
              )}
            </dl>
            {guess.data?.seconds && (
              <p className="secondary t-small">
                La stima viene dalle due esecuzioni attuali con il numero di pagine più vicino: non è una promessa.
              </p>
            )}

            <div className="actions">
              {(error ?? blocked) && <p className="secondary">{error ?? blocked}</p>}
              <button
                type="button"
                className="button button-primary"
                disabled={Boolean(blocked) || busy !== null}
                onClick={start}
              >
                Avvia estrazione
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
