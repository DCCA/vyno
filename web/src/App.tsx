import { useEffect, useMemo, useRef, useState } from "react"
import {
  Activity,
  Clock3,
  Loader2,
  Menu,
  Play,
  RefreshCcw,
  X,
} from "lucide-react"
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { InlineNotice } from "@/components/system/notice"
import { ErrorBoundary } from "@/components/system/error-boundary"
import { ConfirmDialog, useConfirm } from "@/components/system/confirm-dialog"
import { Toaster } from "@/components/system/toast"
import { ConsoleProvider, type ConsoleContextValue } from "@/app/console-context"
import { api } from "@/lib/api"
import {
  diffObjects,
  formatElapsed,
  parseProfilePayload,
  surfaceFromLegacyQuery,
  toInt,
} from "@/lib/console-utils"
import { navItemsForLifecycle, surfaceForPathname, surfacePaths } from "@/app/navigation"
import type {
  ConsoleSurface,
  FeedbackSummary,
  HistoryItem,
  Notice,
  NoticeScope,
  OnboardingStatus,
  PreviewResult,
  PreflightReport,
  RunPolicy,
  RunProgress,
  RunStatus,
  ScheduleConfig,
  ScheduleStatus,
  SaveAction,
  RunArtifact,
  RunItem,
  SourceHealthItem,
  SourceMap,
  SourcePack,
  TimelineEvent,
  TimelineNote,
  TimelineRun,
  TimelineSummary,
  UnifiedSourceRow,
} from "@/app/types"
import { DashboardPage } from "@/features/dashboard/DashboardPage"
import { HistoryPage } from "@/features/history/HistoryPage"
import { OnboardingPage } from "@/features/onboarding/OnboardingPage"
import { ProfilePage } from "@/features/profile/ProfilePage"
import { RunCenterPage } from "@/features/run-center/RunCenterPage"
import { SchedulePage } from "@/features/schedule/SchedulePage"
import { SourcesPage } from "@/features/sources/SourcesPage"
import { TimelinePage } from "@/features/timeline/TimelinePage"

function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const uiStateHydratedRef = useRef(false)
  const { confirmState, confirm, handleClose: handleConfirmClose } = useConfirm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [sourceTypes, setSourceTypes] = useState<string[]>([])
  const [sources, setSources] = useState<SourceMap>({})
  const [sourceType, setSourceType] = useState("rss")
  const [sourceValue, setSourceValue] = useState("")
  const [sourceSearch, setSourceSearch] = useState("")
  const [showAllUnifiedSources, setShowAllUnifiedSources] = useState(false)
  const [sourceStatusFilter, setSourceStatusFilter] = useState<"all" | "healthy" | "failing">("all")
  const [unifiedSourceRows, setUnifiedSourceRows] = useState<UnifiedSourceRow[]>([])
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null)
  const [profileBaseline, setProfileBaseline] = useState<Record<string, unknown> | null>(null)
  const [profileJson, setProfileJson] = useState("")
  const [profileDiff, setProfileDiff] = useState<Record<string, unknown>>({})
  const [profileDiffComputedAt, setProfileDiffComputedAt] = useState("")
  const [runPolicyBaseline, setRunPolicyBaseline] = useState<RunPolicy | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null)
  const [runProgress, setRunProgress] = useState<RunProgress | null>(null)
  const [sourceHealth, setSourceHealth] = useState<SourceHealthItem[]>([])
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null)
  const [scheduleDraft, setScheduleDraft] = useState<ScheduleConfig>({
    enabled: false,
    cadence: "daily",
    time_local: "09:00",
    hourly_minute: 0,
    quiet_hours_enabled: false,
    quiet_start_local: "22:00",
    quiet_end_local: "07:00",
    timezone: "UTC",
  })
  const [scheduleBaseline, setScheduleBaseline] = useState<ScheduleConfig | null>(null)
  const [scheduleStatus, setScheduleStatus] = useState<ScheduleStatus | null>(null)
  const [preflight, setPreflight] = useState<PreflightReport | null>(null)
  const [sourcePacks, setSourcePacks] = useState<SourcePack[]>([])
  const [previewResult, setPreviewResult] = useState<PreviewResult | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [runNowLoading, setRunNowLoading] = useState(false)
  const [activateLoading, setActivateLoading] = useState(false)
  const [saveAction, setSaveAction] = useState<SaveAction>("")
  const [activeSourcePackId, setActiveSourcePackId] = useState("")
  const [activeRollbackId, setActiveRollbackId] = useState("")
  const [runPolicy, setRunPolicy] = useState<RunPolicy>({
    default_mode: "fresh_only",
    allow_run_override: true,
    seen_reset_guard: "confirm",
  })
  const [runNowModeOverride, setRunNowModeOverride] = useState("default")
  const [seenResetDays, setSeenResetDays] = useState("30")
  const [seenResetPreviewCount, setSeenResetPreviewCount] = useState<number | null>(null)
  const [seenResetConfirm, setSeenResetConfirm] = useState(false)
  const [timelineRuns, setTimelineRuns] = useState<TimelineRun[]>([])
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([])
  const [timelineSummary, setTimelineSummary] = useState<TimelineSummary | null>(null)
  const [timelineNotes, setTimelineNotes] = useState<TimelineNote[]>([])
  const [timelineRunItems, setTimelineRunItems] = useState<RunItem[]>([])
  const [timelineRunArtifacts, setTimelineRunArtifacts] = useState<RunArtifact[]>([])
  const [timelineRunId, setTimelineRunId] = useState("")
  const [timelineStageFilter, setTimelineStageFilter] = useState("all")
  const [timelineSeverityFilter, setTimelineSeverityFilter] = useState("all")
  const [timelineOrder, setTimelineOrder] = useState<"asc" | "desc">("desc")
  const [timelineLivePaused, setTimelineLivePaused] = useState(false)
  const [timelineSelectedEventId, setTimelineSelectedEventId] = useState(0)
  const [timelineNoteAuthor, setTimelineNoteAuthor] = useState("admin")
  const [timelineNoteText, setTimelineNoteText] = useState("")
  const [feedbackSummary, setFeedbackSummary] = useState<FeedbackSummary | null>(null)
  const [globalNotice, setGlobalNotice] = useState<Notice | null>(null)
  const [localNotices, setLocalNotices] = useState<Partial<Record<Exclude<NoticeScope, "global">, Notice>>>({})
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const currentSurface = surfaceForPathname(location.pathname)
  const onboardingLifecycle = onboarding?.lifecycle ?? "needs_setup"
  const onboardingRevisitMode = useMemo(
    () => new URLSearchParams(location.search).get("mode") === "revisit",
    [location.search],
  )

  const sortedSourceRows = useMemo(
    () => Object.entries(sources).sort((a, b) => a[0].localeCompare(b[0])),
    [sources],
  )
  const totalSourceCount = useMemo(
    () => sortedSourceRows.reduce((sum, [, values]) => sum + values.length, 0),
    [sortedSourceRows],
  )
  const filteredUnifiedSourceRows = useMemo(() => {
    const query = sourceSearch.trim().toLowerCase()
    return unifiedSourceRows.filter((row) => {
      if (sourceStatusFilter !== "all" && row.health !== sourceStatusFilter) return false
      if (!query) return true
      return (
        row.type.toLowerCase().includes(query) ||
        row.type_label.toLowerCase().includes(query) ||
        row.source.toLowerCase().includes(query) ||
        row.identity_title.toLowerCase().includes(query) ||
        row.identity_subtitle.toLowerCase().includes(query) ||
        row.preview_title.toLowerCase().includes(query) ||
        row.preview_description.toLowerCase().includes(query) ||
        row.preview_host.toLowerCase().includes(query) ||
        row.last_error.toLowerCase().includes(query) ||
        row.hint.toLowerCase().includes(query)
      )
    })
  }, [sourceSearch, sourceStatusFilter, unifiedSourceRows])
  const unifiedRowsVisible = useMemo(
    () => (showAllUnifiedSources ? filteredUnifiedSourceRows : filteredUnifiedSourceRows.slice(0, 12)),
    [filteredUnifiedSourceRows, showAllUnifiedSources],
  )
  const profileJsonParseError = useMemo(() => {
    if (!profileJson.trim()) return ""
    try {
      parseProfilePayload(profileJson)
      return ""
    } catch (error) {
      return error instanceof Error ? error.message : String(error)
    }
  }, [profileJson])
  const localProfileDiff = useMemo(() => {
    if (!profileBaseline || profileJsonParseError) return {}
    try {
      const parsed = parseProfilePayload(profileJson)
      return diffObjects(profileBaseline, parsed)
    } catch {
      return {}
    }
  }, [profileBaseline, profileJson, profileJsonParseError])
  const localDiffCount = useMemo(() => Object.keys(localProfileDiff).length, [localProfileDiff])
  const serverDiffCount = useMemo(() => Object.keys(profileDiff).length, [profileDiff])
  const profileWorkspaceDirty = localDiffCount > 0 || Boolean(profileJsonParseError)
  const runPolicyChangeCount = useMemo(() => {
    if (!runPolicyBaseline) return 0
    let count = 0
    if (runPolicy.default_mode !== runPolicyBaseline.default_mode) count += 1
    if (runPolicy.allow_run_override !== runPolicyBaseline.allow_run_override) count += 1
    if (runPolicy.seen_reset_guard !== runPolicyBaseline.seen_reset_guard) count += 1
    return count
  }, [runPolicy, runPolicyBaseline])
  const runPolicyDirty = runPolicyChangeCount > 0
  const scheduleDirty = useMemo(() => {
    if (!scheduleBaseline) return false
    return (
      scheduleDraft.enabled !== scheduleBaseline.enabled ||
      scheduleDraft.cadence !== scheduleBaseline.cadence ||
      scheduleDraft.time_local !== scheduleBaseline.time_local ||
      scheduleDraft.hourly_minute !== scheduleBaseline.hourly_minute ||
      scheduleDraft.quiet_hours_enabled !== scheduleBaseline.quiet_hours_enabled ||
      scheduleDraft.quiet_start_local !== scheduleBaseline.quiet_start_local ||
      scheduleDraft.quiet_end_local !== scheduleBaseline.quiet_end_local ||
      scheduleDraft.timezone !== scheduleBaseline.timezone
    )
  }, [scheduleBaseline, scheduleDraft])
  const profileWorkspaceChangeCount = localDiffCount + runPolicyChangeCount
  const selectedTimelineEvent = useMemo(
    () => timelineEvents.find((row) => row.id === timelineSelectedEventId) ?? null,
    [timelineEvents, timelineSelectedEventId],
  )
  const timelineStageOptions = useMemo(() => {
    const values = [...new Set(timelineEvents.map((row) => row.stage).filter(Boolean))].sort((a, b) => a.localeCompare(b))
    if (timelineStageFilter !== "all" && !values.includes(timelineStageFilter)) {
      values.push(timelineStageFilter)
    }
    return values
  }, [timelineEvents, timelineStageFilter])

  const digestBusy = Boolean(
    runNowLoading || activateLoading || previewLoading || runStatus?.active?.run_id || runProgress?.is_active,
  )
  const showRunActivity = Boolean(runProgress || digestBusy)
  const runActivityFacts = useMemo(() => {
    if (!runProgress) return [] as string[]
    const details = runProgress.details ?? {}
    const facts: string[] = []
    const fetchDone = toInt(details.fetch_done)
    const fetchTotal = toInt(details.fetch_total)
    if (fetchDone !== null && fetchTotal !== null && fetchTotal > 0) {
      facts.push(`Sources ${fetchDone}/${fetchTotal}`)
    }
    const processedCount = toInt(details.processed_count)
    const totalCount = toInt(details.total_count)
    if (processedCount !== null && totalCount !== null && totalCount > 0) {
      facts.push(`Items ${processedCount}/${totalCount}`)
    }
    const cacheHits = toInt(details.cache_hits)
    if (cacheHits !== null && cacheHits > 0) {
      facts.push(`Cache hits ${cacheHits}`)
    }
    const fallbackCount = toInt(details.fallback_count)
    if (fallbackCount !== null && fallbackCount > 0) {
      facts.push(`Fallbacks ${fallbackCount}`)
    }
    const sourceErrors = toInt(details.source_error_count)
    if (sourceErrors !== null && sourceErrors > 0) {
      facts.push(`Source errors ${sourceErrors}`)
    }
    const summaryErrors = toInt(details.summary_error_count)
    if (summaryErrors !== null && summaryErrors > 0) {
      facts.push(`Summary errors ${summaryErrors}`)
    }
    return facts.slice(0, 4)
  }, [runProgress])

  const onboardingDone = onboardingLifecycle === "ready"
  const setupPercent = onboarding?.progress.total
    ? Math.round((onboarding.progress.completed / onboarding.progress.total) * 100)
    : 0
  const visibleNavItems = useMemo(() => navItemsForLifecycle(onboardingLifecycle), [onboardingLifecycle])
  const digestLoadingMessage = runProgress
    ? `${runProgress.stage_label}: ${runProgress.stage_detail || runProgress.message}`
    : previewLoading
      ? "Preparing onboarding preview digest..."
      : activateLoading
        ? "Preparing live digest run..."
        : runNowLoading
          ? "Preparing digest run..."
          : runStatus?.active?.run_id
            ? "Digest run in progress. Waiting for progress details..."
            : ""
  const globalLoadingText =
    saveAction === "source-add"
      ? "Adding source..."
      : saveAction === "source-remove"
        ? "Removing source..."
        : saveAction === "onboarding-preflight"
          ? "Running preflight checks..."
          : saveAction === "source-pack"
            ? "Applying source pack..."
            : saveAction === "schedule-save"
              ? "Saving schedule..."
            : saveAction === "profile-validate"
              ? "Validating profile..."
              : saveAction === "profile-diff"
                ? "Computing profile diff..."
                : saveAction === "profile-save"
                  ? "Saving profile overlay..."
                    : saveAction === "run-policy-save"
                      ? "Saving run policy..."
                      : saveAction === "profile-feedback-refresh"
                        ? "Refreshing personalization summary..."
                      : saveAction === "timeline-refresh"
                        ? "Refreshing timeline..."
                      : saveAction === "timeline-export"
                        ? "Exporting timeline..."
                        : saveAction === "timeline-note"
                          ? "Saving timeline note..."
                          : saveAction === "timeline-item-feedback"
                            ? "Saving item feedback..."
                            : saveAction === "source-feedback"
                              ? "Saving source feedback..."
                            : saveAction === "seen-reset-preview"
                              ? "Previewing seen reset..."
                              : saveAction === "seen-reset-apply"
                              ? "Resetting seen history..."
                              : saveAction === "rollback"
                                ? "Rolling back to snapshot..."
                                : runNowLoading
                                  ? "Starting digest run..."
                                  : activateLoading
                                    ? "Starting live run..."
                                    : previewLoading
                                      ? "Running onboarding preview..."
                                      : loading
                                        ? "Loading configuration..."
                                        : ""

  function setScopedNotice(scope: NoticeScope, kind: Notice["kind"], text: string) {
    const next = { kind, text }
    if (scope === "global") {
      setGlobalNotice(next)
      return
    }
    setLocalNotices((prev) => ({ ...prev, [scope]: next }))
  }

  function clearScopedNotice(scope: NoticeScope) {
    if (scope === "global") {
      setGlobalNotice(null)
      return
    }
    setLocalNotices((prev) => {
      const copy = { ...prev }
      delete copy[scope]
      return copy
    })
  }

  useEffect(() => {
    const legacySurface = surfaceFromLegacyQuery(location.search)
    if (!legacySurface || legacySurface === "dashboard") {
      uiStateHydratedRef.current = true
      return
    }
    const params = new URLSearchParams(location.search)
    params.delete("surface")
    navigate(
      {
        pathname: surfacePaths[legacySurface],
        search: params.toString() ? `?${params.toString()}` : "",
      },
      { replace: true },
    )
    uiStateHydratedRef.current = true
  }, [location.search, navigate])

  useEffect(() => {
    void refreshAll()
      const timer = setInterval(() => {
      const requests: Array<Promise<unknown>> = [
        api<RunStatus>("/api/run-status"),
        api<RunProgress>("/api/run-progress"),
        api<{ items: SourceHealthItem[] }>("/api/source-health"),
        api<OnboardingStatus>("/api/onboarding/status"),
        api<{ schedule: ScheduleConfig }>("/api/config/schedule"),
        api<{ schedule_status: ScheduleStatus }>("/api/schedule/status"),
        api<{ runs: TimelineRun[] }>("/api/timeline/runs?limit=50"),
        api<{ run_policy: RunPolicy }>("/api/config/run-policy"),
        api<FeedbackSummary>("/api/feedback/summary"),
      ]
      const shouldRefreshSourcePreviews = currentSurface === "sources"
      if (shouldRefreshSourcePreviews) {
        requests.push(api<{ items: UnifiedSourceRow[] }>("/api/source-previews"))
      }
      void Promise.all(requests)
        .then((results) => {
          const [status, progress, health, onboardingStatus, scheduleConfigData, scheduleData, timelineData, policyData, feedbackData, previewData] =
            results as [
              RunStatus,
              RunProgress,
              { items: SourceHealthItem[] },
              OnboardingStatus,
              { schedule: ScheduleConfig },
              { schedule_status: ScheduleStatus },
              { runs: TimelineRun[] },
              { run_policy: RunPolicy },
              FeedbackSummary,
              { items: UnifiedSourceRow[] } | undefined,
            ]
          setRunStatus(status)
          setRunProgress(progress.available ? progress : null)
          setSourceHealth(health.items)
          if (previewData) {
            setUnifiedSourceRows(previewData.items)
          }
          setOnboarding(onboardingStatus)
          if (!scheduleDirty) {
            setScheduleDraft(scheduleConfigData.schedule)
            setScheduleBaseline(scheduleConfigData.schedule)
          }
          setScheduleStatus(scheduleData.schedule_status)
          setTimelineRuns(timelineData.runs)
          if (!runPolicyDirty) {
            setRunPolicy(policyData.run_policy)
            setRunPolicyBaseline(policyData.run_policy)
          }
          setFeedbackSummary(feedbackData)
          if (!timelineRunId && timelineData.runs.length > 0) {
            setTimelineRunId(timelineData.runs[0].run_id)
          }
        })
        .catch(() => undefined)
    }, 8000)
    return () => clearInterval(timer)
  }, [currentSurface, runPolicyDirty, scheduleDirty, timelineRunId])

  useEffect(() => {
    const activeRunId = runStatus?.active?.run_id || runProgress?.run_id
    const shouldPollFast = Boolean(runStatus?.active?.run_id || runProgress?.is_active)
    if (!shouldPollFast) return
    let cancelled = false
    const poll = async () => {
      try {
        const query = activeRunId ? `?run_id=${encodeURIComponent(activeRunId)}` : ""
        const [status, progress] = await Promise.all([
          api<RunStatus>("/api/run-status"),
          api<RunProgress>(`/api/run-progress${query}`),
        ])
        if (cancelled) return
        setRunStatus(status)
        setRunProgress(progress.available ? progress : null)
      } catch {
        // Keep last known progress when polling errors transiently.
      }
    }
    void poll()
    const timer = setInterval(() => {
      void poll()
    }, 1500)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [runStatus?.active?.run_id, runProgress?.is_active, runProgress?.run_id])

  useEffect(() => {
    if (!globalNotice || globalNotice.kind !== "ok") return
    const timer = window.setTimeout(() => setGlobalNotice(null), 5000)
    return () => window.clearTimeout(timer)
  }, [globalNotice])

  useEffect(() => {
    const timers: number[] = []
    for (const [scope, notice] of Object.entries(localNotices)) {
      if (!notice || notice.kind !== "ok") continue
      timers.push(
        window.setTimeout(() => {
          clearScopedNotice(scope as NoticeScope)
        }, 5000),
      )
    }
    return () => {
      timers.forEach((timer) => window.clearTimeout(timer))
    }
  }, [localNotices])

  useEffect(() => {
    setShowAllUnifiedSources(false)
  }, [sourceSearch, sourceStatusFilter, sources, sourceHealth.length])

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (location.pathname !== surfacePaths.sources) return
    const params = new URLSearchParams(location.search)
    const nextSearch = params.get("q") ?? ""
    const nextStatus = params.get("status")
    if (nextSearch !== sourceSearch) {
      setSourceSearch(nextSearch)
    }
    if (nextStatus === "healthy" || nextStatus === "failing" || nextStatus === "all") {
      if (nextStatus !== sourceStatusFilter) {
        setSourceStatusFilter(nextStatus)
      }
    }
  }, [location.pathname, location.search, sourceSearch, sourceStatusFilter])

  useEffect(() => {
    if (location.pathname !== surfacePaths.sources || !uiStateHydratedRef.current) return
    const params = new URLSearchParams(location.search)
    if (sourceSearch) params.set("q", sourceSearch)
    else params.delete("q")
    if (sourceStatusFilter !== "all") params.set("status", sourceStatusFilter)
    else params.delete("status")
    const nextSearch = params.toString()
    const normalized = nextSearch ? `?${nextSearch}` : ""
    if (normalized !== location.search) {
      navigate({ pathname: location.pathname, search: normalized }, { replace: true })
    }
  }, [location.pathname, location.search, navigate, sourceSearch, sourceStatusFilter])

  useEffect(() => {
    if (location.pathname !== surfacePaths.timeline) return
    const params = new URLSearchParams(location.search)
    const runId = params.get("run_id") ?? ""
    const stage = params.get("stage") ?? "all"
    const severity = params.get("severity") ?? "all"
    const order = params.get("order") === "asc" ? "asc" : "desc"
    if (runId && runId !== timelineRunId) setTimelineRunId(runId)
    if (stage !== timelineStageFilter) setTimelineStageFilter(stage)
    if (severity !== timelineSeverityFilter) setTimelineSeverityFilter(severity)
    if (order !== timelineOrder) setTimelineOrder(order)
  }, [location.pathname, location.search, timelineOrder, timelineRunId, timelineSeverityFilter, timelineStageFilter])

  useEffect(() => {
    if (location.pathname !== surfacePaths.timeline || !uiStateHydratedRef.current) return
    const params = new URLSearchParams(location.search)
    if (timelineRunId) params.set("run_id", timelineRunId)
    else params.delete("run_id")
    if (timelineStageFilter !== "all") params.set("stage", timelineStageFilter)
    else params.delete("stage")
    if (timelineSeverityFilter !== "all") params.set("severity", timelineSeverityFilter)
    else params.delete("severity")
    if (timelineOrder !== "desc") params.set("order", timelineOrder)
    else params.delete("order")
    const nextSearch = params.toString()
    const normalized = nextSearch ? `?${nextSearch}` : ""
    if (normalized !== location.search) {
      navigate({ pathname: location.pathname, search: normalized }, { replace: true })
    }
  }, [location.pathname, location.search, navigate, timelineOrder, timelineRunId, timelineSeverityFilter, timelineStageFilter])

  useEffect(() => {
    if (!timelineRunId) return
    void refreshTimeline({ silent: true })
  }, [timelineRunId, timelineStageFilter, timelineSeverityFilter, timelineOrder])

  useEffect(() => {
    if (currentSurface !== "timeline" || !timelineRunId) return
    if (timelineLivePaused) return
    const activeRunId = runStatus?.active?.run_id ?? ""
    const isLive = activeRunId !== "" && activeRunId === timelineRunId
    if (!isLive) return
    const timer = setInterval(() => {
      void refreshTimeline({ silent: true })
    }, 2500)
    return () => clearInterval(timer)
  }, [currentSurface, runStatus?.active?.run_id, timelineLivePaused, timelineOrder, timelineRunId, timelineSeverityFilter, timelineStageFilter])

  async function refreshAll(options?: { preserveProfileWorkspace?: boolean; preserveRunPolicyWorkspace?: boolean; preserveScheduleWorkspace?: boolean }) {
    setLoading(true)
    try {
      const [
        typeData,
        sourceData,
        sourcePreviewData,
        profileData,
        historyData,
        statusData,
        progressData,
        healthData,
        onboardingData,
        scheduleConfigData,
        scheduleData,
        sourcePackData,
        timelineData,
        policyData,
        feedbackData,
      ] = await Promise.all([
        api<{ types: string[] }>("/api/config/source-types"),
        api<{ sources: SourceMap }>("/api/config/sources"),
        api<{ items: UnifiedSourceRow[] }>("/api/source-previews"),
        api<{ profile: Record<string, unknown> }>("/api/config/profile"),
        api<{ snapshots: HistoryItem[] }>("/api/config/history"),
        api<RunStatus>("/api/run-status"),
        api<RunProgress>("/api/run-progress"),
        api<{ items: SourceHealthItem[] }>("/api/source-health"),
        api<OnboardingStatus>("/api/onboarding/status"),
        api<{ schedule: ScheduleConfig }>("/api/config/schedule"),
        api<{ schedule_status: ScheduleStatus }>("/api/schedule/status"),
        api<{ packs: SourcePack[] }>("/api/onboarding/source-packs"),
        api<{ runs: TimelineRun[] }>("/api/timeline/runs?limit=50"),
        api<{ run_policy: RunPolicy }>("/api/config/run-policy"),
        api<FeedbackSummary>("/api/feedback/summary"),
      ])
      const preserveProfileWorkspace = options?.preserveProfileWorkspace ?? true
      const preserveRunPolicyWorkspace = options?.preserveRunPolicyWorkspace ?? true
      const preserveScheduleWorkspace = options?.preserveScheduleWorkspace ?? true
      setSourceTypes(typeData.types)
      setSources(sourceData.sources)
      setUnifiedSourceRows(sourcePreviewData.items)
      if (!preserveProfileWorkspace || !profileWorkspaceDirty || !profile) {
        setProfile(profileData.profile)
        setProfileBaseline(profileData.profile)
        setProfileJson(JSON.stringify(profileData.profile, null, 2))
      }
      if (!preserveScheduleWorkspace || !scheduleDirty || !scheduleBaseline) {
        setScheduleDraft(scheduleConfigData.schedule)
        setScheduleBaseline(scheduleConfigData.schedule)
      }
      setProfileDiff({})
      setProfileDiffComputedAt("")
      setHistory(historyData.snapshots)
      setRunStatus(statusData)
      setRunProgress(progressData.available ? progressData : null)
      setSourceHealth(healthData.items)
      setOnboarding(onboardingData)
      setScheduleStatus(scheduleData.schedule_status)
      setSourcePacks(sourcePackData.packs)
      if (!preserveRunPolicyWorkspace || !runPolicyDirty || !runPolicyBaseline) {
        setRunPolicy(policyData.run_policy)
        setRunPolicyBaseline(policyData.run_policy)
      }
      setFeedbackSummary(feedbackData)
      setTimelineRuns(timelineData.runs)
      if (timelineData.runs.length > 0) {
        const preferred = timelineRunId && timelineData.runs.some((row) => row.run_id === timelineRunId)
        const nextRunId = preferred ? timelineRunId : timelineData.runs[0].run_id
        setTimelineRunId(nextRunId)
      } else {
        setTimelineRunId("")
      }
      if (typeData.types.length > 0 && !typeData.types.includes(sourceType)) {
        setSourceType(typeData.types[0])
      }
    } catch (error) {
      setScopedNotice("global", "error", String(error))
    } finally {
      setLoading(false)
    }
  }

  function updateProfileField(path: string, value: unknown) {
    setProfile((prev) => {
      if (!prev) return prev
      const next = structuredClone(prev)
      const parts = path.split(".")
      let cursor: Record<string, unknown> = next
      for (let i = 0; i < parts.length - 1; i += 1) {
        const key = parts[i]
        const current = cursor[key]
        if (typeof current !== "object" || current === null) {
          cursor[key] = {}
        }
        cursor = cursor[key] as Record<string, unknown>
      }
      cursor[parts[parts.length - 1]] = value
      setProfileJson(JSON.stringify(next, null, 2))
      return next
    })
  }

  function updateScheduleField(field: keyof ScheduleConfig, value: string | boolean | number) {
    setScheduleDraft((prev) => ({ ...prev, [field]: value }))
  }

  function syncScheduleIntoProfile(nextSchedule: ScheduleConfig) {
    setProfile((prev) => {
      if (!prev) return prev
      const next = structuredClone(prev)
      next.schedule = nextSchedule
      try {
        setProfileJson(JSON.stringify(next, null, 2))
      } catch {
        // Keep the current editor text if the local expert payload cannot be regenerated safely.
      }
      return next
    })
    setProfileBaseline((prev) => {
      if (!prev) return prev
      const next = structuredClone(prev)
      next.schedule = nextSchedule
      return next
    })
  }

  async function handleSourceMutation(action: "add" | "remove") {
    if (!sourceType || !sourceValue.trim()) {
      setScopedNotice("sources", "error", "Select a source type and enter a value.")
      return
    }
    setSaveAction(action === "add" ? "source-add" : "source-remove")
    setSaving(true)
    try {
      await api(`/api/config/sources/${action}`, {
        method: "POST",
        body: JSON.stringify({ source_type: sourceType, value: sourceValue }),
      })
      await refreshAll({ preserveProfileWorkspace: false, preserveRunPolicyWorkspace: false })
      setSourceValue("")
      setScopedNotice("sources", "ok", `Source ${action} completed.`)
    } catch (error) {
      setScopedNotice("sources", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  function editUnifiedSourceRow(row: UnifiedSourceRow) {
    if (!row.can_edit) return
    setSourceType(row.type)
    setSourceValue(row.source)
    setScopedNotice("sources", "ok", `Loaded ${row.type} source for editing.`)
  }

  async function deleteUnifiedSourceRow(row: UnifiedSourceRow) {
    if (!row.can_delete) return
    const confirmed = await confirm({
      title: `Delete ${row.type} source?`,
      description: row.source,
      confirmLabel: "Delete",
      variant: "destructive",
    })
    if (!confirmed) return
    setSaveAction("source-remove")
    setSaving(true)
    try {
      await api("/api/config/sources/remove", {
        method: "POST",
        body: JSON.stringify({ source_type: row.type, value: row.source }),
      })
      await refreshAll({ preserveProfileWorkspace: false, preserveRunPolicyWorkspace: false })
      setScopedNotice("sources", "ok", `Removed ${row.type}: ${row.source}`)
    } catch (error) {
      setScopedNotice("sources", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function runNow() {
    setRunNowLoading(true)
    setSaving(true)
    try {
      const selectedMode = runNowModeOverride === "default" ? "" : runNowModeOverride
      const result = await api<{ started: boolean; run_id?: string; active_run_id?: string; mode?: string }>("/api/run-now", {
        method: "POST",
        body: JSON.stringify(selectedMode ? { mode: selectedMode } : {}),
      })
      if (result.started) {
        const modeText = result.mode ? ` (${result.mode})` : ""
        setScopedNotice("run", "ok", `Run started: ${result.run_id}${modeText}`)
      } else {
        setScopedNotice("run", "error", `Run already active: ${result.active_run_id}`)
      }
      const [status, progress] = await Promise.all([
        api<RunStatus>("/api/run-status"),
        api<RunProgress>(`/api/run-progress${result.run_id ? `?run_id=${encodeURIComponent(result.run_id)}` : ""}`),
      ])
      setRunStatus(status)
      setRunProgress(progress.available ? progress : null)
    } catch (error) {
      setScopedNotice("run", "error", String(error))
    } finally {
      setRunNowLoading(false)
      setSaving(false)
    }
  }

  async function runOnboardingPreflight() {
    setSaveAction("onboarding-preflight")
    setSaving(true)
    try {
      const result = await api<PreflightReport>("/api/onboarding/preflight")
      setPreflight(result)
      const status = await api<OnboardingStatus>("/api/onboarding/status")
      setOnboarding(status)
      setScopedNotice(
        "onboarding",
        result.ok ? "ok" : "error",
        result.ok ? `Preflight passed (${result.pass_count} checks).` : `Preflight found ${result.fail_count} failing checks.`,
      )
    } catch (error) {
      setScopedNotice("onboarding", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function applySourcePack(packId: string) {
    setSaveAction("source-pack")
    setActiveSourcePackId(packId)
    setSaving(true)
    try {
      const result = await api<{ added_count: number; existing_count: number; error_count: number }>(
        "/api/onboarding/source-packs/apply",
        {
          method: "POST",
          body: JSON.stringify({ pack_id: packId }),
        },
      )
      await refreshAll({ preserveProfileWorkspace: false, preserveRunPolicyWorkspace: false })
      setScopedNotice(
        "onboarding",
        result.error_count > 0 ? "error" : "ok",
        `Source pack applied: added=${result.added_count}, existing=${result.existing_count}, errors=${result.error_count}.`,
      )
    } catch (error) {
      setScopedNotice("onboarding", "error", String(error))
    } finally {
      setSaveAction("")
      setActiveSourcePackId("")
      setSaving(false)
    }
  }

  async function runOnboardingPreview() {
    setPreviewLoading(true)
    try {
      const result = await api<PreviewResult>("/api/onboarding/preview", { method: "POST" })
      setPreviewResult(result)
      const status = await api<OnboardingStatus>("/api/onboarding/status")
      setOnboarding(status)
      setScopedNotice("onboarding", "ok", `Preview run completed (${result.status}).`)
    } catch (error) {
      setScopedNotice("onboarding", "error", String(error))
    } finally {
      setPreviewLoading(false)
    }
  }

  async function activateOnboarding() {
    setActivateLoading(true)
    setSaving(true)
    try {
      const result = await api<{ started: boolean; run_id?: string; active_run_id?: string }>("/api/onboarding/activate", {
        method: "POST",
      })
      const [status, progress, onboardingStatus] = await Promise.all([
        api<RunStatus>("/api/run-status"),
        api<RunProgress>(`/api/run-progress${result.run_id ? `?run_id=${encodeURIComponent(result.run_id)}` : ""}`),
        api<OnboardingStatus>("/api/onboarding/status"),
      ])
      setRunStatus(status)
      setRunProgress(progress.available ? progress : null)
      setOnboarding(onboardingStatus)
      setScopedNotice(
        "onboarding",
        result.started ? "ok" : "error",
        result.started ? `Live run started: ${result.run_id}` : `Run already active: ${result.active_run_id}`,
      )
    } catch (error) {
      setScopedNotice("onboarding", "error", String(error))
    } finally {
      setActivateLoading(false)
      setSaving(false)
    }
  }

  async function validateProfile(scope: "profile" = "profile") {
    if (!profile) return
    setSaveAction("profile-validate")
    setSaving(true)
    try {
      const parsed = parseProfilePayload(profileJson)
      const result = await api<{ profile: Record<string, unknown> }>("/api/config/profile/validate", {
        method: "POST",
        body: JSON.stringify({ profile: parsed }),
      })
      setProfile(result.profile)
      setProfileJson(JSON.stringify(result.profile, null, 2))
      setScopedNotice(scope, "ok", "Profile validated.")
    } catch (error) {
      setScopedNotice(scope, "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function computeProfileDiff(scope: "profile" = "profile") {
    setSaveAction("profile-diff")
    setSaving(true)
    try {
      const parsed = parseProfilePayload(profileJson)
      const result = await api<{ diff: Record<string, unknown> }>("/api/config/profile/diff", {
        method: "POST",
        body: JSON.stringify({ profile: parsed }),
      })
      setProfileDiff(result.diff)
      setProfileDiffComputedAt(new Date().toISOString())
      setScopedNotice(scope, "ok", "Diff updated.")
    } catch (error) {
      setScopedNotice(scope, "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function saveRunPolicy(scope: "profile" = "profile") {
    setSaveAction("run-policy-save")
    setSaving(true)
    try {
      const result = await api<{ run_policy: RunPolicy }>("/api/config/run-policy", {
        method: "POST",
        body: JSON.stringify({
          default_mode: runPolicy.default_mode,
          allow_run_override: runPolicy.allow_run_override,
          seen_reset_guard: runPolicy.seen_reset_guard,
        }),
      })
      setRunPolicy(result.run_policy)
      setRunPolicyBaseline(result.run_policy)
      setScopedNotice(scope, "ok", "Run policy saved.")
      await refreshFeedbackSummary({ silent: true })
    } catch (error) {
      setScopedNotice(scope, "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function saveSchedule(scope: "schedule" = "schedule") {
    setSaveAction("schedule-save")
    setSaving(true)
    try {
      const payload: ScheduleConfig = {
        enabled: Boolean(scheduleDraft.enabled),
        cadence: scheduleDraft.cadence === "hourly" ? "hourly" : "daily",
        time_local: String(scheduleDraft.time_local || "").trim(),
        hourly_minute: Math.max(0, Math.min(59, Number(scheduleDraft.hourly_minute ?? 0) || 0)),
        quiet_hours_enabled: Boolean(scheduleDraft.quiet_hours_enabled),
        quiet_start_local: String(scheduleDraft.quiet_start_local || "").trim(),
        quiet_end_local: String(scheduleDraft.quiet_end_local || "").trim(),
        timezone: String(scheduleDraft.timezone || "").trim(),
      }
      const result = await api<{ schedule: ScheduleConfig }>("/api/config/schedule", {
        method: "POST",
        body: JSON.stringify(payload),
      })
      setScheduleDraft(result.schedule)
      setScheduleBaseline(result.schedule)
      syncScheduleIntoProfile(result.schedule)
      await refreshAll({
        preserveProfileWorkspace: true,
        preserveRunPolicyWorkspace: true,
        preserveScheduleWorkspace: false,
      })
      setScopedNotice(scope, "ok", result.schedule.enabled ? "Schedule saved." : "Schedule saved and paused.")
    } catch (error) {
      setScopedNotice(scope, "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function saveProfileWorkspace() {
    const dirtyProfile = localDiffCount > 0
    const dirtyPolicy = runPolicyDirty
    if (!dirtyProfile && !dirtyPolicy) {
      setScopedNotice("profile", "ok", "No profile changes to save.")
      return
    }
    setSaveAction("profile-save")
    setSaving(true)
    const savedParts: string[] = []
    try {
      if (dirtyPolicy) {
        const policyResult = await api<{ run_policy: RunPolicy }>("/api/config/run-policy", {
          method: "POST",
          body: JSON.stringify({
            default_mode: runPolicy.default_mode,
            allow_run_override: runPolicy.allow_run_override,
            seen_reset_guard: runPolicy.seen_reset_guard,
          }),
        })
        setRunPolicy(policyResult.run_policy)
        setRunPolicyBaseline(policyResult.run_policy)
        savedParts.push("digest policy")
      }
      if (dirtyProfile) {
        const parsed = parseProfilePayload(profileJson)
        await api("/api/config/profile/save", {
          method: "POST",
          body: JSON.stringify({ profile: parsed }),
        })
        savedParts.push("profile changes")
        await refreshAll({ preserveProfileWorkspace: false, preserveRunPolicyWorkspace: false })
      }
      setScopedNotice("profile", "ok", `Saved ${savedParts.join(" and ")}.`)
    } catch (error) {
      if (savedParts.length > 0) {
        setScopedNotice("profile", "error", `Saved ${savedParts.join(" and ")}, but a later step failed: ${String(error)}`)
      } else {
        setScopedNotice("profile", "error", String(error))
      }
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function previewSeenReset() {
    setSaveAction("seen-reset-preview")
    setSaving(true)
    try {
      const days = Number.parseInt(seenResetDays, 10)
      const payload = Number.isFinite(days) && days > 0 ? { older_than_days: days } : {}
      const result = await api<{ affected_count: number }>("/api/seen/reset/preview", {
        method: "POST",
        body: JSON.stringify(payload),
      })
      setSeenResetPreviewCount(result.affected_count)
      setScopedNotice("profile", "ok", `Preview complete: ${result.affected_count} seen keys affected.`)
    } catch (error) {
      setScopedNotice("profile", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function applySeenReset() {
    setSaveAction("seen-reset-apply")
    setSaving(true)
    try {
      const days = Number.parseInt(seenResetDays, 10)
      const payload: Record<string, unknown> = { confirm: seenResetConfirm }
      if (Number.isFinite(days) && days > 0) {
        payload.older_than_days = days
      }
      const result = await api<{ deleted_count: number }>("/api/seen/reset/apply", {
        method: "POST",
        body: JSON.stringify(payload),
      })
      setSeenResetPreviewCount(null)
      setSeenResetConfirm(false)
      setScopedNotice("profile", "ok", `Seen reset applied: ${result.deleted_count} keys removed.`)
      await refreshAll({ preserveProfileWorkspace: false, preserveRunPolicyWorkspace: false })
    } catch (error) {
      setScopedNotice("profile", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function rollback(snapshotId: string) {
    setSaveAction("rollback")
    setActiveRollbackId(snapshotId)
    setSaving(true)
    try {
      await api("/api/config/rollback", {
        method: "POST",
        body: JSON.stringify({ snapshot_id: snapshotId }),
      })
      await refreshAll({ preserveProfileWorkspace: false, preserveRunPolicyWorkspace: false })
      setScopedNotice("history", "ok", `Rolled back to ${snapshotId}.`)
    } catch (error) {
      setScopedNotice("history", "error", String(error))
    } finally {
      setSaveAction("")
      setActiveRollbackId("")
      setSaving(false)
    }
  }

  async function refreshTimeline(options?: { silent?: boolean }) {
    if (!timelineRunId) {
      setTimelineEvents([])
      setTimelineSummary(null)
      setTimelineNotes([])
      setTimelineRunItems([])
      setTimelineRunArtifacts([])
      setTimelineSelectedEventId(0)
      return
    }
    if (!options?.silent) {
      setSaveAction("timeline-refresh")
      setSaving(true)
    }
    try {
      const runIdQuery = encodeURIComponent(timelineRunId)
      const stageQuery = timelineStageFilter === "all" ? "" : `&stage=${encodeURIComponent(timelineStageFilter)}`
      const severityQuery = timelineSeverityFilter === "all" ? "" : `&severity=${encodeURIComponent(timelineSeverityFilter)}`
      const orderQuery = `&order=${encodeURIComponent(timelineOrder)}`
      const [eventsResult, notesResult, summaryResult, itemsResult, artifactsResult] = await Promise.all([
        api<{ events: TimelineEvent[] }>(`/api/timeline/events?run_id=${runIdQuery}&limit=400${stageQuery}${severityQuery}${orderQuery}`),
        api<{ notes: TimelineNote[] }>(`/api/timeline/notes?run_id=${runIdQuery}&limit=200`),
        api<{ summary: TimelineSummary }>(`/api/timeline/summary?run_id=${runIdQuery}`).catch(() => ({ summary: null as TimelineSummary | null })),
        api<{ items: RunItem[] }>(`/api/run-items?run_id=${runIdQuery}`),
        api<{ artifacts: RunArtifact[] }>(`/api/run-artifacts?run_id=${runIdQuery}`),
      ])
      const nextEvents = eventsResult.events ?? []
      setTimelineEvents(nextEvents)
      setTimelineSelectedEventId((current) => {
        if (nextEvents.length === 0) return 0
        if (current > 0 && nextEvents.some((row) => row.id === current)) return current
        return nextEvents[0].id
      })
      setTimelineNotes(notesResult.notes ?? [])
      setTimelineSummary(summaryResult.summary ?? null)
      setTimelineRunItems(itemsResult.items ?? [])
      setTimelineRunArtifacts(artifactsResult.artifacts ?? [])
    } catch (error) {
      setScopedNotice("timeline", "error", String(error))
    } finally {
      if (!options?.silent) {
        setSaveAction("")
        setSaving(false)
      }
    }
  }

  async function exportTimeline() {
    if (!timelineRunId) return
    setSaveAction("timeline-export")
    setSaving(true)
    try {
      const runIdQuery = encodeURIComponent(timelineRunId)
      const payload = await api<Record<string, unknown>>(`/api/timeline/export?run_id=${runIdQuery}`)
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement("a")
      anchor.href = url
      anchor.download = `timeline-${timelineRunId}.json`
      anchor.click()
      URL.revokeObjectURL(url)
      setScopedNotice("timeline", "ok", "Timeline JSON exported.")
    } catch (error) {
      setScopedNotice("timeline", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function addTimelineNote() {
    if (!timelineRunId || !timelineNoteText.trim()) {
      setScopedNotice("timeline", "error", "Select a run and enter a note.")
      return
    }
    setSaveAction("timeline-note")
    setSaving(true)
    try {
      await api("/api/timeline/notes", {
        method: "POST",
        body: JSON.stringify({
          run_id: timelineRunId,
          author: timelineNoteAuthor.trim() || "admin",
          note: timelineNoteText.trim(),
        }),
      })
      setTimelineNoteText("")
      await refreshTimeline({ silent: true })
      setScopedNotice("timeline", "ok", "Timeline note saved.")
    } catch (error) {
      setScopedNotice("timeline", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function refreshFeedbackSummary(options?: { silent?: boolean }) {
    if (!options?.silent) {
      setSaveAction("profile-feedback-refresh")
      setSaving(true)
    }
    try {
      const result = await api<FeedbackSummary>("/api/feedback/summary")
      setFeedbackSummary(result)
    } catch (error) {
      setScopedNotice("profile", "error", String(error))
    } finally {
      if (!options?.silent) {
        setSaveAction("")
        setSaving(false)
      }
    }
  }

  async function submitItemFeedback(itemId: string, label: string) {
    if (!timelineRunId || !itemId) {
      setScopedNotice("timeline", "error", "Select a run item before sending feedback.")
      return
    }
    setSaveAction("timeline-item-feedback")
    setSaving(true)
    try {
      await api("/api/feedback/item", {
        method: "POST",
        body: JSON.stringify({ run_id: timelineRunId, item_id: itemId, label }),
      })
      await refreshFeedbackSummary({ silent: true })
      setScopedNotice("timeline", "ok", "Item feedback saved.")
    } catch (error) {
      setScopedNotice("timeline", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function submitSourceFeedback(row: UnifiedSourceRow, label: string) {
    setSaveAction("source-feedback")
    setSaving(true)
    try {
      await api("/api/feedback/source", {
        method: "POST",
        body: JSON.stringify({
          source_type: row.type,
          source_value: row.source,
          label,
        }),
      })
      await refreshAll({ preserveProfileWorkspace: false, preserveRunPolicyWorkspace: false })
      await refreshFeedbackSummary({ silent: true })
      const verb =
        label === "mute_source" ? "muted" : label === "prefer_source" ? "preferred" : "down-ranked"
      setScopedNotice("sources", "ok", `Source ${verb}: ${row.source}`)
    } catch (error) {
      setScopedNotice("sources", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  function navigateToSurface(surface: ConsoleSurface) {
    navigate(surfacePaths[surface])
  }

  const consoleValue: ConsoleContextValue = {
    ui: {
      loading,
      saving,
      saveAction,
      globalNotice,
      localNotices,
      clearScopedNotice,
    },
    run: {
      runStatus,
      runProgress,
      runPolicy,
      setRunPolicy,
      runNowModeOverride,
      setRunNowModeOverride,
      runNowLoading,
      digestBusy,
      onRunNow: () => void runNow(),
      onRefreshAll: () => void refreshAll(),
    },
    source: {
      sources,
      sourceTypes,
      sourceType,
      setSourceType,
      sourceValue,
      setSourceValue,
      sourceSearch,
      setSourceSearch,
      sourceStatusFilter,
      setSourceStatusFilter,
      sourceHealth,
      filteredUnifiedSourceRows,
      unifiedRowsVisible,
      showAllUnifiedSources,
      setShowAllUnifiedSources,
      onHandleSourceMutation: (action) => void handleSourceMutation(action),
      onEditUnifiedSourceRow: editUnifiedSourceRow,
      onDeleteUnifiedSourceRow: (row) => void deleteUnifiedSourceRow(row),
      onSourceFeedback: (row, label) => void submitSourceFeedback(row, label),
    },
    profile: {
      profile,
      profileJson,
      setProfileJson,
      updateProfileField,
      profileJsonParseError,
      profileWorkspaceChangeCount,
      localProfileDiff,
      profileDiff,
      profileDiffComputedAt,
      runPolicyDirty,
      runPolicyChangeCount,
      seenResetDays,
      setSeenResetDays,
      seenResetConfirm,
      setSeenResetConfirm,
      seenResetPreviewCount,
      feedbackSummary,
      onValidateProfile: () => void validateProfile("profile"),
      onComputeProfileDiff: () => void computeProfileDiff("profile"),
      onSaveProfileWorkspace: () => void saveProfileWorkspace(),
      onPreviewSeenReset: () => void previewSeenReset(),
      onApplySeenReset: () => void applySeenReset(),
    },
    schedule: {
      scheduleDraft,
      scheduleDirty,
      scheduleStatus,
      onChangeScheduleField: updateScheduleField,
      onSaveSchedule: () => void saveSchedule(),
    },
    onboarding: {
      onboarding,
      onboardingLifecycle,
      setupPercent,
      preflight,
      sourcePacks,
      previewResult,
      previewLoading,
      activateLoading,
      activeSourcePackId,
      onRunPreflight: () => void runOnboardingPreflight(),
      onApplySourcePack: (packId) => void applySourcePack(packId),
      onRunPreview: () => void runOnboardingPreview(),
      onActivate: () => void activateOnboarding(),
    },
    timeline: {
      timelineRunId,
      setTimelineRunId,
      timelineRuns,
      timelineStageFilter,
      setTimelineStageFilter,
      timelineStageOptions,
      timelineSeverityFilter,
      setTimelineSeverityFilter,
      timelineOrder,
      setTimelineOrder,
      timelineLivePaused,
      setTimelineLivePaused,
      timelineSummary,
      timelineRunItems,
      timelineRunArtifacts,
      timelineEvents,
      timelineSelectedEventId,
      setTimelineSelectedEventId,
      selectedTimelineEvent,
      timelineNoteAuthor,
      setTimelineNoteAuthor,
      timelineNoteText,
      setTimelineNoteText,
      onRefreshTimeline: () => void refreshTimeline(),
      onExportTimeline: () => void exportTimeline(),
      onAddTimelineNote: () => void addTimelineNote(),
      timelineNotes,
      onSubmitItemFeedback: (itemId, label) => void submitItemFeedback(itemId, label),
    },
    historyState: {
      history,
      activeRollbackId,
      onRollback: (snapshotId) => void rollback(snapshotId),
    },
    nav: {
      navigateToSurface,
      onRevisitSetupGuide: () => navigate(`${surfacePaths.onboarding}?mode=revisit`),
    },
  }

  return (
    <ConsoleProvider value={consoleValue}>
    <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-lg">
      Skip to content
    </a>
    <main className="min-h-screen bg-console-canvas pb-10" aria-label="Digest Control Center">
      <div className="mx-auto grid w-full max-w-[1560px] gap-5 px-4 py-5 md:px-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:px-8 lg:py-7">
        {mobileNavOpen ? (
          <div className="fixed inset-0 z-40 bg-black/30 lg:hidden" onClick={() => setMobileNavOpen(false)} />
        ) : null}
        <aside className={`${mobileNavOpen ? "fixed inset-x-0 top-0 z-50 max-h-screen overflow-y-auto p-4" : "hidden"} lg:sticky lg:relative lg:inset-auto lg:top-6 lg:z-auto lg:block lg:max-h-none lg:overflow-visible lg:p-0 lg:self-start`}>
          <div className="bg-console-rail space-y-5 rounded-[2rem] p-5 text-white shadow-[0_30px_70px_-40px_rgba(15,23,42,0.9)] animate-surface-enter lg:max-h-[calc(100vh-3rem)] lg:overflow-y-auto lg:overscroll-contain lg:pr-3 [scrollbar-gutter:stable]">
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/60">Vyno</p>
                  <h1 className="font-display text-[1.6rem] tracking-tight text-white">Control Center</h1>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="border border-white/10 bg-white/5 text-white hover:bg-white/10 lg:hidden"
                  onClick={() => setMobileNavOpen((prev) => !prev)}
                  aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
                  aria-expanded={mobileNavOpen}
                >
                  {mobileNavOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-sm leading-6 text-white/68">
                {onboardingDone
                  ? "Premium daily workspace for signals, automation, and intervention."
                  : "Guided setup canvas for turning a raw workspace into a recurring digest product."}
              </p>
            </div>

            <div className="space-y-2">
              <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">Navigation</p>
              <nav aria-label="Workspace surfaces" className="space-y-2">
                {visibleNavItems.map((item, index) => {
                  const Icon = item.icon
                  const badge =
                    item.id === "onboarding"
                      ? `${onboarding?.progress.completed ?? 0}/${onboarding?.progress.total ?? 0}`
                      : undefined
                  return (
                    <NavLink
                      key={item.id}
                      to={surfacePaths[item.id]}
                      className={({ isActive }) =>
                        `group flex min-h-[58px] w-full items-center justify-between rounded-[1.35rem] border px-3.5 py-3 text-left transition-all duration-200 ${
                          isActive
                            ? "border-white/18 bg-white/12 shadow-[0_18px_30px_-28px_rgba(255,255,255,0.9)]"
                            : "border-white/8 bg-white/[0.03] hover:border-white/14 hover:bg-white/[0.08]"
                        }`
                      }
                      style={{ animationDelay: `${index * 35}ms` }}
                    >
                      {({ isActive }) => (
                        <>
                          <span className="flex items-center gap-3">
                            <span className={`rounded-2xl p-2 ${isActive ? "bg-white/12" : "bg-white/[0.06]"}`}>
                              <Icon className="h-4 w-4 text-white" />
                            </span>
                            <span>
                              <span className="block text-sm font-semibold text-white">{item.label}</span>
                              <span className="block text-[11px] text-white/55">{item.hint}</span>
                            </span>
                          </span>
                          {badge ? (
                            <Badge variant={item.id === "onboarding" && !onboardingDone ? "warning" : "secondary"} className="bg-white/10 text-white">
                              {badge}
                            </Badge>
                          ) : isActive ? (
                            <Badge variant="outline" className="border-white/10 bg-white/8 text-white">
                              Open
                            </Badge>
                          ) : null}
                        </>
                      )}
                    </NavLink>
                  )
                })}
              </nav>
            </div>

            <div className="rounded-[1.6rem] border border-white/10 bg-white/5 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/55">System pulse</p>
              <div className="mt-3 space-y-3 text-sm text-white/78">
                <div className="flex items-center justify-between">
                  <span>Run state</span>
                  <Badge variant={runStatus?.active ? "warning" : "success"} className="text-[10px]">
                    {runStatus?.active ? "Running" : "Idle"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Schedule</span>
                  <span className="truncate text-right">
                    {scheduleStatus?.enabled ? (scheduleStatus.next_run_at || "Scheduled") : "Not scheduled"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Source health</span>
                  <span>{sourceHealth.length > 0 ? `${sourceHealth.length} issues` : "Clear"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Default mode</span>
                  <span>{runPolicy.default_mode}</span>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-col gap-5">
        <header className="rounded-[2rem] border border-border/80 bg-panel-subtle p-5 animate-surface-enter">
          <div className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_auto] 2xl:items-end">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="lg:hidden"
                  onClick={() => setMobileNavOpen((prev) => !prev)}
                  aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
                  aria-expanded={mobileNavOpen}
                >
                  {mobileNavOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
                  {mobileNavOpen ? "Close" : "Menu"}
                </Button>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary/80">Dashboard builder style workspace</p>
              </div>
              <h1 className="max-w-[11ch] font-display text-3xl leading-[0.92] tracking-[-0.04em] text-foreground md:text-[2.85rem]">
                Daily digest orchestration
              </h1>
              <p className="max-w-3xl text-[0.96rem] leading-7 text-muted-foreground">
                A modular workspace for setup, source management, run orchestration, and operational review without falling back to generic admin chrome.
              </p>
            </div>

            <div className="rounded-[1.6rem] border border-border/80 bg-white/88 p-3 shadow-[0_22px_34px_-28px_rgba(15,23,42,0.35)] 2xl:max-w-[42rem] 2xl:justify-self-end">
              <div className="flex flex-wrap items-center gap-2 2xl:justify-end">
                {runStatus?.active ? <Badge variant="warning">Active {runStatus.active.run_id}</Badge> : <Badge variant="success">No active run</Badge>}
                {runStatus?.latest ? <Badge variant="outline">Last {runStatus.latest.status}</Badge> : null}
                {runStatus?.latest_completed && runStatus.latest_completed.source_error_count > 0 ? (
                  <Badge variant="warning">Source errors {runStatus.latest_completed.source_error_count}</Badge>
                ) : null}
                <Button variant="outline" onClick={() => void refreshAll()} disabled={loading || saving}>
                {loading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <RefreshCcw className="h-4 w-4" />}
                {loading ? "Refreshing..." : "Refresh"}
                </Button>
                <div className="min-w-[220px]">
                  <Select
                    value={runNowModeOverride}
                    onValueChange={setRunNowModeOverride}
                    disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id) || !runPolicy.allow_run_override}
                  >
                    <SelectTrigger className="rounded-full bg-background/85">
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
                <Button onClick={() => void runNow()} disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id)}>
                  {runNowLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
                  {runNowLoading ? "Starting..." : "Run now"}
                </Button>
              </div>
            </div>
          </div>
        </header>

        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4 animate-surface-enter [animation-delay:40ms]" aria-label="Run status ribbon">
          <div className="console-status-ribbon rounded-[1.4rem] px-4 py-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-primary/75">Surface</p>
            <p className="mt-2 font-display text-xl">{currentSurface}</p>
          </div>
          <div className="console-status-ribbon rounded-[1.4rem] px-4 py-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-primary/75">Mode default</p>
            <p className="mt-2 font-display text-xl">{runPolicy.default_mode}</p>
          </div>
          <div className="console-status-ribbon rounded-[1.4rem] px-4 py-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-primary/75">Source health</p>
            <p className="mt-2 font-display text-xl">{sourceHealth.length > 0 ? `${sourceHealth.length} issues` : "Clear"}</p>
          </div>
          <div className="console-status-ribbon rounded-[1.4rem] px-4 py-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-primary/75">Latest completion</p>
            <p className="mt-2 font-display text-xl">{runStatus?.latest_completed?.status ?? "n/a"}</p>
          </div>
        </section>

        {globalLoadingText ? (
          <Card aria-live="polite" aria-busy className="border-primary/20 bg-primary/5">
            <CardContent className="flex items-center gap-2 py-3">
              <Loader2 className="h-4 w-4 text-primary motion-safe:animate-spin motion-reduce:animate-none" />
              <p className="text-sm font-medium text-foreground">{globalLoadingText}</p>
            </CardContent>
          </Card>
        ) : null}

        {showRunActivity ? (
          <Card aria-live="polite" aria-busy={digestBusy} className="border-primary/25 bg-card/95">
            <CardHeader className="pb-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  <CardTitle className="font-display text-base">Digest Activity</CardTitle>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={digestBusy ? "warning" : "success"}>{digestBusy ? "Running" : "Completed"}</Badge>
                  <Badge variant="secondary">run_id: {runProgress?.run_id || runStatus?.active?.run_id || "-"}</Badge>
                </div>
              </div>
              <CardDescription className="text-xs">{digestLoadingMessage || "Digest activity is idle."}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {runProgress && typeof runProgress.percent === "number" ? (
                <div className="space-y-1">
                  <Progress value={runProgress.percent} />
                  <p className="text-xs text-muted-foreground">{Math.round(runProgress.percent)}% complete</p>
                </div>
              ) : (
                <div className="space-y-1">
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div className="h-full w-1/3 bg-primary motion-safe:animate-pulse motion-reduce:animate-none" />
                  </div>
                  <p className="text-xs text-muted-foreground">{digestLoadingMessage || "Waiting for digest activity."}</p>
                </div>
              )}
              {runProgress ? (
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Clock3 className="h-3.5 w-3.5" /> Elapsed {formatElapsed(runProgress.elapsed_s)}
                  </span>
                  {runActivityFacts.map((fact) => (
                    <Badge key={fact} variant="secondary" className="text-[11px]">
                      {fact}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}

        <InlineNotice notice={globalNotice} onDismiss={() => clearScopedNotice("global")} />

          <section id="main-content" className="space-y-4 animate-surface-enter" aria-live="polite" aria-label="Console surface content">
            {loading || !profile ? (
              <Card aria-busy>
                <CardHeader className="pb-2">
                  <div className="h-5 w-52 rounded-md skeleton-shimmer" />
                  <div className="h-3.5 w-72 rounded-md skeleton-shimmer" />
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid gap-3 md:grid-cols-4">
                    <div className="h-20 rounded-xl skeleton-shimmer" />
                    <div className="h-20 rounded-xl skeleton-shimmer" />
                    <div className="h-20 rounded-xl skeleton-shimmer" />
                    <div className="h-20 rounded-xl skeleton-shimmer" />
                  </div>
                  <div className="h-44 rounded-xl skeleton-shimmer" />
                </CardContent>
              </Card>
            ) : (
              <Routes>
                <Route
                  path="/"
                  element={
                    onboardingDone ? (
                      <ErrorBoundary><DashboardPage /></ErrorBoundary>
                    ) : (
                      <Navigate to={surfacePaths.onboarding} replace />
                    )
                  }
                />
                <Route
                  path="/run"
                  element={<ErrorBoundary><RunCenterPage /></ErrorBoundary>}
                />
                <Route
                  path="/onboarding"
                  element={<ErrorBoundary><OnboardingPage /></ErrorBoundary>}
                />
                <Route
                  path="/sources"
                  element={<ErrorBoundary><SourcesPage /></ErrorBoundary>}
                />
                <Route
                  path="/profile"
                  element={<ErrorBoundary><ProfilePage /></ErrorBoundary>}
                />
                <Route
                  path="/schedule"
                  element={<ErrorBoundary><SchedulePage /></ErrorBoundary>}
                />
                <Route
                  path="/timeline"
                  element={<ErrorBoundary><TimelinePage /></ErrorBoundary>}
                />
                <Route
                  path="/history"
                  element={<ErrorBoundary><HistoryPage /></ErrorBoundary>}
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            )}
          </section>
        </div>
      </div>
      <Toaster />
      <ConfirmDialog state={confirmState} onClose={handleConfirmClose} />
    </main>
    </ConsoleProvider>
  )
}

export default App
