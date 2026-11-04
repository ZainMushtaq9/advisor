"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import {
  PageHeader,
  StateNotice,
  QualityBadge,
} from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtNum, fmtDate } from "@/lib/format";

const TICKERS = ["HUBC", "NML", "OGDC", "HBL"];

interface MacroResponse {
  indicators?: {
    indicator_code: string;
    name: string;
    unit: string;
    publisher: string;
    latest: {
      observation_date: string;
      value: string | null;
      source_key: string;
      quality_status: string;
    } | null;
  }[];
}

interface RegimesResponse {
  regimes?: { observation_date: string; regime_label: string; method_version: string }[];
}

interface EventsResponse {
  events?: { event_date: string; event_type: string; title: string; quality_status: string }[];
}

interface ExposuresResponse {
  ticker: string;
  status: string;
  reason?: string;
  exposures?: { exposure_key: string; direction: string; evidence_ref: string }[];
}

/**
 * Macro page: SBP/PBS indicators read directly from official pages, one
 * assigned regime (tightening), scheduled and occurred events, and
 * issuer-evidenced company exposures. Projections appear only as
 * FORECAST-marked outlook, never as observations.
 */
export default function MacroPage() {
  const [ticker, setTicker] = useState("HUBC");
  const macro = useApi<MacroResponse>("/macro");
  const regimes = useApi<RegimesResponse>("/macro/regimes");
  const events = useApi<EventsResponse>("/macro/events");
  const exposures = useApi<ExposuresResponse>(`/macro/exposures?ticker=${ticker}`);

  return (
    <div className="pb-10">
      <PageHeader
        title="Macro & sectors"
        description="Twelve stored macro observations (six VERIFIED via SBP/PBS cross-publisher agreement documented in the Phase 10 notes, six UNVERIFIED), one assigned regime, four events and six issuer-evidenced exposures. Missing series — October CPI year-on-year, KIBOR/yields, USD/PKR, commodity prices — are absent, never estimated."
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Indicators (latest observation each)">
          {macro.state === "loading" && <p className="text-sm">Loading…</p>}
          {macro.state === "error" && <StateNotice kind="error" message={macro.error} />}
          {macro.state === "ready" && (
            <DataTable
              caption="Macro indicators"
              columns={[
                { key: "name", header: "Indicator", accessor: "name" },
                { key: "value", header: "Value", render: (r) => fmtNum(r.latest?.value ?? null) },
                { key: "unit", header: "Unit", accessor: "unit" },
                { key: "observation_date", header: "Observed", render: (r) => fmtDate(r.latest?.observation_date ?? null) },
                { key: "publisher", header: "Publisher", accessor: "publisher" },
                { key: "quality", header: "Quality", render: (r) => <QualityBadge status={r.latest?.quality_status} /> },
              ]}
              rows={macro.data.indicators ?? []}
              emptyTitle="No indicators"
              emptyDescription="No macro indicators were returned."
            />
          )}
        </Card>
        <Card title="Regime">
          {regimes.state === "loading" && <p className="text-sm">Loading…</p>}
          {regimes.state === "error" && <StateNotice kind="error" message={regimes.error} />}
          {regimes.state === "ready" && (
            <DataTable
              caption="Macro regimes"
              columns={[
                { key: "observation_date", header: "As of", accessor: "observation_date" },
                { key: "regime_label", header: "Label", accessor: "regime_label" },
                { key: "method_version", header: "Method", accessor: "method_version" },
              ]}
              rows={regimes.data.regimes ?? []}
              emptyTitle="No regime assigned"
              emptyDescription="No regime row was returned."
            />
          )}
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            Disinflation, external pressure, slowdown and fiscal consolidation
            were explicitly NOT assigned, with reasons recorded in Phase 10.
          </p>
        </Card>
        <Card title="Macro events">
          {events.state === "loading" && <p className="text-sm">Loading…</p>}
          {events.state === "error" && <StateNotice kind="error" message={events.error} />}
          {events.state === "ready" && (
            <DataTable
              caption="Macro events"
              columns={[
                { key: "event_date", header: "Date", render: (r) => fmtDate(r.event_date) },
                { key: "title", header: "Event", accessor: "title" },
                { key: "event_type", header: "Type", accessor: "event_type" },
                { key: "quality", header: "Quality", render: (r) => <QualityBadge status={r.quality_status} /> },
              ]}
              rows={events.data.events ?? []}
              emptyTitle="No events"
              emptyDescription="No macro events were returned."
            />
          )}
        </Card>
        <Card title="Company exposures">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <label htmlFor="macro-ticker" className="text-sm font-medium">
              Company:
            </label>
            <select
              id="macro-ticker"
              value={ticker}
              onChange={(event) => setTicker(event.target.value)}
              className="rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-navy-700 dark:bg-navy-900"
            >
              {TICKERS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          {exposures.state === "loading" && <p className="text-sm">Loading…</p>}
          {exposures.state === "error" && <StateNotice kind="error" message={exposures.error} />}
          {exposures.state === "ready" &&
            (exposures.data.exposures && exposures.data.exposures.length > 0 ? (
              <DataTable
                caption={`Macro exposures for ${ticker}`}
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
        </Card>
      </div>
    </div>
  );
}
