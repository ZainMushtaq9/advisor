"use client";

import { useState } from "react";
import Link from "next/link";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, QualityBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface SecurityRow {
  id: number;
  company_id: number;
  company_name: string;
  ticker: string;
  security_type: string;
  status: string;
}

interface SecuritiesResponse {
  total: number;
  items: SecurityRow[];
}

const PAGE_SIZE = 50;

/** Security directory: tickers, classes and registry quality. */
export default function SecuritiesPage() {
  const [search, setSearch] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [offset, setOffset] = useState(0);

  const query = submitted ? `&ticker=${encodeURIComponent(submitted.toUpperCase())}` : "";
  const securities = useApi<SecuritiesResponse>(
    `/securities?limit=${PAGE_SIZE}&skip=${offset}${query}`,
  );

  return (
    <div className="pb-10">
      <PageHeader
        title="Securities"
        description="Security directory from the registry: one row per listed security, with its ticker, class and quality. Bare-name matches for preference/rights classes are ambiguous — only the ticker disambiguates them."
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
          <label htmlFor="security-search" className="sr-only">
            Search securities by ticker
          </label>
          <input
            id="security-search"
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

        {securities.state === "loading" && <p className="text-sm">Loading…</p>}
        {securities.state === "error" && <StateNotice kind="error" message={securities.error} />}
        {securities.state === "ready" && (
          <>
            <DataTable<SecurityRow>
              caption="Security directory"
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
                { key: "company_name", header: "Company", accessor: "company_name" },
                { key: "security_type", header: "Class", accessor: "security_type" },
                { key: "status", header: "Quality", render: (r) => <QualityBadge status={r.status} /> },
              ]}
              rows={securities.data.items}
              emptyTitle="No securities"
              emptyDescription="No registry security matches this search."
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
                Showing {offset + 1}–{offset + securities.data.items.length} of{" "}
                {securities.data.total}
              </span>
              <button
                type="button"
                disabled={offset + PAGE_SIZE >= securities.data.total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="rounded-md border border-neutral-300 px-3 py-1 disabled:opacity-50 dark:border-navy-700"
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
