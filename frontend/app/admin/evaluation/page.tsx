"use client";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, StatusBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface EvaluationSummary {
  latest_run_id: string | null;
  latest_run_status: string | null;
  metrics_total: number;
  metrics_computed: number;
  metrics_not_evaluable: number;
  golden_total: number;
  golden_passed: number;
  golden_failed: string[];
  promoted_models: number;
  gates_met: number;
  datasets: number;
  model_cards: number;
  promotion_gates: number;
}

interface ModelCard {
  model_key: string;
  version: string;
  purpose: string;
  evaluation_status: string;
  limitations: string;
  promotion_status: string;
}

interface PromotionGate {
  gate_key: string;
  applies_to: string;
  requirement: string;
  status: string;
  reason: string;
}

interface EvalMetric {
  subject_key: string;
  metric_key: string;
  value: number | null;
  status: string;
  reason: string;
}

interface GoldenResult {
  run_id: string;
  case_key: string;
  passed: boolean;
}

interface GoldenCase {
  case_key: string;
  category: string;
  input_desc: string;
  expected_outcome: string;
}

/**
 * Evaluation dashboard (Phase 26). Read-only and GET-only:
 * evaluation runs execute through the CLI, never from this page.
 * No model is promoted here, no accuracy claim is made here, and
 * every NOT_EVALUABLE metric is shown without a number — never
 * zero-filled, never estimated. Promotion gates are NOT_MET until
 * positive out-of-sample evidence exists; a failed golden case is
 * shown as a finding, not hidden.
 */
export default function EvaluationPage() {
  const summary = useApi<EvaluationSummary>("/evaluation/summary");
  const cards = useApi<{ model_cards: ModelCard[] }>("/evaluation/model-cards");
  const gates = useApi<{ gates: PromotionGate[] }>("/evaluation/gates");
  const cases = useApi<{ golden_cases: GoldenCase[] }>(
    "/evaluation/golden-cases",
  );

  const summaryData = summary.state === "ready" ? summary.data : null;
  const cardRows = cards.state === "ready" ? cards.data.model_cards : [];
  const gateRows = gates.state === "ready" ? gates.data.gates : [];
  const caseRows = cases.state === "ready" ? cases.data.golden_cases : [];
  const runId = summaryData?.latest_run_id ?? null;
  const metrics = useApi<{ run_id: string; metrics: EvalMetric[] }>(
    runId ? `/evaluation/metrics?run_id=${runId}` : null,
  );
  const golden = useApi<{ run_id: string; golden_results: GoldenResult[] }>(
    runId ? `/evaluation/golden-results?run_id=${runId}` : null,
  );
  const metricRows = metrics.state === "ready" ? metrics.data.metrics : [];
  const goldenRows = golden.state === "ready" ? golden.data.golden_results : [];

  return (
    <div className="pb-10">
      <PageHeader
        title="Evaluation"
        description="Model evaluation, forecast monitoring and research quality benchmarking. This page performs no writes — evaluation runs execute through the CLI. No model is promoted, no forecast is scored, and no recommendation outcome is shown until out-of-sample evidence exists."
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        {summary.state === "error" && (
          <StateNotice kind="error" message={summary.error} />
        )}
        <Card title="Latest evaluation run">
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
                Metrics: {summaryData.metrics_total} total ·{" "}
                {summaryData.metrics_computed} computed ·{" "}
                {summaryData.metrics_not_evaluable} not evaluable (shown without
                values)
              </p>
              <p>
                Golden cases: {summaryData.golden_passed} /{" "}
                {summaryData.golden_total} passed
                {summaryData.golden_failed.length > 0 && (
                  <span> · failed: {summaryData.golden_failed.join(", ")}</span>
                )}
              </p>
              <p>
                Promoted models: {summaryData.promoted_models} · Gates met:{" "}
                {summaryData.gates_met} / {summaryData.promotion_gates} ·
                Datasets: {summaryData.datasets} · Model cards:{" "}
                {summaryData.model_cards}
              </p>
            </div>
          )}
        </Card>
        <Card title="Model cards — none promoted">
          {cards.state === "error" && (
            <StateNotice kind="error" message={cards.error} />
          )}
          {cards.state === "ready" && (
            <DataTable<ModelCard>
              caption="Model cards"
              columns={[
                { key: "model_key", header: "Model", accessor: "model_key" },
                { key: "version", header: "Version", accessor: "version" },
                {
                  key: "evaluation_status",
                  header: "Evaluation status",
                  accessor: "evaluation_status",
                },
                {
                  key: "promotion_status",
                  header: "Promotion",
                  render: (row) => (
                    <StatusBadge status={row.promotion_status} />
                  ),
                },
              ]}
              rows={cardRows}
            />
          )}
        </Card>
        <Card title="Promotion gates — none met">
          {gates.state === "error" && (
            <StateNotice kind="error" message={gates.error} />
          )}
          {gates.state === "ready" && (
            <DataTable<PromotionGate>
              caption="Promotion gates"
              columns={[
                { key: "gate_key", header: "Gate", accessor: "gate_key" },
                {
                  key: "applies_to",
                  header: "Applies to",
                  accessor: "applies_to",
                },
                {
                  key: "reason",
                  header: "Missing evidence",
                  accessor: "reason",
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge status={row.status} />,
                },
              ]}
              rows={gateRows}
            />
          )}
        </Card>
        <Card title="Latest run metrics">
          {metrics.state === "error" && (
            <StateNotice kind="error" message={metrics.error} />
          )}
          {metrics.state === "ready" && (
            <DataTable<EvalMetric>
              caption="Evaluation metrics"
              columns={[
                {
                  key: "subject_key",
                  header: "Subject",
                  accessor: "subject_key",
                },
                { key: "metric_key", header: "Metric", accessor: "metric_key" },
                {
                  key: "value",
                  header: "Value",
                  render: (row) =>
                    row.value === null
                      ? "not evaluable — no value"
                      : String(row.value),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge status={row.status} />,
                },
                { key: "reason", header: "Reason", accessor: "reason" },
              ]}
              rows={metricRows}
            />
          )}
        </Card>
        <Card title="Golden suite — latest run results">
          {golden.state === "error" && (
            <StateNotice kind="error" message={golden.error} />
          )}
          {golden.state === "ready" && (
            <DataTable<GoldenResult>
              caption="Golden results"
              columns={[
                { key: "case_key", header: "Case", accessor: "case_key" },
                {
                  key: "passed",
                  header: "Passed",
                  render: (row) => (
                    <StatusBadge status={row.passed ? "PASS" : "FAIL"} />
                  ),
                },
              ]}
              rows={goldenRows}
            />
          )}
        </Card>
        <Card title="Golden cases">
          {cases.state === "error" && (
            <StateNotice kind="error" message={cases.error} />
          )}
          {cases.state === "ready" && (
            <DataTable<GoldenCase>
              caption="Golden test cases"
              columns={[
                { key: "case_key", header: "Case", accessor: "case_key" },
                { key: "category", header: "Category", accessor: "category" },
                {
                  key: "expected_outcome",
                  header: "Expected outcome",
                  accessor: "expected_outcome",
                },
              ]}
              rows={caseRows}
            />
          )}
        </Card>
      </div>
    </div>
  );
}
