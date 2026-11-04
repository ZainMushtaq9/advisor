import { FoundationShell } from "@/components/foundation-shell";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";

export default function AlertsPage() {
  return (
    <FoundationShell
      title="Alerts"
      description="Foundation shell for alerts. No alerts are active and no alert history is shown here, because no data source or alert rule is connected yet."
      planned={[
        "User-defined alert rules (later phase)",
        "Alert history with the data and rule that triggered each alert",
      ]}
    >
      <Card title="Alerts (foundation)">
        <DataTable
          caption="Alerts — no records yet"
          columns={[
            { key: "rule", header: "Rule" },
            { key: "status", header: "Status" },
          ]}
          rows={[]}
        />
      </Card>
    </FoundationShell>
  );
}
