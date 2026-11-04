import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface FoundationShellProps {
  title: string;
  description: string;
  /** What a later phase will add here — stated as intent, never as data. */
  planned?: string[];
  children?: ReactNode;
  className?: string;
}

/**
 * Every Phase 2 route renders through this shell so no page can be
 * mistaken for a live product screen: the banner is always visible and
 * no fabricated PSX figures are ever rendered.
 */
export function FoundationShell({
  title,
  description,
  planned = [],
  children,
  className,
}: FoundationShellProps) {
  return (
    <div className={cn("mx-auto w-full max-w-6xl px-4 py-8", className)}>
      <div
        role="note"
        aria-label="Foundation shell notice"
        className="mb-6 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100"
      >
        Foundation shell — this page is structure only. No market data, prices,
        indices, company financials, forecasts, or recommendations are shown
        here. Content arrives only when a later phase connects verified data.
      </div>
      <h1 className="text-3xl font-bold tracking-tight text-navy-900 dark:text-white">
        {title}
      </h1>
      <p className="mt-2 max-w-3xl text-base leading-relaxed text-neutral-600 dark:text-neutral-300">
        {description}
      </p>
      {planned.length > 0 && (
        <section aria-label="Planned for a later phase" className="mt-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
            Planned for a later phase (not available yet)
          </h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-neutral-600 dark:text-neutral-300">
            {planned.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      )}
      {children && <div className="mt-8">{children}</div>}
    </div>
  );
}
