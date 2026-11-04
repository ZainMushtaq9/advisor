import { FoundationShell } from "@/components/foundation-shell";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";

export default function ResearchPage() {
  return (
    <FoundationShell
      title="Research"
      description="Foundation shell for the research workspace. No reports, analyses, or recommendations are shown here; research content requires verified inputs and, for recommendations, an audit pass in later phases."
      planned={[
        "Research reports citing stored outputs by id and version",
        "Analysis views with stated methods, inputs, and limitations",
      ]}
    >
      <Card title="Research reports (foundation)">
        <DataTable
          caption="Research reports — no records yet"
          columns={[
            { key: "title", header: "Report" },
            { key: "status", header: "Status" },
          ]}
          rows={[]}
        />
      </Card>
    </FoundationShell>
  );
}
