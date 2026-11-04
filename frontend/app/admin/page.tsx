"use client";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import type { ApiHealth } from "@/lib/types";

interface EndpointStatus {
  endpoint: string;
  status: string;
  detail?: string;
}

/**
 * Admin page: backend health and per-area status counts. Read-only and
 * GET-only: no credentials, secrets, connection strings or internal paths
 * are ever displayed, and no action is offered from this page.
 */
export default function AdminPage() {
  const health = useApi<ApiHealth>("/health");
  const statuses = useApi<Record<string, unknown>>("/reports/status");

  const rows: EndpointStatus[] = [
    { endpoint: "Backend /health", status: health.state === "ready" ? "ok" : health.state },
    { endpoint: "Registry", status: "see Companies" },
    { endpoint: "Market", status: "see Market" },
    { endpoint: "Fundamentals / Valuation", status: "see Fundamentals, Valuation" },
    { endpoint: "Macro", status: "see Macro" },
    { endpoint: "Forecasting", status: "see Forecasts" },
    { endpoint: "Risk / Decisions", status: "see Risk, Research" },
    { endpoint: "Portfolio / Backtesting", status: "see Portfolio, Research" },
    { endpoint: "Screener / Alerts / Reports", status: "see Screener, Alerts, Reports" },
  ];

  return (
    <div className="pb-10">
      <PageHeader
        title="Admin"
        description="Backend health and product status. This page performs no writes, shows no credentials, and offers no publish, promote, send or execute action — those do not exist in the web UI by design."
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Backend health">
          {health.state === "loading" && <p className="text-sm">Loading…</p>}
          {health.state === "error" && <StateNotice kind="error" message={health.error} />}
          {health.state === "ready" && (
            <p className="text-sm">
              Status: <strong>{health.data.status}</strong> · Service:{" "}
              {health.data.service}
            </p>
          )}
          {health.state === "error" && (
            <p className="text-sm">
              The backend is unreachable. Check that the API server is running
              on the configured base URL; no data is shown until it responds.
            </p>
          )}
        </Card>
        <Card title="Areas">
          <DataTable<EndpointStatus>
            caption="Product areas"
            columns={[
              { key: "endpoint", header: "Area", accessor: "endpoint" },
              { key: "status", header: "Status", accessor: "status" },
            ]}
            rows={rows}
            emptyTitle="No areas"
            emptyDescription="No area rows are available."
          />
        </Card>
        <Card title="Reports status (live)">
          {statuses.state === "loading" && <p className="text-sm">Loading…</p>}
          {statuses.state === "error" && <StateNotice kind="error" message={statuses.error} />}
          {statuses.state === "ready" && (
            <p className="text-sm">
              Total reports: {String(statuses.data.total ?? "—")} · DRAFT:{" "}
              {String(
                (statuses.data.by_status as Record<string, number> | undefined)?.DRAFT ??
                  "—",
              )}{" "}
              · Published externally: {String(statuses.data.published_externally ?? "—")}
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
