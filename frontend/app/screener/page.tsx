"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface ScreenRow {
  name: string;
  version: string;
  description: string;
  latest_run?: { as_of_date: string; universe_size: number; matched_count: number };
}

interface ScreensResponse {
  disclaimer?: string;
  screens?: ScreenRow[];
}

interface ResultRow {
  ticker: string;
  outcome: string;
  score: string | null;
  filters?: Record<string, { outcome: string; value: string | null }>;
}

interface ResultsResponse {
  disclaimer?: string;
  screen: string;
  total?: number;
  results?: ResultRow[];
}

/**
 * Screener page: filter results over stored rows. A MATCH means the stored
 * filters passed — it is not an investment opportunity, not a
 * recommendation, and not a forecast. The technical screen matches nothing
 * because zero technical values are calculable.
 */
export default function ScreenerPage() {
  const [screen, setScreen] = useState("liquid_leaders");
  const [offset, setOffset] = useState(0);
  const screens = useApi<ScreensResponse>("/screener/screens");
  const results = useApi<ResultsResponse>(
    `/screener/screens/${screen}/results?limit=50&offset=${offset}&sort=ticker`,
  );

  return (
    <div className="pb-10">
      <PageHeader
        title="Screener"
        description="Filter results over stored rows, with per-filter outcomes and the as-of and price dates on every result. Phase 15 user-facing values ride along as evidence only, never as score inputs; abstained forecasts contribute nothing."
        banners={[
          "Screen matches are filter results, not investment opportunities, not recommendations, and not forecasts.",
        ]}
      />
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <label htmlFor="screen-select" className="text-sm font-medium">
            Screen:
          </label>
          <select
            id="screen-select"
            value={screen}
            onChange={(event) => {
              setScreen(event.target.value);
              setOffset(0);
            }}
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-navy-700 dark:bg-navy-900"
          >
            {(screens.state === "ready" ? screens.data.screens ?? [] : []).map((s) => (
              <option key={s.name} value={s.name}>
                {s.name} — {s.description}
              </option>
            ))}
            {screens.state !== "ready" && (
              <option value="liquid_leaders">liquid_leaders</option>
            )}
          </select>
        </div>

        {screens.state === "ready" && (
          <Card title="Screens">
            <DataTable<ScreenRow>
              caption="Screen definitions"
              columns={[
                { key: "name", header: "Screen", accessor: "name" },
                { key: "description", header: "Description", accessor: "description" },
                { key: "matched", header: "Matched", render: (r) => String(r.latest_run?.matched_count ?? "—") },
                { key: "universe", header: "Universe", render: (r) => String(r.latest_run?.universe_size ?? "—") },
              ]}
              rows={screens.data.screens ?? []}
              emptyTitle="No screens"
              emptyDescription="No screen definitions were returned."
            />
          </Card>
        )}

        <div className="mt-4">
          <Card title={`Results — ${screen}`}>
            {results.state === "loading" && <p className="text-sm">Loading…</p>}
            {results.state === "error" && <StateNotice kind="error" message={results.error} />}
            {results.state === "ready" && (
              <>
                <DataTable<ResultRow>
                  caption={`Screener results for ${screen}`}
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
                    { key: "outcome", header: "Outcome", accessor: "outcome" },
                    { key: "score", header: "Score", render: (r) => r.score ?? "—" },
                  ]}
                  rows={results.data.results ?? []}
                  emptyTitle="No results"
                  emptyDescription="No results were returned for this screen."
                />
                <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
                  <button
                    type="button"
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - 50))}
                    className="rounded-md border border-neutral-300 px-3 py-1 disabled:opacity-50 dark:border-navy-700"
                  >
                    Previous
                  </button>
                  <span>
                    Showing {offset + 1}–{offset + (results.data.results ?? []).length} of{" "}
                    {results.data.total ?? "—"}
                  </span>
                  <button
                    type="button"
                    disabled={
                      results.data.total === undefined ||
                      offset + 50 >= results.data.total
                    }
                    onClick={() => setOffset(offset + 50)}
                    className="rounded-md border border-neutral-300 px-3 py-1 disabled:opacity-50 dark:border-navy-700"
                  >
                    Next
                  </button>
                </div>
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
