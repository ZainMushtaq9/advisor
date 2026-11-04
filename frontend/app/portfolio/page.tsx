import { FoundationShell } from "@/components/foundation-shell";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";

export default function PortfolioPage() {
  return (
    <FoundationShell
      title="Portfolio"
      description="Foundation shell for the portfolio workspace. No holdings, values, or allocations are shown here. Nothing on this page executes or simulates a trade — there is no broker connection in this project."
      planned={[
        "Portfolio holdings from user-entered, audited inputs (later phase)",
        "Risk views with stated methods and limitations",
      ]}
    >
      <Card title="Holdings (foundation)">
        <DataTable
          caption="Portfolio holdings — no records yet"
          columns={[
            { key: "name", header: "Holding" },
            { key: "quantity", header: "Quantity" },
            { key: "value", header: "Value" },
          ]}
          rows={[]}
        />
      </Card>
    </FoundationShell>
  );
}
