// Every word the interface shows, in one place, in Italian; tr() gives it in the language of the
// interface (src/i18n). Manual text stays in its own language.
import type { RunStatus, Tier, Version } from "../api/types";
import { locale, tr } from "../i18n/i18n";

/** A table of labels read in the language of the interface at every lookup. */
function labels<K extends string>(italian: Record<K, string>): Record<K, string> {
  return new Proxy(italian, { get: (table, key) => (typeof key === "string" && key in table ? tr(table[key as K]) : undefined) });
}

export const APP_NAME = "Grafi di manutenzione";
export const appName = () => tr(APP_NAME);

export const TYPE_LABEL: Record<string, string> = labels({
  Asset: "Macchina",
  Symptom: "Sintomo",
  ErrorCode: "Codice di errore",
  FailureMode: "Causa",
  CorrectiveAction: "Azione",
  Component: "Componente",
});

export const RELATION_LABEL: Record<string, string> = labels({
  MAY_INDICATE: "può indicare",
  INDICATES: "indica",
  RESOLVED_BY: "si risolve con",
  AFFECTS: "riguarda",
  HAS_COMPONENT: "ha il componente",
  GENERATES_ERROR: "può dare il codice",
});

export const TIER_LABEL: Record<Tier | "proposed", string> = labels({
  proposed: "Proposta",
  green: "Verificata",
  yellow: "In dubbio",
  red: "Scartata",
});

export const WITNESS_LABEL: Record<string, string> = labels({
  structure: "struttura della pagina",
  agreement: "accordo delle due letture",
  verifier: "verificatore",
  reviewer: "revisore",
});

export const REVIEWER_LABEL: Record<string, string> = labels({
  human: "una persona",
  agent: "l'agente",
  script: "uno script di prova",
  auto: "in automatico",
});

export const STATION_LABEL: Record<string, string> = labels({
  read: "Leggi",
  map: "Mappa",
  extract: "Estrai",
  check: "Controlla",
  merge: "Unisci",
  ask: "Chiedi",
});

export function statusLabel(status: RunStatus, decidedBy: string | null = null): string {
  switch (status) {
    case "approved":
      return tr(decidedBy === "auto" ? "Approvato dal sistema" : "Approvato");
    case "awaiting_approval":
      return tr("Da approvare");
    case "incomplete":
      return tr("Incompleto");
    case "rejected":
      return tr("Rifiutato");
    case "running":
      return tr("In corso");
    default:
      return tr("Non riuscita");
  }
}

export type Tone = "ok" | "warn" | "stop" | "run" | "idle";

export function statusTone(status: RunStatus): Tone {
  switch (status) {
    case "approved":
      return "ok";
    case "awaiting_approval":
    case "incomplete":
      return "warn";
    case "running":
      return "run";
    case "rejected":
      return "idle";
    default:
      return "stop";
  }
}

function italianIteration(version: Pick<Version, "iteration" | "origin" | "copied_from">): string {
  if (version.origin === "workspace") return version.copied_from ? "Risposte" : "Interfaccia";
  return version.iteration === "" ? "Attuale" : version.iteration;
}

export function iterationLabel(version: Pick<Version, "iteration" | "origin" | "copied_from">): string {
  return tr(italianIteration(version));
}

export function versionLabel(version: Version): string {
  const italian = italianIteration(version);
  const kind = tr(italian);
  const run = version.repetition ? `r${version.repetition}` : version.run;
  // A copy named after its kind («risposte-1») says the kind once: «Risposte 1».
  if (run.toLowerCase().startsWith(italian.toLowerCase())) return `${kind} ${run.slice(italian.length).replace(/^[-_ ]+/, "")}`.trim();
  return `${kind} ${run}`;
}

/** How the library names a manual: maker and model, the words printed on the machine. */
export const manualName = (machine: { brand: string; model: string; name: string }) =>
  [machine.brand, machine.model].filter((part) => part && part !== "not_stated").join(" ") || machine.name;

export const formatNumber = (value: number | null | undefined) =>
  value === null || value === undefined ? "" : new Intl.NumberFormat(locale()).format(value);

export const formatDate = (value: string | null) =>
  value
    ? new Intl.DateTimeFormat(locale(), { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(
        new Date(value),
      )
    : "";

/** «28/09, 23:41»: for dense tables where the year is the current one. */
export const formatShortDate = (value: string | null) =>
  value
    ? new Intl.DateTimeFormat(locale(), { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(value))
    : "";

export function formatUsd(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined) return "";
  return `${value.toLocaleString(locale(), { minimumFractionDigits: digits, maximumFractionDigits: digits })} USD`;
}

export function formatDuration(seconds: number): string {
  const whole = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(whole / 60);
  return `${String(minutes).padStart(2, "0")}:${String(whole % 60).padStart(2, "0")}`;
}

export const pageRef = (page: number) => `p. ${page}`;

export const CONDITION_PREFIX: Record<string, string> = labels({
  if: "Vale se",
  prerequisite: "Prima",
  warning: "Attenzione",
  expected: "Risultato atteso",
  order: "Ordine",
});

export const plural = (count: number, one: string, many: string) =>
  `${formatNumber(count)} ${tr(count === 1 ? one : many)}`;

/** An estimate from past runs: «4–6 min», or «~5 min» when both ends read the same. */
export function formatRange(low: number, high: number, format: (value: number) => string, unit: string): string {
  const [from, to] = [format(Math.min(low, high)), format(Math.max(low, high))];
  return from === to ? `~${from} ${unit}` : `${from}–${to} ${unit}`;
}

export const formatMinutes = (seconds: number) => formatNumber(Math.max(1, Math.round(seconds / 60)));
export const formatCost = (usd: number) => usd.toLocaleString(locale(), { minimumFractionDigits: 3, maximumFractionDigits: 3 });
