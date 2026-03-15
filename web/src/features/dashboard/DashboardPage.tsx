import { Activity, AlertTriangle, ArrowRight, CheckCircle2, Clock3, Database, Play, Rocket } from "lucide-react"
import { useNavigate } from "react-router-dom"

import { useNavActions, useOnboardingState, useRunState, useScheduleState, useSourceState, useTimelineState } from "@/app/console-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MetricCard } from "@/components/ui/metric-card"
import { WorkspaceHeader } from "@/components/system/page-header"

export function DashboardPage() {
  const navigate = useNavigate()
  const { runStatus } = useRunState()
  const { sourceHealth } = useSourceState()
  const { scheduleStatus } = useScheduleState()
  const { onboarding, setupPercent } = useOnboardingState()
  const { timelineRuns } = useTimelineState()
  const { navigateToSurface } = useNavActions()

  const onboardingDone = (onboarding?.lifecycle ?? "needs_setup") === "ready"
  const hasRuns = Boolean(runStatus?.latest_completed)
  const hasSchedule = Boolean(scheduleStatus?.enabled)
  const hasHealthIssues = sourceHealth.length > 0

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
          { label: `source alerts: ${sourceHealth.length}`, variant: hasHealthIssues ? "warning" : "success" },
          { label: onboardingDone ? "setup complete" : `setup: ${setupPercent}%`, variant: onboardingDone ? "success" : "warning" },
          {
            label: hasSchedule ? `next: ${scheduleStatus?.next_run_at || "scheduled"}` : "schedule off",
            variant: hasSchedule ? "success" : "warning",
          },
        ]}
      />

      <GuidanceCard
        hasRuns={hasRuns}
        hasSchedule={hasSchedule}
        hasHealthIssues={hasHealthIssues}
        healthCount={sourceHealth.length}
        nextRunAt={scheduleStatus?.next_run_at}
        onNavigate={navigateToSurface}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Latest run" value={runStatus?.latest?.status ?? "n/a"} detail={runStatus?.latest?.run_id || "No run yet"} />
        <MetricCard label="Source alerts" value={String(sourceHealth.length)} detail={hasHealthIssues ? "Needs attention" : "Healthy"} />
        <MetricCard
          label={onboardingDone ? "Next schedule" : "Setup completion"}
          value={onboardingDone ? (scheduleStatus?.next_run_at || "Scheduled") : `${setupPercent}%`}
          detail={onboardingDone ? "Automation window" : "Activation progress"}
        />
        <MetricCard label="Scheduled status" value={hasSchedule ? "On" : "Off"} detail={hasSchedule ? "Recurring" : "Manual only"} />
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
                <Clock3 className="h-4 w-4" />
              </Button>
              <Button variant="outline" className="justify-between" onClick={() => navigateToSurface("timeline")}>
                Open Timeline
                <Activity className="h-4 w-4" />
              </Button>
            </div>
            <div className="rounded-[1.35rem] border border-border/80 bg-secondary/30 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={hasSchedule ? "success" : "warning"}>
                  {hasSchedule ? "Automation enabled" : "Automation not enabled"}
                </Badge>
                <Badge variant="outline">timeline runs {timelineRuns.length}</Badge>
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {hasSchedule
                  ? scheduleStatus?.next_run_at
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
            <MetricCard variant="inline" label="Source health" value={hasHealthIssues ? `${sourceHealth.length} active alerts` : "No active alerts"} />
            <MetricCard variant="inline" label="Schedule" value={hasSchedule ? "Enabled" : "Disabled"} />
          </CardContent>
        </Card>
      </div>

      {hasHealthIssues ? (
        <Card>
          <CardHeader>
            <CardTitle className="font-display">Source health alerts</CardTitle>
            <CardDescription>Recent ingestion failures that can reduce digest quality.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {sourceHealth.slice(0, 6).map((item) => (
              <div key={`${item.kind}:${item.source}`} className="rounded-[1.3rem] border border-amber-300/40 bg-amber-50/40 p-4 dark:border-amber-700/30 dark:bg-amber-950/20">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="truncate font-mono text-[11px]">{item.source}</p>
                    <p className="text-xs text-muted-foreground">{item.count} failures in recent runs</p>
                    <p className="text-xs text-muted-foreground">{item.hint || "No hint available"}</p>
                  </div>
                  <Badge variant="warning">{item.kind}</Badge>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={() => navigate(`/sources?q=${encodeURIComponent(item.source)}&status=failing`)}
                >
                  View in Sources
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
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

function GuidanceCard({
  hasRuns,
  hasSchedule,
  hasHealthIssues,
  healthCount,
  nextRunAt,
  onNavigate,
}: {
  hasRuns: boolean
  hasSchedule: boolean
  hasHealthIssues: boolean
  healthCount: number
  nextRunAt: string | undefined
  onNavigate: (surface: "run" | "schedule" | "sources") => void
}) {
  if (hasHealthIssues) {
    return (
      <Card className="border-amber-300/50 bg-amber-50/30 dark:border-amber-700/30 dark:bg-amber-950/15">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
            <div>
              <p className="text-sm font-semibold">Review {healthCount} failing source{healthCount !== 1 ? "s" : ""} before the next run</p>
              <p className="text-xs text-muted-foreground">Failing sources reduce digest quality. Fix or mute them to keep signal clean.</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => onNavigate("sources")}>
            Open Sources
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!hasRuns) {
    return (
      <Card className="border-accent/30 bg-accent/5">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-3">
            <Play className="h-5 w-5 shrink-0 text-accent" />
            <div>
              <p className="text-sm font-semibold">Run your first digest to see how sources perform</p>
              <p className="text-xs text-muted-foreground">A test run validates your setup and shows what the digest looks like.</p>
            </div>
          </div>
          <Button size="sm" onClick={() => onNavigate("run")}>
            Open Run Center
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!hasSchedule) {
    return (
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-3">
            <Clock3 className="h-5 w-5 shrink-0 text-primary" />
            <div>
              <p className="text-sm font-semibold">Enable a schedule so digests run automatically</p>
              <p className="text-xs text-muted-foreground">Without a schedule, digests only run when you manually trigger them.</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => onNavigate("schedule")}>
            Manage Schedule
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-emerald-200/60 bg-emerald-50/30 dark:border-emerald-800/30 dark:bg-emerald-950/15">
      <CardContent className="flex items-center gap-3 py-4">
        <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
        <div>
          <p className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">All good</p>
          <p className="text-xs text-emerald-700 dark:text-emerald-400">
            {nextRunAt ? `Next digest runs at ${nextRunAt}.` : "Schedule is enabled and waiting for the next window."}
            {" "}No action needed.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
