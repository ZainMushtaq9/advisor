"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface Decision {
  company_id: number;
  decision_date: string;
  screening_outcome: string;
  research_conclusion: string;
  user_facing: string;
  confidence: string;
  total_score: string;
}

interface BacktestRun {
  strategy_key: string;
  status: string;
  window_start: string;
  window_end: string;
}

interface BacktestStatus {
  scope_note?: string;
  runs?: BacktestRun[];
}

interface OrchestrationStatus {
  scope_note?: string;
  agents?: number;
  runs?: { run_key: string; status: string }[];
  evaluations_passed?: number;
  evaluations_total?: number;
}

interface RagResult {
  ticker: string;
  title: string;
  page: number;
  section: string;
  snippet?: string;
  score?: number;
}

interface RagSearch {
  scope?: string;
  query: string;
  results?: RagResult[];
}

/**
 * Research page: decisions (all user-facing WITHHELD), backtests (all
 * NOT_RUNNABLE on a single observation), orchestration (demo graph only,
 * rule-based fallback — no LLM execution), and grounded document search
 * (chunk-level citations, snippets capped at 500 chars, no bodies served).
 */
export default function ResearchPage() {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const decisions = useApi<{ decisions?: Decision[] }>("/decisions");
  const backtests = useApi<BacktestStatus>("/backtesting/status");
  const orchestration = useApi<OrchestrationStatus>("/orchestration/status");
  const rag = useApi<RagSearch>(
    submitted !== null
      ? `/rag/search?q=${encodeURIComponent(submitted)}&role=internal&top_k=5`
      : null,
  );

  return (
    <div className="pb-10">
      <PageHeader
        title="Research"
        description="Decision engine output, backtesting status, agent orchestration status and grounded document search — all from stored rows. Nothing here executes, publishes, promotes a quality status, or sends an external message."
        banners={[
          "Backtests are NOT_RUNNABLE: a single price observation yields zero return intervals, so no return-based metric is computable and no paper order exists.",
          "Agents run in rule-based fallback mode only. No agent output can override a deterministic calculation, and the injection probe was QUARANTINED, not executed.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Decisions (research opinions only)">
          {decisions.state === "loading" && <p className="text-sm">Loading…</p>}
          {decisions.state === "error" && <StateNotice kind="error" message={decisions.error} />}
          {decisions.state === "ready" && (
            <DataTable<Decision>
              caption="Decisions"
              columns={[
                { key: "company_id", header: "Company id", render: (r) => String(r.company_id) },
                { key: "decision_date", header: "Date", accessor: "decision_date" },
                { key: "screening_outcome", header: "Screening", accessor: "screening_outcome" },
                { key: "research_conclusion", header: "Research conclusion", accessor: "research_conclusion" },
                { key: "user_facing", header: "User-facing", accessor: "user_facing" },
                { key: "confidence", header: "Confidence", accessor: "confidence" },
              ]}
              rows={decisions.data.decisions ?? []}
              emptyTitle="No decisions"
              emptyDescription="No decision rows were returned."
            />
          )}
        </Card>

        <Card title="Backtesting">
          {backtests.state === "loading" && <p className="text-sm">Loading…</p>}
          {backtests.state === "error" && <StateNotice kind="error" message={backtests.error} />}
          {backtests.state === "ready" && (
            <>
              {backtests.data.scope_note && (
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  {backtests.data.scope_note}
                </p>
              )}
              <DataTable<BacktestRun>
                caption="Backtest runs"
                columns={[
                  { key: "strategy_key", header: "Strategy", accessor: "strategy_key" },
                  { key: "status", header: "Status", accessor: "status" },
                  { key: "window_start", header: "From", accessor: "window_start" },
                  { key: "window_end", header: "To", accessor: "window_end" },
                ]}
                rows={backtests.data.runs ?? []}
                emptyTitle="No runs"
                emptyDescription="No backtest runs were returned."
              />
            </>
          )}
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            The paper ledger reconciles to PKR 1,000,000.00 per simulated
            portfolio (SIMULATION) and holds zero paper orders, because every
            user-facing decision value is WITHHELD.
          </p>
        </Card>

        <Card title="Orchestration">
          {orchestration.state === "loading" && <p className="text-sm">Loading…</p>}
          {orchestration.state === "error" && <StateNotice kind="error" message={orchestration.error} />}
          {orchestration.state === "ready" && (
            <>
              {orchestration.data.scope_note && (
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  {orchestration.data.scope_note}
                </p>
              )}
              <p className="text-sm">
                Registered agents: {orchestration.data.agents ?? "—"} · Evaluations:{" "}
                {orchestration.data.evaluations_passed ?? "—"}/
                {orchestration.data.evaluations_total ?? "—"} passed
              </p>
              <div className="mt-3">
                <DataTable
                  caption="Orchestration runs"
                  columns={[
                    { key: "run_key", header: "Run", accessor: "run_key" },
                    { key: "status", header: "Status", accessor: "status" },
                  ]}
                  rows={orchestration.data.runs ?? []}
                  emptyTitle="No runs"
                  emptyDescription="No orchestration runs were returned."
                />
              </div>
            </>
          )}
        </Card>

        <Card title="Grounded document search (issuer reports only)">
          <form
            className="mb-4 flex flex-wrap gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setSubmitted(query.trim());
            }}
          >
            <label htmlFor="rag-query" className="sr-only">
              Search indexed issuer reports
            </label>
            <input
              id="rag-query"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="e.g. HUBC net profit"
              className="min-w-64 flex-1 rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-navy-700 dark:bg-navy-900"
            />
            <button
              type="submit"
              className="rounded-md bg-navy-900 px-4 py-2 text-sm font-medium text-white dark:bg-accent-500 dark:text-navy-950"
            >
              Search
            </button>
          </form>
          {rag.state === "loading" && <p className="text-sm">Loading…</p>}
          {rag.state === "error" && <StateNotice kind="error" message={rag.error} />}
          {rag.state === "ready" && (
            <>
              {rag.data.scope && (
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  {rag.data.scope}
                </p>
              )}
              <DataTable<RagResult>
                caption="Search results"
                columns={[
                  { key: "ticker", header: "Ticker", accessor: "ticker" },
                  { key: "title", header: "Document", accessor: "title" },
                  { key: "page", header: "Page", render: (r) => String(r.page) },
                  { key: "section", header: "Section", accessor: "section" },
                  { key: "snippet", header: "Preview (≤500 chars)", render: (r) => r.snippet ?? "" },
                ]}
                rows={rag.data.results ?? []}
                emptyTitle="No results"
                emptyDescription="No indexed passage matches this query. HBL has no indexed document."
              />
            </>
          )}
          {rag.state !== "ready" && submitted === null && (
            <p className="text-sm text-neutral-600 dark:text-neutral-300">
              Search the three indexed issuer reports (HUBC, NML, OGDC — 943
              chunks). Vector retrieval is registered but NOT implemented: no
              verified local embedding model exists on this host.
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
