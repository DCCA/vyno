import { Activity, Database, Rocket } from "lucide-react"

import { useNavActions, useOnboardingState, useRunState, useScheduleState, useSourceState, useTimelineState } from "@/app/console-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MetricCard } from "@/components/ui/metric-card"
import { WorkspaceHeader } from "@/components/system/page-header"

export function DashboardPage() {
  const { runStatus } = useRunState()
  const { sourceHealth } = useSourceState()
  const { scheduleStatus } = useScheduleState()
  const { onboarding, setupPercent } = useOnboardingState()
  const { timelineRuns } = useTimelineState()
  const { navigateToSurface } = useNavActions()

  const onboardingDone = (onboarding?.lifecycle ?? "needs_setup") === "ready"

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Dashboard"
        description={
          onboardingDone
            ? "Automation-first home for the next scheduled digest, latest result, and follow-up actions."
            : "Finish setup here, then let the digest run automatically on its saved schedule."
        }
        badges={[
          { label: `latest: ${runStatus?.latest?.status ?? "n/a"}` },
          { label: `source alerts: ${sourceHealth.length}`, variant: sourceHealth.length > 0 ? "warning" : "success" },
          { label: onboardingDone ? "setup complete" : `setup: ${setupPercent}%`, variant: onboardingDone ? "success" : "warning" },
          {
            label: scheduleStatus?.enabled ? `next: ${scheduleStatus.next_run_at || "scheduled"}` : "schedule off",
            variant: scheduleStatus?.enabled ? "success" : "warning",
          },
        ]}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Latest run" value={runStatus?.latest?.status ?? "n/a"} detail={runStatus?.latest?.run_id || "No run yet"} />
        <MetricCard label="Source alerts" value={String(sourceHealth.length)} detail={sourceHealth.length > 0 ? "Needs attention" : "Healthy"} />
        <MetricCard
          label={onboardingDone ? "Next schedule" : "Setup completion"}
          value={onboardingDone ? (scheduleStatus?.next_run_at || "Scheduled") : `${setupPercent}%`}
          detail={onboardingDone ? "Automation window" : "Activation progress"}
        />
        <MetricCard label="Scheduled status" value={scheduleStatus?.enabled ? "On" : "Off"} detail={scheduleStatus?.enabled ? "Recurring" : "Manual only"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <Card>
          <CardHeader>
            <CardTitle className="font-display">{onboardingDone ? "Automation Control" : "Activation Focus"}</CardTitle>
            <CardDescription>
              {onboardingDone
                ? "The digest is now a recurring product workflow. Use this module to jump into interventions."
                : "Complete the setup path first, then the dashboard becomes your recurring product home."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {onboardingDone ? (
                <Button className="justify-between" onClick={() => navigateToSurface("run")}>
                  Open Run Center
                  <Rocket className="h-4 w-4" />
                </Button>
              ) : (
                <Button className="justify-between" onClick={() => navigateToSurface("onboarding")}>
                  Continue Setup
                  <Rocket className="h-4 w-4" />
                </Button>
              )}
              <Button variant="outline" className="justify-between" onClick={() => navigateToSurface("sources")}>
                Open Sources
                <Database className="h-4 w-4" />
              </Button>
              <Button variant="outline" className="justify-between" onClick={() => navigateToSurface("schedule")}>
                Manage Schedule
                <Rocket className="h-4 w-4" />
              </Button>
              <Button variant="outline" className="justify-between" onClick={() => navigateToSurface("timeline")}>
                Open Timeline
                <Activity className="h-4 w-4" />
              </Button>
            </div>
            <div className="rounded-[1.35rem] border border-border/80 bg-secondary/30 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={scheduleStatus?.enabled ? "success" : "warning"}>
                  {scheduleStatus?.enabled ? "Automation enabled" : "Automation not enabled"}
                </Badge>
                <Badge variant="outline">timeline runs {timelineRuns.length}</Badge>
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {scheduleStatus?.enabled
                  ? scheduleStatus.next_run_at
                    ? `Next scheduled digest: ${scheduleStatus.next_run_at}`
                    : "A recurring schedule is configured and waiting for its next window."
                  : "Automation is currently off. The product will keep depending on manual runs until a schedule is enabled."}
              </p>
              {scheduleStatus?.last_error ? <p className="mt-3 text-sm text-amber-800">{scheduleStatus.last_error}</p> : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="font-display">Current Posture</CardTitle>
            <CardDescription>High-signal readout for the workspace without opening deeper diagnostic screens.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <MetricCard variant="inline" label="Lifecycle" value={onboardingDone ? "Recurring use" : "Guided setup"} />
            <MetricCard variant="inline" label="Last completed run" value={runStatus?.latest_completed?.status ?? "n/a"} />
            <MetricCard variant="inline" label="Source health" value={sourceHealth.length > 0 ? `${sourceHealth.length} active alerts` : "No active alerts"} />
            <MetricCard variant="inline" label="Schedule" value={scheduleStatus?.enabled ? "Enabled" : "Disabled"} />
          </CardContent>
        </Card>
      </div>

      {sourceHealth.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="font-display">Source health alerts</CardTitle>
            <CardDescription>Recent ingestion failures that can reduce digest quality.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {sourceHealth.slice(0, 6).map((item) => (
              <div key={`${item.kind}:${item.source}`} className="rounded-[1.3rem] border border-amber-300/40 bg-amber-50/40 p-4">
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
