import { Link } from "react-router-dom";
import { editGraphRoute, questionsRoute } from "../api/client";
import type { Version } from "../api/types";
import { tr } from "../i18n/i18n";
import { Icon } from "./Icon";
export const EDIT_REASONS: Record<string, string> = {
  PROCESS_RUNNING: "Disponibile al termine dell’estrazione",
  UNAPPLIED_ANSWERS: "Applica prima le risposte",
  GRAPH_UNAVAILABLE: "Grafo assente o formato non supportato",
};
export function EditGraphButton({
  manualId,
  version,
}: {
  manualId: string;
  version: Version | undefined;
}) {
  const reason = version?.edit_reason
    ? tr(EDIT_REASONS[version.edit_reason] ?? version.edit_reason)
    : undefined;
  return (
    <>
      {version?.can_edit ? (
        <Link
          className="button button-bar"
          to={editGraphRoute(manualId, version.version_id)}
        >
          <Icon name="pencil" />
          {tr("Modifica grafo")}
        </Link>
      ) : (
        <button className="button button-bar" disabled title={reason}>
          <Icon name="pencil" />
          {tr("Modifica grafo")}
        </button>
      )}
      {reason && (
        <span className="t-small secondary">
          {version?.edit_reason === "UNAPPLIED_ANSWERS" ? (
            <Link to={questionsRoute(manualId, version.version_id)}>
              {reason}
            </Link>
          ) : (
            reason
          )}
        </span>
      )}
    </>
  );
}
