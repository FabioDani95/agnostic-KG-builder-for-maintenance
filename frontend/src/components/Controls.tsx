import { type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Icon } from "./Icon";
import { APP_NAME } from "../text/it";

export function SegmentedControl<T extends string>({
  label,
  options,
  value,
  onChange,
  fill = false,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  fill?: boolean;
}) {
  return (
    <div className={fill ? "segmented segmented-fill" : "segmented"} role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function SearchField({
  label,
  value,
  onChange,
  width = 288,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  width?: number;
}) {
  return (
    <label className="search" style={{ width }}>
      <span className="visually-hidden">{label}</span>
      <Icon name="search" size={16} />
      <input
        className="input"
        type="search"
        placeholder={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

export function BackLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className="button button-plain" style={{ paddingLeft: 0 }}>
      <Icon name="chevron-left" size={16} />
      {children}
    </Link>
  );
}

/** Top bar of the document screens: the app name or a way back, and at most two controls. */
export function TopBar({ back, children }: { back?: ReactNode; children?: ReactNode }) {
  return (
    <header className="topbar">
      <div className="container">
        {back ?? (
          <Link to="/" className="topbar-name">
            {APP_NAME}
          </Link>
        )}
        <div className="row">{children}</div>
      </div>
    </header>
  );
}

export function ProgressBar({ value, total, label }: { value: number; total: number; label: string }) {
  const share = total > 0 ? Math.min(1, value / total) : 0;
  return (
    <div
      className="progress"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-valuenow={value}
    >
      <span style={{ width: `${share * 100}%` }} />
    </div>
  );
}
