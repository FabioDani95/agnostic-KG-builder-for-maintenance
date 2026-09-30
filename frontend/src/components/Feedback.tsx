import { Icon } from "./Icon";
import { tr } from "../i18n/i18n";

/** Waiting for data: a turning mark in the place the data will fill, named for screen readers. */
export function Loading({ label }: { label: string }) {
  return (
    <div className="loading" role="status">
      <Icon name="loader" size={20} className="spin" />
      <span className="visually-hidden">{tr(label)}</span>
    </div>
  );
}

/** Something went wrong: what happened, and a way to try again when there is one. */
export function Problem({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="problem" role="alert">
      <Icon name="alert" />
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="button button-secondary" onClick={onRetry}>
          {tr("Riprova")}
        </button>
      )}
    </div>
  );
}
