import { type KeyboardEvent, type ReactNode, useMemo } from "react";
import { Icon } from "./Icon";

export interface Column<T> {
  key: string;
  label: string;
  span: number; // columns of the 12-column grid
  numeric?: boolean;
  render: (row: T) => ReactNode;
  /** The value to sort by; a column without it cannot be sorted. */
  sort?: (row: T) => string | number | null | undefined;
}

export type SortDirection = "asc" | "desc";
export interface Sorting {
  key: string;
  direction: SortDirection;
}

export function sortRows<T>(rows: T[], columns: Column<T>[], sorting: Sorting | null): T[] {
  const column = sorting && columns.find((item) => item.key === sorting.key);
  if (!sorting || !column?.sort) return rows;
  const value = column.sort;
  const sign = sorting.direction === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const left = value(a);
    const right = value(b);
    if (left == null || left === "") return right == null || right === "" ? 0 : 1; // empty values last
    if (right == null || right === "") return -1;
    if (typeof left === "number" && typeof right === "number") return (left - right) * sign;
    return String(left).localeCompare(String(right), "it", { numeric: true }) * sign;
  });
}

/** Next sorting after a click on a header: a new column sorts up, the same one flips. */
export function nextSorting(current: Sorting | null, key: string): Sorting {
  return current?.key === key
    ? { key, direction: current.direction === "asc" ? "desc" : "asc" }
    : { key, direction: "asc" };
}

/**
 * A table on a 12-column grid: rows of 36 px, numbers right-aligned, the whole row opens its item.
 * Headers with a sort value sort on click; `actions` adds a trailing column of row buttons.
 */
export function Table<T>({
  label,
  columns,
  rows,
  rowKey,
  onOpen,
  empty,
  sorting = null,
  onSort,
  actions,
}: {
  label: string;
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  onOpen?: (row: T) => void;
  empty: string;
  sorting?: Sorting | null;
  onSort?: (key: string) => void;
  actions?: (row: T) => ReactNode;
}) {
  const template = actions ? "repeat(12, minmax(0, 1fr)) 32px" : "repeat(12, minmax(0, 1fr))";
  const shown = useMemo(() => sortRows(rows, columns, sorting), [rows, columns, sorting]);
  const keyDown = (row: T) => (event: KeyboardEvent) => {
    // Keys pressed on a button inside the row belong to that button.
    if (event.target !== event.currentTarget) return;
    if (onOpen && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      onOpen(row);
    }
  };
  return (
    <div className="table" role="table" aria-label={label}>
      <div className="table-row table-head" role="row" style={{ gridTemplateColumns: template }}>
        {columns.map((column) => {
          const active = sorting?.key === column.key;
          const sortable = Boolean(column.sort && onSort);
          return (
            <span
              key={column.key}
              role="columnheader"
              className={column.numeric ? "num" : undefined}
              style={{ gridColumn: `span ${column.span}` }}
              aria-sort={active ? (sorting!.direction === "asc" ? "ascending" : "descending") : undefined}
            >
              {sortable ? (
                <button type="button" className="th-sort" data-active={active} onClick={() => onSort!(column.key)}>
                  {column.label}
                  <Icon
                    name={active ? (sorting!.direction === "asc" ? "sort-up" : "sort-down") : "sortable"}
                    size={12}
                  />
                </button>
              ) : (
                column.label
              )}
            </span>
          );
        })}
        {actions && <span role="columnheader" />}
      </div>
      {shown.length === 0 && <div className="table-empty">{empty}</div>}
      {shown.map((row) => (
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
                style={{ gridColumn: `span ${column.span}` }}
                title={typeof content === "string" ? content : undefined}
              >
                {content}
              </span>
            );
          })}
          {actions && (
            <span role="cell" className="row-actions" onClick={(event) => event.stopPropagation()}>
              {actions(row)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
