import { FoundationShell } from "@/components/foundation-shell";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { ChartContainer } from "@/components/chart-container";

export default function DashboardPage() {
  return (
    <FoundationShell
      title="Dashboard"
      description="Foundation shell for the market overview. No index values, prices, movers, or volumes are shown here, because no verified data source is connected yet."
      planned={[
        "Market overview from validated stored data, with source and freshness labels",
        "Sector summaries stating which symbols were included or excluded",
      ]}
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <ChartContainer title="Index chart (foundation)" series={null} />
        <Card title="Market overview (foundation)">
          <DataTable
            caption="Market overview — no records yet"
            columns={[
              { key: "label", header: "Measure" },
              { key: "value", header: "Value" },
            ]}
            rows={[]}
          />
        </Card>
      </div>
    </FoundationShell>
  );
}
