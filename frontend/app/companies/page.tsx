"use client";

import { useState } from "react";
import Link from "next/link";
import { DataTable } from "@/components/data-table";
import { Badge } from "@/components/ui";
import { PageHeader, StateNotice, QualityBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { useWatchlist } from "@/lib/watchlist";

interface CompanyRow {
  id: number;
  legal_name: string;
  sector_name: string | null;
  sector_source: string | null;
  status: string;
  securities_count: number;
}

interface CompaniesResponse {
  total: number;
  items: CompanyRow[];
  skip?: number;
  limit?: number;
}

interface StatisticsResponse {
  companies: number;
  securities: number;
  sectors: number;
  quality_status?: string;
}

const PAGE_SIZE = 50;

/**
 * Phase 23 company directory. It renders ONLY rows returned by the backend
 * registry API, with server-side search and pagination. A company with
 * loaded statements (HUBC, NML, OGDC) links to a detail page; every other
 * company links to the same detail page, which states its limits honestly.
 * The watchlist is stored only in this browser (see lib/watchlist.ts).
 */
export default function CompaniesPage() {
  const [search, setSearch] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [offset, setOffset] = useState(0);
  const { tickers: watched, toggle } = useWatchlist();

  const query = submitted ? `&search=${encodeURIComponent(submitted)}` : "";
  const companies = useApi<CompaniesResponse>(
    `/companies?limit=${PAGE_SIZE}&skip=${offset}${query}`,
  );
  const stats = useApi<StatisticsResponse>("/registry/statistics");

  const total = companies.state === "ready" ? companies.data.total : null;

  return (
    <div className="pb-10">
      <PageHeader
        title="Companies"
        description="Company directory from the registry database. Only records that exist in the registry are listed; an empty table means no matching registry record, not that the market is empty. All registry rows are UNVERIFIED."
        banners={[
          "Scope: Main Board / Normal Counter only. GEM and non-compliant counters are not captured.",
        ]}
      />
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        <div className="mb-4 flex flex-wrap gap-2">
          {stats.state === "ready" && (
            <Badge tone="info">
              Registry connected — {stats.data.companies} companies,{" "}
              {stats.data.securities} securities, {stats.data.sectors} sectors{" "}
              <QualityBadge status={stats.data.quality_status} />
            </Badge>
          )}
          {stats.state === "error" && <Badge>Registry statistics unavailable</Badge>}
        </div>

        <form
          className="mb-4 flex flex-wrap gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            setOffset(0);
            setSubmitted(search.trim());
          }}
        >
          <label htmlFor="company-search" className="sr-only">
            Search companies by legal name
          </label>
          <input
            id="company-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by company name (e.g. Hub Power)"
            className="min-w-64 flex-1 rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-navy-700 dark:bg-navy-900"
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

        {companies.state === "loading" && <p className="text-sm">Loading…</p>}
        {companies.state === "error" && (
          <StateNotice kind="error" message={companies.error} />
        )}
        {companies.state === "ready" && (
          <>
            <DataTable<CompanyRow>
              caption="Company directory from the registry database"
              columns={[
                {
                  key: "name",
                  header: "Company",
                  render: (row) => (
                    <Link
                      href={`/companies/${row.id}`}
                      className="font-medium text-accent-600 hover:underline"
                    >
                      {row.legal_name}
                    </Link>
                  ),
                },
                {
                  key: "sector",
                  header: "Sector",
                  render: (row) => row.sector_name ?? "Unavailable",
                },
                { key: "status", header: "Status", accessor: "status" },
                {
                  key: "securities",
                  header: "Securities",
                  render: (row) => String(row.securities_count),
                },
                {
                  key: "watch",
                  header: "Watchlist (this browser only)",
                  render: (row) => (
                    <button
                      type="button"
                      aria-pressed={watched.includes(row.legal_name)}
                      onClick={() => toggle(row.legal_name)}
                      className="rounded-md border border-neutral-300 px-2 py-1 text-xs dark:border-navy-700"
                    >
                      {watched.includes(row.legal_name) ? "Watched ✓" : "Watch"}
                    </button>
                  ),
                },
              ]}
              rows={companies.data.items}
              emptyTitle="No matching registry records"
              emptyDescription="No registry record matches this search. Nothing is shown rather than placeholder companies."
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
                Showing {offset + 1}–{offset + companies.data.items.length} of{" "}
                {total ?? "—"}
              </span>
              <button
                type="button"
                disabled={total === null || offset + PAGE_SIZE >= total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="rounded-md border border-neutral-300 px-3 py-1 disabled:opacity-50 dark:border-navy-700"
              >
                Next
              </button>
            </div>
            <p className="mt-4 text-xs text-neutral-500 dark:text-neutral-400">
              Search matches legal names only (the registry API&apos;s search
              field); for a ticker, use the Securities page or open a
              statement company directly:{" "}
              <Link href="/companies/HUBC" className="underline">HUBC</Link> ·{" "}
              <Link href="/companies/NML" className="underline">NML</Link> ·{" "}
              <Link href="/companies/OGDC" className="underline">OGDC</Link> ·{" "}
              <Link href="/companies/HBL" className="underline">HBL</Link>.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
