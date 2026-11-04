import { FoundationShell } from "@/components/foundation-shell";
import { DataTable } from "@/components/data-table";
import { ChartContainer } from "@/components/chart-container";

export default function CompaniesPage() {
  return (
    <FoundationShell
      title="Companies"
      description="Foundation shell for the company directory. No company names, symbols, prices, or financials are listed here, because no verified company data is connected yet."
      planned={[
        "Company directory from validated stored data",
        "Per-company analysis pages with inputs, methods, and limitations",
      ]}
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <ChartContainer
          title="Company price chart (foundation)"
          series={null}
        />
        <DataTable
          caption="Company directory — no records yet"
          columns={[
            { key: "name", header: "Company" },
            { key: "symbol", header: "Symbol" },
            { key: "sector", header: "Sector" },
          ]}
          rows={[]}
        />
      </div>
    </FoundationShell>
  );
}
