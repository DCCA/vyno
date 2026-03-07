import { Activity, Database, Rocket } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { WorkspaceHeader } from "@/components/system/page-header"
import type { RunStatus, ScheduleStatus, SourceHealthItem, TimelineRun } from "@/app/types"

export function DashboardPage({
  runStatus,
  sourceHealth,
  setupPercent,
  timelineRuns,
  scheduleStatus,
  onboardingDone,
  onOpenRun,
  onOpenSources,
  onOpenTimeline,
  onOpenOnboarding,
}: {
  runStatus: RunStatus | null
  sourceHealth: SourceHealthItem[]
  setupPercent: number
  timelineRuns: TimelineRun[]
  scheduleStatus: ScheduleStatus | null
  onboardingDone: boolean
  onOpenRun: () => void
  onOpenSources: () => void
  onOpenTimeline: () => void
  onOpenOnboarding: () => void
}) {
  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Dashboard"
        description={
          onboardingDone
            ? "Automation-first home for the next scheduled digest, latest result, and follow-up actions."
            : "Finish setup here, then let the digest run automatically every day."
        }
        badges={[
          { label: `latest: ${runStatus?.latest?.status ?? "n/a"}` },
          { label: `source alerts: ${sourceHealth.length}`, variant: sourceHealth.length > 0 ? "warning" : "success" },
          { label: `setup: ${setupPercent}%` },
          {
            label: scheduleStatus?.enabled ? `next: ${scheduleStatus.next_run_at || "scheduled"}` : "schedule off",
            variant: scheduleStatus?.enabled ? "success" : "warning",
          },
        ]}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Latest run" value={runStatus?.latest?.status ?? "n/a"} />
        <MetricCard label="Source alerts" value={String(sourceHealth.length)} />
        <MetricCard label="Setup completion" value={`${setupPercent}%`} />
        <MetricCard label="Scheduled status" value={scheduleStatus?.enabled ? "On" : "Off"} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">{onboardingDone ? "Automation Status" : "Next Step"}</CardTitle>
          <CardDescription>
            {onboardingDone
              ? "The digest should no longer depend on manual runs for daily operation."
              : "Finish guided setup before relying on the digest day to day."}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {onboardingDone ? (
            <Button className="justify-between" onClick={onOpenRun}>
              Open Run Center
              <Rocket className="h-4 w-4" />
            </Button>
          ) : (
            <Button className="justify-between" onClick={onOpenOnboarding}>
              Continue Setup
              <Rocket className="h-4 w-4" />
            </Button>
          )}
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

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Daily Automation</CardTitle>
          <CardDescription>
            {scheduleStatus?.enabled
              ? "Daily automation is enabled from the web app process."
              : "Enable a daily schedule during setup so the digest runs without manual launches."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex flex-wrap gap-2">
            <Badge variant={scheduleStatus?.enabled ? "success" : "warning"}>
              {scheduleStatus?.enabled ? "Automation enabled" : "Automation not enabled"}
            </Badge>
            <Badge variant="secondary">timeline runs: {timelineRuns.length}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {scheduleStatus?.enabled
              ? scheduleStatus.next_run_at
                ? `Next scheduled digest: ${scheduleStatus.next_run_at}`
                : "A daily schedule is configured."
              : "Setup is incomplete until a daily schedule is configured."}
          </p>
          {scheduleStatus?.last_error ? <p className="text-sm text-amber-800">{scheduleStatus.last_error}</p> : null}
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
