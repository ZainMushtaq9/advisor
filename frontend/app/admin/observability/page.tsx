"use client";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, StatusBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface ObservabilitySummary {
  latest_run_id: string | null;
  latest_run_status: string | null;
  slos_total: number;
  slos_met: number;
  slos_unmet: number;
  slos_not_evaluable: number;
  sources_total: number;
  sources_stale: string[];
  sources_unknown: string[];
  exceptions_open: number;
  incidents_open: number;
  performance_probes: number;
}

interface Readiness {
  database: { status: string; reachable: boolean };
  migration_head: string | null;
  migration_expected: string;
  migration_matches: boolean;
  latest_observability_run: string | null;
  auth_enforcement: string;
  ready: boolean;
}

interface SloRow {
  slo_key: string;
  category: string;
  metric_key: string;
  target_value: number;
  comparison: string;
  unit: string;
  rationale: string;
  latest_value: number | null;
  latest_status: string | null;
  latest_reason: string | null;
}

interface HealthRow {
  source_key: string;
  category: string;
  latest_observation_date: string | null;
  coverage_numerator: number | null;
  coverage_denominator: number | null;
  freshness_days: number | null;
  status: string;
  notes: string;
}

interface ExceptionRow {
  run_id: string;
  exception_key: string;
  severity: string;
  title: string;
  status: string;
  resolution_note: string | null;
}

interface IncidentRow {
  incident_key: string;
  severity: string;
  title: string;
  runbook_ref: string;
  status: string;
  resolution_note: string | null;
}

interface ProbeRow {
  probe_key: string;
  metric_key: string;
  value: number | null;
  unit: string;
  notes: string;
}

/**
 * Observability dashboard (Phase 27). Read-only and GET-only:
 * observability runs execute through the CLI, never from this page.
 * Unmet SLOs are shown as findings, never hidden or averaged away;
 * a NOT_EVALUABLE value is shown without a number, never zero-filled.
 * Stale sources, open exceptions, and resolved incidents are all
 * shown with their reasons. Nothing here is a promotion, a
 * publication, a send, or a trade — none of those capabilities
 * exist in this project.
 */
export default function ObservabilityPage() {
  const summary = useApi<ObservabilitySummary>("/observability/summary");
  const readiness = useApi<Readiness>("/observability/readiness");
  const slos = useApi<{ run_id: string | null; items: SloRow[] }>(
    "/observability/slos",
  );
  const health = useApi<{ run_id: string | null; items: HealthRow[] }>(
    "/observability/source-health",
  );
  const exceptions = useApi<{ items: ExceptionRow[] }>(
    "/observability/exceptions",
  );
  const incidents = useApi<{ items: IncidentRow[] }>(
    "/observability/incidents",
  );
  const performance = useApi<{ run_id: string | null; items: ProbeRow[] }>(
    "/observability/performance",
  );

  const summaryData = summary.state === "ready" ? summary.data : null;
  const readinessData = readiness.state === "ready" ? readiness.data : null;
  const sloRows = slos.state === "ready" ? slos.data.items : [];
  const healthRows = health.state === "ready" ? health.data.items : [];
  const exceptionRows =
    exceptions.state === "ready" ? exceptions.data.items : [];
  const incidentRows = incidents.state === "ready" ? incidents.data.items : [];
  const probeRows =
    performance.state === "ready" ? performance.data.items : [];

  return (
    <div className="pb-10">
      <PageHeader
        title="Observability"
        description="System health, data-quality SLOs, source freshness, exception queue, incident reports, and performance baselines. This page performs no writes — observability runs execute through the CLI. An unmet SLO is a finding, not an error to hide; a stale source is reported with its reason."
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        {summary.state === "error" && (
          <StateNotice kind="error" message={summary.error} />
        )}
        <Card title="Readiness">
          {readiness.state === "loading" && <p className="text-sm">Loading…</p>}
          {readinessData && (
            <div className="text-sm">
              <p>
                Database: {readinessData.database.status} · Migration:{" "}
                {readinessData.migration_head ?? "unknown"} (expected{" "}
                {readinessData.migration_expected}) · Ready:{" "}
                <StatusBadge
                  status={readinessData.ready ? "ready" : "not ready"}
                />
              </p>
              <p>
                Auth enforcement: {readinessData.auth_enforcement} · Latest
                observability run:{" "}
                {readinessData.latest_observability_run ?? "none"}
              </p>
            </div>
          )}
        </Card>
        <Card title="Latest observability run">
          {summary.state === "loading" && <p className="text-sm">Loading…</p>}
          {summaryData && (
            <div className="text-sm">
              <p>
                Latest run:{" "}
                <strong>{summaryData.latest_run_id ?? "none"}</strong>
                {summaryData.latest_run_status && (
                  <span>
                    {" "}
                    · status:{" "}
                    <StatusBadge status={summaryData.latest_run_status} />
                  </span>
                )}
              </p>
              <p>
                SLOs: {summaryData.slos_total} total · {summaryData.slos_met}{" "}
                met · {summaryData.slos_unmet} unmet ·{" "}
                {summaryData.slos_not_evaluable} not evaluable (shown without
                values)
              </p>
              <p>
                Sources: {summaryData.sources_total} total · stale:{" "}
                {summaryData.sources_stale.length > 0
                  ? summaryData.sources_stale.join(", ")
                  : "none"}{" "}
                · unknown:{" "}
                {summaryData.sources_unknown.length > 0
                  ? summaryData.sources_unknown.join(", ")
                  : "none"}
              </p>
              <p>
                Open exceptions: {summaryData.exceptions_open} · Open
                incidents: {summaryData.incidents_open} · Performance probes:{" "}
                {summaryData.performance_probes}
              </p>
            </div>
          )}
        </Card>
        <Card title="Data-quality SLOs — per source category">
          {slos.state === "error" && (
            <StateNotice kind="error" message={slos.error} />
          )}
          {slos.state === "ready" && (
            <DataTable<SloRow>
              caption="SLO definitions with latest measurements"
              columns={[
                { key: "slo_key", header: "SLO", accessor: "slo_key" },
                { key: "category", header: "Category", accessor: "category" },
                {
                  key: "latest_value",
                  header: "Value",
                  render: (row) =>
                    row.latest_value === null
                      ? "not evaluable — no value"
                      : String(row.latest_value),
                },
                {
                  key: "target_value",
                  header: "Target",
                  render: (row) =>
                    `${row.comparison} ${String(row.target_value)} ${row.unit}`,
                },
                {
                  key: "latest_status",
                  header: "Status",
                  render: (row) => (
                    <StatusBadge status={row.latest_status ?? "unknown"} />
                  ),
                },
                {
                  key: "latest_reason",
                  header: "Reason",
                  accessor: "latest_reason",
                },
              ]}
              rows={sloRows}
            />
          )}
        </Card>
        <Card title="Source health">
          {health.state === "error" && (
            <StateNotice kind="error" message={health.error} />
          )}
          {health.state === "ready" && (
            <DataTable<HealthRow>
              caption="Source health snapshot"
              columns={[
                { key: "source_key", header: "Source", accessor: "source_key" },
                {
                  key: "latest_observation_date",
                  header: "Latest observation",
                  accessor: "latest_observation_date",
                },
                {
                  key: "coverage",
                  header: "Coverage",
                  render: (row) =>
                    row.coverage_denominator === null
                      ? String(row.coverage_numerator ?? "—")
                      : `${String(row.coverage_numerator ?? "—")} / ${String(row.coverage_denominator)}`,
                },
                {
                  key: "freshness_days",
                  header: "Freshness (days)",
                  render: (row) =>
                    row.freshness_days === null
                      ? "unknown"
                      : String(row.freshness_days),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge status={row.status} />,
                },
              ]}
              rows={healthRows}
            />
          )}
        </Card>
        <Card title="Exception queue">
          {exceptions.state === "error" && (
            <StateNotice kind="error" message={exceptions.error} />
          )}
          {exceptions.state === "ready" && (
            <DataTable<ExceptionRow>
              caption="Exception queue"
              columns={[
                {
                  key: "exception_key",
                  header: "Exception",
                  accessor: "exception_key",
                },
                { key: "severity", header: "Severity", accessor: "severity" },
                { key: "title", header: "Title", accessor: "title" },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge status={row.status} />,
                },
              ]}
              rows={exceptionRows}
            />
          )}
        </Card>
        <Card title="Incident reports">
          {incidents.state === "error" && (
            <StateNotice kind="error" message={incidents.error} />
          )}
          {incidents.state === "ready" && (
            <DataTable<IncidentRow>
              caption="Incident reports"
              columns={[
                {
                  key: "incident_key",
                  header: "Incident",
                  accessor: "incident_key",
                },
                { key: "severity", header: "Severity", accessor: "severity" },
                { key: "title", header: "Title", accessor: "title" },
                {
                  key: "runbook_ref",
                  header: "Runbook",
                  accessor: "runbook_ref",
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge status={row.status} />,
                },
              ]}
              rows={incidentRows}
            />
          )}
        </Card>
        <Card title="Performance baseline">
          {performance.state === "error" && (
            <StateNotice kind="error" message={performance.error} />
          )}
          {performance.state === "ready" && (
            <DataTable<ProbeRow>
              caption="Performance probes (single samples, not percentiles)"
              columns={[
                { key: "probe_key", header: "Probe", accessor: "probe_key" },
                { key: "metric_key", header: "Metric", accessor: "metric_key" },
                {
                  key: "value",
                  header: "Value",
                  render: (row) =>
                    row.value === null
                      ? "not available on this dialect"
                      : `${String(row.value)} ${row.unit}`,
                },
                { key: "notes", header: "Notes", accessor: "notes" },
              ]}
              rows={probeRows}
            />
          )}
        </Card>
      </div>
    </div>
  );
}
