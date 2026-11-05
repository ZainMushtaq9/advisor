"use client";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, QualityBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtDate } from "@/lib/format";

interface NewsEvent {
  id: number;
  event_date: string;
  date_status: string;
  event_type: string;
  headline: string;
  publisher: string | null;
  source_type: string | null;
  relevance_score: number | null;
  review_status?: string | null;
  quality_status?: string | null;
}

interface NewsResponse {
  scope_note?: string;
  events?: NewsEvent[];
}

interface QualityResponse {
  companies_with_events?: number;
  universe_companies?: number;
  alias_rows?: number;
  ambiguous_aliases?: number;
}

/**
 * News page: seed events derived ONLY from already-stored rows. No live
 * collection runs (PSX Terms-gated, outlet terms unreviewed), no article
 * bodies are served, no sentiment is stored, and scores are
 * review-worthiness only — never buy/sell signals.
 */
export default function NewsPage() {
  const feed = useApi<NewsResponse>("/news");
  const quality = useApi<QualityResponse>("/news/quality");

  return (
    <div className="pb-10">
      <PageHeader
        title="News & events"
        description="Seed events derived only from stored rows: four company earnings events and four macro events. Universe-wide live coverage does not exist in this product, and no PSX announcement collection runs."
        banners={[
          "Coverage is 4 of 470 companies. An empty result for any other company means no stored event, not no news in the world.",
          "No article body is served anywhere; summaries are capped at 280 characters and no sentiment is stored.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Coverage">
          {quality.state === "loading" && <p className="text-sm">Loading…</p>}
          {quality.state === "error" && <StateNotice kind="error" message={quality.error} />}
          {quality.state === "ready" && (
            <p className="text-sm">
              Companies with events:{" "}
              <strong>{quality.data.companies_with_events ?? "—"}</strong> of{" "}
              {quality.data.universe_companies ?? "—"} · Alias rows:{" "}
              {quality.data.alias_rows ?? "—"} · Ambiguous aliases:{" "}
              {quality.data.ambiguous_aliases ?? "—"} (bare-name matches for these are
              capped and forced to review; only the ticker disambiguates them).
            </p>
          )}
        </Card>
        <Card title="Event feed (seed only)">
          {feed.state === "loading" && <p className="text-sm">Loading…</p>}
          {feed.state === "error" && <StateNotice kind="error" message={feed.error} />}
          {feed.state === "ready" && (
            <>
              {feed.data.scope_note && (
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  {feed.data.scope_note}
                </p>
              )}
              <DataTable<NewsEvent>
                caption="Seed news events"
                columns={[
                  { key: "event_date", header: "Date", render: (r) => fmtDate(r.event_date) },
                  { key: "headline", header: "Headline", accessor: "headline" },
                  { key: "event_type", header: "Type", accessor: "event_type" },
                  { key: "publisher", header: "Publisher", render: (r) => r.publisher ?? "" },
                  { key: "date_status", header: "Date status", accessor: "date_status" },
                  { key: "review_status", header: "Review", render: (r) => r.review_status ?? "" },
                  { key: "quality", header: "Quality", render: (r) => <QualityBadge status={r.quality_status} /> },
                ]}
                rows={feed.data.events ?? []}
                emptyTitle="No events"
                emptyDescription="No stored events were returned."
              />
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
