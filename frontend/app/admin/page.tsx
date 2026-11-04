import { FoundationShell } from "@/components/foundation-shell";
import { Card } from "@/components/ui";
import { DataTable } from "@/components/data-table";

export default function AdminPage() {
  return (
    <FoundationShell
      title="Admin"
      description="Foundation shell for operator views. No system status, task queues, or user data are shown here. Admin actions in later phases go through backend tasks, never direct database edits from the browser."
      planned={[
        "Operator monitoring (task state, validation and audit queues)",
        "Human-gate tasks for recommendations",
      ]}
    >
      <Card title="Operator queue (foundation)">
        <DataTable
          caption="Operator queue — no records yet"
          columns={[
            { key: "task", header: "Task" },
            { key: "state", header: "State" },
          ]}
          rows={[]}
        />
      </Card>
    </FoundationShell>
  );
}
