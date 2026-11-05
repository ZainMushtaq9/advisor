"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import {
  PageHeader,
  StateNotice,
  StatusBadge,
} from "@/components/data-states";
import { useApi } from "@/lib/use-api";

const TICKERS = ["HUBC", "NML", "OGDC"];

interface AssessmentsResponse {
  ticker: string;
  scope_note?: string;
  assessments?: {
    target_key: string;
    horizon: string;
    origin_date: string;
    computation_status: string;
    point_estimate: string | null;
    reason: string | null;
  }[];
}

interface ForecastingStatus {
  targets?: number;
  feature_snapshots?: number;
  assessments?: number;
  computed?: number;
  scope_note?: string;
}

/**
 * Forecasts page: every assessment is insufficient_inputs and no forecast
 * is stored. A naive point exists for length-1 series, but its interval
 * needs 10 residuals it does not have — so the point is recorded as
 * abstained in evidence, never shown as a forecast.
 */
export default function ForecastsPage() {
  const [ticker, setTicker] = useState("HUBC");
  const assessments = useApi<AssessmentsResponse>(
    `/forecasting/assessments?ticker=${ticker}&limit=100`,
  );
  const status = useApi<ForecastingStatus>("/forecasting/status");

  return (
    <div className="pb-10">
      <PageHeader
        title="Forecasts"
        description="Forecast assessments over 1-day, 1-week, 1-month, 3-month, 6-month and 12-month horizons. All 156 assessments are insufficient_inputs and zero forecasts are computed. A horizon never changes the verdict: a 12-month forecast from one observation is exactly as unsupported as a 1-day one."
        banners={[
          "No forecast figure appears anywhere in this product. Any number labelled as a forecast elsewhere would be a fabrication.",
        ]}
      />
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        <div className="mb-4">
          {status.state === "ready" && (
            <p className="text-sm text-neutral-600 dark:text-neutral-300">
              Targets: {status.data.targets ?? "—"} · Feature snapshots:{" "}
              {status.data.feature_snapshots ?? "—"} · Assessments:{" "}
              {status.data.assessments ?? "—"} · Computed: {status.data.computed ?? "—"}
            </p>
          )}
        </div>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <label htmlFor="fc-ticker" className="text-sm font-medium">
            Company:
          </label>
          <select
            id="fc-ticker"
            value={ticker}
            onChange={(event) => setTicker(event.target.value)}
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-navy-700 dark:bg-navy-900"
          >
            {TICKERS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        {assessments.state === "loading" && <p className="text-sm">Loading…</p>}
        {assessments.state === "error" && <StateNotice kind="error" message={assessments.error} />}
        {assessments.state === "ready" && (
          <Card title={`Assessments — ${ticker}`}>
            {assessments.data.scope_note && (
              <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                {assessments.data.scope_note}
              </p>
            )}
            <DataTable
              caption={`Forecast assessments for ${ticker}`}
              columns={[
                { key: "target_key", header: "Target", accessor: "target_key" },
                { key: "horizon", header: "Horizon", accessor: "horizon" },
                { key: "origin_date", header: "Origin", accessor: "origin_date" },
                { key: "computation_status", header: "Status", render: (r) => <StatusBadge status={r.computation_status} /> },
                { key: "reason", header: "Reason", render: (r) => r.reason ?? "" },
              ]}
              rows={assessments.data.assessments ?? []}
              emptyTitle="No assessments"
              emptyDescription="No forecast assessments were returned."
            />
            <p className="mt-3 text-xs text-neutral-500 dark:text-neutral-400">
              Unblockers: 10 more trading days (11 closes) unlock naive intervals
              for close_price and volume; 30 closes unlock AR(1). Each new day also
              adds one return, direction and volatility observation.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
