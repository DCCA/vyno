import { Loader2, Play, RefreshCcw } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import type { Notice, RunPolicy, RunStatus, SaveAction } from "@/app/types"

export function RunCenterPage({
  notice,
  onDismissNotice,
  runNowModeOverride,
  setRunNowModeOverride,
  runPolicy,
  runStatus,
  saving,
  runNowLoading,
  loading,
  saveAction,
  onRefreshAll,
  onRunNow,
  onOpenTimeline,
}: {
  notice: Notice | null | undefined
  onDismissNotice: () => void
  runNowModeOverride: string
  setRunNowModeOverride: (value: string) => void
  runPolicy: RunPolicy
  runStatus: RunStatus | null
  saving: boolean
  runNowLoading: boolean
  loading: boolean
  saveAction: SaveAction
  onRefreshAll: () => void
  onRunNow: () => void
  onOpenTimeline: () => void
}) {
  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Run Center"
        description="Manual runs, mode overrides, and live progress visibility in a dedicated execution workspace."
        badges={[
          { label: `default mode: ${runPolicy.default_mode}` },
          { label: runStatus?.active ? `active: ${runStatus.active.run_id}` : "idle", variant: runStatus?.active ? "warning" : "success" },
        ]}
      />

      <InlineNotice notice={notice} onDismiss={onDismissNotice} />

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Run Controls</CardTitle>
          <CardDescription>Choose a one-time mode override when allowed, then start or refresh run state.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-[1fr,auto,auto]">
          <div className="space-y-2">
            <Label>One-time mode override</Label>
            <Select
              value={runNowModeOverride}
              onValueChange={setRunNowModeOverride}
              disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id) || !runPolicy.allow_run_override}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Run now: default ({runPolicy.default_mode})</SelectItem>
                <SelectItem value="fresh_only">Run now: fresh_only</SelectItem>
                <SelectItem value="balanced">Run now: balanced</SelectItem>
                <SelectItem value="replay_recent">Run now: replay_recent</SelectItem>
                <SelectItem value="backfill">Run now: backfill</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            <Button variant="outline" onClick={onRefreshAll} disabled={loading || saving}>
              {loading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <RefreshCcw className="h-4 w-4" />}
              {loading ? "Refreshing..." : "Refresh"}
            </Button>
          </div>
          <div className="flex items-end">
            <Button onClick={onRunNow} disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id)}>
              {runNowLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
              {runNowLoading ? "Starting..." : "Run now"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Latest Completion Snapshot</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Badge variant="secondary">run_id: {runStatus?.latest_completed?.run_id ?? "-"}</Badge>
          <Badge variant="secondary">status: {runStatus?.latest_completed?.status ?? "-"}</Badge>
          <Badge variant="secondary">source errors: {runStatus?.latest_completed?.source_error_count ?? 0}</Badge>
          <Badge variant="secondary">summary errors: {runStatus?.latest_completed?.summary_error_count ?? 0}</Badge>
          <Button variant="outline" size="sm" onClick={onOpenTimeline}>
            Open timeline details
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
