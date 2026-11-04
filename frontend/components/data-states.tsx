import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { qualityTone, statusTone } from "@/lib/format";

/** Page header: title, plain-language description, and honesty banners. */
export function PageHeader({
  title,
  description,
  banners = [],
}: {
  title: string;
  description: string;
  banners?: string[];
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 pt-8">
      <h1 className="text-2xl font-bold tracking-tight text-navy-900 dark:text-white">
        {title}
      </h1>
      <p className="mt-2 max-w-3xl text-sm text-neutral-600 dark:text-neutral-300">
        {description}
      </p>
      {banners.map((banner) => (
        <p
          key={banner}
          role="note"
          className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100"
        >
          {banner}
        </p>
      ))}
    </div>
  );
}

/** Loading / error / empty states shared by every data screen. */
export function StateNotice({
  kind,
  message,
}: {
  kind: "loading" | "error" | "empty";
  message: string;
}) {
  if (kind === "loading") {
    return (
      <div role="status" aria-label="Loading" className="px-4 py-8 text-sm text-neutral-600 dark:text-neutral-300">
        Loading…
      </div>
    );
  }
  return (
    <div
      role={kind === "error" ? "alert" : "status"}
      className={cn(
        "mx-4 my-6 rounded-md border px-3 py-2 text-sm",
        kind === "error"
          ? "border-red-300 bg-red-50 text-red-900 dark:border-red-700 dark:bg-red-950 dark:text-red-100"
          : "border-neutral-200 bg-neutral-50 text-neutral-700 dark:border-navy-700 dark:bg-navy-900 dark:text-neutral-200",
      )}
    >
      {message}
    </div>
  );
}

/** Quality status pill, shown verbatim from the API. Never upgraded here. */
export function QualityBadge({ status }: { status: string | null | undefined }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        qualityTone(status),
      )}
    >
      {status ?? "unknown"}
    </span>
  );
}

/** Computation status pill (computed / insufficient_inputs / not_applicable). */
export function StatusBadge({ status }: { status: string | null | undefined }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        statusTone(status),
      )}
    >
      {status ?? "unknown"}
    </span>
  );
}

/** Source, date, unit and quality line shown next to financial values. */
export function SourceLine({
  source,
  date,
  unit,
  quality,
  children,
}: {
  source?: string | null;
  date?: string | null;
  unit?: string | null;
  quality?: string | null;
  children?: ReactNode;
}) {
  return (
    <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
      {source ? `Source: ${source}. ` : ""}
      {date ? `Date: ${date}. ` : ""}
      {unit ? `Unit: ${unit}. ` : ""}
      {quality ? (
        <>
          Quality: <QualityBadge status={quality} />{" "}
        </>
      ) : null}
      {children}
    </p>
  );
}
