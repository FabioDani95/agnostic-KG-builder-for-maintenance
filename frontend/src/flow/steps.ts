// Where a version stands in the making of a graph, and what a person can do next.
// Pure functions of the API rows, shared by the library, the manual, the inbox and the run log.
import { graphRoute, liveRoute, questionsRoute } from "../api/client";
import type { ManualRow, Version } from "../api/types";
import { tr } from "../i18n/i18n";
import { formatDuration, formatNumber, formatUsd, statusLabel } from "../text/it";

export type StepState = "done" | "current" | "waiting" | "optional" | "failed";

export interface Step {
  key: "extract" | "questions" | "approval";
  label: string;
  state: StepState;
  detail: string;
}

type Stage = Pick<Version, "status" | "open_questions" | "decided_by" | "seconds" | "cost_usd">;

const questionsText = (count: number) => (count === 1 ? tr("1 domanda") : tr("{n} domande", { n: formatNumber(count) }));

/** The three steps of a graph: extraction, the questions for a person, the approval. */
export function lifecycle(version: Stage): Step[] {
  const { status, open_questions: open } = version;
  const ended = status !== "running" && status !== "failed";
  const extract: Step =
    status === "running"
      ? { key: "extract", label: tr("Estrazione"), state: "current", detail: tr("In corso") }
      : status === "failed"
        ? { key: "extract", label: tr("Estrazione"), state: "failed", detail: tr("Non riuscita") }
        : {
            key: "extract",
            label: tr("Estrazione"),
            state: "done",
            detail:
              [version.seconds ? formatDuration(version.seconds) : "", version.cost_usd != null ? formatUsd(version.cost_usd) : ""]
                .filter(Boolean)
                .join(" · ") || tr("Fatta"),
          };
  const questions: Step = !ended
    ? { key: "questions", label: tr("Domande"), state: "waiting", detail: tr("Dopo l'estrazione") }
    : status === "awaiting_approval" && open > 0
      ? { key: "questions", label: tr("Domande"), state: "current", detail: tr("{questions} per te", { questions: questionsText(open) }) }
      : open > 0
        ? { key: "questions", label: tr("Domande"), state: "optional", detail: tr("{questions} senza risposta", { questions: questionsText(open) }) }
        : { key: "questions", label: tr("Domande"), state: "done", detail: tr("Nessuna aperta") };
  const approval: Step = !ended
    ? { key: "approval", label: tr("Approvazione"), state: "waiting", detail: tr("Alla fine") }
    : status === "awaiting_approval"
      ? open > 0
        ? { key: "approval", label: tr("Approvazione"), state: "waiting", detail: tr("Dopo le risposte") }
        : { key: "approval", label: tr("Approvazione"), state: "current", detail: tr("Tocca a te") }
      : status === "approved"
        ? { key: "approval", label: tr("Approvazione"), state: "done", detail: statusLabel(status, version.decided_by) }
        : { key: "approval", label: tr("Approvazione"), state: "failed", detail: statusLabel(status, version.decided_by) };
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
  if (status === "running") return { label: tr("Segui l'esecuzione"), to: liveRoute(manualId, id), urgent: false };
  if (status === "failed") return { label: tr("Vedi dove si è fermata"), to: liveRoute(manualId, id), urgent: false };
  if (status === "awaiting_approval" && open > 0)
    return {
      label: open === 1 ? "Rispondi alla domanda" : tr("Rispondi alle {n} domande", { n: formatNumber(open) }),
      to: questionsRoute(manualId, id),
      urgent: true,
    };
  if (status === "awaiting_approval") return { label: tr("Controlla e approva"), to: graphRoute(manualId, id), urgent: true };
  return { label: tr("Apri il grafo"), to: graphRoute(manualId, id), urgent: false };
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
