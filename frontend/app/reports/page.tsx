"use client";

import Link from "next/link";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { PageHeader, StateNotice, QualityBadge } from "@/components/data-states";
import { useApi } from "@/lib/use-api";
import { fmtDate } from "@/lib/format";

interface ReportRow {
  id: number;
  template_key: string;
  subject_label: string;
  report_date: string;
  data_cutoff_date: string;
  price_date: string;
  status: string;
  quality_status: string;
}

interface ReportsResponse {
  total: number;
  items: ReportRow[];
}

interface TemplatesResponse {
  templates?: { template_key: string; audience: string; sections: string[] }[];
}

/**
 * Reports page: all 22 reports are DRAFT — internally unreviewed. There is
 * no publish step and no external publication path, so no report here is
 * ever presented as published. Approval is an explicit CLI transition only
 * and is not offered in this GET-only web UI.
 */
export default function ReportsPage() {
  const reports = useApi<ReportsResponse>("/reports?limit=50&offset=0");
  const templates = useApi<TemplatesResponse>("/reports/templates");

  return (
    <div className="pb-10">
      <PageHeader
        title="Reports"
        description="Research reports with fixed section lists, figure kinds and computation statuses. Every non-computed figure carries no value — never zero-filled, never estimated. Future scheduled events appear only in labelled scheduled sections, never as occurred."
        banners={[
          "All reports are DRAFT. APPROVED would mean internally reviewed only — and no report has been approved. Nothing here is published externally.",
        ]}
      />
      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pt-6">
        <Card title="Reports">
          {reports.state === "loading" && <p className="text-sm">Loading…</p>}
          {reports.state === "error" && <StateNotice kind="error" message={reports.error} />}
          {reports.state === "ready" && (
            <DataTable<ReportRow>
              caption="Reports"
              columns={[
                {
                  key: "subject_label",
                  header: "Subject",
                  render: (r) => (
                    <Link href={`/reports/${r.id}`} className="font-medium text-accent-600 hover:underline">
                      {r.subject_label}
                    </Link>
                  ),
                },
                { key: "template_key", header: "Template", accessor: "template_key" },
                { key: "report_date", header: "Report date", render: (r) => fmtDate(r.report_date) },
                { key: "price_date", header: "Price date", render: (r) => fmtDate(r.price_date) },
                { key: "status", header: "Status", accessor: "status" },
                { key: "quality", header: "Quality", render: (r) => <QualityBadge status={r.quality_status} /> },
              ]}
              rows={reports.data.items}
              emptyTitle="No reports"
              emptyDescription="No reports were returned."
            />
          )}
        </Card>
        <Card title="Templates">
          {templates.state === "loading" && <p className="text-sm">Loading…</p>}
          {templates.state === "error" && <StateNotice kind="error" message={templates.error} />}
          {templates.state === "ready" && (
            <DataTable
              caption="Report templates"
              columns={[
                { key: "template_key", header: "Template", accessor: "template_key" },
                { key: "audience", header: "Audience", accessor: "audience" },
                { key: "sections", header: "Sections", render: (r) => (r.sections ?? []).join(", ") },
              ]}
              rows={templates.data.templates ?? []}
              emptyTitle="No templates"
              emptyDescription="No report templates were returned."
            />
          )}
        </Card>
      </div>
    </div>
  );
}
