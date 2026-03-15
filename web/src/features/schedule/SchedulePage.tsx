import { useMemo } from "react"
import { AlertTriangle, Clock3, Play, Rocket } from "lucide-react"

import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MetricCard } from "@/components/ui/metric-card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import type { Notice, SaveAction, ScheduleConfig, ScheduleStatus } from "@/app/types"

export function SchedulePage({
  notice,
  onDismissNotice,
  lifecycle,
  scheduleDraft,
  scheduleDirty,
  scheduleStatus,
  saveAction,
  saving,
  onChangeScheduleField,
  onSaveSchedule,
  onRunNow,
  onOpenTimeline,
  onOpenRun,
  onOpenOnboarding,
}: {
  notice: Notice | null | undefined
  onDismissNotice: () => void
  lifecycle: "needs_setup" | "ready"
  scheduleDraft: ScheduleConfig
  scheduleDirty: boolean
  scheduleStatus: ScheduleStatus | null
  saveAction: SaveAction
  saving: boolean
  onChangeScheduleField: (field: keyof ScheduleConfig, value: string | boolean | number) => void
  onSaveSchedule: () => void
  onRunNow: () => void
  onOpenTimeline: () => void
  onOpenRun: () => void
  onOpenOnboarding: () => void
}) {
  const enabled = scheduleDraft.enabled
  const schedulerState = schedulerStateMeta(scheduleStatus)
  const cadenceSummary = describeSchedule(scheduleDraft)
  const timezoneOptions = useMemo(() => {
    const intlWithSupportedValues = Intl as typeof Intl & { supportedValuesOf?: (key: string) => string[] }
    if (typeof Intl === "undefined" || typeof intlWithSupportedValues.supportedValuesOf !== "function") return []
    try {
      return intlWithSupportedValues.supportedValuesOf("timeZone")
    } catch {
      return []
    }
  }, [])

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Schedule"
        description={
          lifecycle === "ready"
            ? "Manage background automation directly from the product, including hourly cadence and quiet hours."
            : "Finish setup by configuring when the web app should run the digest automatically without relying on an open terminal."
        }
        badges={[
          { label: enabled ? "automation enabled" : "automation paused", variant: enabled ? "success" : "warning" },
          { label: `cadence: ${scheduleDraft.cadence}`, variant: "secondary" },
          { label: `state: ${schedulerState.label}`, variant: schedulerState.variant },
          {
            label: scheduleStatus?.next_run_at ? `next: ${formatTimestampBadge(scheduleStatus.next_run_at)}` : "next run not scheduled",
            variant: scheduleStatus?.enabled ? "secondary" : "warning",
          },
        ]}
        actions={
          <div className="flex flex-wrap gap-2 lg:justify-end">
            <Button variant="outline" onClick={onOpenTimeline}>
              <Clock3 className="h-4 w-4" />
              Open Timeline
            </Button>
            <Button onClick={onRunNow} disabled={saving || Boolean(scheduleStatus?.active_run_id)}>
              <Play className="h-4 w-4" />
              Run now
            </Button>
          </div>
        }
      />

      <InlineNotice notice={notice} onDismiss={onDismissNotice} />

      {lifecycle === "needs_setup" ? (
        <Card>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 py-5">
            <div className="space-y-1">
              <p className="text-sm font-semibold">Setup mode</p>
              <p className="text-sm text-muted-foreground">
                This same workspace is available during setup, but it stays out of the main menu until activation is complete.
              </p>
            </div>
            <Button variant="outline" onClick={onOpenOnboarding}>
              Back to setup guide
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader>
            <CardTitle className="font-display">Automation Status</CardTitle>
            <CardDescription>High-signal readout for the current automation posture before you change anything.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            <MetricCard variant="compact"
              label="Next run"
              value={formatTimestamp(scheduleStatus?.next_run_at) || "Not scheduled"}
              detail={enabled ? cadenceSummary : "Automation is paused"}
            />
            <MetricCard variant="compact"
              label="Last result"
              value={scheduleStatus?.last_result || "No scheduled run yet"}
              detail={formatTimestamp(scheduleStatus?.last_triggered_at) || "No prior trigger recorded"}
            />
            <MetricCard variant="compact"
              label="Scheduler state"
              value={schedulerState.title}
              detail={schedulerState.detail}
            />
            <MetricCard variant="compact"
              label="Active run"
              value={scheduleStatus?.active_run_id || "None"}
              detail={scheduleStatus?.active_run_id ? "A digest is currently running." : "No current automation run."}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="font-display">Schedule Controls</CardTitle>
            <CardDescription>Save, pause, or resume the cadence used by the background scheduler service.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-[1.25rem] border border-border/80 bg-secondary/25 p-4">
              <div className="space-y-1">
                <p className="text-sm font-semibold">Automation enabled</p>
                <p className="text-sm text-muted-foreground">Pause or resume the schedule without deleting its cadence, quiet hours, or timezone.</p>
              </div>
              <Switch
                checked={enabled}
                onCheckedChange={(checked) => onChangeScheduleField("enabled", checked)}
                aria-label="Enable or pause the schedule"
              />
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2 rounded-[1.25rem] border border-border/80 bg-secondary/20 p-4">
                <Label htmlFor="schedule-cadence">Cadence</Label>
                <Select
                  value={scheduleDraft.cadence}
                  onValueChange={(value) => onChangeScheduleField("cadence", value === "hourly" ? "hourly" : "daily")}
                >
                  <SelectTrigger id="schedule-cadence">
                    <SelectValue placeholder="Choose cadence" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hourly">Hourly</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 rounded-[1.25rem] border border-border/80 bg-secondary/20 p-4">
                <Label htmlFor="schedule-timezone">Timezone</Label>
                <Input
                  id="schedule-timezone"
                  list={timezoneOptions.length > 0 ? "schedule-timezone-options" : undefined}
                  value={scheduleDraft.timezone}
                  onChange={(event) => onChangeScheduleField("timezone", event.target.value)}
                  placeholder="America/Sao_Paulo"
                />
                {timezoneOptions.length > 0 ? (
                  <datalist id="schedule-timezone-options">
                    {timezoneOptions.map((option: string) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                ) : null}
              </div>
            </div>

            {scheduleDraft.cadence === "hourly" ? (
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2 rounded-[1.25rem] border border-border/80 bg-secondary/20 p-4">
                  <Label htmlFor="schedule-hourly-minute">Minute past the hour</Label>
                  <Input
                    id="schedule-hourly-minute"
                    type="number"
                    min={0}
                    max={59}
                    value={String(scheduleDraft.hourly_minute)}
                    onChange={(event) => onChangeScheduleField("hourly_minute", Number(event.target.value || 0))}
                  />
                </div>
                <div className="space-y-2 rounded-[1.25rem] border border-border/80 bg-secondary/20 p-4">
                  <p className="text-sm font-semibold">Hourly preview</p>
                  <p className="text-sm text-muted-foreground">
                    Runs every hour at :{String(scheduleDraft.hourly_minute).padStart(2, "0")} in {scheduleDraft.timezone || "UTC"}.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-2 rounded-[1.25rem] border border-border/80 bg-secondary/20 p-4">
                <Label htmlFor="schedule-daily-time">Daily time</Label>
                <Input
                  id="schedule-daily-time"
                  type="time"
                  value={scheduleDraft.time_local}
                  onChange={(event) => onChangeScheduleField("time_local", event.target.value)}
                />
              </div>
            )}

            <div className="space-y-4 rounded-[1.25rem] border border-border/80 bg-secondary/20 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-sm font-semibold">Quiet hours</p>
                  <p className="text-sm text-muted-foreground">Skip runs during a local-time blackout window instead of disturbing the user late at night.</p>
                </div>
                <Switch
                  checked={scheduleDraft.quiet_hours_enabled}
                  onCheckedChange={(checked) => onChangeScheduleField("quiet_hours_enabled", checked)}
                  aria-label="Enable quiet hours"
                />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="schedule-quiet-start">Quiet start</Label>
                  <Input
                    id="schedule-quiet-start"
                    type="time"
                    value={scheduleDraft.quiet_start_local}
                    onChange={(event) => onChangeScheduleField("quiet_start_local", event.target.value)}
                    disabled={!scheduleDraft.quiet_hours_enabled}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="schedule-quiet-end">Quiet end</Label>
                  <Input
                    id="schedule-quiet-end"
                    type="time"
                    value={scheduleDraft.quiet_end_local}
                    onChange={(event) => onChangeScheduleField("quiet_end_local", event.target.value)}
                    disabled={!scheduleDraft.quiet_hours_enabled}
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button onClick={onSaveSchedule} disabled={saving || !scheduleDirty}>
                <Clock3 className="h-4 w-4" />
                {saveAction === "schedule-save" ? "Saving..." : enabled ? "Save schedule" : "Save paused state"}
              </Button>
              <Button variant="outline" onClick={onOpenRun}>
                <Rocket className="h-4 w-4" />
                Open Run Center
              </Button>
              {scheduleDirty ? <Badge variant="warning">Unsaved changes</Badge> : <Badge variant="success">Saved</Badge>}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader>
            <CardTitle className="font-display">What Happens Next</CardTitle>
            <CardDescription>Explain the current schedule in plain language before the user leaves the page.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>
              {enabled
                ? `${cadenceSummary} while the background scheduler service is running.`
                : "The digest is currently in manual mode because scheduled automation is paused."}
            </p>
            <p>
              {scheduleStatus?.next_run_at
                ? `Next allowed run: ${scheduleStatus.next_run_at}`
                : "No next run is currently scheduled."}
            </p>
            <p>If the scheduler is stopped, no digest will run until the background service is started again.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="font-display">Issues And Recovery</CardTitle>
            <CardDescription>Keep scheduler problems and next-step guidance visible near the controls.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {scheduleStatus?.last_error ? (
              <div className="rounded-[1.25rem] border border-amber-300/50 bg-amber-50/50 p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-700" />
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-amber-900">Latest scheduler issue</p>
                    <p className="text-sm text-amber-800">{scheduleStatus.last_error}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-[1.25rem] border border-emerald-200/70 bg-emerald-50/55 p-4">
                <p className="text-sm font-semibold text-emerald-900">No active scheduler issue</p>
                <p className="mt-1 text-sm text-emerald-800">Automation is clear to continue with the current schedule.</p>
              </div>
            )}

            <div className="space-y-2 rounded-[1.25rem] border border-border/80 bg-secondary/20 p-4">
              <p className="text-sm font-semibold">Current state guidance</p>
              <p className="text-sm text-muted-foreground">{schedulerState.nextStep}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


function schedulerStateMeta(status: ScheduleStatus | null): {
  label: string
  title: string
  detail: string
  nextStep: string
  variant: "success" | "warning" | "secondary"
} {
  const state = status?.scheduler_status || "disabled"
  if (state === "running") {
    return {
      label: "running",
      title: "Running",
      detail: "Ready for the next allowed schedule window.",
      nextStep: "No action needed. You can leave the schedule as-is or run a digest immediately for testing.",
      variant: "success",
    }
  }
  if (state === "quiet_hours") {
    return {
      label: "quiet hours",
      title: "Quiet Hours",
      detail: "The scheduler is intentionally holding runs until the quiet-hours window ends.",
      nextStep: "No action is required unless you want to shorten or disable quiet hours.",
      variant: "secondary",
    }
  }
  if (state === "run_active") {
    return {
      label: "run active",
      title: "Run Active",
      detail: "A digest is currently running under the scheduler or manual controls.",
      nextStep: "Wait for the current digest to finish before expecting another scheduled trigger.",
      variant: "warning",
    }
  }
  if (state === "waiting_for_run_lock") {
    return {
      label: "waiting for run lock",
      title: "Waiting",
      detail: "The scheduled digest could not start because another run was already active.",
      nextStep: "Open Run Center or Timeline to inspect the current run and let it finish before the next scheduled attempt.",
      variant: "warning",
    }
  }
  if (state === "error") {
    return {
      label: "error",
      title: "Error",
      detail: "The scheduler hit an issue while preparing or starting automation.",
      nextStep: "Review the latest scheduler issue below, then adjust the schedule or inspect the run diagnostics.",
      variant: "warning",
    }
  }
  return {
    label: "disabled",
    title: "Paused",
    detail: "Automation is disabled and the product will depend on manual runs.",
    nextStep: "Enable the schedule and save it when you are ready to return to recurring automation.",
    variant: "secondary",
  }
}

function describeSchedule(schedule: ScheduleConfig): string {
  if (schedule.cadence === "hourly") {
    const base = `The digest will run every hour at :${String(schedule.hourly_minute).padStart(2, "0")} in ${schedule.timezone}.`
    if (!schedule.quiet_hours_enabled) return base
    return `${base} Quiet hours suppress runs from ${schedule.quiet_start_local} to ${schedule.quiet_end_local}.`
  }
  const base = `The digest will run every day at ${schedule.time_local} in ${schedule.timezone}.`
  if (!schedule.quiet_hours_enabled) return base
  return `${base} Quiet hours suppress runs from ${schedule.quiet_start_local} to ${schedule.quiet_end_local}.`
}

function formatTimestamp(value: string | undefined): string {
  if (!value) return ""
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString()
}

function formatTimestampBadge(value: string | undefined): string {
  if (!value) return ""
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}
