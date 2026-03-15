import { History, Loader2, Undo2 } from "lucide-react"

import { useHistoryState, useUiState } from "@/app/console-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { MetricCard } from "@/components/ui/metric-card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { formatTimestamp } from "@/lib/format"

export function HistoryPage() {
  const { saving, saveAction, localNotices, clearScopedNotice } = useUiState()
  const { history, activeRollbackId, onRollback } = useHistoryState()
  const notice = localNotices.history

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="History"
        description="Review configuration history as a product ledger and roll back with clearer, calmer context."
        badges={[{ label: `snapshots: ${history.length}` }]}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard variant="compact" label="Snapshots" value={String(history.length)} />
        <MetricCard variant="compact" label="Latest action" value={history[0]?.action ?? "n/a"} />
        <MetricCard variant="compact" label="Rollback mode" value="Manual" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Snapshot Ledger</CardTitle>
          <CardDescription>Rollback overlay state to a previous snapshot when needed, without mixing archival data with live editing.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <InlineNotice notice={notice} onDismiss={() => clearScopedNotice("history")} />
          {history.length === 0 ? (
            <EmptyState
              icon={History}
              title="No snapshots yet"
              description="Configuration changes will appear here as snapshots you can roll back to."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Created</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Snapshot</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{formatTimestamp(row.created_at)}</TableCell>
                    <TableCell>{row.action}</TableCell>
                    <TableCell className="font-mono text-xs">{row.id}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="outline" size="sm" onClick={() => onRollback(row.id)} disabled={saving}>
                        {saveAction === "rollback" && activeRollbackId === row.id ? (
                          <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" />
                        ) : (
                          <Undo2 className="h-3.5 w-3.5" />
                        )}
                        {saveAction === "rollback" && activeRollbackId === row.id ? "Rolling back..." : "Rollback"}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
