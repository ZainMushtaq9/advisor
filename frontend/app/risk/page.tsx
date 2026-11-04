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
import { fmtNum } from "@/lib/format";

const TICKERS = ["HUBC", "NML", "OGDC"];

interface RiskProfile {
  ticker: string;
  values?: { metric_key: string; value: string | null; computation_status: string; reason: string | null }[];
}

interface MarketRisk {
  values?: { metric_key: string; value: string | null; computation_status: string; reason: string | null }[];
}

interface ControlsResponse {
  controls?: { rule_key: string; threshold: string }[];
  checks?: { rule_key: string; subject: string; outcome: string; detail: string }[];
}

interface StressResponse {
  scenarios?: { scenario_key: string; description: string }[];
  results?: { scenario_key: string; portfolio: string; impact: string | null; computation_status: string }[];
}

/**
 * Risk page: computed values (liquidity tiers, concentration, abstention
 * rates) beside NOT_CALCULABLE series metrics. Controls include one real
 * BREACH on the simulated reference portfolio — the breach is the finding,
 * not a reason to move the threshold. Stress impacts are simulation
 * arithmetic on 2026-11-03 closes only, never forecasts.
 */
export default function RiskPage() {
  const [ticker, setTicker] = useState("HUBC");
  const profile = useApi<RiskProfile>(`/risk/profile?ticker=${ticker}`);
  const market = useApi<MarketRisk>("/risk/market");
  const controls = useApi<ControlsResponse>("/risk/controls");
  const stress = useApi<StressResponse>("/risk/stress");

  return (
    <div className="pb-10">
      <PageHeader
        title="Risk"
        description="Risk metrics, controls, stress results and review-only flags. All eight series metrics per security are NOT_CALCULABLE: volatility, beta, drawdown, VaR/ES need 251 observations and gap risk needs previous closes that do not exist."
        banners={[
          "Flags are review-only — never fraud, default or solvency conclusions. The single-name cap BREACH applies to a SIMULATED equal-weight reference portfolio, never a real holding.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Company risk profile">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <label htmlFor="risk-ticker" className="text-sm font-medium">
              Company:
            </label>
            <select
              id="risk-ticker"
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
          {profile.state === "loading" && <p className="text-sm">Loading…</p>}
          {profile.state === "error" && <StateNotice kind="error" message={profile.error} />}
          {profile.state === "ready" && (
            <DataTable
              caption={`Risk values for ${ticker}`}
              columns={[
                { key: "metric_key", header: "Metric", accessor: "metric_key" },
                { key: "value", header: "Value", render: (r) => fmtNum(r.value) },
                { key: "computation_status", header: "Status", render: (r) => <StatusBadge status={r.computation_status} /> },
                { key: "reason", header: "Reason", render: (r) => r.reason ?? "" },
              ]}
              rows={profile.data.values ?? []}
              emptyTitle="No risk values"
              emptyDescription="No risk values are stored for this company."
            />
          )}
        </Card>
        <Card title="Market risk values">
          {market.state === "loading" && <p className="text-sm">Loading…</p>}
          {market.state === "error" && <StateNotice kind="error" message={market.error} />}
          {market.state === "ready" && (
            <DataTable
              caption="Market risk values"
              columns={[
                { key: "metric_key", header: "Metric", accessor: "metric_key" },
                { key: "value", header: "Value", render: (r) => fmtNum(r.value) },
                { key: "computation_status", header: "Status", render: (r) => <StatusBadge status={r.computation_status} /> },
                { key: "reason", header: "Reason", render: (r) => r.reason ?? "" },
              ]}
              rows={market.data.values ?? []}
              emptyTitle="No market risk values"
              emptyDescription="No market risk values were returned."
            />
          )}
        </Card>
        <Card title="Controls (v1) and checks">
          {controls.state === "loading" && <p className="text-sm">Loading…</p>}
          {controls.state === "error" && <StateNotice kind="error" message={controls.error} />}
          {controls.state === "ready" && (
            <DataTable
              caption="Control checks"
              columns={[
                { key: "rule_key", header: "Rule", accessor: "rule_key" },
                { key: "subject", header: "Subject", accessor: "subject" },
                { key: "outcome", header: "Outcome", accessor: "outcome" },
                { key: "detail", header: "Detail", accessor: "detail" },
              ]}
              rows={controls.data.checks ?? []}
              emptyTitle="No checks"
              emptyDescription="No control checks were returned."
            />
          )}
        </Card>
        <Card title="Stress scenarios (simulation arithmetic only)">
          {stress.state === "loading" && <p className="text-sm">Loading…</p>}
          {stress.state === "error" && <StateNotice kind="error" message={stress.error} />}
          {stress.state === "ready" && (
            <DataTable
              caption="Stress results"
              columns={[
                { key: "scenario_key", header: "Scenario", accessor: "scenario_key" },
                { key: "portfolio", header: "Portfolio", accessor: "portfolio" },
                { key: "impact", header: "Impact", render: (r) => fmtNum(r.impact) },
                { key: "computation_status", header: "Status", render: (r) => <StatusBadge status={r.computation_status} /> },
              ]}
              rows={stress.data.results ?? []}
              emptyTitle="No stress results"
              emptyDescription="No stress results were returned."
            />
          )}
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            Rate, FX and oil scenarios are defined but insufficient_inputs: no
            sensitivity coefficient is stored, so none is computed from an assumed
            coefficient.
          </p>
        </Card>
      </div>
    </div>
  );
}
