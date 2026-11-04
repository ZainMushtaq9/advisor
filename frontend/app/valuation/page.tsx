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
import { fmtNum, fmtPkr, fmtDate } from "@/lib/format";

const TICKERS = ["HUBC", "NML", "OGDC", "HBL"];

interface ValuationsResponse {
  ticker: string;
  status: string;
  reason?: string;
  price_date?: string;
  price?: string;
  bs_date?: string;
  publication_date?: string | null;
  methods?: { method_key: string; status: string; value: string | null; reason: string | null }[];
}

/**
 * Valuation page: seventeen methods per company. Only trailing P/E (where
 * EPS is positive and publication is known and on/before the price date)
 * and statement-date book values compute; share-count methods cannot
 * compute without a par value, and DCF/DDM cannot compute without
 * source-backed assumptions — those stay insufficient, never estimated.
 */
export default function ValuationPage() {
  const [ticker, setTicker] = useState("HUBC");
  const valuations = useApi<ValuationsResponse>(`/valuations?ticker=${ticker}`);

  return (
    <div className="pb-10">
      <PageHeader
        title="Valuation"
        description="Seventeen valuation methods assessed per company. Outputs are descriptive estimates with stated assumptions — not price targets, not investment advice, not buy/sell signals. No averaging of incompatible models is performed."
        banners={[
          "Book values are statement-date, company-level values — not market fair values and not per-share values.",
        ]}
      />
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <label htmlFor="val-ticker" className="text-sm font-medium">
            Company:
          </label>
          <select
            id="val-ticker"
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

        {valuations.state === "loading" && <p className="text-sm">Loading…</p>}
        {valuations.state === "error" && <StateNotice kind="error" message={valuations.error} />}
        {valuations.state === "ready" &&
          (valuations.data.methods && valuations.data.methods.length > 0 ? (
            <Card title={`Valuation — ${ticker}`}>
              <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                Price date: {fmtDate(valuations.data.price_date)} · Price:{" "}
                {fmtPkr(valuations.data.price)} · Balance-sheet date:{" "}
                {fmtDate(valuations.data.bs_date)} · Publication date:{" "}
                {fmtDate(valuations.data.publication_date)}
              </p>
              <SourceLine unit="PKR; multiples unitless" quality="UNVERIFIED" />
              <div className="mt-3">
                <DataTable
                  caption={`Valuation methods for ${ticker}`}
                  columns={[
                    { key: "method_key", header: "Method", accessor: "method_key" },
                    { key: "value", header: "Value", render: (r) => fmtNum(r.value) },
                    { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
                    { key: "reason", header: "Reason", render: (r) => r.reason ?? "" },
                  ]}
                  rows={valuations.data.methods}
                  emptyTitle="No methods"
                  emptyDescription="No valuation rows were returned."
                />
              </div>
            </Card>
          ) : (
            <StateNotice
              kind="empty"
              message={`Status: ${valuations.data.status}. ${valuations.data.reason ?? "No configured company-period with statements."}`}
            />
          ))}
      </div>
    </div>
  );
}
