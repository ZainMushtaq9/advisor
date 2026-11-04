"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtDate } from "@/lib/format";

interface AlertRow {
  id: number;
  rule_key: string;
  ticker: string | null;
  event_time: string | null;
  as_of_date: string;
  severity: string;
  title: string;
  lifecycle_state?: string;
}

interface AlertsResponse {
  disclaimer?: string;
  total: number;
  alerts: AlertRow[];
}

interface RulesResponse {
  rules?: { rule_key: string; description: string; severity_default: string }[];
}

const PAGE_SIZE = 50;

/**
 * Alerts page: in-app notifications only. Lifecycle changes (acknowledge,
 * mute, resolve) exist in the Phase 21 CLI, not in this GET-only web API,
 * so this page offers no action buttons — only the stored state and the
 * disclaimer. No external channel is ever used.
 */
export default function AlertsPage() {
  const [offset, setOffset] = useState(0);
  const alerts = useApi<AlertsResponse>(`/alerts?limit=${PAGE_SIZE}&offset=${offset}`);
  const rules = useApi<RulesResponse>("/alerts/rules");

  return (
    <div className="pb-10">
      <PageHeader
        title="Alerts"
        description="Notifications about stored events, delivered in-app only. Alerts are not instructions, not opportunities and not forecasts. External channels (email, SMS, push) are recorded disabled with consent False and are refused without sending."
        banners={[
          "False-positive rate is NOT_MEASURABLE: all alerts are NEW with no user-feedback labels yet. Volume, duplicates and suppression reasons are reported instead.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Alerts">
          {alerts.state === "loading" && <p className="text-sm">Loading…</p>}
          {alerts.state === "error" && <StateNotice kind="error" message={alerts.error} />}
          {alerts.state === "ready" && (
            <>
              {alerts.data.disclaimer && (
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  {alerts.data.disclaimer}
                </p>
              )}
              <DataTable<AlertRow>
                caption="Alerts"
                columns={[
                  { key: "as_of_date", header: "As of", render: (r) => fmtDate(r.as_of_date) },
                  { key: "severity", header: "Severity", accessor: "severity" },
                  { key: "rule_key", header: "Rule", accessor: "rule_key" },
                  { key: "ticker", header: "Ticker", render: (r) => r.ticker ?? "—" },
                  { key: "title", header: "Title", accessor: "title" },
                  { key: "lifecycle_state", header: "State", render: (r) => r.lifecycle_state ?? "NEW" },
                ]}
                rows={alerts.data.alerts}
                emptyTitle="No alerts"
                emptyDescription="No alerts were returned."
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
                  Showing {offset + 1}–{offset + alerts.data.alerts.length} of{" "}
                  {alerts.data.total}
                </span>
                <button
                  type="button"
                  disabled={offset + PAGE_SIZE >= alerts.data.total}
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  className="rounded-md border border-neutral-300 px-3 py-1 disabled:opacity-50 dark:border-navy-700"
                >
                  Next
                </button>
              </div>
            </>
          )}
        </Card>
        <Card title="Alert rules">
          {rules.state === "loading" && <p className="text-sm">Loading…</p>}
          {rules.state === "error" && <StateNotice kind="error" message={rules.error} />}
          {rules.state === "ready" && (
            <DataTable
              caption="Alert rules"
              columns={[
                { key: "rule_key", header: "Rule", accessor: "rule_key" },
                { key: "description", header: "Description", accessor: "description" },
                { key: "severity_default", header: "Default severity", accessor: "severity_default" },
              ]}
              rows={rules.data.rules ?? []}
              emptyTitle="No rules"
              emptyDescription="No alert rules were returned."
            />
          )}
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            Suppressed with reasons (never silently dropped): 2 FUTURE_SCHEDULED,
            1 STALE, 1 UNKNOWN_DATE, 5 NO_EVENT_DATE, 3 NO_SERIES.
          </p>
        </Card>
      </div>
    </div>
  );
}
