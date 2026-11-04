/** Shared API shapes. These are contracts only — no market data lives here. */

export interface ApiHealth {
  status: string;
  /** Present only when a backend actually answers; absent in foundation mode. */
  service?: string;
  database?: string;
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

/** Generic table column definition for the reusable DataTable. */
export interface TableColumn<T> {
  key: string;
  header: string;
  /** Render a cell. Return a string/number or a React node via `render`. */
  accessor?: keyof T;
  render?: (row: T) => React.ReactNode;
}
