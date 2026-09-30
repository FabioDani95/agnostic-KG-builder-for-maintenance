import { type DragEvent, type ReactNode, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ApiError, liveRoute, OFFLINE, postJson, useApi } from "../api/client";
import type { Estimate, Identified, Machine, Upload } from "../api/types";
import { SegmentedControl } from "../components/Controls";
import { Problem } from "../components/Feedback";
import { Icon } from "../components/Icon";
import { Shell } from "../components/Shell";
import { useStatus } from "../status/StatusProvider";
import { formatCost, formatMinutes, formatNumber, formatRange, plural } from "../text/it";
import { tr } from "../i18n/i18n";

type Reviewers = "agent" | "agent_human" | "human";
type Source = "upload" | "library";

export const REVIEWERS: { value: Reviewers; label: string; text: string }[] = [
  { value: "agent", label: "Solo agente", text: "L'agente risponde a tutti i dubbi. Tu approvi il grafo alla fine." },
  {
    value: "agent_human",
    label: "Agente, poi io",
    text: "L'agente risponde ai dubbi che sa risolvere; i restanti, al massimo 10, arrivano a te.",
  },
  { value: "human", label: "Solo io", text: "I dubbi arrivano a te, al massimo 10; gli altri restano da verificare." },
];

const EMPTY: Machine = { name: "", brand: "", model: "", type: "" };

export function fileSize(bytes: number): string {
  if (bytes < 1_048_576) return `${formatNumber(Math.max(1, Math.round(bytes / 1024)))} KB`;
  return `${(bytes / 1_048_576).toLocaleString("it-IT", { maximumFractionDigits: 1 })} MB`;
}

async function send(file: File): Promise<Upload> {
  const body = new FormData();
  body.append("file", file);
  let response: Response;
  try {
    response = await fetch("/api/uploads", { method: "POST", body });
  } catch {
    throw new ApiError(0, OFFLINE);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, data.detail ?? response.statusText);
  return data as Upload;
}

/** Why the run cannot start yet, in the order a person would fix it; null when it can. */
export function blocker(input: {
  running: string | null;
  hasManual: boolean;
  name: string;
  worst: number | null;
  estimated: boolean;
}): string | null {
  if (input.running) return tr("C'è già un'esecuzione in corso ({name}): aspetta che finisca.", { name: input.running });
  if (!input.hasManual) return tr("Carica il manuale in PDF o sceglilo dalla libreria.");
  if (!input.name.trim()) return tr("Scrivi il nome della macchina.");
  if (input.estimated && input.worst === null) return tr("Non ho esecuzioni passate da cui stimare il costo.");
  return null;
}

function StepCard({
  number,
  title,
  done,
  working = false,
  children,
}: {
  number: number;
  title: string;
  done: boolean;
  working?: boolean;
  children: ReactNode;
}) {
  return (
    <section className="card">
      <header className="card-head">
        <h2 className="card-title">
          <span className="step-number" data-done={done} aria-hidden="true">
            {done ? <Icon name="check" size={12} /> : number}
          </span>
          {title}
        </h2>
        {working && (
          <span role="status">
            <Icon name="loader" size={16} className="spin" />
            <span className="visually-hidden">{tr("Lettura dei dati della macchina")}</span>
          </span>
        )}
      </header>
      <div className="card-body stack" style={{ gap: 12 }}>
        {children}
      </div>
    </section>
  );
}

/**
 * Making a graph: which manual, which machine, who answers the doubts; on the right a summary that
 * fills in as the steps are done, with the estimated time and cost and the start button.
 * `?manuale=<id>` starts from a manual already in the library (a new version of its graph).
 */
export function NewGraph() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const status = useStatus();
  const input = useRef<HTMLInputElement>(null);
  const [source, setSource] = useState<Source>(params.get("manuale") ? "library" : "upload");
  const [picked, setPicked] = useState(params.get("manuale") ?? "");
  const [over, setOver] = useState(false);
  const [upload, setUpload] = useState<Upload | null>(null);
  const [machine, setMachine] = useState<Machine>(EMPTY);
  const [reviewers, setReviewers] = useState<Reviewers>("agent_human");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"upload" | "start" | null>(null);
  // The machine read from the first pages by a small model, right after the upload.
  // Busy while the machine is read from the first pages; the problem, if the reading fails.
  const [reading, setReading] = useState<{ busy: boolean; problem: string | null }>({ busy: false, problem: null });
  const latestUpload = useRef<string | null>(null);

  const manuals = status.manuals ?? [];
  const chosen = source === "library" ? manuals.find((row) => row.id === picked) : undefined;
  const existing = chosen ?? (upload?.duplicate_of ? manuals.find((row) => row.id === upload.duplicate_of) : undefined);
  const pages = source === "library" ? chosen?.pages ?? null : upload?.pages ?? null;
  const guess = useApi<Estimate>(pages ? `/api/estimate?pages=${pages}` : null);

  // A manual from the library brings its machine; a new PDF brings the guess read from it.
  useEffect(() => {
    if (chosen) setMachine(chosen.machine);
  }, [chosen]);

  const choose = async (file: File | undefined) => {
    if (!file) return;
    setError(null);
    setBusy("upload");
    try {
      const done = await send(file);
      setUpload(done);
      latestUpload.current = done.upload_id;
      setMachine(done.machine ?? { ...EMPTY, name: file.name.replace(/\.pdf$/i, "") });
      setReading({ busy: false, problem: null });
      if (!done.duplicate_of) void read(done.upload_id);
    } catch (failure) {
      setUpload(null);
      setError((failure as Error).message);
    } finally {
      setBusy(null);
      if (input.current) input.current.value = "";
    }
  };

  const read = async (uploadId: string) => {
    setReading({ busy: true, problem: null });
    try {
      const found = await postJson<Identified>(`/api/uploads/${uploadId}/machine`);
      if (latestUpload.current !== uploadId) return; // another file was chosen meanwhile
      setMachine((current) => ({ ...found.machine, name: found.machine.name || current.name }));
      setReading({ busy: false, problem: null });
      status.refresh();
    } catch (failure) {
      if (latestUpload.current !== uploadId) return;
      setReading({ busy: false, problem: (failure as Error).message });
    }
  };

  const drop = (event: DragEvent) => {
    event.preventDefault();
    setOver(false);
    void choose(event.dataTransfer.files[0]);
  };

  const start = async () => {
    setError(null);
    setBusy("start");
    try {
      const manualId =
        source === "library"
          ? picked
          : (await postJson<{ id: string }>("/api/manuals", { upload_id: upload!.upload_id, ...machine })).id;
      const run = await postJson<{ version_id: string }>(`/api/manuals/${encodeURIComponent(manualId)}/runs`, { reviewers });
      status.refresh();
      navigate(liveRoute(manualId, run.version_id));
    } catch (failure) {
      setError((failure as Error).message);
      setBusy(null);
    }
  };

  const worst = guess.data?.cost_usd?.[1] ?? null;
  const hasManual = source === "library" ? Boolean(chosen) : Boolean(upload);
  const blocked = blocker({
    running: status.active?.name ?? null,
    hasManual,
    name: machine.name,
    worst,
    estimated: Boolean(guess.data),
  });
  const locked = Boolean(existing);
  const field = (key: keyof Machine, label: string, required = false) => (
    <div className="field">
      <label htmlFor={`machine-${key}`}>
        {tr(label)}
        {required && <span className="required"> *</span>}
      </label>
      <input
        id={`machine-${key}`}
        className="input"
        value={machine[key]}
        required={required}
        aria-invalid={required && hasManual && !machine[key].trim() ? true : undefined}
        disabled={locked || !hasManual || reading.busy}
        onChange={(event) => setMachine({ ...machine, [key]: event.target.value })}
      />
    </div>
  );
  const title = source === "library" && chosen ? tr("Nuova versione di {name}", { name: chosen.machine.name }) : "Nuovo grafo";

  return (
    <Shell trail={[{ to: "/", label: "Grafi" }]} title={title}>
      <div className="split">
        <div className="stack">
          <StepCard number={1} title={tr("Manuale")} done={hasManual}>
            <SegmentedControl<Source>
              label={tr("Da dove viene il manuale")}
              value={source}
              onChange={(value) => {
                setSource(value);
                setError(null);
                if (value === "upload") setMachine(upload?.machine ?? EMPTY);
              }}
              options={[
                { value: "upload", label: "Carica un PDF" },
                { value: "library", label: "Dalla libreria" },
              ]}
            />
            {source === "upload" && !upload && (
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
                <Icon name="upload" size={20} />
                <p className="strong">{tr(busy === "upload" ? "Lettura del PDF in corso" : "Trascina qui il manuale in PDF")}</p>
                <button type="button" className="button button-plain" disabled={busy === "upload"} onClick={() => input.current?.click()}>
                  {tr("Scegli un file")}
                </button>
              </div>
            )}
            <input
              ref={input}
              type="file"
              accept="application/pdf,.pdf"
              className="visually-hidden"
              tabIndex={-1}
              onChange={(event) => void choose(event.target.files?.[0])}
            />
            {source === "upload" && upload && (
              <>
                <div className="file-row">
                  <Icon name="file" />
                  <span className="strong" title={upload.file_name} style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {upload.file_name}
                  </span>
                  <span className="num">{plural(upload.pages, "pagina", "pagine")}</span>
                  <span className="num">{fileSize(upload.size_bytes)}</span>
                  <button type="button" className="button button-plain" disabled={busy !== null} onClick={() => input.current?.click()}>
                    {tr("Cambia")}
                  </button>
                </div>
                {upload.duplicate_of && (
                  <p className="message">
                    {tr("È il manuale di «{name}», già nella libreria: l'esecuzione sarà una sua nuova versione.", {
                      name: existing?.machine.name ?? upload.machine?.name ?? "",
                    })}
                  </p>
                )}
              </>
            )}
            {source === "library" && (
              <div className="field">
                <label htmlFor="library-manual">{tr("Manuale della libreria")}</label>
                <select id="library-manual" className="input" value={picked} onChange={(event) => setPicked(event.target.value)}>
                  <option value="">{tr("Scegli un manuale")}</option>
                  {manuals.map((row) => (
                    <option key={row.id} value={row.id}>
                      {row.machine.brand} {row.machine.model} · {plural(row.pages ?? 0, "pagina", "pagine")}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </StepCard>

          <StepCard
            number={2}
            title={tr("Macchina")}
            done={hasManual && !reading.busy && Boolean(machine.name.trim())}
            working={reading.busy}
          >
            {reading.problem && source === "upload" && <Problem message={reading.problem} />}
            <div className="fields-2">
              {field("name", "Macchina", true)}
              {field("brand", "Marca")}
              {field("model", "Modello")}
              {field("type", "Tipo")}
            </div>
          </StepCard>

          <StepCard number={3} title={tr("Chi risponde ai dubbi")} done>
            <div className="choices" role="radiogroup" aria-label={tr("Chi risponde ai dubbi")}>
              {REVIEWERS.map((option) => (
                <label key={option.value} className="choice" data-checked={reviewers === option.value}>
                  <input
                    type="radio"
                    name="reviewers"
                    value={option.value}
                    checked={reviewers === option.value}
                    onChange={() => setReviewers(option.value)}
                  />
                  <span className="strong">{tr(option.label)}</span>
                  <span className="t-small secondary">{tr(option.text)}</span>
                </label>
              ))}
            </div>
          </StepCard>
        </div>

        <aside className="card summary" aria-label={tr("Riepilogo")}>
          <header className="card-head">
            <h2 className="card-title">{tr("Riepilogo")}</h2>
          </header>
          <div className="card-body stack" style={{ gap: 12 }}>
            <dl className="facts">
              <dt>{tr("Manuale")}</dt>
              <dd>{hasManual ? machine.name || tr("Senza nome") : "–"}</dd>
              <dt>{tr("Pagine")}</dt>
              <dd>{pages ? formatNumber(pages) : "–"}</dd>
              <dt>{tr("Dubbi")}</dt>
              <dd>{tr(REVIEWERS.find((option) => option.value === reviewers)?.label ?? "")}</dd>
              <dt>{tr("Tempo stimato")}</dt>
              <dd>
                {guess.data?.seconds
                  ? formatRange(guess.data.seconds[0], guess.data.seconds[1], formatMinutes, "min")
                  : "–"}
              </dd>
              <dt>{tr("Costo stimato")}</dt>
              <dd>
                {guess.data?.cost_usd ? formatRange(guess.data.cost_usd[0], guess.data.cost_usd[1], formatCost, "USD") : "–"}
              </dd>
            </dl>
            {(error ?? blocked) && (
              <p className="t-small blocked" role={error ? "alert" : undefined}>
                {error ?? blocked}
                {!error && status.active && (
                  <>
                    {" "}
                    <Link to={liveRoute(status.active.manualId, status.active.versionId)}>{tr("Seguila")}</Link>
                  </>
                )}
              </p>
            )}
            <button
              type="button"
              className="button button-primary"
              disabled={Boolean(blocked) || busy !== null || reading.busy}
              onClick={start}
            >
              <Icon name="play" />
              {tr(busy === "start" ? "Avvio in corso" : "Avvia estrazione")}
            </button>
          </div>
        </aside>
      </div>
    </Shell>
  );
}
