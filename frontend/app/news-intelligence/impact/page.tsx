"use client";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface ImpactRow {
  article_id: number;
  title: string | null;
  importance_score: number;
  credibility_score: number;
  credibility_class: string;
  company_relevance: number | null;
  sector_relevance: number | null;
  market_relevance: number;
  horizon: string;
  confidence: number;
  status: string;
  counterarguments: string[];
}

interface ImpactResponse {
  scope_note?: string;
  impacts?: ImpactRow[];
}

/**
 * News impact dashboard: the five dimensions are kept separate
 * (importance, credibility, company/sector/market relevance) and
 * conflicting records are preserved as counterarguments. No
 * percentage impact and no target price is ever shown here.
 */
export default function NewsImpactPage() {
  const impact = useApi<ImpactResponse>("/news-intelligence/impact");

  return (
    <div className="pb-10">
      <PageHeader
        title="News impact"
        description="Separated impact dimensions per article. A high importance score is not a price prediction, and correlation between news and movement is not causality."
        banners={[
          "Company relevance is blank (not zero) for macro items: null means not applicable to the item's scope.",
          "Counterarguments preserve conflicting coverage side-by-side; no version is silently chosen.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Impact assessments (highest importance first)">
          {impact.state === "loading" && <p className="text-sm">Loading…</p>}
          {impact.state === "error" && <StateNotice kind="error" message={impact.error} />}
          {impact.state === "ready" && (
            <>
              {impact.data.scope_note && (
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  {impact.data.scope_note}
                </p>
              )}
              <DataTable<ImpactRow>
                caption="News impact assessments"
                columns={[
                  { key: "title", header: "Article", render: (r) => r.title ?? "" },
                  { key: "importance_score", header: "Importance", accessor: "importance_score" },
                  { key: "credibility_score", header: "Credibility", accessor: "credibility_score" },
                  { key: "credibility_class", header: "Credibility class", accessor: "credibility_class" },
                  { key: "company_relevance", header: "Company relevance", render: (r) => r.company_relevance ?? "" },
                  { key: "sector_relevance", header: "Sector relevance", render: (r) => r.sector_relevance ?? "" },
                  { key: "market_relevance", header: "Market relevance", accessor: "market_relevance" },
                  { key: "horizon", header: "Horizon", accessor: "horizon" },
                  { key: "confidence", header: "Confidence", accessor: "confidence" },
                ]}
                rows={impact.data.impacts ?? []}
                emptyTitle="No impact assessments"
                emptyDescription="No stored impact assessments were returned."
              />
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
