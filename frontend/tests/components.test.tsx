import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DataTable } from "@/components/data-table";
import { ChartContainer } from "@/components/chart-container";
import { FoundationShell } from "@/components/foundation-shell";
import { cn } from "@/lib/utils";

describe("foundation components", () => {
  it("cn merges classes, with later Tailwind classes winning", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });

  it("DataTable shows an explicit empty state, never fabricated rows", () => {
    render(
      <DataTable
        caption="Test table — no records yet"
        columns={[{ key: "name", header: "Company" }]}
        rows={[]}
      />,
    );
    expect(screen.getByText("No data yet")).toBeInTheDocument();
  });

  it("ChartContainer with no series shows the empty state, not a line", () => {
    render(<ChartContainer title="Test chart" series={null} />);
    expect(screen.getByText("No chart data yet")).toBeInTheDocument();
  });

  it("every foundation shell carries the shell notice", () => {
    render(<FoundationShell title="Test" description="Test page." />);
    expect(
      screen.getByLabelText("Foundation shell notice"),
    ).toBeInTheDocument();
    expect(screen.getByText(/No market data/)).toBeInTheDocument();
  });
});
