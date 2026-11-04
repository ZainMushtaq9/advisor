"use client";

import Link from "next/link";
import { Card, Badge } from "@/components/ui";
import { ApiStatus } from "@/components/api-status";
import { NAV_ITEMS } from "@/lib/nav";
import { PageHeader, StateNotice, QualityBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface StatisticsResponse {
  companies: number;
  securities: number;
  sectors: number;
  quality_status?: string;
  evidence_rows?: number;
}

interface MarketStatus {
  price_rows?: number;
  trading_dates?: string[];
  quality_status?: string;
}

interface RegimeResponse {
  regimes?: { label?: string; as_of?: string }[];
}

interface AlertsStatus {
  total_alerts?: number;
  by_severity?: Record<string, number>;
}

interface ReportsStatus {
  total?: number;
  by_status?: Record<string, number>;
  published_externally?: number;
}

/**
 * Phase 23 home page. Every figure comes from a live API response; when
 * the backend is unreachable the page says so instead of showing numbers.
 * Nothing here is investment advice, a forecast, or a recommendation.
 */
export default function Home() {
  const stats = useApi<StatisticsResponse>("/registry/statistics");
  const market = useApi<MarketStatus>("/market/status");
  const regimes = useApi<RegimeResponse>("/macro/regimes");
  const alerts = useApi<AlertsStatus>("/alerts/status");
  const reports = useApi<ReportsStatus>("/reports/status");

  const anyError =
    stats.state === "error" ||
    market.state === "error" ||
    regimes.state === "error" ||
    alerts.state === "error" ||
    reports.state === "error";

  return (
    <div className="pb-10">
      <PageHeader
        title="PSX Intelligence AI"
        description="A Pakistan Stock Exchange research workspace built only from stored, labelled observations. Prices cover one trading date, statements cover three companies, forecasts are abstained, decisions are withheld, and reports are drafts — the interface states each limit where the data appears."
        banners={[
          "All figures on this site are descriptive analysis of stored rows, not investment advice, not buy/sell signals, and not forecasts.",
          "Every stored price, statement, ratio and valuation is UNVERIFIED unless its quality badge says otherwise.",
        ]}
      />
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-3 px-4 pt-4">
        <ApiStatus />
        <Badge tone="info">Phase 23 — Frontend Product Experience</Badge>
        <Badge>PKR 0 · Free / open-source only</Badge>
      </div>

      {anyError && (
        <StateNotice
          kind="error"
          message="The backend could not be reached for one or more overview panels. Figures below show only what was actually returned; missing panels are not estimated."
        />
      )}

      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6 sm:grid-cols-2 lg:grid-cols-3">
        <Card title="Registry">
          {stats.state === "loading" && <p className="text-sm">Loading…</p>}
          {stats.state === "ready" && (
            <div className="text-sm">
              <p>
                <strong>{stats.data.companies}</strong> companies ·{" "}
                <strong>{stats.data.securities}</strong> securities ·{" "}
                <strong>{stats.data.sectors}</strong> sectors
              </p>
              <p className="mt-2">
                Quality: <QualityBadge status={stats.data.quality_status} />
              </p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                Scope: Main Board / Normal Counter only. GEM and
                non-compliant counters are not captured.
              </p>
            </div>
          )}
        </Card>
        <Card title="Market snapshot">
          {market.state === "loading" && <p className="text-sm">Loading…</p>}
          {market.state === "ready" && (
            <div className="text-sm">
              <p>
                <strong>{market.data.price_rows ?? "—"}</strong> price rows
              </p>
              <p className="mt-1">
                Trading dates: {(market.data.trading_dates ?? []).join(", ") || "none"}
              </p>
              <p className="mt-2">
                Quality: <QualityBadge status={market.data.quality_status} />
              </p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                One trading date only. No advances/declines can be computed
                without previous closes.
              </p>
            </div>
          )}
        </Card>
        <Card title="Macro regime">
          {regimes.state === "loading" && <p className="text-sm">Loading…</p>}
          {regimes.state === "ready" && (
            <div className="text-sm">
              <p>
                Current label:{" "}
                <strong>{regimes.data.regimes?.[0]?.label ?? "not assigned"}</strong>
              </p>
              <p className="mt-1">As of: {regimes.data.regimes?.[0]?.as_of ?? "—"}</p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                One label only; other candidate regimes were explicitly not
                assigned, with reasons in the Macro section.
              </p>
            </div>
          )}
        </Card>
        <Card title="Alerts">
          {alerts.state === "loading" && <p className="text-sm">Loading…</p>}
          {alerts.state === "ready" && (
            <div className="text-sm">
              <p>
                <strong>{alerts.data.total_alerts ?? "—"}</strong> alerts, in-app only
              </p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                Alerts notify about stored events. They are not instructions,
                opportunities, or forecasts, and no external message is sent.
              </p>
            </div>
          )}
        </Card>
        <Card title="Reports">
          {reports.state === "loading" && <p className="text-sm">Loading…</p>}
          {reports.state === "ready" && (
            <div className="text-sm">
              <p>
                <strong>{reports.data.total ?? "—"}</strong> reports, all DRAFT
              </p>
              <p className="mt-1">
                Published externally: {reports.data.published_externally ?? "—"}
              </p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                A draft means internally unreviewed. There is no publish step
                in this product.
              </p>
            </div>
          )}
        </Card>
        <Card title="Coverage limits">
          <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-600 dark:text-neutral-300">
            <li>Statements: 3 of 470 companies (HUBC, NML, OGDC).</li>
            <li>HBL: pending — its annual report PDF could not be downloaded.</li>
            <li>Technical values: 0 calculable from one price date.</li>
            <li>Forecasts: 120 assessments, 0 computed (abstained).</li>
            <li>Decisions: user-facing values all WITHHELD.</li>
            <li>Backtests: all NOT_RUNNABLE on a single observation.</li>
          </ul>
        </Card>
      </div>

      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6 sm:grid-cols-2 lg:grid-cols-3">
        {NAV_ITEMS.filter((item) => item.href !== "/").map((item) => (
          <Link key={item.href} href={item.href} className="block">
            <Card title={item.label}>
              <p className="text-sm text-neutral-600 dark:text-neutral-300">
                {item.description}
              </p>
              <p className="mt-3 text-sm font-medium text-accent-500">Open →</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
