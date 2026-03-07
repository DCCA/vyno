import { Loader2, Undo2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import type { HistoryItem, Notice, SaveAction } from "@/app/types"

export function HistoryPage({
  notice,
  onDismissNotice,
  history,
  saveAction,
  activeRollbackId,
  saving,
  onRollback,
}: {
  notice: Notice | null | undefined
  onDismissNotice: () => void
  history: HistoryItem[]
  saveAction: SaveAction
  activeRollbackId: string
  saving: boolean
  onRollback: (snapshotId: string) => void
}) {
  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="History"
        description="Review config snapshots and perform rollback without competing with unrelated editing controls."
        badges={[{ label: `snapshots: ${history.length}` }]}
      />

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Snapshot History</CardTitle>
          <CardDescription>Rollback overlay state to a previous snapshot when needed.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <InlineNotice notice={notice} onDismiss={onDismissNotice} />
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
                  <TableCell>{row.created_at}</TableCell>
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
        </CardContent>
      </Card>
    </div>
  )
}
