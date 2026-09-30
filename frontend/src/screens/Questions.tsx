import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { postJson, useApi, versionPath } from "../api/client";
import type { Manual, Questions as QuestionsData, QuestionView } from "../api/types";
import { ProgressBar } from "../components/Controls";
import { Shell } from "../components/Shell";
import { PageDialog } from "../components/PageDialog";
import { formatNumber, pageRef } from "../text/it";

function QuestionCard({
  question,
  busy,
  onAnswer,
  onOpenPage,
}: {
  question: QuestionView;
  busy: boolean;
  onAnswer: (optionId: string, keep: number[], text: string) => void;
  onOpenPage: (page: number) => void;
}) {
  const [partial, setPartial] = useState(false);
  const [keep, setKeep] = useState<number[]>([]);
  const [text, setText] = useState("");
  const [writing, setWriting] = useState<string | null>(null);
  const pages = [...new Set(question.source.map((item) => item.page))];
  const [first, ...others] = question.options;
  const partialOption = question.options.find((option) => option.needs_statements);
  const textOption = question.options.find((option) => option.needs_text);

  return (
    <>
    <h2 className="t-title" style={{ marginBottom: 16 }}>{question.title_it}</h2>
    <div className="stack">

      {question.source.length > 0 && (
        <section>
          <h3 className="card-title" style={{ marginBottom: 8 }}>
            Nel manuale
          </h3>
          <ul className="quote-list">
            {question.source.map((item) => (
              <li key={item.segment_id}>
                <span className="secondary num" style={{ textAlign: "left" }}>
                  {pageRef(item.page)}
                </span>
                <span>{item.text}</span>
              </li>
            ))}
          </ul>
          <div className="row">
            {pages.map((page) => (
              <button key={page} type="button" className="button button-plain" style={{ paddingLeft: 0 }} onClick={() => onOpenPage(page)}>
                Apri la pagina {page}
              </button>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className="card-title" style={{ marginBottom: 8 }}>
          Il sistema propone
        </h3>
        <ol>
          {question.claims_it.map((claim, index) => (
            <li key={index} className="numbered t-large">
              {partial ? (
                <input
                  type="checkbox"
                  aria-label={`Tieni l'affermazione ${index + 1}`}
                  checked={keep.includes(index + 1)}
                  onChange={(event) =>
                    setKeep(event.target.checked ? [...keep, index + 1] : keep.filter((value) => value !== index + 1))
                  }
                />
              ) : (
                <span className="num secondary" style={{ textAlign: "left" }}>
                  {index + 1}
                </span>
              )}
              <span>{claim}</span>
            </li>
          ))}
        </ol>
        <details>
          <summary>Dettagli</summary>
          <ol className="t-small secondary">
            {question.proposal.map((line, index) => (
              <li key={index} style={{ padding: "8px 0" }}>
                {line}
              </li>
            ))}
          </ol>
        </details>
      </section>

      {writing && (
        <div className="field">
          <label htmlFor="answer-text">La tua trascrizione</label>
          <textarea id="answer-text" className="textarea" value={text} onChange={(event) => setText(event.target.value)} />
        </div>
      )}

      <div className="actions">
        {partial ? (
          <>
            <span className="secondary">Scegli i numeri da tenere.</span>
            <button type="button" className="button button-secondary" onClick={() => setPartial(false)}>
              Annulla
            </button>
            <button
              type="button"
              className="button button-primary"
              disabled={busy || keep.length === 0}
              onClick={() => partialOption && onAnswer(partialOption.option_id, keep, "")}
            >
              Tieni le affermazioni scelte
            </button>
          </>
        ) : writing ? (
          <>
            <button type="button" className="button button-secondary" onClick={() => setWriting(null)}>
              Annulla
            </button>
            <button
              type="button"
              className="button button-primary"
              disabled={busy || !text.trim()}
              onClick={() => onAnswer(writing, [], text)}
            >
              Invia la trascrizione
            </button>
          </>
        ) : (
          <>
            {others.map((option) => (
              <button
                key={option.option_id}
                type="button"
                className="button button-secondary"
                disabled={busy}
                onClick={() =>
                  option === partialOption
                    ? setPartial(true)
                    : option === textOption
                      ? setWriting(option.option_id)
                      : onAnswer(option.option_id, [], "")
                }
              >
                {option.label_it}
              </button>
            ))}
            <button type="button" className="button button-primary" disabled={busy} onClick={() => onAnswer(first.option_id, [], "")}>
              {first.label_it}
            </button>
          </>
        )}
      </div>
    </div>
    </>
  );
}

export function Questions() {
  const { manualId = "", versionId = "" } = useParams();
  const navigate = useNavigate();
  const base = `/manuali/${encodeURIComponent(manualId)}/versioni/${encodeURIComponent(versionId)}`;
  const manual = useApi<Manual>(`/api/manuals/${encodeURIComponent(manualId)}`);
  const { data, error, reload } = useApi<QuestionsData>(`${versionPath(manualId, versionId)}/questions`);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [page, setPage] = useState<number | null>(null);
  useEffect(() => setFailure(null), [data]);

  const answer = async (question: QuestionView, optionId: string, keep: number[], text: string) => {
    setBusy(true);
    try {
      const result = await postJson<{ version_id: string }>(
        `${versionPath(manualId, versionId)}/questions/${encodeURIComponent(question.question_id)}/answer`,
        { option_id: optionId, keep, text },
      );
      if (result.version_id !== versionId) {
        // The first answer on a campaign version made a copy: go on there.
        navigate(`/manuali/${encodeURIComponent(manualId)}/versioni/${encodeURIComponent(result.version_id)}/domande`, {
          replace: true,
        });
      } else {
        reload();
      }
    } catch (problem) {
      setFailure((problem as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const act = async (path: string, body?: unknown) => {
    setBusy(true);
    try {
      await postJson(`${versionPath(manualId, versionId)}/${path}`, body);
      navigate(`${base}/esecuzione`);
    } catch (problem) {
      setFailure((problem as Error).message);
      setBusy(false);
    }
  };

  const total = data ? data.open.length + data.answered.length : 0;
  const current = data?.open[0];
  const position = data ? data.answered.length + 1 : 0;

  return (
    <Shell
      trail={[
        { to: "/", label: "Grafi" },
        { to: `/manuali/${encodeURIComponent(manualId)}`, label: manual.data?.machine.name ?? "Manuale" },
        { to: base, label: "Grafo" },
      ]}
      title="Domande per te"
      actions={
        data &&
        current && (
          <div className="row" style={{ gap: 12, marginRight: 8 }}>
            <span className="t-small">
              Domanda <span className="mono">{formatNumber(position)}</span> di <span className="mono">{formatNumber(total)}</span>
            </span>
            <span style={{ width: 160 }}>
              <ProgressBar value={position - 1} total={total} label="Domande a cui hai risposto" />
            </span>
          </div>
        )
      }
    >
        <div className="reading">
          {error && <p className="message">Non riesco a leggere le domande: {error}</p>}
          {data && current && (
            <>
              {data.copy_needed && (
                <p className="message" style={{ marginBottom: 16 }}>
                  Questa versione viene dalla campagna e non si modifica: la prima risposta ne crea una copia in cui
                  continui a rispondere.
                </p>
              )}
              <QuestionCard
                key={current.question_id}
                question={current}
                busy={busy}
                onAnswer={(optionId, keep, text) => answer(current, optionId, keep, text)}
                onOpenPage={setPage}
              />
            </>
          )}
          {data && !current && (
            <>
              <div className="stack">
                {total === 0 ? (
                  <p>Non ci sono domande per te in questa versione.</p>
                ) : (
                  <p>
                    Hai risposto a {total === 1 ? "1 domanda" : `${formatNumber(total)} domande`}.
                    {data.unapplied > 0 ? " Applicale per aggiornare il grafo." : ""}
                  </p>
                )}
                {data.unverified.length > 0 && (
                  <p className="secondary">
                    Oltre il limite di {data.budget} restano{" "}
                    {data.unverified.length === 1 ? "1 domanda senza risposta" : `${formatNumber(data.unverified.length)} domande senza risposta`}:
                    le loro relazioni sono nel grafo ma fuori dalla parte affidabile.
                  </p>
                )}
                <div className="actions">
                  {data.unapplied > 0 && (
                    <button type="button" className="button button-primary" disabled={busy} onClick={() => act("apply")}>
                      Applica le risposte
                    </button>
                  )}
                  {data.unapplied === 0 && data.can_approve && (
                    <>
                      <button type="button" className="button button-secondary" disabled={busy} onClick={() => act("approve", { decision: "reject" })}>
                        Rifiuta
                      </button>
                      <button type="button" className="button button-primary" disabled={busy} onClick={() => act("approve", { decision: "approve" })}>
                        Approva il grafo
                      </button>
                    </>
                  )}
                </div>
              </div>
            </>
          )}
          {failure && (
            <p className="message" role="alert" style={{ marginTop: 24 }}>
              {failure}
            </p>
          )}
        </div>
      {page !== null && <PageDialog manualId={manualId} page={page} marks={[]} onClose={() => setPage(null)} />}
    </Shell>
  );
}
