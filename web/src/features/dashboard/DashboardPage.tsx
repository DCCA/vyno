import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, Play, ThumbsDown, ThumbsUp } from "lucide-react"
import { useNavigate } from "react-router-dom"

import { useNavActions, useOnboardingState, useRunState, useScheduleState, useSourceState, useUiState } from "@/app/console-context"
import type { RunItem } from "@/app/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { formatStatus, formatTimestamp } from "@/lib/format"

export function DashboardPage() {
  const navigate = useNavigate()
  const { runStatus, latestRunItems, onLatestItemFeedback } = useRunState()
  const { sourceHealth } = useSourceState()
  const { scheduleStatus } = useScheduleState()
  const { onboarding, setupPercent } = useOnboardingState()
  const { loading, localNotices, clearScopedNotice } = useUiState()
  const { navigateToSurface } = useNavActions()

  const onboardingDone = (onboarding?.lifecycle ?? "needs_setup") === "ready"
  const latest = runStatus?.latest_completed ?? null
  const hasRuns = Boolean(latest)
  const hasSchedule = Boolean(scheduleStatus?.enabled)
  const hasHealthIssues = sourceHealth.length > 0
  const latestDegraded = Boolean(latest && latest.status !== "success")

  const mustReads = latestRunItems.filter((item) => item.section === "must_read")
  const skimCount = latestRunItems.filter((item) => item.section === "skim").length
  const videoCount = latestRunItems.filter((item) => item.section === "videos").length

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Dashboard"
        description={
          onboardingDone
            ? "The desk view: what the last edition picked, and whether the next one is on track."
            : "Finish setup here, then let the digest run automatically on its saved schedule."
        }
        badges={onboardingDone ? undefined : [{ label: `setup: ${setupPercent}%`, variant: "warning" }]}
      />

      <GuidanceCard
        hasRuns={hasRuns}
        hasSchedule={hasSchedule}
        hasHealthIssues={hasHealthIssues}
        healthCount={sourceHealth.length}
        nextRunAt={scheduleStatus?.next_run_at}
        onNavigate={navigateToSurface}
      />

      <Card>
        <CardContent className="py-4">
          {loading && !runStatus ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-5 w-28" />
                </div>
              ))}
            </div>
          ) : (
            <dl className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div>
                <dt className="text-[13px] font-medium uppercase tracking-[0.04em] text-muted-foreground">Latest run</dt>
                <dd className="mt-1 flex flex-wrap items-baseline gap-x-2">
                  <span className={`text-sm font-semibold ${latestDegraded ? "text-warning-ink" : "text-foreground"}`}>
                    {formatStatus(latest?.status)}
                  </span>
                  {latest ? (
                    <span className="font-mono text-[13px] tabular-nums text-muted-foreground">
                      {formatTimestamp(latest.started_at, "relative")}
                    </span>
                  ) : null}
                </dd>
              </div>
              <div>
                <dt className="text-[13px] font-medium uppercase tracking-[0.04em] text-muted-foreground">Next digest</dt>
                <dd className="mt-1 text-sm font-semibold text-foreground">
                  {hasSchedule ? (
                    <span className="font-mono tabular-nums" title={scheduleStatus?.next_run_at || undefined}>
                      {scheduleStatus?.next_run_at ? formatTimestamp(scheduleStatus.next_run_at, "relative") : "Scheduled"}
                    </span>
                  ) : (
                    "Manual only"
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-[13px] font-medium uppercase tracking-[0.04em] text-muted-foreground">Sources</dt>
                <dd className="mt-1 text-sm font-semibold">
                  {hasHealthIssues ? (
                    <span className="font-mono tabular-nums text-warning-ink">{sourceHealth.length} failing</span>
                  ) : (
                    <span className="text-foreground">All reporting</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-[13px] font-medium uppercase tracking-[0.04em] text-muted-foreground">Schedule</dt>
                <dd className="mt-1 text-sm font-semibold text-foreground">{hasSchedule ? "On" : "Off"}</dd>
              </div>
            </dl>
          )}

          {latestDegraded && latest ? (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning-ink" aria-hidden />
                <p className="text-sm text-muted-foreground">
                  <span className="font-semibold text-foreground">Run {formatStatus(latest.status).toLowerCase()}</span>
                  {" — "}
                  <span className="font-mono tabular-nums">{latest.source_error_count}</span> source error{latest.source_error_count !== 1 ? "s" : ""},{" "}
                  <span className="font-mono tabular-nums">{latest.summary_error_count}</span> summary error{latest.summary_error_count !== 1 ? "s" : ""}
                  {" · "}
                  <span className="font-mono text-[13px]">{latest.run_id}</span>
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={() => navigateToSurface("timeline")}>
                Diagnose in Timeline
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <InlineNotice notice={localNotices.dashboard} onDismiss={() => clearScopedNotice("dashboard")} />

      <Card>
        <CardHeader className="flex flex-row flex-wrap items-baseline justify-between gap-2 space-y-0">
          <div className="space-y-1">
            <CardTitle className="font-display text-lg">The latest edition</CardTitle>
            <CardDescription>
              {latest
                ? `Must-reads your editor selected ${formatTimestamp(latest.started_at, "relative")}. Grade them to sharpen its taste.`
                : "Once the first digest runs, its selections land here for review and feedback."}
            </CardDescription>
          </div>
          {latest ? (
            <Button variant="ghost" size="sm" onClick={() => navigateToSurface("timeline")}>
              Full edition
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          ) : null}
        </CardHeader>
        <CardContent>
          {loading && latestRunItems.length === 0 && hasRuns ? (
            <div className="space-y-4">
              {[0, 1, 2].map((i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              ))}
            </div>
          ) : mustReads.length > 0 ? (
            <>
              <ol className="max-w-[860px] space-y-1">
                {mustReads.map((item, index) => (
                  <EditionRow key={item.item_id} item={item} rank={index + 1} onFeedback={onLatestItemFeedback} />
                ))}
              </ol>
              <p className="mt-4 max-w-[60ch] border-t border-border pt-3 text-sm text-muted-foreground">
                Plus <span className="font-mono tabular-nums">{skimCount}</span> skim item{skimCount !== 1 ? "s" : ""} and{" "}
                <span className="font-mono tabular-nums">{videoCount}</span> video{videoCount !== 1 ? "s" : ""} in the delivered digest.
              </p>
            </>
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-3 py-2">
              <p className="text-sm text-muted-foreground">
                {hasRuns
                  ? "The latest run selected no must-read items. Open the Timeline to see why."
                  : "No editions yet. Run the digest once to put the first selection on the desk."}
              </p>
              <Button size="sm" onClick={() => navigateToSurface(hasRuns ? "timeline" : "run")}>
                {hasRuns ? "Open Timeline" : "Run first digest"}
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {hasHealthIssues ? (
        <Card>
          <CardHeader>
            <CardTitle className="font-display text-lg">Source health</CardTitle>
            <CardDescription>Failing sources reduce edition quality until fixed or muted.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul>
              {sourceHealth.slice(0, 6).map((item) => (
                <li
                  key={`${item.kind}:${item.source}`}
                  className="flex flex-wrap items-center justify-between gap-3 border-t border-border py-3 first:border-0 first:pt-0 last:pb-0"
                >
                  <div className="min-w-0 flex-1 space-y-0.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="truncate font-mono text-[13px]" title={item.source}>{item.source}</p>
                      <Badge variant="warning">{item.kind}</Badge>
                    </div>
                    <p className="max-w-[60ch] text-sm text-muted-foreground">
                      <span className="font-mono tabular-nums">{item.count}</span> recent failure{item.count !== 1 ? "s" : ""}
                      {item.hint ? ` · ${item.hint}` : ""}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/sources?q=${encodeURIComponent(item.source)}&status=failing`)}
                  >
                    View in Sources
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}

function EditionRow({
  item,
  rank,
  onFeedback,
}: {
  item: RunItem
  rank: number
  onFeedback: (itemId: string, label: "more_like_this" | "not_relevant" | "too_technical" | "repeat_source") => void
}) {
  return (
    <li className="group flex items-start gap-3 rounded-md px-2 py-2.5 transition-colors hover:bg-muted/50">
      <span className="mt-0.5 w-5 shrink-0 text-right font-mono text-[13px] tabular-nums text-muted-foreground" aria-hidden>
        {rank}
      </span>
      <div className="min-w-0 flex-1 space-y-0.5">
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="block text-sm font-medium leading-snug text-foreground underline-offset-2 hover:underline"
        >
          {item.title}
        </a>
        <p className="text-[13px] text-muted-foreground">
          <span className="font-mono">{item.source_family}</span>
          {" · score "}
          <span className="font-mono tabular-nums">{item.score_total}</span>
        </p>
        {item.summary ? <p className="line-clamp-2 max-w-[60ch] text-sm text-muted-foreground">{item.summary}</p> : null}
      </div>
      <div className="flex shrink-0 gap-1">
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          aria-label={`More like "${item.title}"`}
          title="More like this"
          onClick={() => onFeedback(item.item_id, "more_like_this")}
        >
          <ThumbsUp className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          aria-label={`Not relevant: "${item.title}"`}
          title="Not relevant"
          onClick={() => onFeedback(item.item_id, "not_relevant")}
        >
          <ThumbsDown className="h-3.5 w-3.5" />
        </Button>
      </div>
    </li>
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
      <Card className="border-warning/40 bg-warning/10">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-warning-ink" aria-hidden />
            <div>
              <p className="text-sm font-semibold">Review {healthCount} failing source{healthCount !== 1 ? "s" : ""} before the next run</p>
              <p className="text-sm text-foreground">Failing sources reduce digest quality. Fix or mute them to keep signal clean.</p>
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
            <Play className="h-5 w-5 shrink-0 text-accent" aria-hidden />
            <div>
              <p className="text-sm font-semibold">Run your first digest to see how sources perform</p>
              <p className="text-sm text-muted-foreground">A test run validates your setup and shows what the digest looks like.</p>
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
            <Clock3 className="h-5 w-5 shrink-0 text-primary" aria-hidden />
            <div>
              <p className="text-sm font-semibold">Enable a schedule so digests run automatically</p>
              <p className="text-sm text-muted-foreground">Without a schedule, digests only run when you manually trigger them.</p>
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

  // Healthy state stays quiet: no painted card, one calm line.
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-4">
        <CheckCircle2 className="h-5 w-5 shrink-0 text-success-ink" aria-hidden />
        <p className="text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">All good.</span>{" "}
          {nextRunAt ? (
            <>
              Next digest <span className="font-mono tabular-nums" title={nextRunAt}>{formatTimestamp(nextRunAt, "relative")}</span>. No action needed.
            </>
          ) : (
            "Schedule is enabled and waiting for the next window. No action needed."
          )}
        </p>
      </CardContent>
    </Card>
  )
}
