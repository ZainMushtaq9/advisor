"use client";

import { useEffect, useRef } from "react";
import { EmptyState } from "./ui";

/**
 * A single generic line point. This type is deliberately market-neutral:
 * callers in later phases map verified series onto it. It carries no
 * PSX symbol, price, or index value by itself.
 */
export interface ChartPoint {
  /** ISO date string, e.g. "2026-01-05". */
  time: string;
  value: number;
}

interface ChartContainerProps {
  title: string;
  /** Null/empty means "no verified series yet" — an empty state renders. */
  series: ChartPoint[] | null;
  height?: number;
}

/**
 * TradingView Lightweight Charts renderer only (Apache-2.0, Phase 1 stack).
 * It supplies no market data and fetches nothing. The TradingView
 * attribution logo is left enabled, as the Phase 1 licence duty requires.
 * Candlestick/bar/volume series are a later-phase addition on this same
 * container; Phase 2 renders the empty state only.
 */
export function ChartContainer({
  title,
  series,
  height = 320,
}: ChartContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!series || series.length === 0 || !containerRef.current) return;
    let chart: ReturnType<
      typeof import("lightweight-charts").createChart
    > | null = null;
    let cancelled = false;

    import("lightweight-charts").then(({ createChart, LineSeries }) => {
      if (cancelled || !containerRef.current) return;
      const element = containerRef.current;
      chart = createChart(element, {
        width: element.clientWidth || 600,
        height,
        layout: { background: { color: "transparent" }, textColor: "#94a3b8" },
        grid: {
          vertLines: { color: "rgba(148, 163, 184, 0.15)" },
          horzLines: { color: "rgba(148, 163, 184, 0.15)" },
        },
        // attributionLogo intentionally NOT disabled (licence duty).
      });
      const line = chart.addSeries(LineSeries, { color: "#38bdf8" });
      line.setData(series);
      chart.timeScale().fitContent();
      const observer = new ResizeObserver(() => {
        chart?.applyOptions({ width: element.clientWidth || 600 });
      });
      observer.observe(element);
      // Keep the observer alive for the chart lifetime.
      (chart as unknown as { __observer?: ResizeObserver }).__observer =
        observer;
    });

    return () => {
      cancelled = true;
      if (chart) {
        const observer = (chart as unknown as { __observer?: ResizeObserver })
          .__observer;
        observer?.disconnect();
        chart.remove();
      }
    };
  }, [series, height]);

  return (
    <section
      aria-label={title}
      className="rounded-lg border border-neutral-200 bg-white p-5 dark:border-navy-700 dark:bg-navy-900"
    >
      <h2 className="mb-3 text-base font-semibold text-navy-900 dark:text-white">
        {title}
      </h2>
      {!series || series.length === 0 ? (
        <EmptyState
          title="No chart data yet"
          description="This chart container is ready, but no verified series has been connected. No placeholder line is drawn."
        />
      ) : (
        <>
          <div ref={containerRef} style={{ height }} className="w-full" />
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            Chart rendered with TradingView Lightweight Charts —{" "}
            <a
              href="https://www.tradingview.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline"
            >
              tradingview.com
            </a>
            . The chart is a renderer only; it supplies no market data.
          </p>
        </>
      )}
    </section>
  );
}
