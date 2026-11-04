"use client";

import { useParams } from "next/navigation";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import {
  PageHeader,
  StateNotice,
  QualityBadge,
  StatusBadge,
} from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtNum, fmtDate } from "@/lib/format";

interface ReportDetail {
  id: number;
  template_key: string;
  subject_label: string;
  report_date: string;
  data_cutoff_date: string;
  price_date: string;
  status: string;
  quality_status: string;
  sections?: { section_key: string; title: string; body_markdown: string }[];
  figures?: {
    figure_key: string;
    label: string;
    value: string | null;
    unit: string | null;
    computation_status: string;
    figure_kind: string;
    source_note?: string | null;
  }[];
}

/**
 * Report detail: sections in the template's fixed order, then the figure
 * table. Non-computed figures show no value. The QA gate (cut-off present,
 * exact sections, DISCLAIMER present, forbidden wording rejected) ran on
 * every draft at build time; this page renders stored text only.
 */
export function ReportDetailClient() {
  const params = useParams<{ id: string }>();
  const report = useApi<ReportDetail>(`/reports/${params.id}`);

  return (
    <div className="pb-10">
      {report.state === "loading" && (
        <div className="mx-auto w-full max-w-6xl px-4 pt-8">
          <p className="text-sm">Loading…</p>
        </div>
      )}
      {report.state === "error" && (
        <div className="mx-auto w-full max-w-6xl px-4 pt-8">
          <StateNotice kind="error" message={report.error} />
        </div>
      )}
      {report.state === "ready" && (
        <>
          <PageHeader
            title={report.data.subject_label}
            description={`Template: ${report.data.template_key}. Report date: ${fmtDate(report.data.report_date)}. Data cut-off: ${fmtDate(report.data.data_cutoff_date)}. Price date: ${fmtDate(report.data.price_date)}.`}
            banners={[
              `Status: ${report.data.status} — a draft is internally unreviewed, never published. Quality: ${report.data.quality_status}.`,
            ]}
          />
          <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
            {(report.data.sections ?? []).map((section) => (
              <Card key={section.section_key} title={section.title}>
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700 dark:text-neutral-200">
                  {section.body_markdown}
                </p>
              </Card>
            ))}
            <Card title="Figures">
              <DataTable
                caption="Report figures"
                columns={[
                  { key: "label", header: "Figure", accessor: "label" },
                  { key: "value", header: "Value", render: (r) => fmtNum(r.value) },
                  { key: "unit", header: "Unit", render: (r) => r.unit ?? "" },
                  { key: "computation_status", header: "Status", render: (r) => <StatusBadge status={r.computation_status} /> },
                  { key: "figure_kind", header: "Kind", accessor: "figure_kind" },
                  { key: "quality", header: "Quality", render: () => <QualityBadge status={report.data.quality_status} /> },
                ]}
                rows={report.data.figures ?? []}
                emptyTitle="No figures"
                emptyDescription="No figures were stored for this report."
              />
              <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
                Figure kinds: sourced_fact, deterministic_calculation,
                model_output, analyst_inference, assumption. No price_target
                figure kind exists in this product.
              </p>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
