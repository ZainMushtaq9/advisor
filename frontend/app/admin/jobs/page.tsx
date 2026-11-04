"use client";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, StatusBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import type { PaginatedResponse } from "@/lib/types";

interface JobDefinition {
  job_key: string;
  title: string;
  schedule_kind: string;
  schedule_spec: Record<string, unknown>;
  status: string;
  pause_reason: string | null;
}

interface JobRun {
  id: number;
  job_key: string;
  idempotency_key: string;
  scheduled_for: string | null;
  status: string;
  attempt: number;
  error: string | null;
  blocked_reason: string | null;
}

interface DeadLetter {
  id: number;
  job_key: string;
  idempotency_key: string;
  error: string;
  resolved: boolean;
}

interface Checkpoint {
  job_key: string;
  watermark_key: string;
  watermark_value: string;
}

interface JobsStatus {
  runs_by_status: Record<string, number>;
  runs_total: number;
  stuck_runs: { run_id: number; job_key: string }[];
  paused_definitions: { job_key: string; pause_reason: string | null }[];
  unresolved_dead_letters: number;
  watermarks: Record<string, string>;
}

function scheduleText(def: JobDefinition): string {
  const spec = def.schedule_spec ?? {};
  const time = typeof spec.time === "string" ? spec.time : "";
  if (def.schedule_kind === "manual") return "Manual only — never auto-due";
  if (def.schedule_kind === "daily") {
    const weekdays = Array.isArray(spec.weekdays) ? spec.weekdays.join(", ") : "every day";
    return `Daily ${time} PKT (${weekdays})`;
  }
  if (def.schedule_kind === "weekly") return `Weekly ${time} PKT (weekday ${String(spec.weekday)})`;
  if (def.schedule_kind === "monthly") return `Monthly ${time} PKT (day ${String(spec.day)})`;
  if (def.schedule_kind === "quarterly") return `Quarterly ${time} PKT (day ${String(spec.day)})`;
  if (def.schedule_kind === "annual") return `Annual ${time} PKT`;
  return def.schedule_kind;
}

/**
 * Jobs operations dashboard (Phase 25). Read-only and GET-only:
 * registration, execution, retry, cancellation and retention
 * run through the CLI, never from this page. Paused collection
 * jobs are shown with their exact pause reasons and are never
 * executed by the runner. There is no resident daemon and no
 * paid scheduler: the runner is single-pass and operator-invoked.
 */
export default function JobsPage() {
  const status = useApi<JobsStatus>("/jobs/status");
  const definitions = useApi<{ definitions: JobDefinition[] }>("/jobs/definitions");
  const runs = useApi<PaginatedResponse<JobRun>>("/jobs/runs?limit=20");
  const deadLetters = useApi<{ dead_letters: DeadLetter[] }>("/jobs/dead-letters");
  const checkpoints = useApi<{ checkpoints: Checkpoint[] }>("/jobs/checkpoints");

  const statusData = status.state === "ready" ? status.data : null;
  const definitionRows = definitions.state === "ready" ? definitions.data.definitions : [];
  const runRows = runs.state === "ready" ? runs.data.items : [];
  const deadRows = deadLetters.state === "ready" ? deadLetters.data.dead_letters : [];
  const checkpointRows = checkpoints.state === "ready" ? checkpoints.data.checkpoints : [];

  return (
    <div className="pb-10">
      <PageHeader
        title="Jobs"
        description="Job automation: registry, runs, checkpoints and dead letters. This page performs no writes — registration, execution, retry, cancellation and retention run through the CLI. Paused collection jobs never run; there is no resident daemon and no paid scheduler."
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        {status.state === "error" && <StateNotice kind="error" message={status.error} />}
        <Card title="Operations status">
          {status.state === "loading" && <p className="text-sm">Loading…</p>}
          {statusData && (
            <div className="text-sm">
              <p>
                Runs total: <strong>{statusData.runs_total}</strong>
                {Object.entries(statusData.runs_by_status).map(([key, value]) => (
                  <span key={key}>
                    {" "}
                    · {key}: {value}
                  </span>
                ))}
              </p>
              <p>Stuck runs (running past lease): {statusData.stuck_runs.length}</p>
              <p>Unresolved dead letters: {statusData.unresolved_dead_letters}</p>
              <p>
                Paused definitions:{" "}
                {statusData.paused_definitions.map((d) => d.job_key).join(", ") || "none"}
              </p>
            </div>
          )}
        </Card>
        <Card title="Job definitions">
          {definitions.state === "error" && <StateNotice kind="error" message={definitions.error} />}
          {definitions.state === "ready" && (
            <DataTable<JobDefinition>
              caption="Registered job definitions"
              columns={[
                { key: "job_key", header: "Job", accessor: "job_key" },
                { key: "title", header: "Title", accessor: "title" },
                {
                  key: "schedule",
                  header: "Schedule",
                  render: (row) => scheduleText(row),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge status={row.status} />,
                },
                {
                  key: "pause_reason",
                  header: "Pause reason",
                  render: (row) => row.pause_reason ?? "—",
                },
              ]}
              rows={definitionRows}
            />
          )}
        </Card>
        <Card title="Recent runs">
          {runs.state === "error" && <StateNotice kind="error" message={runs.error} />}
          {runs.state === "ready" && (
            <DataTable<JobRun>
              caption="Recent job runs"
              columns={[
                { key: "id", header: "Run", accessor: "id" },
                { key: "job_key", header: "Job", accessor: "job_key" },
                { key: "scheduled_for", header: "Scheduled", accessor: "scheduled_for" },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge status={row.status} />,
                },
                { key: "attempt", header: "Attempt", accessor: "attempt" },
                {
                  key: "error",
                  header: "Error",
                  render: (row) => row.error ?? row.blocked_reason ?? "—",
                },
              ]}
              rows={runRows}
            />
          )}
        </Card>
        <Card title="Dead letters">
          {deadLetters.state === "error" && <StateNotice kind="error" message={deadLetters.error} />}
          {deadLetters.state === "ready" && (
            <DataTable<DeadLetter>
              caption="Terminally failed runs awaiting operator retry"
              columns={[
                { key: "id", header: "Letter", accessor: "id" },
                { key: "job_key", header: "Job", accessor: "job_key" },
                { key: "idempotency_key", header: "Key", accessor: "idempotency_key" },
                { key: "error", header: "Error", accessor: "error" },
                {
                  key: "resolved",
                  header: "Resolved",
                  render: (row) => (row.resolved ? "yes" : "no"),
                },
              ]}
              rows={deadRows}
              emptyTitle="No dead letters"
              emptyDescription="No terminally failed runs are waiting for an operator retry."
            />
          )}
        </Card>
        <Card title="Checkpoints">
          {checkpoints.state === "error" && <StateNotice kind="error" message={checkpoints.error} />}
          {checkpoints.state === "ready" && (
            <DataTable<Checkpoint>
              caption="Last successful watermarks per job"
              columns={[
                { key: "job_key", header: "Job", accessor: "job_key" },
                { key: "watermark_key", header: "Watermark", accessor: "watermark_key" },
                { key: "watermark_value", header: "Value", accessor: "watermark_value" },
              ]}
              rows={checkpointRows}
            />
          )}
        </Card>
      </div>
    </div>
  );
}
