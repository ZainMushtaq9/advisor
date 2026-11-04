"use client";

import { useEffect, useState } from "react";
import { FoundationShell } from "@/components/foundation-shell";
import { DataTable } from "@/components/data-table";
import { ApiClient, ApiError } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/env";
import { Badge } from "@/components/ui";

interface IndicatorSummary {
  category: string;
  warmup_bars: number;
  calculable: number;
  not_calculable: number;
  reasons: Record<string, number>;
}

interface CoverageResponse {
  as_of: string | null;
  securities_assessed: number;
  indicators_registered: number;
  securities_with_any_calculable: number;
  per_indicator: Record<string, IndicatorSummary>;
  scope_note: string;
}

interface Verdict {
  indicator_key: string;
  category: string;
  status: string;
  value: string | null;
  reason: string | null;
  detail: string | null;
  warmup_bars: number;
}

interface TickerCoverage {
  ticker: string;
  bars_available: number;
  first_date: string | null;
  last_date: string | null;
  calculable_count: number;
  not_calculable_count: number;
  verdicts: Verdict[];
}

interface TotalsResponse {
  total: number;
  scope_note?: string;
  note?: string;
}

/**
 * Phase 6 indicators page. It renders ONLY coverage verdicts and
 * stored rows returned by the backend indicators API. With one
 * trading day of data, every indicator is NOT_CALCULABLE and the
 * page says so plainly, with the reason and the warm-up required —
 * it never charts a single point as a trend and never invents a
 * value. Signal events are observations only, never buy/sell
 * recommendations.
 */
export default function IndicatorsPage() {
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const [state, setState] = useState<"checking" | "up" | "down">("checking");
  const [ticker, setTicker] = useState("OGDC");
  const [tickerCoverage, setTickerCoverage] = useState<TickerCoverage | null>(null);
  const [tickerState, setTickerState] = useState<
    "idle" | "loading" | "done" | "unknown" | "unavailable"
  >("idle");
  const [valuesTotal, setValuesTotal] = useState<number | null>(null);
  const [signalsTotal, setSignalsTotal] = useState<number | null>(null);
  const [signalsNote, setSignalsNote] = useState<string | null>(null);
  const baseUrl = getApiBaseUrl();

  useEffect(() => {
    let cancelled = false;
    const client = new ApiClient({ baseUrl });
    client
      .get<CoverageResponse>("/indicators/coverage")
      .then((data) => {
        if (!cancelled) {
          setCoverage(data);
          setState("up");
        }
      })
      .catch(() => {
        if (!cancelled) setState("down");
      });
    // Stored totals come from the API, never from static text:
    // the day a value or event exists, this page must say so.
    client
      .get<TotalsResponse>("/indicators/values?limit=1")
      .then((data) => {
        if (!cancelled) setValuesTotal(data.total);
      })
      .catch(() => {});
    client
      .get<TotalsResponse>("/indicators/signals?limit=1")
      .then((data) => {
        if (!cancelled) {
          setSignalsTotal(data.total);
          setSignalsNote(data.note ?? null);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [baseUrl]);

  const checkTicker = () => {
    const symbol = ticker.trim().toUpperCase();
    if (!symbol) return;
    setTickerState("loading");
    const client = new ApiClient({ baseUrl });
    client
      .get<TickerCoverage>(`/indicators/coverage/${symbol}`)
      .then((data) => {
        setTickerCoverage(data);
        setTickerState("done");
      })
      .catch((error: unknown) => {
        setTickerCoverage(null);
        setTickerState(
          error instanceof ApiError && error.status === 404
            ? "unknown"
            : "unavailable"
        );
      });
  };

  const summaryRows = coverage
    ? Object.entries(coverage.per_indicator).map(([key, value]) => ({
        indicator: key,
        category: value.category,
        warmup_bars: value.warmup_bars,
        calculable: value.calculable,
        not_calculable: value.not_calculable,
        reasons: Object.entries(value.reasons)
          .map(([reason, count]) => `${reason} (${count})`)
          .join(", "),
      }))
    : [];

  return (
    <FoundationShell
      title="Technical indicators"
      description={
        state === "down"
          ? "Indicator data unavailable: the backend could not be reached. No indicator values are shown rather than placeholder figures."
          : "Deterministic indicator coverage for the Phase 6 framework. Every value is computed by versioned Python formulas from stored daily prices only; with one trading day of data, every indicator is NOT_CALCULABLE, and each row states why and what would unblock it. Scope: 470 Main Board / Normal Counter snapshot securities; all prices UNVERIFIED single-source."
      }
      planned={[
        "Indicator values and charts once enough trading days accumulate",
        "Signal events once a rule is activated on calculable inputs",
      ]}
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {state === "checking" && <Badge>Checking indicator data…</Badge>}
        {state === "down" && <Badge>Indicator data unavailable</Badge>}
        {state === "up" && coverage && (
          <Badge tone="info">
            {coverage.securities_assessed} securities assessed,{" "}
            {coverage.indicators_registered} indicators registered,{" "}
            {coverage.securities_with_any_calculable} with any calculable
            indicator
          </Badge>
        )}
      </div>
      <DataTable
        caption="Indicator coverage across all assessed securities"
        columns={[
          { key: "indicator", header: "Indicator", accessor: "indicator" },
          { key: "category", header: "Category", accessor: "category" },
          { key: "warmup", header: "Warm-up bars", accessor: "warmup_bars" },
          { key: "calc", header: "Calculable", accessor: "calculable" },
          { key: "notcalc", header: "Not calculable", accessor: "not_calculable" },
          { key: "reasons", header: "Reasons", accessor: "reasons" },
        ]}
        rows={summaryRows}
        emptyTitle="No coverage data yet"
        emptyDescription="No indicator coverage could be loaded. Nothing is shown rather than placeholder figures."
      />
      <div className="mt-8 mb-4 flex flex-wrap items-center gap-2">
        <input
          value={ticker}
          onChange={(event) => setTicker(event.target.value)}
          placeholder="Ticker, e.g. OGDC"
          className="rounded border px-3 py-2"
          aria-label="Ticker"
        />
        <button
          type="button"
          onClick={checkTicker}
          className="rounded bg-neutral-900 px-4 py-2 text-white dark:bg-neutral-100 dark:text-neutral-900"
        >
          Check ticker
        </button>
        {tickerState === "loading" && <Badge>Checking…</Badge>}
        {tickerState === "unknown" && <Badge>Unknown ticker</Badge>}
        {tickerState === "unavailable" && <Badge>Backend unavailable</Badge>}
      </div>
      {tickerState === "done" && tickerCoverage && (
        <>
          <p className="mb-4 text-sm text-neutral-600 dark:text-neutral-300">
            {tickerCoverage.ticker}: {tickerCoverage.bars_available} bars
            available
            {tickerCoverage.first_date && tickerCoverage.last_date
              ? ` (${tickerCoverage.first_date} to ${tickerCoverage.last_date})`
              : ""}
            , {tickerCoverage.calculable_count} calculable,{" "}
            {tickerCoverage.not_calculable_count} not calculable.
          </p>
          <DataTable<Verdict>
            caption={`Indicator verdicts for ${tickerCoverage.ticker}`}
            columns={[
              { key: "indicator", header: "Indicator", accessor: "indicator_key" },
              { key: "category", header: "Category", accessor: "category" },
              { key: "status", header: "Status", accessor: "status" },
              { key: "reason", header: "Reason", accessor: "reason" },
              { key: "detail", header: "Detail", accessor: "detail" },
              { key: "warmup", header: "Warm-up bars", accessor: "warmup_bars" },
            ]}
            rows={tickerCoverage.verdicts}
            emptyTitle="No verdicts"
            emptyDescription="No indicator verdicts were returned for this ticker."
          />
        </>
      )}
      <p className="mt-4 text-sm text-neutral-600 dark:text-neutral-300">
        Stored indicator values:{" "}
        {valuesTotal === null ? "unknown (backend unreachable)" : valuesTotal}
        . Stored signal events:{" "}
        {signalsTotal === null ? "unknown (backend unreachable)" : signalsTotal}
        . {signalsNote ?? ""}
      </p>
      {coverage?.scope_note && (
        <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-300">
          {coverage.scope_note}
        </p>
      )}
    </FoundationShell>
  );
}
