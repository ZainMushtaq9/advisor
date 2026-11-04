"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, QualityBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtNum } from "@/lib/format";

interface PriceRow {
  ticker: string;
  trading_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  turnover: number | null;
  previous_close: number | null;
  is_adjusted: boolean;
  quality_status: string;
  freshness: string;
  source_key: string;
}

interface PricesResponse {
  total: number;
  items: PriceRow[];
}

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

const PAGE_SIZE = 50;

/**
 * Market page: the single-date OHLCV snapshot plus breadth. No chart is
 * drawn — one observation per security is not a series, and drawing one
 * would imply price movement that is not in the data.
 */
export default function MarketPage() {
  const [search, setSearch] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [offset, setOffset] = useState(0);

  const query = submitted ? `&ticker=${encodeURIComponent(submitted.toUpperCase())}` : "";
  const prices = useApi<PricesResponse>(
    `/market/prices?limit=${PAGE_SIZE}&skip=${offset}${query}`,
  );
  const breadth = useApi<BreadthResponse>("/breadth");

  const marketMetrics = (breadth.state === "ready" ? breadth.data.metrics ?? [] : []).filter(
    (m) => m.scope === "MARKET",
  );

  return (
    <div className="pb-10">
      <PageHeader
        title="Market"
        description="Daily OHLCV snapshot for 2026-11-03 only — 444 of 470 snapshot securities have a price row. All rows are UNVERIFIED and unadjusted; previous close and turnover are NULL on every row, so no move, advance/decline or turnover figure can be computed."
        banners={[
          "26 tickers have no 2026-11-03 price (13 rejected on validation, 13 absent from the source file). They are never shown as zero.",
        ]}
      />
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        <form
          className="mb-4 flex flex-wrap gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            setOffset(0);
            setSubmitted(search.trim());
          }}
        >
          <label htmlFor="price-search" className="sr-only">
            Search prices by ticker
          </label>
          <input
            id="price-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Ticker (e.g. HUBC)"
            className="min-w-48 flex-1 rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-navy-700 dark:bg-navy-900"
          />
          <button
            type="submit"
            className="rounded-md bg-navy-900 px-4 py-2 text-sm font-medium text-white dark:bg-accent-500 dark:text-navy-950"
          >
            Search
          </button>
          {submitted && (
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setSubmitted("");
                setOffset(0);
              }}
              className="rounded-md border border-neutral-300 px-4 py-2 text-sm dark:border-navy-700"
            >
              Clear
            </button>
          )}
        </form>

        {prices.state === "loading" && <p className="text-sm">Loading…</p>}
        {prices.state === "error" && <StateNotice kind="error" message={prices.error} />}
        {prices.state === "ready" && (
          <>
            <DataTable<PriceRow>
              caption="Daily prices for 2026-11-03"
              columns={[
                {
                  key: "ticker",
                  header: "Ticker",
                  render: (r) => (
                    <Link href={`/companies/${r.ticker}`} className="font-medium text-accent-600 hover:underline">
                      {r.ticker}
                    </Link>
                  ),
                },
                { key: "close", header: "Close (PKR)", render: (r) => fmtNum(r.close) },
                { key: "open", header: "Open", render: (r) => fmtNum(r.open) },
                { key: "high", header: "High", render: (r) => fmtNum(r.high) },
                { key: "low", header: "Low", render: (r) => fmtNum(r.low) },
                { key: "volume", header: "Volume", render: (r) => fmtNum(r.volume) },
                { key: "quality", header: "Quality", render: (r) => <QualityBadge status={r.quality_status} /> },
                { key: "source", header: "Source", accessor: "source_key" },
              ]}
              rows={prices.data.items}
              emptyTitle="No price rows"
              emptyDescription="No stored price row matches this search. A missing row means no observation, never a zero price."
            />
            <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                className="rounded-md border border-neutral-300 px-3 py-1 disabled:opacity-50 dark:border-navy-700"
              >
                Previous
              </button>
              <span>
                Showing {offset + 1}–{offset + prices.data.items.length} of {prices.data.total}
              </span>
              <button
                type="button"
                disabled={offset + PAGE_SIZE >= prices.data.total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="rounded-md border border-neutral-300 px-3 py-1 disabled:opacity-50 dark:border-navy-700"
              >
                Next
              </button>
            </div>
          </>
        )}

        <div className="mt-8">
          <Card title="Market breadth — 2026-11-03">
            {breadth.state === "loading" && <p className="text-sm">Loading…</p>}
            {breadth.state === "error" && <StateNotice kind="error" message={breadth.error} />}
            {breadth.state === "ready" && (
              <DataTable
                caption="Market breadth metrics"
                columns={[
                  { key: "metric_key", header: "Metric", accessor: "metric_key" },
                  { key: "metric_value", header: "Value", render: (r) => fmtNum(r.metric_value) },
                  { key: "status", header: "Status", accessor: "status" },
                  { key: "coverage_note", header: "Note", render: (r) => r.coverage_note ?? "" },
                ]}
                rows={marketMetrics}
                emptyTitle="No breadth metrics"
                emptyDescription="No breadth metrics were returned."
              />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
