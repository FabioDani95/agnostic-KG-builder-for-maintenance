import { useEffect, useRef } from "react";
import type { RunStatus } from "../api/types";
import { statusLabel, statusTone } from "../text/it";
import { Icon } from "./Icon";
import { tr } from "../i18n/i18n";

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
    <div className={fill ? "segmented segmented-fill" : "segmented"} role="group" aria-label={tr(label)}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
        >
          {tr(option.label)}
        </button>
      ))}
    </div>
  );
}

/** True when a key press is typing into a field, not a shortcut. */
export function typing(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && Boolean(target.closest("input, textarea, select, [contenteditable='true']"));
}

export function SearchField({
  label,
  value,
  onChange,
  width = 280,
  hotkey = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  width?: number | string;
  /** «/» anywhere on the page puts the cursor here. */
  hotkey?: boolean;
}) {
  const field = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (!hotkey) return;
    const press = (event: KeyboardEvent) => {
      if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey || typing(event.target)) return;
      if (document.querySelector("dialog[open]")) return;
      event.preventDefault();
      field.current?.focus();
    };
    window.addEventListener("keydown", press);
    return () => window.removeEventListener("keydown", press);
  }, [hotkey]);
  return (
    <label className="search" style={{ width }}>
      <span className="visually-hidden">{tr(label)}</span>
      <Icon name="search" size={16} />
      <input
        ref={field}
        className="input"
        type="search"
        placeholder={tr(label)}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            onChange("");
            field.current?.blur();
          }
        }}
      />
      {hotkey && !value && (
        <kbd className="kbd" aria-hidden="true">
          /
        </kbd>
      )}
    </label>
  );
}

export function ProgressBar({ value, total, label }: { value: number; total: number; label: string }) {
  const share = total > 0 ? Math.min(1, value / total) : 0;
  return (
    <div
      className="progress"
      role="progressbar"
      aria-label={tr(label)}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-valuenow={value}
    >
      <span style={{ width: `${share * 100}%` }} />
    </div>
  );
}

/** A run's state: a lamp and its word, never the color alone. */
export function StatusBadge({ status, decidedBy = null }: { status: RunStatus; decidedBy?: string | null }) {
  return (
    <span className="badge" data-tone={statusTone(status)} title={statusLabel(status, decidedBy)}>
      <span className="badge-dot" aria-hidden="true" />
      {statusLabel(status, decidedBy)}
    </span>
  );
}

/** A manufacturer's initials on a plate: ABB, AC for Atlas Copco; the name's when the maker is unknown. */
export function monogram(brand: string, name = ""): string {
  const source = brand && brand !== "not_stated" ? brand : name;
  const words = source.trim().split(/\s+/).filter(Boolean);
  if (words.length > 1) return words.slice(0, 3).map((word) => word[0]).join("").toUpperCase();
  return (words[0] ?? "").slice(0, 3).toUpperCase() || "–";
}

export function Monogram({ machine }: { machine: { brand: string; name: string } }) {
  return (
    <span className="monogram" aria-hidden="true">
      {monogram(machine.brand, machine.name)}
    </span>
  );
}
