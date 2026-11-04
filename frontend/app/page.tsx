import Link from "next/link";
import { FoundationShell } from "@/components/foundation-shell";
import { Card, Badge } from "@/components/ui";
import { DataTable } from "@/components/data-table";
import { ChartContainer } from "@/components/chart-container";
import { ApiStatus } from "@/components/api-status";
import { NAV_ITEMS } from "@/lib/nav";

export default function Home() {
  return (
    <FoundationShell
      title="PSX Intelligence AI"
      description="Foundation shell for a Pakistan Stock Exchange research workspace. The layout, navigation, theme, and reusable components are in place; verified market data, analysis, forecasts, and recommendations are not — those arrive in later phases only."
      planned={[
        "Backend connection (FastAPI) and verified market data",
        "Company analysis, sector views, and research reports",
        "Portfolio tracking and alerts, after audit rules are defined",
      ]}
    >
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <ApiStatus />
        <Badge tone="info">Phase 2 — Frontend Foundation</Badge>
        <Badge>PKR 0 · Free / open-source only</Badge>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {NAV_ITEMS.filter((item) => item.href !== "/").map((item) => (
          <Link key={item.href} href={item.href} className="block">
            <Card title={item.label}>
              <p className="text-sm text-neutral-600 dark:text-neutral-300">
                {item.description}
              </p>
              <p className="mt-3 text-sm font-medium text-accent-500">
                Open foundation shell →
              </p>
            </Card>
          </Link>
        ))}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <ChartContainer title="Market chart (foundation)" series={null} />
        <Card title="Recently viewed (foundation)">
          <DataTable
            caption="Recently viewed companies — no records yet"
            columns={[
              { key: "name", header: "Company" },
              { key: "note", header: "Note" },
            ]}
            rows={[]}
            emptyDescription="No records yet. This table stays empty until verified company data is connected in a later phase."
          />
        </Card>
      </div>
    </FoundationShell>
  );
}
