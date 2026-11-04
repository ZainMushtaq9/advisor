import type { TableColumn } from "@/lib/types";
import { EmptyState } from "./ui";

interface DataTableProps<T> {
  caption: string;
  columns: TableColumn<T>[];
  rows: T[];
  /** Shown when rows is empty. Must state that no verified data exists. */
  emptyTitle?: string;
  emptyDescription?: string;
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
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return (
      <div>
        <p className="sr-only">{caption}</p>
        <EmptyState title={emptyTitle} description={emptyDescription} />
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-navy-700">
      <table className="w-full text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-neutral-50 dark:bg-navy-800">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className="px-4 py-3 font-semibold text-neutral-700 dark:text-neutral-200"
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
                <td key={column.key} className="px-4 py-3">
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
