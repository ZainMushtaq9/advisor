"use client";

import { useEffect, useState } from "react";
import { FoundationShell } from "@/components/foundation-shell";
import { DataTable } from "@/components/data-table";
import { ApiClient } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/env";
import { Badge } from "@/components/ui";

interface PriceRow {
  ticker: string;
  trading_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  quality_status: string;
  source_key: string | null;
}

interface PricesResponse {
  total: number;
  items: PriceRow[];
}

interface StatusResponse {
  market_prices_total: number;
  securities_with_observations: number;
  earliest_trading_date: string | null;
  latest_trading_date: string | null;
  scope_note: string;
}

/**
 * Phase 5 market page. It renders ONLY rows returned by the backend
 * market API. While market_prices is empty it shows the table's empty
 * state with the scope note; while the backend is unreachable it says
 * so explicitly. No price is ever fabricated here.
 */
export default function MarketPage() {
  const [rows, setRows] = useState<PriceRow[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [stats, setStats] = useState<StatusResponse | null>(null);
  const [state, setState] = useState<"checking" | "up" | "down">("checking");
  const baseUrl = getApiBaseUrl();

  useEffect(() => {
    let cancelled = false;
    const client = new ApiClient({ baseUrl });
    Promise.all([
      client.get<PricesResponse>("/market/prices?limit=50"),
      client.get<StatusResponse>("/market/status"),
    ])
      .then(([prices, status]) => {
        if (cancelled) return;
        setRows(prices.items);
        setTotal(prices.total);
        setStats(status);
        setState("up");
      })
      .catch(() => {
        if (!cancelled) setState("down");
      });
    return () => {
      cancelled = true;
    };
  }, [baseUrl]);

  return (
    <FoundationShell
      title="Market prices"
      description={
        state === "down"
          ? "Market data unavailable: the backend could not be reached. No price data is shown rather than placeholder figures."
          : "Daily OHLCV observations from the Phase 5 market database. Only rows that exist in the database are listed; an empty table means no price observations have been ingested yet, not that the market is empty. Scope: 470 Main Board / Normal Counter snapshot securities."
      }
      planned={[
        "Per-security price history and charts from verified observations",
      ]}
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {state === "checking" && <Badge>Checking market data…</Badge>}
        {state === "down" && <Badge>Market data unavailable</Badge>}
        {state === "up" && (
          <Badge tone="info">
            Market connected — {stats?.market_prices_total ?? 0} observations,{" "}
            {stats?.securities_with_observations ?? 0} securities with
            observations
            {stats?.earliest_trading_date && stats?.latest_trading_date
              ? `, ${stats.earliest_trading_date} to ${stats.latest_trading_date}`
              : ""}
          </Badge>
        )}
      </div>
      <DataTable<PriceRow>
        caption="Daily OHLCV observations from the market database"
        columns={[
          { key: "ticker", header: "Ticker", accessor: "ticker" },
          { key: "date", header: "Trading date", accessor: "trading_date" },
          { key: "open", header: "Open", accessor: "open" },
          { key: "high", header: "High", accessor: "high" },
          { key: "low", header: "Low", accessor: "low" },
          { key: "close", header: "Close", accessor: "close" },
          { key: "volume", header: "Volume", accessor: "volume" },
          { key: "quality", header: "Quality", accessor: "quality_status" },
          { key: "source", header: "Source", accessor: "source_key" },
        ]}
        rows={rows}
        emptyTitle="No price observations yet"
        emptyDescription="No daily OHLCV observations are in the market database yet. Nothing is shown rather than placeholder prices. All stored prices are official unadjusted values."
      />
      {state === "up" && total !== null && total > rows.length && (
        <p className="mt-4 text-sm text-neutral-600 dark:text-neutral-300">
          Showing {rows.length} of {total} observations (newest first).
        </p>
      )}
    </FoundationShell>
  );
}
