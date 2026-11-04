"use client";

import { useEffect, useState } from "react";
import { FoundationShell } from "@/components/foundation-shell";
import { DataTable } from "@/components/data-table";
import { ApiClient } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/env";
import { Badge } from "@/components/ui";

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
}

interface StatisticsResponse {
  companies: number;
  securities: number;
  sectors: number;
}

/**
 * Phase 4 registry page. It renders ONLY rows returned by the backend
 * registry API. While the registry is empty it shows the table's empty
 * state; while the backend is unreachable it says so explicitly.
 * No company, price, or rating is ever fabricated here.
 */
export default function CompaniesPage() {
  const [rows, setRows] = useState<CompanyRow[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [state, setState] = useState<"checking" | "up" | "down">("checking");
  const baseUrl = getApiBaseUrl();

  useEffect(() => {
    let cancelled = false;
    const client = new ApiClient({ baseUrl });
    Promise.all([
      client.get<CompaniesResponse>("/companies?limit=50"),
      client.get<StatisticsResponse>("/registry/statistics"),
    ])
      .then(([companies, statistics]) => {
        if (cancelled) return;
        setRows(companies.items);
        setTotal(companies.total);
        setStats(statistics);
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
      title="Companies"
      description={
        state === "down"
          ? "Registry unavailable: the backend could not be reached. No company data is shown rather than placeholder figures."
          : "Company directory from the Phase 4 registry database. Only records that exist in the registry are listed; an empty table means the registry is empty, not that the market is empty."
      }
      planned={[
        "Per-company analysis pages with inputs, methods, and limitations",
      ]}
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {state === "checking" && <Badge>Checking registry…</Badge>}
        {state === "down" && <Badge>Registry unavailable</Badge>}
        {state === "up" && (
          <Badge tone="info">
            Registry connected — {total ?? 0} companies,{" "}
            {stats?.securities ?? 0} securities, {stats?.sectors ?? 0}{" "}
            sectors
          </Badge>
        )}
      </div>
      <DataTable<CompanyRow>
        caption="Company directory from the registry database"
        columns={[
          { key: "name", header: "Company", accessor: "legal_name" },
          {
            key: "sector",
            header: "Sector (source taxonomy)",
            render: (row) =>
              row.sector_name
                ? `${row.sector_name}${row.sector_source ? ` (${row.sector_source})` : ""}`
                : "Unavailable",
          },
          { key: "status", header: "Status", accessor: "status" },
          {
            key: "securities",
            header: "Securities",
            render: (row) => String(row.securities_count),
          },
        ]}
        rows={rows}
        emptyTitle="No registry records yet"
        emptyDescription="No verified company records are in the registry yet. Nothing is shown rather than placeholder companies, prices, or ratings."
      />
    </FoundationShell>
  );
}
