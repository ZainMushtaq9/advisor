"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import {
  PageHeader,
  StateNotice,
  StatusBadge,
  SourceLine,
} from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtNum, fmtPkr, fmtDate } from "@/lib/format";

type Tab =
  | "overview"
  | "fundamentals"
  | "valuation"
  | "macro"
  | "ownership"
  | "risk"
  | "news";

const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "fundamentals", label: "Fundamentals" },
  { key: "valuation", label: "Valuation" },
  { key: "macro", label: "Macro" },
  { key: "ownership", label: "Ownership & actions" },
  { key: "risk", label: "Risk" },
  { key: "news", label: "News & reports" },
];

interface CompanyDetail {
  id: number;
  legal_name: string;
  sector_name: string | null;
  sector_source: string | null;
  status: string;
  securities_count: number;
}

interface SecuritiesResponse {
  items: { ticker: string; company_id: number; company_name?: string; security_type: string; status: string }[];
}

interface LatestPrice {
  ticker: string;
  observation: {
    trading_date: string;
    open: number | null;
    high: number | null;
    low: number | null;
    close: number | null;
    volume: number | null;
    turnover: number | null;
    previous_close: number | null;
    is_adjusted: boolean;
    quality_status: string;
    freshness: string;
    source_key: string;
  } | null;
}

interface RatiosResponse {
  ticker: string;
  status: string;
  note?: string;
  period_label?: string;
  period_end?: string;
  period_days?: number;
  metrics?: { metric_key: string; status: string; value: string | null; reason: string | null }[];
  health?: Record<string, { score: string | null }>;
  warnings?: { warning_key: string; severity: string }[];
}

interface ValuationsResponse {
  ticker: string;
  status: string;
  reason?: string;
  price_date?: string;
  price?: string;
  methods?: { method_key: string; status: string; value: string | null; reason: string | null }[];
}

interface ExposuresResponse {
  ticker: string;
  status: string;
  reason?: string;
  exposures?: { exposure_key: string; direction: string; evidence_ref: string }[];
}

interface OwnershipResponse {
  ticker: string;
  rows?: { holder_category: string; holder_name: string | null; shares_held: number | null; percentage: string | null; reporting_date: string }[];
}

interface ActionsResponse {
  ticker: string;
  rows?: { action_type: string; amount_per_share: string | null; fiscal_year: string | null; date_evidence: string | null }[];
}

interface RiskProfile {
  ticker: string;
  values?: { metric_key: string; value: string | null; computation_status: string; reason: string | null }[];
}

interface NewsResponse {
  events?: { id: number; event_date: string; headline: string; event_type: string; primary_company_id: number | null; relevance_score: number | null }[];
}

interface ReportsResponse {
  items?: { id: number; template_key: string; subject_label: string; status: string; report_date: string }[];
}

interface DecisionsResponse {
  decisions?: { screening_outcome: string; research_conclusion: string; user_facing: string; confidence: string }[];
}

/**
 * Company detail page, resolved by registry id (numeric) or ticker.
 * Every tab fetches only when opened. Companies without loaded statements
 * show pending / no-configured-period states from the API — never invented
 * figures.
 */
export function CompanyDetailClient() {
  const params = useParams<{ key: string }>();
  const rawKey = decodeURIComponent(params.key ?? "");
  const isNumeric = /^\d+$/.test(rawKey);
  const [tab, setTab] = useState<Tab>("overview");

  const company = useApi<CompanyDetail>(
    isNumeric ? `/companies/${rawKey}` : null,
  );
  const securitiesById = useApi<SecuritiesResponse>(
    isNumeric ? `/companies/${rawKey}/securities` : null,
  );
  const securitiesByTicker = useApi<SecuritiesResponse>(
    isNumeric ? null : `/securities?ticker=${encodeURIComponent(rawKey.toUpperCase())}`,
  );

  // A non-numeric key is a ticker only if the registry actually holds it;
  // an unknown ticker must resolve to "not found", never to a guessed page.
  const tickerKnown =
    isNumeric ||
    (securitiesByTicker.state === "ready" &&
      securitiesByTicker.data.items.length > 0);
  const ticker = isNumeric
    ? (securitiesById.state === "ready"
      ? securitiesById.data.items[0]?.ticker
      : undefined)
    : tickerKnown
      ? rawKey.toUpperCase()
      : undefined;
  const companyId = isNumeric
    ? (company.state === "ready" ? company.data.id : undefined)
    : (securitiesByTicker.state === "ready"
      ? securitiesByTicker.data.items[0]?.company_id
      : undefined);
  const legalName = isNumeric
    ? (company.state === "ready" ? company.data.legal_name : undefined)
    : (securitiesByTicker.state === "ready"
      ? securitiesByTicker.data.items[0]?.company_name
      : undefined);

  const latest = useApi<LatestPrice>(
    ticker ? `/market/prices/${ticker}/latest` : null,
  );
  const decisions = useApi<DecisionsResponse>(
    tab === "overview" && ticker ? `/decisions?ticker=${ticker}` : null,
  );
  const reports = useApi<ReportsResponse>(
    tab === "overview" || tab === "news"
      ? ticker
        ? `/reports?subject_key=${ticker}&limit=50`
        : null
      : null,
  );
  const ratios = useApi<RatiosResponse>(
    tab === "fundamentals" && ticker ? `/fundamentals/ratios?ticker=${ticker}` : null,
  );
  const valuations = useApi<ValuationsResponse>(
    tab === "valuation" && ticker ? `/valuations?ticker=${ticker}` : null,
  );
  const exposures = useApi<ExposuresResponse>(
    tab === "macro" && ticker ? `/macro/exposures?ticker=${ticker}` : null,
  );
  const ownership = useApi<OwnershipResponse>(
    tab === "ownership" && ticker ? `/ownership?ticker=${ticker}` : null,
  );
  const actions = useApi<ActionsResponse>(
    tab === "ownership" && ticker ? `/actions?ticker=${ticker}` : null,
  );
  const risk = useApi<RiskProfile>(
    tab === "risk" && ticker ? `/risk/profile?ticker=${ticker}` : null,
  );
  const news = useApi<NewsResponse>(tab === "news" ? "/news" : null);

  const resolving =
    (isNumeric &&
      (company.state === "loading" || securitiesById.state === "loading")) ||
    (!isNumeric && securitiesByTicker.state === "loading");
  const resolveFailed =
    (isNumeric && (company.state === "error" || securitiesById.state === "error")) ||
    (!isNumeric && securitiesByTicker.state === "error") ||
    (!isNumeric &&
      securitiesByTicker.state === "ready" &&
      securitiesByTicker.data.items.length === 0) ||
    (ticker === undefined && !resolving);

  const newsForCompany =
    news.state === "ready"
      ? (news.data.events ?? []).filter(
        (e) => companyId !== undefined && e.primary_company_id === companyId,
      )
      : [];

  return (
    <div className="pb-10">
      <PageHeader
        title={
          resolving
            ? "Loading company…"
            : (legalName ?? ticker ?? rawKey)
        }
        description={
          isNumeric && company.state === "ready"
            ? `${company.data.legal_name} — sector: ${company.data.sector_name ?? "unavailable"} (source: ${company.data.sector_source ?? "unavailable"}). Registry quality: ${company.data.status}.`
            : ticker
              ? `Detail for ticker ${ticker}. Registry identity is resolved from the live registry; statement coverage is four companies (HUBC, NML, OGDC, HBL).`
              : "Company could not be resolved."
        }
        banners={[
          "Statement-derived figures cover HUBC, NML, OGDC and HBL. Any other company shows pending or no-configured-period states — that absence is the honest answer, not a gap to fill.",
        ]}
      />

      {resolveFailed && (
        <div className="mx-auto w-full max-w-6xl px-4 pt-4">
          <StateNotice
            kind="error"
            message="This company could not be resolved in the registry. Check the ticker or registry id; nothing is shown rather than a guessed company."
          />
        </div>
      )}

      {!resolveFailed && (
      <>
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        <div role="tablist" aria-label="Company sections" className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <button
              key={t.key}
              role="tab"
              aria-selected={tab === t.key}
              onClick={() => setTab(t.key)}
              className={`rounded-md border px-3 py-1.5 text-sm font-medium ${
                tab === t.key
                  ? "border-navy-900 bg-navy-900 text-white dark:border-accent-500 dark:bg-accent-500 dark:text-navy-950"
                  : "border-neutral-300 dark:border-navy-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mx-auto w-full max-w-6xl px-4 pt-6">
        {tab === "overview" && (
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Latest price (single trading date)">
              {latest.state === "loading" && <p className="text-sm">Loading…</p>}
              {latest.state === "error" && <StateNotice kind="error" message={latest.error} />}
              {latest.state === "ready" &&
                (latest.data.observation ? (
                  <div className="text-sm">
                    <p>
                      Close: <strong>{fmtPkr(latest.data.observation.close)}</strong> · Volume:{" "}
                      {fmtNum(latest.data.observation.volume)}
                    </p>
                    <p className="mt-1">
                      Open {fmtNum(latest.data.observation.open)} · High{" "}
                      {fmtNum(latest.data.observation.high)} · Low{" "}
                      {fmtNum(latest.data.observation.low)}
                    </p>
                    <SourceLine
                      source={latest.data.observation.source_key}
                      date={latest.data.observation.trading_date}
                      unit="PKR per share; volume in shares"
                      quality={latest.data.observation.quality_status}
                    >
                      Freshness: {latest.data.observation.freshness}. Unadjusted:{" "}
                      {latest.data.observation.is_adjusted ? "no" : "yes — unadjusted"}. Previous
                      close and turnover: not available.
                    </SourceLine>
                  </div>
                ) : (
                  <StateNotice kind="empty" message="No price row stored for this ticker on 2026-11-03." />
                ))}
            </Card>
            <Card title="Decision (research opinion only)">
              {decisions.state === "loading" && <p className="text-sm">Loading…</p>}
              {decisions.state === "error" && <StateNotice kind="error" message={decisions.error} />}
              {decisions.state === "ready" &&
                (decisions.data.decisions?.[0] ? (
                  <div className="text-sm">
                    <p>Screening: {decisions.data.decisions[0].screening_outcome}</p>
                    <p className="mt-1">Research conclusion: {decisions.data.decisions[0].research_conclusion}</p>
                    <p className="mt-1">
                      User-facing: <strong>{decisions.data.decisions[0].user_facing}</strong> ·
                      Confidence: {decisions.data.decisions[0].confidence}
                    </p>
                    <p className="mt-2 text-neutral-600 dark:text-neutral-300">
                      A WITHHELD user-facing value is not advice. No decision here
                      authorises any trade; there is no order path in this product.
                    </p>
                  </div>
                ) : (
                  <StateNotice kind="empty" message="No decision row stored for this company." />
                ))}
            </Card>
            <Card title="Reports for this company">
              {reports.state === "loading" && <p className="text-sm">Loading…</p>}
              {reports.state === "error" && <StateNotice kind="error" message={reports.error} />}
              {reports.state === "ready" && (
                <ul className="space-y-2 text-sm">
                  {(reports.data.items ?? []).map((r) => (
                    <li key={r.id}>
                      <Link href={`/reports/${r.id}`} className="font-medium text-accent-600 hover:underline">
                        {r.template_key}
                      </Link>{" "}
                      — {r.status} · {fmtDate(r.report_date)}
                    </li>
                  ))}
                  {(reports.data.items ?? []).length === 0 && (
                    <li>No reports stored for this company.</li>
                  )}
                </ul>
              )}
            </Card>
          </div>
        )}

        {tab === "fundamentals" && (
          <Card title="Fundamentals — statement-derived ratios">
            {ratios.state === "loading" && <p className="text-sm">Loading…</p>}
            {ratios.state === "error" && <StateNotice kind="error" message={ratios.error} />}
            {ratios.state === "ready" &&
              (ratios.data.status === "assessed" ? (
                <>
                  <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                    Period: {ratios.data.period_label ?? ratios.data.period_end} (
                    {ratios.data.period_days ?? "—"} days). All values UNVERIFIED.
                  </p>
                  <DataTable
                    caption="Fundamental ratios"
                    columns={[
                      { key: "metric_key", header: "Metric", accessor: "metric_key" },
                      { key: "value", header: "Value", render: (r) => fmtNum(r.value) },
                      { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
                      { key: "reason", header: "Reason", render: (r) => r.reason ?? "" },
                    ]}
                    rows={ratios.data.metrics ?? []}
                    emptyTitle="No ratios"
                    emptyDescription="No ratio rows were returned."
                  />
                  {(ratios.data.warnings ?? []).length > 0 && (
                    <p className="mt-3 text-sm">
                      Warnings (review-only, never proof of fraud or insolvency):{" "}
                      {(ratios.data.warnings ?? []).map((w) => w.warning_key).join(", ")}
                    </p>
                  )}
                </>
              ) : (
                <StateNotice
                  kind="empty"
                  message={`Status: ${ratios.data.status}. ${ratios.data.note ?? "No configured period exists for this company."}`}
                />
              ))}
          </Card>
        )}

        {tab === "valuation" && (
          <Card title="Valuation — seventeen methods">
            {valuations.state === "loading" && <p className="text-sm">Loading…</p>}
            {valuations.state === "error" && <StateNotice kind="error" message={valuations.error} />}
            {valuations.state === "ready" &&
              (valuations.data.methods && valuations.data.methods.length > 0 ? (
                <>
                  <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                    Price date: {fmtDate(valuations.data.price_date)} · Price:{" "}
                    {fmtPkr(valuations.data.price)}. Values are descriptive
                    estimates, not price targets and not investment advice.
                  </p>
                  <DataTable
                    caption="Valuation methods"
                    columns={[
                      { key: "method_key", header: "Method", accessor: "method_key" },
                      { key: "value", header: "Value", render: (r) => fmtNum(r.value) },
                      { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
                      { key: "reason", header: "Reason", render: (r) => r.reason ?? "" },
                    ]}
                    rows={valuations.data.methods}
                    emptyTitle="No methods"
                    emptyDescription="No valuation rows were returned."
                  />
                </>
              ) : (
                <StateNotice
                  kind="empty"
                  message={`Status: ${valuations.data.status}. ${valuations.data.reason ?? "No configured company-period with statements."}`}
                />
              ))}
          </Card>
        )}

        {tab === "macro" && (
          <Card title="Macro exposures">
            {exposures.state === "loading" && <p className="text-sm">Loading…</p>}
            {exposures.state === "error" && <StateNotice kind="error" message={exposures.error} />}
            {exposures.state === "ready" &&
              (exposures.data.exposures && exposures.data.exposures.length > 0 ? (
                <DataTable
                  caption="Company macro exposures"
                  columns={[
                    { key: "exposure_key", header: "Exposure", accessor: "exposure_key" },
                    { key: "direction", header: "Direction", accessor: "direction" },
                    { key: "evidence_ref", header: "Evidence", accessor: "evidence_ref" },
                  ]}
                  rows={exposures.data.exposures}
                  emptyTitle="No exposures"
                  emptyDescription="No exposure rows were returned."
                />
              ) : (
                <StateNotice
                  kind="empty"
                  message={`Status: ${exposures.data.status}. ${exposures.data.reason ?? "No exposures stored for this company."}`}
                />
              ))}
            <p className="mt-3 text-sm">
              <Link href="/macro" className="font-medium text-accent-500">
                Full macro section →
              </Link>
            </p>
          </Card>
        )}

        {tab === "ownership" && (
          <div className="grid gap-4">
            <Card title="Ownership holdings (as at reporting date)">
              {ownership.state === "loading" && <p className="text-sm">Loading…</p>}
              {ownership.state === "error" && <StateNotice kind="error" message={ownership.error} />}
              {ownership.state === "ready" && (
                <DataTable
                  caption="Ownership holdings"
                  columns={[
                    { key: "holder_category", header: "Category", accessor: "holder_category" },
                    { key: "holder_name", header: "Holder", render: (r) => r.holder_name ?? "—" },
                    { key: "shares_held", header: "Shares", render: (r) => fmtNum(r.shares_held) },
                    { key: "percentage", header: "Percent", render: (r) => fmtNum(r.percentage) },
                    { key: "reporting_date", header: "As at", accessor: "reporting_date" },
                  ]}
                  rows={ownership.data.rows ?? []}
                  emptyTitle="No ownership rows"
                  emptyDescription="No ownership rows are stored for this company (only HUBC has loaded ownership)."
                />
              )}
            </Card>
            <Card title="Corporate actions (dividends)">
              {actions.state === "loading" && <p className="text-sm">Loading…</p>}
              {actions.state === "error" && <StateNotice kind="error" message={actions.error} />}
              {actions.state === "ready" && (
                <DataTable
                  caption="Corporate actions"
                  columns={[
                    { key: "action_type", header: "Type", accessor: "action_type" },
                    { key: "amount_per_share", header: "Per share (PKR)", render: (r) => fmtNum(r.amount_per_share) },
                    { key: "fiscal_year", header: "Fiscal year", render: (r) => r.fiscal_year ?? "" },
                    { key: "date_evidence", header: "Date evidence", render: (r) => r.date_evidence ?? "" },
                  ]}
                  rows={actions.data.rows ?? []}
                  emptyTitle="No action rows"
                  emptyDescription="No corporate actions are stored for this company. Stored actions carry NULL dates — no date is ever invented."
                />
              )}
            </Card>
          </div>
        )}

        {tab === "risk" && (
          <Card title="Risk profile">
            {risk.state === "loading" && <p className="text-sm">Loading…</p>}
            {risk.state === "error" && <StateNotice kind="error" message={risk.error} />}
            {risk.state === "ready" && (
              <DataTable
                caption="Risk metric values"
                columns={[
                  { key: "metric_key", header: "Metric", accessor: "metric_key" },
                  { key: "value", header: "Value", render: (r) => fmtNum(r.value) },
                  { key: "computation_status", header: "Status", render: (r) => <StatusBadge status={r.computation_status} /> },
                  { key: "reason", header: "Reason", render: (r) => r.reason ?? "" },
                ]}
                rows={risk.data.values ?? []}
                emptyTitle="No risk values"
                emptyDescription="No risk values are stored for this company."
              />
            )}
            <p className="mt-3 text-xs text-neutral-500 dark:text-neutral-400">
              Series risk metrics need 251 observations; one price date cannot
              supply them. Flags are review-only, never fraud, default or
              solvency conclusions.
            </p>
          </Card>
        )}

        {tab === "news" && (
          <div className="grid gap-4">
            <Card title="News events for this company">
              {news.state === "loading" && <p className="text-sm">Loading…</p>}
              {news.state === "error" && <StateNotice kind="error" message={news.error} />}
              {news.state === "ready" && (
                <DataTable
                  caption="News events for this company"
                  columns={[
                    { key: "event_date", header: "Date", accessor: "event_date" },
                    { key: "headline", header: "Headline", accessor: "headline" },
                    { key: "event_type", header: "Type", accessor: "event_type" },
                  ]}
                  rows={newsForCompany}
                  emptyTitle="No events for this company"
                  emptyDescription="No stored news event links to this company. Seed coverage is 4 of 470 companies."
                />
              )}
            </Card>
            <Card title="Reports for this company">
              {reports.state === "loading" && <p className="text-sm">Loading…</p>}
              {reports.state === "error" && <StateNotice kind="error" message={reports.error} />}
              {reports.state === "ready" && (
                <ul className="space-y-2 text-sm">
                  {(reports.data.items ?? []).map((r) => (
                    <li key={r.id}>
                      <Link href={`/reports/${r.id}`} className="font-medium text-accent-600 hover:underline">
                        {r.template_key}
                      </Link>{" "}
                      — {r.status} · {fmtDate(r.report_date)}
                    </li>
                  ))}
                  {(reports.data.items ?? []).length === 0 && (
                    <li>No reports stored for this company.</li>
                  )}
                </ul>
              )}
            </Card>
          </div>
        )}
      </div>
      </>
      )}
    </div>
  );
}
