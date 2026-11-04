/** Display formatting for stored values. Nothing here computes a value:
 * every number shown comes from the API. Missing values stay missing. */

/** Render a stored decimal string (or number) without inventing precision. */
export function fmtNum(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "not available";
  if (typeof value === "number") return String(value);
  return value;
}

/** PKR amounts: stored values are already in PKR; this only adds the label. */
export function fmtPkr(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "not available";
  return `PKR ${fmtNum(value)}`;
}

/** ISO date (YYYY-MM-DD) shown as-is; datetimes trimmed to the date. */
export function fmtDate(value: string | null | undefined): string {
  if (!value) return "not available";
  return value.slice(0, 10);
}

/** Quality status shown verbatim; never upgraded in the UI. */
export function qualityTone(status: string | null | undefined): string {
  switch (status) {
    case "VERIFIED":
      return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100";
    case "PARTIALLY_VERIFIED":
      return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100";
    default:
      return "bg-neutral-100 text-neutral-700 dark:bg-navy-800 dark:text-neutral-200";
  }
}

/** Computation status shown verbatim from the API. */
export function statusTone(status: string | null | undefined): string {
  switch (status) {
    case "computed":
      return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100";
    case "insufficient_inputs":
      return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100";
    case "not_applicable":
      return "bg-neutral-100 text-neutral-700 dark:bg-navy-800 dark:text-neutral-200";
    default:
      return "bg-neutral-100 text-neutral-700 dark:bg-navy-800 dark:text-neutral-200";
  }
}
