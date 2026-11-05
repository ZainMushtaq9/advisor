"use client";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, StatusBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface GateItem {
  result: string;
  evidence: string;
}

interface AcceptanceSummary {
  latest_run_id: string | null;
  verdict: string | null;
  gate: Record<string, GateItem>;
  scenarios: {
    total: number;
    pass: number;
    fail: number;
    blocked: number;
    not_evaluable: number;
  };
  recomputations: { total: number; matched: number; mismatched: number };
  defects: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    open: number;
    fixed: number;
    accepted: number;
  };
}

interface ScenarioRow {
  scenario_key: string;
  case_name: string;
  outcome: string;
  evidence: Record<string, unknown>;
  reason: string;
}

// The API returns matches as a boolean; the table renders it as text.
interface ApiRecomputationRow {
  check_key: string;
  claimed_value: string;
  recomputed_value: string;
  matches: boolean;
  tolerance: string;
  method: string;
}

interface RecomputationRow {
  check_key: string;
  claimed_value: string;
  recomputed_value: string;
  matches: string;
  tolerance: string;
  method: string;
}

interface DefectRow {
  defect_key: string;
  severity: string;
  status: string;
  title: string;
  impact: string;
  unblocker: string;
}

export default function AcceptancePage() {
  const summary = useApi<AcceptanceSummary>("/acceptance/summary");
  const scenarios = useApi<{ scenarios: ScenarioRow[] }>("/acceptance/scenarios");
  const recomputations = useApi<{
    recomputations: ApiRecomputationRow[];
  }>("/acceptance/recomputations");
  const defects = useApi<{ defects: DefectRow[] }>("/acceptance/defects");

  const summaryData = summary.state === "ready" ? summary.data : null;
  const scenarioRows =
    scenarios.state === "ready" ? scenarios.data.scenarios : [];
  const recomputationRows =
    recomputations.state === "ready"
      ? recomputations.data.recomputations
      : [];
  const defectRows =
    defects.state === "ready" ? defects.data.defects : [];
  const gateEntries = summaryData ? Object.entries(summaryData.gate) : [];

  return (
    <div>
      <PageHeader
        title="Acceptance"
        description="End-to-end integration, system acceptance and independent audit. Read-only; runs execute through the CLI. An acceptance record is not a promotion, a publication, a send, or a trade."
      />
      {summary.state === "loading" && <StateNotice kind="loading" message="Loading acceptance summary…" />}
      {summary.state === "error" && (
        <StateNotice kind="error" message="Acceptance summary is unavailable." />
      )}
      {summaryData && summaryData.latest_run_id === null && (
        <StateNotice
          kind="empty"
          message="No acceptance run has been recorded yet. Run scripts/run_acceptance.py --commit."
        />
      )}
      {summaryData && summaryData.latest_run_id !== null && (
        <>
          <Card>
            <h2>Latest run: {summaryData.latest_run_id}</h2>
            <p>
              Verdict: <StatusBadge status={summaryData.verdict ?? "unknown"} />
            </p>
            <p>
              Scenarios: {summaryData.scenarios.pass} pass,{" "}
              {summaryData.scenarios.fail} fail,{" "}
              {summaryData.scenarios.blocked} blocked,{" "}
              {summaryData.scenarios.not_evaluable} not evaluable (of{" "}
              {summaryData.scenarios.total}).
            </p>
            <p>
              Recomputations: {summaryData.recomputations.matched} matched,{" "}
              {summaryData.recomputations.mismatched} mismatched (of{" "}
              {summaryData.recomputations.total}).
            </p>
            <p>
              Defects: {summaryData.defects.critical} critical,{" "}
              {summaryData.defects.high} high, {summaryData.defects.medium}{" "}
              medium, {summaryData.defects.low} low;{" "}
              {summaryData.defects.open} open, {summaryData.defects.fixed}{" "}
              fixed, {summaryData.defects.accepted} accepted.
            </p>
          </Card>
          <Card>
            <h2>Acceptance gate</h2>
            <DataTable
              caption="Acceptance gate evaluation"
              columns={[
                { key: "item", header: "Gate item", accessor: "item" },
                { key: "result", header: "Result", accessor: "result" },
                { key: "evidence", header: "Evidence", accessor: "evidence" },
              ]}
              rows={gateEntries.map(([item, value]) => ({
                item,
                result: value.result,
                evidence: value.evidence,
              }))}
            />
          </Card>
        </>
      )}
      {scenarioRows.length > 0 && (
        <Card>
          <h2>End-to-end scenarios</h2>
          <DataTable<ScenarioRow>
            caption="End-to-end scenario results"
            columns={[
              { key: "scenario_key", header: "Scenario", accessor: "scenario_key" },
              { key: "case_name", header: "Case", accessor: "case_name" },
              { key: "outcome", header: "Outcome", accessor: "outcome" },
              { key: "reason", header: "Reason", accessor: "reason" },
            ]}
            rows={scenarioRows.map((row) => ({
              scenario_key: row.scenario_key,
              case_name: row.case_name,
              outcome: row.outcome,
              reason: row.reason,
              evidence: row.evidence,
            }))}
          />
        </Card>
      )}
      {recomputationRows.length > 0 && (
        <Card>
          <h2>Independent recomputations</h2>
          <DataTable<RecomputationRow>
            caption="Independent recomputation results"
            columns={[
              { key: "check_key", header: "Check", accessor: "check_key" },
              { key: "claimed_value", header: "Claimed", accessor: "claimed_value" },
              { key: "recomputed_value", header: "Recomputed", accessor: "recomputed_value" },
              { key: "matches", header: "Matches", accessor: "matches" },
            ]}
            rows={recomputationRows.map((row) => ({
              check_key: row.check_key,
              claimed_value: row.claimed_value,
              recomputed_value: row.recomputed_value,
              matches: row.matches ? "yes" : "NO — see method",
              tolerance: row.tolerance,
              method: row.method,
            }))}
          />
        </Card>
      )}
      {defectRows.length > 0 && (
        <Card>
          <h2>Defect register</h2>
          <DataTable<DefectRow>
            caption="Defect register"
            columns={[
              { key: "defect_key", header: "Defect", accessor: "defect_key" },
              { key: "severity", header: "Severity", accessor: "severity" },
              { key: "status", header: "Status", accessor: "status" },
              { key: "title", header: "Title", accessor: "title" },
              { key: "unblocker", header: "Unblocker / fix", accessor: "unblocker" },
            ]}
            rows={defectRows.map((row) => ({
              defect_key: row.defect_key,
              severity: row.severity,
              status: row.status,
              title: row.title,
              impact: row.impact,
              unblocker: row.unblocker,
            }))}
          />
        </Card>
      )}
    </div>
  );
}
