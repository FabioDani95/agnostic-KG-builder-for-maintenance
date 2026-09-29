// Every word the interface shows, in one place. Manual text stays in its own language.
import type { RunStatus, Tier, Version } from "../api/types";

export const APP_NAME = "Grafi di manutenzione";

export const TYPE_LABEL: Record<string, string> = {
  Asset: "Macchina",
  Symptom: "Sintomo",
  ErrorCode: "Codice di errore",
  FailureMode: "Causa",
  CorrectiveAction: "Azione",
  Component: "Componente",
};

export const RELATION_LABEL: Record<string, string> = {
  MAY_INDICATE: "può indicare",
  INDICATES: "indica",
  RESOLVED_BY: "si risolve con",
  AFFECTS: "riguarda",
  HAS_COMPONENT: "ha il componente",
  GENERATES_ERROR: "può dare il codice",
};

export const TIER_LABEL: Record<Tier | "proposed", string> = {
  proposed: "Proposta",
  green: "Verificata",
  yellow: "In dubbio",
  red: "Scartata",
};

export const WITNESS_LABEL: Record<string, string> = {
  structure: "struttura della pagina",
  agreement: "accordo delle due letture",
  verifier: "verificatore",
  reviewer: "revisore",
};

export const REVIEWER_LABEL: Record<string, string> = {
  human: "una persona",
  agent: "l'agente",
  script: "uno script di prova",
  auto: "in automatico",
};

export const STATION_LABEL: Record<string, string> = {
  read: "Leggi",
  map: "Mappa",
  extract: "Estrai",
  check: "Controlla",
  merge: "Unisci",
  ask: "Chiedi",
};

export function statusLabel(status: RunStatus, decidedBy: string | null = null): string {
  switch (status) {
    case "approved":
      return decidedBy === "auto" ? "Approvato dal sistema" : "Approvato";
    case "awaiting_approval":
      return "Da approvare";
    case "incomplete":
      return "Incompleto";
    case "rejected":
      return "Rifiutato";
    case "running":
      return "In corso";
    default:
      return "Non riuscita";
  }
}

export function iterationLabel(version: Pick<Version, "iteration" | "origin" | "copied_from">): string {
  if (version.origin === "workspace") return version.copied_from ? "Risposte" : "Interfaccia";
  return version.iteration === "" ? "Attuale" : version.iteration;
}

export function versionLabel(version: Version): string {
  const run = version.repetition ? `r${version.repetition}` : version.run;
  return `${iterationLabel(version)} ${run}`;
}

const numbers = new Intl.NumberFormat("it-IT");
const dates = new Intl.DateTimeFormat("it-IT", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export const formatNumber = (value: number | null | undefined) =>
  value === null || value === undefined ? "" : numbers.format(value);

export const formatDate = (value: string | null) => (value ? dates.format(new Date(value)) : "");

export function formatUsd(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined) return "";
  return `${value.toLocaleString("it-IT", { minimumFractionDigits: digits, maximumFractionDigits: digits })} USD`;
}

export function formatDuration(seconds: number): string {
  const whole = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(whole / 60);
  return `${String(minutes).padStart(2, "0")}:${String(whole % 60).padStart(2, "0")}`;
}

export const pageRef = (page: number) => `p. ${page}`;

export const CONDITION_PREFIX: Record<string, string> = {
  if: "Vale se",
  prerequisite: "Prima",
  warning: "Attenzione",
  expected: "Risultato atteso",
  order: "Ordine",
};

export const plural = (count: number, one: string, many: string) =>
  `${formatNumber(count)} ${count === 1 ? one : many}`;
