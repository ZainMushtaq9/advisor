"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import {
  PageHeader,
  StateNotice,
  StatusBadge,
  SourceLine,
} from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtNum } from "@/lib/format";

const TICKERS = ["HUBC", "NML", "OGDC", "HBL"];

interface RatiosResponse {
  ticker: string;
  status: string;
  note?: string;
  period_label?: string;
  period_end?: string;
  period_days?: number;
  metrics?: { metric_key: string; status: string; value: string | null; reason: string | null }[];
  health?: Record<string, { score: string | null }>;
  warnings?: { warning_key: string; severity: string }[];
}

/**
 * Fundamentals page: statement-derived ratios for one selected ticker.
 * Periods are never annualised and no TTM is synthesised: each company
 * keeps its own period.
 */
export default function FundamentalsPage() {
  const [ticker, setTicker] = useState("HUBC");
  const ratios = useApi<RatiosResponse>(`/fundamentals/ratios?ticker=${ticker}`);

  return (
    <div className="pb-10">
      <PageHeader
        title="Fundamentals"
        description="Statement-derived ratios and health scores. All values are UNVERIFIED and period-specific: HUBC is a full FY2026 year, NML is nine months to 31 Mar 2025, OGDC is six months to 31 Dec 2025, HBL is a full year to 31 Dec 2025. Averages use two balance-sheet dates only. Health scores are descriptive, not a credit rating and not investment advice."
        banners={[
          "NML's nine-month result is a LOSS — it is shown as a loss, never hidden or replaced by the full-year figure.",
        ]}
      />
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <label htmlFor="fund-ticker" className="text-sm font-medium">
            Company:
          </label>
          <select
            id="fund-ticker"
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

        {ratios.state === "loading" && <p className="text-sm">Loading…</p>}
        {ratios.state === "error" && <StateNotice kind="error" message={ratios.error} />}
        {ratios.state === "ready" &&
          (ratios.data.status === "assessed" ? (
            <div className="grid gap-4">
              <Card title={`Ratios — ${ticker}`}>
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  Period: {ratios.data.period_label ?? ratios.data.period_end} (
                  {ratios.data.period_days ?? "—"} days).
                </p>
                <SourceLine unit="Ratios are unitless unless stated; currency values in PKR thousands as stored" quality="UNVERIFIED" />
                <div className="mt-3">
                  <DataTable
                    caption={`Fundamental ratios for ${ticker}`}
                    columns={[
                      { key: "metric_key", header: "Metric", accessor: "metric_key" },
                      { key: "value", header: "Value", render: (r) => fmtNum(r.value) },
                      { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
                      { key: "reason", header: "Reason", render: (r) => r.reason ?? "" },
                    ]}
                    rows={ratios.data.metrics ?? []}
                    emptyTitle="No ratios"
                    emptyDescription="No ratio rows were returned."
                  />
                </div>
                {(ratios.data.warnings ?? []).length > 0 && (
                  <p className="mt-3 text-sm">
                    Warnings (review-only, never proof of fraud or insolvency):{" "}
                    {(ratios.data.warnings ?? []).map((w) => w.warning_key).join(", ")}
                  </p>
                )}
              </Card>
              <Card title="Health scores (descriptive only)">
                <DataTable
                  caption={`Health scores for ${ticker}`}
                  columns={[
                    { key: "dimension", header: "Dimension", accessor: "dimension" },
                    { key: "score", header: "Score", accessor: "score" },
                  ]}
                  rows={Object.entries(ratios.data.health ?? {}).map(([dimension, v]) => ({
                    dimension,
                    score: v.score ?? "not available",
                  }))}
                  emptyTitle="No health scores"
                  emptyDescription="No health rows were returned."
                />
                <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
                  No aggregate grade is computed. Sector is NULL for all three
                  companies because each is alone in its sector.
                </p>
              </Card>
            </div>
          ) : (
            <StateNotice
              kind="empty"
              message={`Status: ${ratios.data.status}. ${ratios.data.note ?? "No configured period exists for this company."}`}
            />
          ))}
      </div>
    </div>
  );
}
