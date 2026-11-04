import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Simple card container used across foundation screens. */
export function Card({
  title,
  children,
  className,
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "rounded-lg border border-neutral-200 bg-white p-5 shadow-sm dark:border-navy-700 dark:bg-navy-900",
        className,
      )}
    >
      {title && (
        <h2 className="mb-2 text-base font-semibold text-navy-900 dark:text-white">
          {title}
        </h2>
      )}
      {children}
    </section>
  );
}

/** Small label pill. `tone` is presentational only — never a market signal. */
export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "info";
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
        tone === "info"
          ? "bg-navy-50 text-navy-700 dark:bg-navy-800 dark:text-navy-100"
          : "bg-neutral-100 text-neutral-700 dark:bg-navy-800 dark:text-neutral-200",
      )}
    >
      {children}
    </span>
  );
}

/** Accessible loading placeholder (used by route loading.tsx files). */
export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div
      role="status"
      aria-label={label}
      className="mx-auto w-full max-w-6xl px-4 py-8"
    >
      <div className="h-8 w-64 animate-pulse rounded bg-neutral-200 dark:bg-navy-800" />
      <div className="mt-4 h-4 w-full max-w-xl animate-pulse rounded bg-neutral-200 dark:bg-navy-800" />
      <div className="mt-2 h-4 w-2/3 max-w-md animate-pulse rounded bg-neutral-200 dark:bg-navy-800" />
      <span className="sr-only">{label}</span>
    </div>
  );
}

/** Empty state shown whenever a table/chart has no verified data to show. */
export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-neutral-300 px-4 py-8 text-center dark:border-navy-600">
      <p className="font-medium text-neutral-700 dark:text-neutral-200">
        {title}
      </p>
      <p className="mx-auto mt-1 max-w-md text-sm text-neutral-500 dark:text-neutral-400">
        {description}
      </p>
    </div>
  );
}

/** Friendly error panel; never exposes stack traces or secrets. */
export function ErrorState({
  title = "Something went wrong",
  description = "This section could not be loaded. Please try again later. No data is shown because none was loaded.",
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-300 bg-red-50 px-4 py-4 text-sm text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100"
    >
      <p className="font-semibold">{title}</p>
      <p className="mt-1">{description}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md border border-red-400 px-3 py-1.5 font-medium hover:bg-red-100 dark:hover:bg-red-900"
        >
          Try again
        </button>
      )}
    </div>
  );
}
