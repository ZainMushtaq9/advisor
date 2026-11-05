"use client";

import Link from "next/link";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, QualityBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtNum } from "@/lib/format";
import {
  marketStatusView,
  type MarketStatusResponse,
} from "@/lib/market-status";

interface BreadthResponse {
  metrics?: {
    trading_date: string;
    scope: string;
    metric_key: string;
    metric_value: string | null;
    status: string;
    coverage_note?: string | null;
  }[];
}

interface Decision {
  company_id: number;
  screening_outcome: string;
  research_conclusion: string;
  user_facing: string;
  confidence: string;
  total_score: string;
}

interface DecisionsResponse {
  decisions?: Decision[];
}

interface AlertsStatus {
  total_alerts?: number;
  by_severity?: Record<string, number>;
}

/**
 * Dashboard: live overview from stored rows only. No chart is drawn from a
 * single price date — a one-point chart would imply a series that does not
 * exist, so breadth and coverage figures are shown as tables instead.
 */
export default function DashboardPage() {
  const market = useApi<MarketStatusResponse>("/market/status");
  const breadth = useApi<BreadthResponse>("/breadth");
  const decisions = useApi<DecisionsResponse>("/decisions");
  const alerts = useApi<AlertsStatus>("/alerts/status");

  const marketView =
    market.state === "ready" ? marketStatusView(market.data) : null;

  const marketMetrics = (breadth.state === "ready" ? breadth.data.metrics ?? [] : []).filter(
    (m) => m.scope === "MARKET",
  );

  return (
    <div className="pb-10">
      <PageHeader
        title="Dashboard"
        description="Market overview from validated stored data, with source and freshness labels. All prices are UNVERIFIED single-date observations; nothing here is a forecast or a recommendation."
        banners={[
          "Decision user-facing values are all WITHHELD: confidence caps at LOW while every input is UNVERIFIED. Withheld means not shown as advice, not hidden data.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6 lg:grid-cols-2">
        <Card title="Market snapshot">
          {market.state === "loading" && <p className="text-sm">Loading…</p>}
          {market.state === "error" && (
            <StateNotice kind="error" message={market.error} />
          )}
          {market.state === "ready" && (
            <div className="text-sm">
              <p>
                <strong>{marketView?.priceRows ?? "—"}</strong> price rows on{" "}
                {marketView?.tradingDates.join(", ") || "no trading date"}
              </p>
              <p className="mt-2">
                Quality: <QualityBadge status={marketView?.qualityStatus} />
              </p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                {marketView?.scopeNote ??
                  "470 Main Board / Normal Counter snapshot securities."}{" "}
                All rows are unadjusted (is_adjusted false) and carry no
                previous close or turnover.
              </p>
              <p className="mt-3">
                <Link href="/market" className="font-medium text-accent-500">
                  Browse prices →
                </Link>
              </p>
            </div>
          )}
        </Card>

        <Card title="Market breadth — 2026-11-03" className="min-w-0">
          {breadth.state === "loading" && <p className="text-sm">Loading…</p>}
          {breadth.state === "error" && (
            <StateNotice kind="error" message={breadth.error} />
          )}
          {breadth.state === "ready" && (
            <DataTable
              caption="Market breadth metrics for 2026-11-03"
              layout="fixed"
              columns={[
                { key: "metric_key", header: "Metric", accessor: "metric_key" },
                { key: "metric_value", header: "Value", accessor: "metric_value" },
                { key: "status", header: "Status", accessor: "status" },
              ]}
              rows={marketMetrics.map((m) => ({
                metric_key: m.metric_key,
                metric_value: fmtNum(m.metric_value),
                status: m.status,
              }))}
              emptyTitle="No breadth metrics"
              emptyDescription="No breadth metrics were returned. Nothing is estimated."
            />
          )}
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            Advances, declines and turnover distribution are NOT_CALCULABLE:
            previous_close and turnover are NULL on all stored price rows.
          </p>
        </Card>

        <Card
          title="Decisions (research opinions only)"
          className="min-w-0 lg:col-span-2"
        >
          {decisions.state === "loading" && <p className="text-sm">Loading…</p>}
          {decisions.state === "error" && (
            <StateNotice kind="error" message={decisions.error} />
          )}
          {decisions.state === "ready" && (
            <DataTable
              caption="Phase 15 decisions"
              layout="fixed"
              columns={[
                { key: "company_id", header: "Company id", accessor: "company_id" },
                { key: "screening_outcome", header: "Screening", accessor: "screening_outcome" },
                { key: "research_conclusion", header: "Research conclusion", accessor: "research_conclusion" },
                { key: "user_facing", header: "User-facing", accessor: "user_facing" },
                { key: "confidence", header: "Confidence", accessor: "confidence" },
              ]}
              rows={(decisions.data.decisions ?? []).map((d) => ({
                company_id: String(d.company_id),
                screening_outcome: d.screening_outcome,
                research_conclusion: d.research_conclusion,
                user_facing: d.user_facing,
                confidence: d.confidence,
              }))}
              emptyTitle="No decisions"
              emptyDescription="No decision rows were returned."
            />
          )}
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            HOLD_CANDIDATE is a research conclusion, not advice: the
            user-facing value is WITHHELD for every company.
          </p>
        </Card>

        <Card title="Alerts">
          {alerts.state === "loading" && <p className="text-sm">Loading…</p>}
          {alerts.state === "error" && (
            <StateNotice kind="error" message={alerts.error} />
          )}
          {alerts.state === "ready" && (
            <div className="text-sm">
              <p>
                <strong>{alerts.data.total_alerts ?? "—"}</strong> alerts, all
                NEW, delivered in-app only.
              </p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                By severity:{" "}
                {Object.entries(alerts.data.by_severity ?? {})
                  .map(([k, v]) => `${k} ${v}`)
                  .join(" · ") || "not reported"}
              </p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                False-positive rate is NOT_MEASURABLE: no alert has a
                user-feedback label yet.
              </p>
              <p className="mt-3">
                <Link href="/alerts" className="font-medium text-accent-500">
                  Browse alerts →
                </Link>
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
