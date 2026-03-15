import { Activity, Loader2, RefreshCcw, Save } from "lucide-react"

import { useTimelineState, useUiState } from "@/app/console-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { MetricCard } from "@/components/ui/metric-card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { formatElapsed } from "@/lib/console-utils"
import { formatTimestamp } from "@/lib/format"

export function TimelinePage() {
  const { saving, saveAction, localNotices, clearScopedNotice } = useUiState()
  const {
    timelineRunId, setTimelineRunId, timelineRuns, timelineStageFilter, setTimelineStageFilter,
    timelineStageOptions, timelineSeverityFilter, setTimelineSeverityFilter, timelineOrder, setTimelineOrder,
    timelineLivePaused, setTimelineLivePaused, timelineSummary, timelineRunItems, timelineRunArtifacts,
    timelineEvents, timelineSelectedEventId, setTimelineSelectedEventId, selectedTimelineEvent,
    timelineNoteAuthor, setTimelineNoteAuthor, timelineNoteText, setTimelineNoteText,
    onRefreshTimeline, onExportTimeline, onAddTimelineNote, timelineNotes, onSubmitItemFeedback,
  } = useTimelineState()
  const notice = localNotices.timeline
  const telegramArtifact = timelineRunArtifacts.find((row) => row.channel === "telegram")
  const obsidianArtifact = timelineRunArtifacts.find((row) => row.channel === "obsidian")
  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Timeline"
        description="Inspect live and historical run behavior through a modular event browser with summary-first diagnostics."
        badges={[
          { label: timelineRunId ? `run: ${timelineRunId}` : "no run selected" },
          { label: timelineSummary?.mode?.name ? `mode: ${timelineSummary.mode.name}` : "mode: n/a" },
          { label: timelineSummary?.strictness_level ? `strictness: ${timelineSummary.strictness_level}` : "strictness: n/a", variant: timelineSummary?.strictness_level === "high" ? "warning" : "secondary" },
        ]}
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard variant="compact" label="Run selected" value={timelineRunId || "n/a"} />
        <MetricCard variant="compact" label="Events" value={timelineSummary ? String(timelineSummary.event_count) : "0"} />
        <MetricCard variant="compact" label="Errors" value={timelineSummary ? String(timelineSummary.error_event_count) : "0"} />
        <MetricCard variant="compact" label="Duration" value={timelineSummary ? formatElapsed(timelineSummary.duration_s) : "n/a"} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Run Browser</CardTitle>
          <CardDescription>Filter and inspect a run as a structured browser rather than a raw operations log.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <InlineNotice notice={notice} onDismiss={() => clearScopedNotice("timeline")} />
          <div className="grid gap-3 md:grid-cols-[2fr,1fr,1fr,1fr,auto]">
            <div className="space-y-2">
              <Label>Run</Label>
              <Select value={timelineRunId} onValueChange={setTimelineRunId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select run" />
                </SelectTrigger>
                <SelectContent>
                  {timelineRuns.map((row) => (
                    <SelectItem key={row.run_id} value={row.run_id}>
                      {row.run_id} ({row.status})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Stage</Label>
              <Select value={timelineStageFilter} onValueChange={setTimelineStageFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">all</SelectItem>
                  {timelineStageOptions.map((stage) => (
                    <SelectItem key={stage} value={stage}>
                      {stage}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Severity</Label>
              <Select value={timelineSeverityFilter} onValueChange={setTimelineSeverityFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">all</SelectItem>
                  <SelectItem value="info">info</SelectItem>
                  <SelectItem value="warn">warn</SelectItem>
                  <SelectItem value="error">error</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Order</Label>
              <Select value={timelineOrder} onValueChange={(value) => setTimelineOrder(value === "asc" ? "asc" : "desc")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">newest first</SelectItem>
                  <SelectItem value="asc">oldest first</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end gap-2">
              <Button variant="outline" onClick={onRefreshTimeline} disabled={saving || !timelineRunId}>
                {saveAction === "timeline-refresh" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <RefreshCcw className="h-4 w-4" />}
                {saveAction === "timeline-refresh" ? "Refreshing..." : "Refresh"}
              </Button>
              <Button variant="outline" onClick={onExportTimeline} disabled={saving || !timelineRunId}>
                {saveAction === "timeline-export" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Save className="h-4 w-4" />}
                {saveAction === "timeline-export" ? "Exporting..." : "Export JSON"}
              </Button>
            </div>
            <div className="col-span-full flex items-center justify-between rounded-md border bg-muted/20 p-3">
              <div>
                <p className="text-sm font-medium">Live polling</p>
                <p className="text-xs text-muted-foreground">Automatic refresh for active runs while Timeline is open.</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">{timelineLivePaused ? "Paused" : "Live"}</span>
                <Switch
                  aria-label="Toggle live timeline polling"
                  checked={!timelineLivePaused}
                  onCheckedChange={(checked) => setTimelineLivePaused(!checked)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="font-display">Timeline Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {timelineSummary ? (
                <div className="space-y-3">
                  <div className="flex flex-wrap gap-2">
                    <Badge variant={timelineSummary.status === "success" ? "success" : timelineSummary.status === "partial" ? "warning" : "outline"}>
                      status: {timelineSummary.status}
                    </Badge>
                    <Badge variant="secondary">events: {timelineSummary.event_count}</Badge>
                    <Badge variant="secondary">errors: {timelineSummary.error_event_count}</Badge>
                    <Badge variant="secondary">warnings: {timelineSummary.warn_event_count}</Badge>
                    <Badge variant="secondary">duration: {formatElapsed(timelineSummary.duration_s)}</Badge>
                    <Badge variant="secondary">
                      M/S/V: {timelineSummary.must_read_count}/{timelineSummary.skim_count}/{timelineSummary.video_count}
                    </Badge>
                    {timelineSummary.mode?.name ? <Badge variant="secondary">mode: {timelineSummary.mode.name}</Badge> : null}
                    {timelineSummary.strictness_level ? (
                      <Badge variant={timelineSummary.strictness_level === "high" ? "warning" : timelineSummary.strictness_level === "medium" ? "outline" : "success"}>
                        strictness: {timelineSummary.strictness_level}
                        {typeof timelineSummary.strictness_score === "number" ? ` (${timelineSummary.strictness_score})` : ""}
                      </Badge>
                    ) : null}
                  </div>

                  {timelineSummary.filter_funnel ? (
                    <div className="rounded-md border bg-muted/20 p-3 text-xs">
                      <p className="mb-1 font-semibold text-foreground">Filter funnel</p>
                      <p className="font-mono text-muted-foreground">
                        fetched={timelineSummary.filter_funnel.fetched} - post_window={timelineSummary.filter_funnel.post_window} - post_seen=
                        {timelineSummary.filter_funnel.post_seen} - post_block={timelineSummary.filter_funnel.post_block} - selected=
                        {timelineSummary.filter_funnel.selected}
                      </p>
                    </div>
                  ) : null}

                  {(timelineSummary.restriction_reasons ?? []).length > 0 ? (
                    <div className="space-y-1 text-xs">
                      <p className="font-semibold text-foreground">Top restriction reasons</p>
                      {(timelineSummary.restriction_reasons ?? []).map((reason) => (
                        <p key={`${reason.key}:${reason.dropped}`} className="text-muted-foreground">
                          {reason.label}: dropped {reason.dropped} ({reason.ratio_pct}%)
                        </p>
                      ))}
                    </div>
                  ) : null}

                  {(timelineSummary.recommendations ?? []).length > 0 ? (
                    <div className="space-y-1 text-xs">
                      <p className="font-semibold text-foreground">Recommended actions</p>
                      {(timelineSummary.recommendations ?? []).map((line) => (
                        <p key={line} className="text-muted-foreground">
                          {line}
                        </p>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No summary available for this run.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-display">Delivered Digest Review</CardTitle>
              <CardDescription>Review the archived digest exactly as rendered and capture item-level feedback for future runs.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 xl:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-semibold">Telegram archive</p>
                  {telegramArtifact ? (
                    <pre className="max-h-[280px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs whitespace-pre-wrap">
                      {telegramArtifact.content}
                    </pre>
                  ) : (
                    <p className="text-sm text-muted-foreground">No archived Telegram payload for this run.</p>
                  )}
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-semibold">Obsidian archive</p>
                  {obsidianArtifact ? (
                    <pre className="max-h-[280px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs whitespace-pre-wrap">
                      {obsidianArtifact.content}
                    </pre>
                  ) : (
                    <p className="text-sm text-muted-foreground">No archived Obsidian note for this run.</p>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm font-semibold">Selected items</p>
                {timelineRunItems.length > 0 ? (
                  timelineRunItems.map((row) => (
                    <div key={`${row.run_id}:${row.item_id}`} className="rounded-md border bg-muted/10 p-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="secondary">{row.section}</Badge>
                        <span>rank {row.section_rank}</span>
                        <span>source {row.source_family}</span>
                        <span>score {row.adjusted_total}</span>
                        {row.raw_total !== row.adjusted_total ? <span>raw {row.raw_total}</span> : null}
                        {row.score_mode === "legacy_raw" ? <Badge variant="outline">legacy score</Badge> : null}
                      </div>
                      <p className="mt-2 text-sm font-semibold">{row.title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{row.summary || row.description || row.url}</p>
                      {Object.keys(row.adjustment_breakdown ?? {}).length > 0 ? (
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                          {Object.entries(row.adjustment_breakdown).map(([key, value]) => (
                            <span key={key}>
                              {formatAdjustmentLabel(key)} {value > 0 ? "+" : ""}
                              {value}
                            </span>
                          ))}
                        </div>
                      ) : null}
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" onClick={() => onSubmitItemFeedback(row.item_id, "more_like_this")}>
                          More like this
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => onSubmitItemFeedback(row.item_id, "not_relevant")}>
                          Not relevant
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => onSubmitItemFeedback(row.item_id, "too_technical")}>
                          Too technical
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => onSubmitItemFeedback(row.item_id, "repeat_source")}>
                          Repeat source
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <EmptyState title="No items archived" description="Selected items will appear here after the run delivers." />
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-display">Timeline Events</CardTitle>
            </CardHeader>
            <CardContent>
              {timelineEvents.length === 0 ? (
                <EmptyState
                  icon={Activity}
                  title="No events"
                  description="No events match the selected filters for this run."
                />
              ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>Time (UTC)</TableHead>
                    <TableHead>Stage</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Message</TableHead>
                    <TableHead>Elapsed</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {timelineEvents.map((row) => (
                    <TableRow
                      key={`${row.run_id}:${row.id}`}
                      className="cursor-pointer"
                      data-state={row.id === timelineSelectedEventId ? "selected" : undefined}
                      onClick={() => setTimelineSelectedEventId(row.id)}
                    >
                      <TableCell>{row.event_index}</TableCell>
                      <TableCell className="font-mono text-xs">{formatTimestamp(row.ts_utc)}</TableCell>
                      <TableCell className="font-mono text-xs">{row.stage}</TableCell>
                      <TableCell>
                        <Badge variant={row.severity === "error" ? "warning" : row.severity === "warn" ? "outline" : "secondary"}>
                          {row.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs">{row.message}</TableCell>
                      <TableCell>{formatElapsed(row.elapsed_s)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="font-display">Event Details</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedTimelineEvent ? (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">
                    #{selectedTimelineEvent.event_index} {selectedTimelineEvent.stage} at {selectedTimelineEvent.ts_utc}
                  </p>
                  <pre className="max-h-[280px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                    {JSON.stringify(selectedTimelineEvent.details ?? {}, null, 2)}
                  </pre>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Select an event row to inspect details.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-display">Review Notes</CardTitle>
              <CardDescription>Capture run observations and follow-up actions for future improvements.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 md:grid-cols-[180px,1fr,auto]">
                <div className="space-y-1">
                  <Label htmlFor="timeline-note-author">Author</Label>
                  <Input id="timeline-note-author" value={timelineNoteAuthor} onChange={(event) => setTimelineNoteAuthor(event.target.value)} />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="timeline-note-text">Note</Label>
                  <Input
                    id="timeline-note-text"
                    placeholder="Add note about this run..."
                    value={timelineNoteText}
                    onChange={(event) => setTimelineNoteText(event.target.value)}
                  />
                </div>
                <Button onClick={onAddTimelineNote} disabled={saving || !timelineRunId || !timelineNoteText.trim()}>
                  {saveAction === "timeline-note" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Save className="h-4 w-4" />}
                  {saveAction === "timeline-note" ? "Saving..." : "Add Note"}
                </Button>
              </div>
              <div className="space-y-2">
                {timelineNotes.length > 0 ? (
                  timelineNotes.map((row) => (
                    <div key={row.id} className="rounded-md border bg-muted/20 p-3">
                      <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <span className="font-semibold text-foreground">{row.author || "admin"}</span>
                        <span>{formatTimestamp(row.created_at_utc)}</span>
                      </div>
                      <p className="text-sm">{row.note}</p>
                    </div>
                  ))
                ) : (
                  <EmptyState title="No notes yet" description="Add a note above to capture observations about this run." />
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function formatAdjustmentLabel(value: string): string {
  switch (value) {
    case "quality_prior":
      return "quality prior"
    case "feedback_bias":
      return "feedback"
    case "source_preference":
      return "source preference"
    case "content_depth":
      return "content depth"
    case "research_balance":
      return "research balance"
    default:
      return value.replace(/_/g, " ")
  }
}

