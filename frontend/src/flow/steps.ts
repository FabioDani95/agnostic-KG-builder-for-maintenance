// Where a version stands in the making of a graph, and what a person can do next.
// Pure functions of the API rows, shared by the library, the manual, the inbox and the run log.
import { graphRoute, liveRoute, questionsRoute } from "../api/client";
import type { ManualRow, Version } from "../api/types";
import { formatDuration, formatNumber, formatUsd, statusLabel } from "../text/it";

export type StepState = "done" | "current" | "waiting" | "optional" | "failed";

export interface Step {
  key: "extract" | "questions" | "approval";
  label: string;
  state: StepState;
  detail: string;
}

type Stage = Pick<Version, "status" | "open_questions" | "decided_by" | "seconds" | "cost_usd">;

const questionsText = (count: number) => (count === 1 ? "1 domanda" : `${formatNumber(count)} domande`);

/** The three steps of a graph: extraction, the questions for a person, the approval. */
export function lifecycle(version: Stage): Step[] {
  const { status, open_questions: open } = version;
  const ended = status !== "running" && status !== "failed";
  const extract: Step =
    status === "running"
      ? { key: "extract", label: "Estrazione", state: "current", detail: "In corso" }
      : status === "failed"
        ? { key: "extract", label: "Estrazione", state: "failed", detail: "Non riuscita" }
        : {
            key: "extract",
            label: "Estrazione",
            state: "done",
            detail:
              [version.seconds ? formatDuration(version.seconds) : "", version.cost_usd != null ? formatUsd(version.cost_usd) : ""]
                .filter(Boolean)
                .join(" · ") || "Fatta",
          };
  const questions: Step = !ended
    ? { key: "questions", label: "Domande", state: "waiting", detail: "Dopo l'estrazione" }
    : status === "awaiting_approval" && open > 0
      ? { key: "questions", label: "Domande", state: "current", detail: `${questionsText(open)} per te` }
      : open > 0
        ? { key: "questions", label: "Domande", state: "optional", detail: `${questionsText(open)} senza risposta` }
        : { key: "questions", label: "Domande", state: "done", detail: "Nessuna aperta" };
  const approval: Step = !ended
    ? { key: "approval", label: "Approvazione", state: "waiting", detail: "Alla fine" }
    : status === "awaiting_approval"
      ? open > 0
        ? { key: "approval", label: "Approvazione", state: "waiting", detail: "Dopo le risposte" }
        : { key: "approval", label: "Approvazione", state: "current", detail: "Tocca a te" }
      : status === "approved"
        ? { key: "approval", label: "Approvazione", state: "done", detail: statusLabel(status, version.decided_by) }
        : { key: "approval", label: "Approvazione", state: "failed", detail: statusLabel(status, version.decided_by) };
  return [extract, questions, approval];
}

export interface NextStep {
  label: string;
  to: string;
  /** A person is holding up the graph: this is the thing to do. */
  urgent: boolean;
}

/** The one action that moves this version forward, or simply opens it. */
export function nextStep(manualId: string, version: Pick<Version, "version_id" | "status" | "open_questions">): NextStep {
  const { version_id: id, status, open_questions: open } = version;
  if (status === "running") return { label: "Segui l'esecuzione", to: liveRoute(manualId, id), urgent: false };
  if (status === "failed") return { label: "Vedi dove si è fermata", to: liveRoute(manualId, id), urgent: false };
  if (status === "awaiting_approval" && open > 0)
    return {
      label: open === 1 ? "Rispondi alla domanda" : `Rispondi alle ${formatNumber(open)} domande`,
      to: questionsRoute(manualId, id),
      urgent: true,
    };
  if (status === "awaiting_approval") return { label: "Controlla e approva", to: graphRoute(manualId, id), urgent: true };
  return { label: "Apri il grafo", to: graphRoute(manualId, id), urgent: false };
}

export interface Inbox {
  /** The run waits for a person: questions to answer or a graph to approve. */
  waiting: ManualRow[];
  running: ManualRow[];
  /** Approved graphs that still carry questions nobody answered: worth a look, not blocking. */
  doubts: ManualRow[];
}

export function inbox(rows: ManualRow[]): Inbox {
  const result: Inbox = { waiting: [], running: [], doubts: [] };
  for (const row of rows) {
    const latest = row.latest;
    if (!latest) continue;
    if (latest.status === "awaiting_approval") result.waiting.push(row);
    else if (latest.status === "running") result.running.push(row);
    else if (latest.open_questions > 0 && latest.status !== "failed") result.doubts.push(row);
  }
  result.doubts.sort((a, b) => (b.latest?.open_questions ?? 0) - (a.latest?.open_questions ?? 0));
  return result;
}

/** "<manual>/runs/<run>" from /api/jobs/active, as the manual and version the screens use. */
export function activeVersion(run: string | null | undefined): { manualId: string; versionId: string } | null {
  const match = run?.match(/^([^/]+)\/runs\/([^/]+)$/);
  return match ? { manualId: match[1], versionId: `workspace~${match[2]}` } : null;
}
