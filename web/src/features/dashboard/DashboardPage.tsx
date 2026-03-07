import { Activity, Database, Rocket } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { WorkspaceHeader } from "@/components/system/page-header"
import type { RunStatus, SourceHealthItem, TimelineRun } from "@/app/types"

export function DashboardPage({
  runStatus,
  sourceHealth,
  setupPercent,
  timelineRuns,
  onOpenRun,
  onOpenSources,
  onOpenTimeline,
}: {
  runStatus: RunStatus | null
  sourceHealth: SourceHealthItem[]
  setupPercent: number
  timelineRuns: TimelineRun[]
  onOpenRun: () => void
  onOpenSources: () => void
  onOpenTimeline: () => void
}) {
  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Dashboard"
        description="Summary-first operator workspace for current run health, setup readiness, and next actions."
        badges={[
          { label: `latest: ${runStatus?.latest?.status ?? "n/a"}` },
          { label: `source alerts: ${sourceHealth.length}`, variant: sourceHealth.length > 0 ? "warning" : "success" },
          { label: `setup: ${setupPercent}%` },
          { label: `timeline runs: ${timelineRuns.length}` },
        ]}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Latest run" value={runStatus?.latest?.status ?? "n/a"} />
        <MetricCard label="Source alerts" value={String(sourceHealth.length)} />
        <MetricCard label="Setup completion" value={`${setupPercent}%`} />
        <MetricCard label="Timeline runs" value={String(timelineRuns.length)} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Operational Focus</CardTitle>
          <CardDescription>Start with summary, then move into the workspace that owns the task.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <Button className="justify-between" onClick={onOpenRun}>
            Open Run Center
            <Rocket className="h-4 w-4" />
          </Button>
          <Button variant="outline" className="justify-between" onClick={onOpenSources}>
            Open Sources
            <Database className="h-4 w-4" />
          </Button>
          <Button variant="outline" className="justify-between" onClick={onOpenTimeline}>
            Open Timeline
            <Activity className="h-4 w-4" />
          </Button>
        </CardContent>
      </Card>

      {sourceHealth.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="font-display">Source health alerts</CardTitle>
            <CardDescription>Recent ingestion failures that can reduce digest quality.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {sourceHealth.slice(0, 6).map((item) => (
              <div key={`${item.kind}:${item.source}`} className="rounded-lg border border-amber-300/40 bg-amber-50/30 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="truncate font-mono text-[11px]">{item.source}</p>
                    <p className="text-xs text-muted-foreground">{item.count} failures in recent runs</p>
                    <p className="text-xs text-muted-foreground">{item.hint || "No hint available"}</p>
                  </div>
                  <Badge variant="warning">{item.kind}</Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="font-display">System calm</CardTitle>
            <CardDescription>No current source-health alerts are competing for attention.</CardDescription>
          </CardHeader>
        </Card>
      )}
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card className="border-border/80 bg-card/95">
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="font-display text-2xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  )
}
