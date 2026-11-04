"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtNum, fmtPkr } from "@/lib/format";

interface PortfolioRow {
  name: string;
  method: string;
  capital: string;
  price_date: string;
  status: string;
  invested: string;
  cash: string;
  reconciles: boolean;
}

interface PortfoliosResponse {
  portfolios?: PortfolioRow[];
}

interface PortfolioDetail {
  name: string;
  method: string;
  capital: string;
  price_date: string;
  status: string;
  invested: string;
  cash: string;
  holdings?: { ticker: string; units: string; value: string; weight: string }[];
  exclusions?: { ticker: string; reason: string }[];
}

interface ComparisonsResponse {
  comparisons?: { name: string; portfolio_a: string; portfolio_b: string; status: string; detail: string }[];
}

/**
 * Portfolio page: SIMULATED portfolios on hypothetical PKR 1,000,000.
 * Every holding and cash figure reconciles exactly; expected returns,
 * historical returns, forecasts and transaction costs are all null (no
 * validated source) and are shown as not available, never merged into an
 * invented return figure. Mean-variance is NOT_CALCULABLE.
 */
export default function PortfolioPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const portfolios = useApi<PortfoliosResponse>("/portfolios");
  const detail = useApi<PortfolioDetail>(
    selected ? `/portfolios/${selected}` : null,
  );
  const comparisons = useApi<ComparisonsResponse>("/portfolios/comparisons");

  return (
    <div className="pb-10">
      <PageHeader
        title="Portfolio (SIMULATED)"
        description="Three simulated portfolios constructed from 2026-11-03 closes on hypothetical capital of PKR 1,000,000, in whole shares. These are not real holdings, not accounts, and not advice. No broker, order or execution path exists anywhere in this product."
        banners={[
          "SIMULATION: every figure below is hypothetical. The rule-based portfolios are MORE concentrated than the equal-weight baseline (2 names at ~50% vs 3 names at ~33%) — screening narrowed the set and raised concentration.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Simulated portfolios">
          {portfolios.state === "loading" && <p className="text-sm">Loading…</p>}
          {portfolios.state === "error" && <StateNotice kind="error" message={portfolios.error} />}
          {portfolios.state === "ready" && (
            <DataTable<PortfolioRow>
              caption="Simulated portfolios"
              columns={[
                {
                  key: "name",
                  header: "Portfolio",
                  render: (r) => (
                    <button
                      type="button"
                      onClick={() => setSelected(r.name)}
                      className="font-medium text-accent-600 hover:underline"
                    >
                      {r.name}
                    </button>
                  ),
                },
                { key: "method", header: "Method", accessor: "method" },
                { key: "invested", header: "Invested", render: (r) => fmtPkr(r.invested) },
                { key: "cash", header: "Cash", render: (r) => fmtPkr(r.cash) },
                { key: "status", header: "Status", accessor: "status" },
                { key: "reconciles", header: "Reconciles", render: (r) => (r.reconciles ? "yes" : "no") },
              ]}
              rows={portfolios.data.portfolios ?? []}
              emptyTitle="No portfolios"
              emptyDescription="No simulated portfolios were returned."
            />
          )}
        </Card>

        {selected && (
          <Card title={`Holdings — ${selected} (SIMULATED)`}>
            {detail.state === "loading" && <p className="text-sm">Loading…</p>}
            {detail.state === "error" && <StateNotice kind="error" message={detail.error} />}
            {detail.state === "ready" && (
              <>
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  Method: {detail.data.method} · Price date: {detail.data.price_date} ·
                  Invested: {fmtPkr(detail.data.invested)} · Cash: {fmtPkr(detail.data.cash)}
                </p>
                <DataTable
                  caption={`Holdings for ${selected}`}
                  columns={[
                    { key: "ticker", header: "Ticker", accessor: "ticker" },
                    { key: "units", header: "Units", accessor: "units" },
                    { key: "value", header: "Value (PKR)", render: (r) => fmtNum(r.value) },
                    { key: "weight", header: "Weight", accessor: "weight" },
                  ]}
                  rows={detail.data.holdings ?? []}
                  emptyTitle="No holdings"
                  emptyDescription="No holdings were returned for this portfolio."
                />
                {(detail.data.exclusions ?? []).length > 0 && (
                  <p className="mt-3 text-sm">
                    Excluded:{" "}
                    {(detail.data.exclusions ?? [])
                      .map((e) => `${e.ticker} (${e.reason})`)
                      .join("; ")}
                  </p>
                )}
              </>
            )}
          </Card>
        )}

        <Card title="Comparisons">
          {comparisons.state === "loading" && <p className="text-sm">Loading…</p>}
          {comparisons.state === "error" && <StateNotice kind="error" message={comparisons.error} />}
          {comparisons.state === "ready" && (
            <DataTable
              caption="Portfolio comparisons"
              columns={[
                { key: "name", header: "Comparison", accessor: "name" },
                { key: "status", header: "Status", accessor: "status" },
                { key: "detail", header: "Detail", accessor: "detail" },
              ]}
              rows={comparisons.data.comparisons ?? []}
              emptyTitle="No comparisons"
              emptyDescription="No comparisons were returned."
            />
          )}
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            Mean-variance is NOT_CALCULABLE: no validated expected returns (0
            forecasts computed) and no covariance matrix (0 return observations).
          </p>
        </Card>
      </div>
    </div>
  );
}
