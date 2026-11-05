"use client";

import { useState } from "react";

import { Card } from "@/components/ui";
import { PageHeader, StateNotice } from "@/components/data-states";
import { useApi } from "@/lib/use-api";

interface Citation {
  title: string | null;
  source: string | null;
  canonical_url: string | null;
  published_at: string | null;
}

interface AssistantResponse {
  answer_kind: string;
  answer_text: string;
  citations: Citation[];
  retrieval?: string;
  note?: string;
}

/**
 * AI news assistant: answers ONLY from stored rows, with a source
 * link on every factual claim. Recommendation questions are answered
 * with uncertainty, never a signal; missing-data answers carry no
 * citation (an invented citation would be worse than none).
 */
export default function NewsAssistantPage() {
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState("");
  const answer = useApi<AssistantResponse>(
    asked ? `/news-intelligence/assistant?q=${encodeURIComponent(asked)}` : null
  );

  return (
    <div className="pb-10">
      <PageHeader
        title="News assistant"
        description="Ask about stored news. Answers come only from stored rows; retrieval is deterministic full-text (vector retrieval is not implemented)."
        banners={[
          "Try: 'Show me HUBC dividends', 'Compare HUBC news with price movement', 'What happened in Nishat Mills'.",
          "A recommendation question ('Should I buy…?') is always answered with uncertainty — this assistant never issues buy/sell advice.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Ask a question">
          <div className="flex gap-2 text-sm">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Show me HUBC dividends"
              className="flex-1 border px-2 py-1"
            />
            <button
              type="button"
              className="border px-3 py-1"
              onClick={() => setAsked(question)}
            >
              Ask
            </button>
          </div>
        </Card>
        {asked && (
          <Card title="Answer">
            {answer.state === "loading" && <p className="text-sm">Loading…</p>}
            {answer.state === "error" && <StateNotice kind="error" message={answer.error} />}
            {answer.state === "ready" && (
              <>
                <p className="text-sm">
                  <strong>{answer.data.answer_kind}:</strong> {answer.data.answer_text}
                </p>
                {answer.data.citations.length > 0 && (
                  <ul className="mt-3 list-disc pl-5 text-sm">
                    {answer.data.citations.map((c, i) => (
                      <li key={i}>
                        {c.canonical_url ? (
                          <a href={c.canonical_url} target="_blank" rel="noreferrer">
                            {c.title ?? "Source"}
                          </a>
                        ) : (
                          <span>
                            {c.title ?? "Source"} (no stored link)
                          </span>
                        )}{" "}
                        — {c.source ?? ""}
                      </li>
                    ))}
                  </ul>
                )}
                {answer.data.note && (
                  <p className="mt-3 text-sm text-neutral-600 dark:text-neutral-300">
                    {answer.data.note}
                  </p>
                )}
              </>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
