"use client";

import { useState } from "react";

import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, QualityBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtDate } from "@/lib/format";

interface FeedArticle {
  id: number;
  title: string;
  source: string;
  canonical_url: string;
  published_at: string | null;
  summary: string;
  processor: string;
  status: string;
  quality_status: string;
  sentiment: string | null;
  event_category: string | null;
  tickers: string[];
  importance_score: number | null;
  credibility_score: number | null;
}

interface FeedResponse {
  scope_note?: string;
  articles?: FeedArticle[];
}

/**
 * News Intelligence feed: processed articles (metadata + 280-char
 * summaries + links only; no article bodies) with filters. Scores are
 * separated impact dimensions, never buy/sell signals. An empty
 * result means no stored articles match, not no news in the world.
 */
export default function NewsIntelligencePage() {
  const [ticker, setTicker] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [category, setCategory] = useState("");
  const [source, setSource] = useState("");
  const params = new URLSearchParams();
  if (ticker) params.set("ticker", ticker.toUpperCase());
  if (sentiment) params.set("sentiment", sentiment);
  if (category) params.set("event_category", category);
  if (source) params.set("source", source);
  const query = params.toString();
  const feed = useApi<FeedResponse>(
    `/news-intelligence/feed${query ? `?${query}` : ""}`
  );

  return (
    <div className="pb-10">
      <PageHeader
        title="News intelligence"
        description="Processed news articles with separated sentiment, importance and credibility. No live PSX announcement collection runs while the Terms gate is uncleared; collection jobs are paused and refusals are recorded."
        banners={[
          "Summaries are capped at 280 characters and no article body is stored or served.",
          "Every article here is REVIEW or PROCESSED by the rule-based fallback unless an LLM record exists; nothing here is a buy/sell signal.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Filters">
          <div className="flex flex-wrap gap-3 text-sm">
            <label>
              Ticker{" "}
              <input
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                placeholder="HUBC"
                className="border px-2 py-1"
              />
            </label>
            <label>
              Sentiment{" "}
              <select
                value={sentiment}
                onChange={(e) => setSentiment(e.target.value)}
                className="border px-2 py-1"
              >
                <option value="">Any</option>
                <option value="positive">positive</option>
                <option value="negative">negative</option>
                <option value="neutral">neutral</option>
                <option value="mixed">mixed</option>
              </select>
            </label>
            <label>
              Category{" "}
              <input
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="earnings"
                className="border px-2 py-1"
              />
            </label>
            <label>
              Source key{" "}
              <input
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="phase11_seed"
                className="border px-2 py-1"
              />
            </label>
          </div>
        </Card>
        <Card title="Article feed">
          {feed.state === "loading" && <p className="text-sm">Loading…</p>}
          {feed.state === "error" && <StateNotice kind="error" message={feed.error} />}
          {feed.state === "ready" && (
            <>
              {feed.data.scope_note && (
                <p className="mb-3 text-sm text-neutral-600 dark:text-neutral-300">
                  {feed.data.scope_note}
                </p>
              )}
              <DataTable<FeedArticle>
                caption="Processed news articles"
                columns={[
                  { key: "published_at", header: "Published", render: (r) => fmtDate(r.published_at) },
                  { key: "title", header: "Title", accessor: "title" },
                  { key: "tickers", header: "Tickers", render: (r) => r.tickers.join(", ") },
                  { key: "sentiment", header: "Sentiment", render: (r) => r.sentiment ?? "" },
                  { key: "event_category", header: "Category", render: (r) => r.event_category ?? "" },
                  { key: "importance_score", header: "Importance", render: (r) => r.importance_score ?? "" },
                  { key: "status", header: "Status", accessor: "status" },
                  { key: "quality", header: "Quality", render: (r) => <QualityBadge status={r.quality_status} /> },
                  {
                    key: "link",
                    header: "Source",
                    render: (r) =>
                      r.canonical_url ? (
                        <a href={r.canonical_url} target="_blank" rel="noreferrer">
                          Open
                        </a>
                      ) : (
                        "No stored link"
                      ),
                  },
                ]}
                rows={feed.data.articles ?? []}
                emptyTitle="No articles"
                emptyDescription="No stored articles match these filters."
              />
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
