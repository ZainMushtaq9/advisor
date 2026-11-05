import type { TableColumn } from "@/lib/types";
import { cn } from "@/lib/utils";
import { EmptyState } from "./ui";

interface DataTableProps<T> {
  caption: string;
  columns: TableColumn<T>[];
  rows: T[];
  /** Shown when rows is empty. Must state that no verified data exists. */
  emptyTitle?: string;
  emptyDescription?: string;
  /**
   * "auto" (default) sizes columns to their content and scrolls sideways
   * when the content is wider than the card. "fixed" forces the table to
   * the card width and wraps cell text instead, so a wide table in a narrow
   * card never shows an internal horizontal scrollbar. Use "fixed" for
   * tables whose columns carry long unbroken tokens in half-width cards.
   */
  layout?: "auto" | "fixed";
}

/**
 * Professional, accessible data table.
 * Foundation rule: it renders rows it is given and an explicit empty state
 * otherwise. Callers must never pass fabricated PSX rows to it.
 */
export function DataTable<T>({
  caption,
  columns,
  rows,
  emptyTitle = "No data yet",
  emptyDescription = "No verified records are available for this table. Nothing is shown rather than placeholder figures.",
  layout = "auto",
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return (
      <div>
        <p className="sr-only">{caption}</p>
        <EmptyState title={emptyTitle} description={emptyDescription} />
      </div>
    );
  }
  const fixed = layout === "fixed";
  return (
    <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-navy-700">
      <table className={cn("w-full text-left text-sm", fixed && "table-fixed")}>
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-neutral-50 dark:bg-navy-800">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn(
                  "px-4 py-3 font-semibold text-neutral-700 dark:text-neutral-200",
                  fixed && "whitespace-normal break-words px-3 py-2",
                )}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={index}
              className="border-t border-neutral-200 dark:border-navy-700"
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn(
                    "px-4 py-3",
                    fixed && "whitespace-normal break-words px-3 py-2",
                  )}
                >
                  {column.render
                    ? column.render(row)
                    : column.accessor
                      ? String(row[column.accessor] ?? "")
                      : ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
