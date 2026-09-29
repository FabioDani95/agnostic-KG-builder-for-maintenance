import { type KeyboardEvent, type ReactNode } from "react";

export interface Column<T> {
  key: string;
  label: string;
  span: number; // columns of the 12-column grid
  numeric?: boolean;
  render: (row: T) => ReactNode;
}

/** A table on the page grid: rows of 48 px, numbers right-aligned, the whole row opens its item. */
export function Table<T>({
  label,
  columns,
  rows,
  rowKey,
  onOpen,
  empty,
}: {
  label: string;
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  onOpen?: (row: T) => void;
  empty: string;
}) {
  const template = columns.map((column) => `${column.span}fr`).join(" ");
  const keyDown = (row: T) => (event: KeyboardEvent) => {
    if (onOpen && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      onOpen(row);
    }
  };
  return (
    <div className="table" role="table" aria-label={label}>
      <div className="table-row table-head" role="row" style={{ gridTemplateColumns: template }}>
        {columns.map((column) => (
          <span key={column.key} role="columnheader" className={column.numeric ? "num" : undefined}>
            {column.label}
          </span>
        ))}
      </div>
      {rows.length === 0 && <div className="table-empty">{empty}</div>}
      {rows.map((row) => (
        <div
          key={rowKey(row)}
          className="table-row"
          role={onOpen ? "link" : "row"}
          tabIndex={onOpen ? 0 : undefined}
          style={{ gridTemplateColumns: template }}
          onClick={onOpen ? () => onOpen(row) : undefined}
          onKeyDown={onOpen ? keyDown(row) : undefined}
        >
          {columns.map((column) => {
            const content = column.render(row);
            return (
              <span
                key={column.key}
                role="cell"
                className={column.numeric ? "num" : undefined}
                title={typeof content === "string" ? content : undefined}
              >
                {content}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
}
