"use client";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface CoverageResponse {
  as_of: string;
  securities_assessed: number;
  indicators_registered: number;
  securities_with_any_calculable: number;
  per_indicator?: Record<
    string,
    {
      category: string;
      warmup_bars: number;
      calculable: number;
      not_calculable: number;
      reasons: Record<string, number>;
    }
  >;
}

/**
 * Technical page: coverage only. With one price date, zero indicators are
 * calculable for any security — the table states the reason counts instead
 * of drawing a chart from one point or showing zeros as values.
 */
export default function IndicatorsPage() {
  const coverage = useApi<CoverageResponse>("/indicators/coverage");

  const rows = coverage.state === "ready"
    ? Object.entries(coverage.data.per_indicator ?? {}).map(([key, v]) => ({
      indicator: key,
      category: v.category,
      warmup_bars: String(v.warmup_bars),
      calculable: String(v.calculable),
      not_calculable: String(v.not_calculable),
      reasons: Object.entries(v.reasons)
        .map(([reason, count]) => `${reason} ${count}`)
        .join(" · "),
    }))
    : [];

  return (
    <div className="pb-10">
      <PageHeader
        title="Technical analysis"
        description="Deterministic indicator coverage from the single stored price date. Every indicator is NOT_CALCULABLE for every security: 444 priced securities lack warm-up bars and 26 have no price row at all. No signal is generated — the activated-rules set is empty by design."
        banners={[
          "Weekly and monthly aggregation stays 'partial' by design: no validated trading calendar exists, and the official holiday schedule is itself Terms-gated.",
          "Corporate-action adjustment methodology is scoped out: no adjustment data source exists, and designing one would be fabrication. All values use unadjusted closes.",
        ]}
      />
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        {coverage.state === "loading" && <p className="text-sm">Loading…</p>}
        {coverage.state === "error" && <StateNotice kind="error" message={coverage.error} />}
        {coverage.state === "ready" && (
          <Card title={`Coverage as of ${coverage.data.as_of}`}>
            <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
              Securities assessed: {coverage.data.securities_assessed} · Indicators
              registered: {coverage.data.indicators_registered} · Securities with any
              calculable value: {coverage.data.securities_with_any_calculable}
            </p>
            <DataTable
              caption="Indicator coverage"
              columns={[
                { key: "indicator", header: "Indicator", accessor: "indicator" },
                { key: "category", header: "Category", accessor: "category" },
                { key: "warmup_bars", header: "Warm-up bars", accessor: "warmup_bars" },
                { key: "calculable", header: "Calculable", accessor: "calculable" },
                { key: "not_calculable", header: "Not calculable", accessor: "not_calculable" },
                { key: "reasons", header: "Reasons", accessor: "reasons" },
              ]}
              rows={rows}
              emptyTitle="No coverage rows"
              emptyDescription="No coverage rows were returned."
            />
            <p className="mt-3 text-xs text-neutral-500 dark:text-neutral-400">
              Unblockers: four more trading days unlock the first SMA(5) values;
              daily_return additionally needs a present previous_close in a future
              source file — more trading days alone do not unblock it.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
