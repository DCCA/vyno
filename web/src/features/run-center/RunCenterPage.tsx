import { Loader2, Play, RefreshCcw } from "lucide-react"

import { useNavActions, useRunState, useUiState } from "@/app/console-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { MetricCard } from "@/components/ui/metric-card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"

export function RunCenterPage() {
  const { loading, saving, saveAction, localNotices, clearScopedNotice } = useUiState()
  const { runStatus, runPolicy, runNowModeOverride, setRunNowModeOverride, runNowLoading, onRunNow, onRefreshAll } = useRunState()
  const { navigateToSurface } = useNavActions()
  const notice = localNotices.run

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Run Center"
        description="Launch one-off runs, control temporary mode overrides, and inspect the latest completion posture."
        badges={[
          { label: `default mode: ${runPolicy.default_mode}` },
          { label: runStatus?.active ? `active: ${runStatus.active.run_id}` : "idle", variant: runStatus?.active ? "warning" : "success" },
        ]}
      />

      <InlineNotice notice={notice} onDismiss={() => clearScopedNotice("run")} />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard variant="compact" label="Run state" value={runStatus?.active ? "Running" : "Idle"} />
        <MetricCard variant="compact" label="Override" value={runPolicy.allow_run_override ? "Allowed" : "Locked"} />
        <MetricCard variant="compact" label="Latest result" value={runStatus?.latest_completed?.status ?? "n/a"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle className="font-display">Launch Deck</CardTitle>
            <CardDescription>Pick a temporary mode when allowed, then trigger or refresh operational state.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>One-time mode override</Label>
              <Select
                value={runNowModeOverride}
                onValueChange={setRunNowModeOverride}
                disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id) || !runPolicy.allow_run_override}
              >
                <SelectTrigger className="rounded-[1.1rem]">
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
            <div className="grid gap-3 md:grid-cols-2">
              <Button variant="outline" onClick={onRefreshAll} disabled={loading || saving}>
                {loading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <RefreshCcw className="h-4 w-4" />}
                {loading ? "Refreshing..." : "Refresh"}
              </Button>
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
            <CardDescription>Use this as the fast operational summary before opening deeper run diagnostics.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">run_id {runStatus?.latest_completed?.run_id ?? "-"}</Badge>
              <Badge variant="secondary">status {runStatus?.latest_completed?.status ?? "-"}</Badge>
              <Badge variant="outline">source errors {runStatus?.latest_completed?.source_error_count ?? 0}</Badge>
              <Badge variant="outline">summary errors {runStatus?.latest_completed?.summary_error_count ?? 0}</Badge>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigateToSurface("timeline")}>
              Open timeline details
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
