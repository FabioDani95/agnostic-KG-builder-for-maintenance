import { useEffect, useRef, useState } from "react";
import type { FieldDescriptor } from "../api/types";
import { tr, useLang } from "../i18n/i18n";
import { useEditor } from "./EditorSessionProvider";
export function parseValue(text: string, type: string): unknown {
  if (type === "number" || type === "integer") {
    const n = Number(text);
    if (
      !text.trim() ||
      !Number.isFinite(n) ||
      (type === "integer" && !Number.isInteger(n))
    )
      throw new Error(tr("Inserisci un numero valido"));
    return n;
  }
  if (type === "array") {
    let list: unknown;
    try {
      list = JSON.parse(text);
    } catch {
      throw new Error(tr("Inserisci una lista di testi"));
    }
    if (!Array.isArray(list) || list.some((v) => typeof v !== "string"))
      throw new Error(tr("Inserisci una lista di testi"));
    return list;
  }
  return text;
}
export function EditableCell({
  value,
  field,
  label,
  onChange,
  onRemove,
  readOnly,
}: {
  value: unknown;
  field: FieldDescriptor;
  label: string;
  onChange: (value: unknown) => void;
  onRemove?: () => void;
  readOnly?: boolean;
}) {
  useLang();
  const { dispatch } = useEditor();
  const type =
    field.type ??
    (Array.isArray(value)
      ? "array"
      : typeof value === "number"
        ? "number"
        : typeof value === "boolean"
          ? "boolean"
          : "string");
  const formatted =
    value == null
      ? ""
      : type === "array"
        ? JSON.stringify(value)
        : String(value);
  const [active, setActive] = useState(false);
  const [text, setText] = useState(formatted);
  const [error, setError] = useState("");
  const ref = useRef<HTMLInputElement | HTMLTextAreaElement>(null);
  useEffect(() => {
    if (!active) setText(formatted);
  }, [formatted, active]);
  const cancel = () => {
    setText(formatted);
    setError("");
    setActive(false);
    dispatch({ type: "pending", value: false });
  };
  const commit = () => {
    if (!active) return;
    if (text === formatted) {
      cancel();
      return;
    }
    try {
      const next = parseValue(text, type);
      if (JSON.stringify(next) !== JSON.stringify(value)) onChange(next);
      setError("");
      setActive(false);
      dispatch({ type: "pending", value: false });
    } catch (e) {
      setError(e instanceof Error ? e.message : tr("Valore non valido"));
      ref.current?.focus();
    }
  };
  if (readOnly) return <span title={formatted}>{formatted || "–"}</span>;
  if (type === "boolean")
    return (
      <select
        aria-label={label}
        value={value == null ? "null" : String(value)}
        onChange={(e) =>
          onChange(e.target.value === "null" ? null : e.target.value === "true")
        }
      >
        <option value="null">{tr("Vuoto")}</option>
        <option value="true">true</option>
        <option value="false">false</option>
      </select>
    );
  const props = {
    "aria-label": label,
    "aria-invalid": Boolean(error),
    value: text,
    onFocus: () => setActive(true),
    onChange: (
      e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    ) => {
      setActive(true);
      setText(e.target.value);
      dispatch({ type: "pending", value: true });
    },
    onBlur: commit,
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        cancel();
      }
      if (
        e.key === "Enter" &&
        !(
          field.name === "instruction_text" ||
          field.name === "description" ||
          type === "array"
        )
      ) {
        e.preventDefault();
        commit();
      }
    },
  };
  return (
    <div className="editor-cell">
      {field.name === "instruction_text" ||
      field.name === "description" ||
      type === "array" ? (
        <textarea
          ref={ref as React.Ref<HTMLTextAreaElement>}
          {...props}
          rows={active ? 4 : 1}
        />
      ) : (
        <input ref={ref as React.Ref<HTMLInputElement>} {...props} />
      )}
      {error && <span role="alert">{error}</span>}
      <details>
        <summary aria-label={tr("Azioni campo")}>⋯</summary>
        <button
          onClick={() => {
            onChange(type === "array" ? [] : type === "string" ? "" : null);
            cancel();
          }}
        >
          {tr("Svuota")}
        </button>
        <button
          onClick={() => {
            onChange(null);
            cancel();
          }}
        >
          {tr("Imposta senza valore")}
        </button>
        {onRemove && (
          <button
            onClick={() => {
              onRemove();
              cancel();
            }}
          >
            {tr("Rimuovi campo facoltativo")}
          </button>
        )}
      </details>
    </div>
  );
}
