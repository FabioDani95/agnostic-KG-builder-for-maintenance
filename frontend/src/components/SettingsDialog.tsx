import { type ReactNode, useEffect, useRef, useState } from "react";
import { putJson } from "../api/client";
import type { Preferences, Reasoning } from "../api/types";
import { SegmentedControl } from "./Controls";
import { Problem } from "./Feedback";
import { Icon } from "./Icon";
import { tr } from "../i18n/i18n";

const REASONING_LABEL: Record<Reasoning, string> = { none: "Nessuno", low: "Basso", medium: "Medio", high: "Alto" };

type Draft = Omit<Preferences, "key" | "choices">;

function Group({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="settings-group">
      <h3 className="settings-title">{title}</h3>
      {children}
    </section>
  );
}

function Row({ label, htmlFor, children }: { label: string; htmlFor?: string; children: ReactNode }) {
  return (
    <div className="settings-row">
      <label htmlFor={htmlFor}>{label}</label>
      {children}
    </div>
  );
}

/**
 * Settings in a window in the middle, as in The Fixer: the model settings of the next runs, the
 * OpenAI key, how many questions a person gets, how the graph is drawn. Nothing is saved until
 * «Salva»; Esc and «Annulla» leave everything as it was.
 */
export function SettingsDialog({
  settings,
  onClose,
  onSaved,
}: {
  settings: Preferences;
  onClose: () => void;
  onSaved: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [draft, setDraft] = useState<Draft>(() => {
    const { key: _key, choices: _choices, ...values } = settings;
    return values;
  });
  const [key, setKey] = useState("");
  const [clearKey, setClearKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    dialog.current?.showModal();
  }, []);

  const change = (values: Partial<Draft>) => setDraft((current) => ({ ...current, ...values }));
  const reasoning = settings.choices.reasoning.map((value) => ({ value, label: tr(REASONING_LABEL[value]) }));
  const save = async () => {
    setSaving(true);
    setProblem(null);
    try {
      await putJson("/api/settings", { ...draft, ...(key.trim() ? { api_key: key.trim() } : {}), clear_api_key: clearKey });
      onSaved();
      onClose();
    } catch (failure) {
      setProblem((failure as Error).message);
      setSaving(false);
    }
  };
  const keySource = clearKey ? "env" : settings.key.source;

  return (
    <dialog ref={dialog} className="modal" aria-labelledby="settings-heading" onClose={onClose}>
      <header className="modal-head">
        <h2 id="settings-heading" className="card-title">
          {tr("Impostazioni")}
        </h2>
        <button type="button" className="icon-button" aria-label={tr("Chiudi")} onClick={onClose}>
          <Icon name="x" />
        </button>
      </header>

      <div className="modal-body">
        {problem && <Problem message={problem} />}

        <Group title={tr("OpenAI")}>
          <Row label={tr("Chiave")} htmlFor="settings-key">
            <div className="row">
              <input
                id="settings-key"
                className="input"
                type="password"
                autoComplete="off"
                value={key}
                placeholder={
                  keySource === "custom"
                    ? tr("Chiave impostata qui {hint}", { hint: settings.key.hint ?? "" })
                    : settings.key.source === "none" && !settings.key.hint
                      ? tr("Nessuna chiave")
                      : tr("Chiave del file .env {hint}", { hint: settings.key.source === "env" ? settings.key.hint ?? "" : "" })
                }
                onChange={(event) => {
                  setKey(event.target.value);
                  setClearKey(false);
                }}
              />
              {settings.key.source === "custom" && !clearKey && (
                <button type="button" className="button button-plain" onClick={() => setClearKey(true)} title={tr("Usa la chiave del file .env")}>
                  {tr("Usa .env")}
                </button>
              )}
            </div>
          </Row>
        </Group>

        <Group title={tr("Estrazione")}>
          <Row label={tr("Ragionamento")}>
            <SegmentedControl<Reasoning>
              label={tr("Ragionamento dell'estrazione")}
              fill
              value={draft.reasoning}
              onChange={(value) => change({ reasoning: value })}
              options={reasoning}
            />
          </Row>
          <Row label={tr("Letture per unità")}>
            <SegmentedControl<string>
              label={tr("Letture per unità")}
              fill
              value={String(draft.reads)}
              onChange={(value) => change({ reads: Number(value) })}
              options={["1", "2", "3"].map((value) => ({ value, label: value }))}
            />
          </Row>
        </Group>

        <Group title={tr("Agente")}>
          <Row label={tr("Modello")} htmlFor="settings-agent-model">
            <select
              id="settings-agent-model"
              className="input"
              value={draft.agent_model}
              onChange={(event) => change({ agent_model: event.target.value })}
            >
              {settings.choices.agent_models.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </Row>
          <Row label={tr("Ragionamento")}>
            <SegmentedControl<Reasoning>
              label={tr("Ragionamento dell'agente")}
              fill
              value={draft.agent_reasoning}
              onChange={(value) => change({ agent_reasoning: value })}
              options={reasoning}
            />
          </Row>
        </Group>

        <Group title={tr("Domande")}>
          <Row label={tr("Massimo per persona")}>
            <SegmentedControl<string>
              label={tr("Massimo di domande per persona")}
              fill
              value={String(draft.human_questions)}
              onChange={(value) => change({ human_questions: Number(value) })}
              options={["5", "10", "15", "20"].map((value) => ({ value, label: value }))}
            />
          </Row>
        </Group>

        <Group title={tr("Grafo")}>
          <label className="check">
            <input
              type="checkbox"
              checked={draft.show_code_relations}
              onChange={(event) => change({ show_code_relations: event.target.checked })}
            />
            {tr("Relazioni aggiunte dal codice")}
          </label>
          <label className="check">
            <input type="checkbox" checked={draft.node_labels} onChange={(event) => change({ node_labels: event.target.checked })} />
            {tr("Nomi sempre visibili sui nodi")}
          </label>
        </Group>
      </div>

      <footer className="modal-foot">
        <button type="button" className="button button-secondary" onClick={onClose} disabled={saving}>
          {tr("Annulla")}
        </button>
        <button type="button" className="button button-primary" onClick={save} disabled={saving}>
          {saving && <Icon name="loader" className="spin" />}
          {tr("Salva")}
        </button>
      </footer>
    </dialog>
  );
}
