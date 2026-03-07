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
import { api } from "@/lib/api"
import {
  diffObjects,
  formatElapsed,
  parseProfilePayload,
  sourceHealthMatches,
  surfaceFromLegacyQuery,
  toInt,
} from "@/lib/console-utils"
import { navItems, surfaceForPathname, surfacePaths } from "@/app/navigation"
import type {
  ConsoleSurface,
  HistoryItem,
  Notice,
  NoticeScope,
  OnboardingStatus,
  PreviewResult,
  PreflightReport,
  RunPolicy,
  RunProgress,
  RunStatus,
  SaveAction,
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
import { ReviewPage } from "@/features/review/ReviewPage"
import { RunCenterPage } from "@/features/run-center/RunCenterPage"
import { SourcesPage } from "@/features/sources/SourcesPage"
import { TimelinePage } from "@/features/timeline/TimelinePage"

function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const uiStateHydratedRef = useRef(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [sourceTypes, setSourceTypes] = useState<string[]>([])
  const [sources, setSources] = useState<SourceMap>({})
  const [sourceType, setSourceType] = useState("rss")
  const [sourceValue, setSourceValue] = useState("")
  const [sourceSearch, setSourceSearch] = useState("")
  const [showAllUnifiedSources, setShowAllUnifiedSources] = useState(false)
  const [sourceStatusFilter, setSourceStatusFilter] = useState<"all" | "healthy" | "failing">("all")
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null)
  const [profileBaseline, setProfileBaseline] = useState<Record<string, unknown> | null>(null)
  const [profileJson, setProfileJson] = useState("")
  const [profileDiff, setProfileDiff] = useState<Record<string, unknown>>({})
  const [profileDiffComputedAt, setProfileDiffComputedAt] = useState("")
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null)
  const [runProgress, setRunProgress] = useState<RunProgress | null>(null)
  const [sourceHealth, setSourceHealth] = useState<SourceHealthItem[]>([])
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null)
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
  const [timelineRunId, setTimelineRunId] = useState("")
  const [timelineStageFilter, setTimelineStageFilter] = useState("all")
  const [timelineSeverityFilter, setTimelineSeverityFilter] = useState("all")
  const [timelineOrder, setTimelineOrder] = useState<"asc" | "desc">("desc")
  const [timelineLivePaused, setTimelineLivePaused] = useState(false)
  const [timelineSelectedEventId, setTimelineSelectedEventId] = useState(0)
  const [timelineNoteAuthor, setTimelineNoteAuthor] = useState("admin")
  const [timelineNoteText, setTimelineNoteText] = useState("")
  const [globalNotice, setGlobalNotice] = useState<Notice | null>(null)
  const [localNotices, setLocalNotices] = useState<Partial<Record<Exclude<NoticeScope, "global">, Notice>>>({})
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const currentSurface = surfaceForPathname(location.pathname)

  const sortedSourceRows = useMemo(
    () => Object.entries(sources).sort((a, b) => a[0].localeCompare(b[0])),
    [sources],
  )
  const totalSourceCount = useMemo(
    () => sortedSourceRows.reduce((sum, [, values]) => sum + values.length, 0),
    [sortedSourceRows],
  )
  const unifiedSourceRows = useMemo(() => {
    const flattened: Array<{ type: string; source: string }> = []
    for (const [type, values] of sortedSourceRows) {
      for (const value of values) {
        flattened.push({ type, source: String(value) })
      }
    }
    return flattened.map((row) => {
      const matches = sourceHealth.filter((item) => sourceHealthMatches(row.type, row.source, item))
      const latest = matches[0]
      return {
        key: `${row.type}:${row.source}`,
        type: row.type,
        source: row.source,
        count: matches.reduce((sum, match) => sum + Math.max(0, match.count || 0), 0),
        health: matches.length > 0 ? "failing" : "healthy",
        last_error: latest?.last_error || "-",
        last_seen: latest?.last_seen || "-",
        hint: latest?.hint || "-",
      } satisfies UnifiedSourceRow
    })
  }, [sortedSourceRows, sourceHealth])
  const filteredUnifiedSourceRows = useMemo(() => {
    const query = sourceSearch.trim().toLowerCase()
    return unifiedSourceRows.filter((row) => {
      if (sourceStatusFilter !== "all" && row.health !== sourceStatusFilter) return false
      if (!query) return true
      return (
        row.type.toLowerCase().includes(query) ||
        row.source.toLowerCase().includes(query) ||
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

  const onboardingDone = Boolean(
    onboarding && onboarding.progress.total > 0 && onboarding.progress.completed >= onboarding.progress.total,
  )
  const setupPercent = onboarding?.progress.total
    ? Math.round((onboarding.progress.completed / onboarding.progress.total) * 100)
    : 0
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
            : saveAction === "profile-validate"
              ? "Validating profile..."
              : saveAction === "profile-diff"
                ? "Computing profile diff..."
                : saveAction === "profile-save"
                  ? "Saving profile overlay..."
                  : saveAction === "run-policy-save"
                    ? "Saving run policy..."
                    : saveAction === "timeline-refresh"
                      ? "Refreshing timeline..."
                      : saveAction === "timeline-export"
                        ? "Exporting timeline..."
                        : saveAction === "timeline-note"
                          ? "Saving timeline note..."
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
      void Promise.all([
        api<RunStatus>("/api/run-status"),
        api<RunProgress>("/api/run-progress"),
        api<{ items: SourceHealthItem[] }>("/api/source-health"),
        api<OnboardingStatus>("/api/onboarding/status"),
        api<{ runs: TimelineRun[] }>("/api/timeline/runs?limit=50"),
        api<{ run_policy: RunPolicy }>("/api/config/run-policy"),
      ])
        .then(([status, progress, health, onboardingStatus, timelineData, policyData]) => {
          setRunStatus(status)
          setRunProgress(progress.available ? progress : null)
          setSourceHealth(health.items)
          setOnboarding(onboardingStatus)
          setTimelineRuns(timelineData.runs)
          setRunPolicy(policyData.run_policy)
          if (!timelineRunId && timelineData.runs.length > 0) {
            setTimelineRunId(timelineData.runs[0].run_id)
          }
        })
        .catch(() => undefined)
    }, 8000)
    return () => clearInterval(timer)
  }, [timelineRunId])

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

  async function refreshAll() {
    setLoading(true)
    try {
      const [
        typeData,
        sourceData,
        profileData,
        historyData,
        statusData,
        progressData,
        healthData,
        onboardingData,
        sourcePackData,
        timelineData,
        policyData,
      ] = await Promise.all([
        api<{ types: string[] }>("/api/config/source-types"),
        api<{ sources: SourceMap }>("/api/config/sources"),
        api<{ profile: Record<string, unknown> }>("/api/config/profile"),
        api<{ snapshots: HistoryItem[] }>("/api/config/history"),
        api<RunStatus>("/api/run-status"),
        api<RunProgress>("/api/run-progress"),
        api<{ items: SourceHealthItem[] }>("/api/source-health"),
        api<OnboardingStatus>("/api/onboarding/status"),
        api<{ packs: SourcePack[] }>("/api/onboarding/source-packs"),
        api<{ runs: TimelineRun[] }>("/api/timeline/runs?limit=50"),
        api<{ run_policy: RunPolicy }>("/api/config/run-policy"),
      ])
      setSourceTypes(typeData.types)
      setSources(sourceData.sources)
      setProfile(profileData.profile)
      setProfileBaseline(profileData.profile)
      setProfileJson(JSON.stringify(profileData.profile, null, 2))
      setProfileDiff({})
      setProfileDiffComputedAt("")
      setHistory(historyData.snapshots)
      setRunStatus(statusData)
      setRunProgress(progressData.available ? progressData : null)
      setSourceHealth(healthData.items)
      setOnboarding(onboardingData)
      setSourcePacks(sourcePackData.packs)
      setRunPolicy(policyData.run_policy)
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
      await refreshAll()
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
    setSourceType(row.type)
    setSourceValue(row.source)
    setScopedNotice("sources", "ok", `Loaded ${row.type} source for editing.`)
  }

  async function deleteUnifiedSourceRow(row: UnifiedSourceRow) {
    if (!window.confirm(`Delete ${row.type} source?\n${row.source}`)) return
    setSaveAction("source-remove")
    setSaving(true)
    try {
      await api("/api/config/sources/remove", {
        method: "POST",
        body: JSON.stringify({ source_type: row.type, value: row.source }),
      })
      await refreshAll()
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
      await refreshAll()
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

  async function validateProfile() {
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
      setScopedNotice("review", "ok", "Profile validated.")
    } catch (error) {
      setScopedNotice("review", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function computeProfileDiff() {
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
      setScopedNotice("review", "ok", "Diff updated.")
    } catch (error) {
      setScopedNotice("review", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function saveProfile() {
    setSaveAction("profile-save")
    setSaving(true)
    try {
      const parsed = parseProfilePayload(profileJson)
      await api("/api/config/profile/save", {
        method: "POST",
        body: JSON.stringify({ profile: parsed }),
      })
      await refreshAll()
      setScopedNotice("review", "ok", "Profile overlay saved.")
    } catch (error) {
      setScopedNotice("review", "error", String(error))
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  async function saveRunPolicy() {
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
      setScopedNotice("profile", "ok", "Run policy saved.")
    } catch (error) {
      setScopedNotice("profile", "error", String(error))
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
      await refreshAll()
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
      await refreshAll()
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
      const [eventsResult, notesResult, summaryResult] = await Promise.all([
        api<{ events: TimelineEvent[] }>(`/api/timeline/events?run_id=${runIdQuery}&limit=400${stageQuery}${severityQuery}${orderQuery}`),
        api<{ notes: TimelineNote[] }>(`/api/timeline/notes?run_id=${runIdQuery}&limit=200`),
        api<{ summary: TimelineSummary }>(`/api/timeline/summary?run_id=${runIdQuery}`).catch(() => ({ summary: null as TimelineSummary | null })),
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

  function navigateToSurface(surface: ConsoleSurface) {
    navigate(surfacePaths[surface])
  }

  function renderSetupStepAction(stepId: string) {
    if (stepId === "preflight") {
      return (
        <Button variant="outline" size="sm" onClick={() => void runOnboardingPreflight()} disabled={saving}>
          {saveAction === "onboarding-preflight" ? <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" /> : null}
          {saveAction === "onboarding-preflight" ? "Running..." : "Run preflight"}
        </Button>
      )
    }
    if (stepId === "sources") {
      const topPack = sourcePacks[0]
      if (topPack) {
        return (
          <Button variant="outline" size="sm" onClick={() => void applySourcePack(topPack.id)} disabled={saving}>
            {saveAction === "source-pack" && activeSourcePackId === topPack.id ? (
              <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" />
            ) : null}
            {saveAction === "source-pack" && activeSourcePackId === topPack.id ? "Applying..." : `Apply ${topPack.name}`}
          </Button>
        )
      }
      return <Button variant="outline" size="sm" onClick={() => navigateToSurface("sources")}>Open sources</Button>
    }
    if (stepId === "outputs" || stepId === "profile") {
      return <Button variant="outline" size="sm" onClick={() => navigateToSurface("profile")}>Open profile</Button>
    }
    if (stepId === "preview") {
      return (
        <Button variant="outline" size="sm" onClick={() => void runOnboardingPreview()} disabled={previewLoading || saving}>
          {previewLoading ? <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-3.5 w-3.5" />}
          {previewLoading ? "Running..." : "Run preview"}
        </Button>
      )
    }
    if (stepId === "activate") {
      return (
        <Button size="sm" onClick={() => void activateOnboarding()} disabled={saving || previewLoading || activateLoading || Boolean(runStatus?.active?.run_id)}>
          {activateLoading ? <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-3.5 w-3.5" />}
          {activateLoading ? "Starting..." : "Activate"}
        </Button>
      )
    }
    if (stepId === "health") {
      return (
        <Button variant="outline" size="sm" onClick={() => void runNow()} disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id)}>
          {runNowLoading ? <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" /> : <RefreshCcw className="h-3.5 w-3.5" />}
          Re-check with run
        </Button>
      )
    }
    return null
  }

  return (
    <main className="min-h-screen bg-console-canvas pb-10" aria-label="Digest Control Center">
      <div className="mx-auto flex w-full max-w-[1380px] flex-col gap-5 px-4 py-6 md:px-6 lg:px-8 lg:py-8">
        <header className="rounded-2xl border border-border/80 bg-card/90 p-5 shadow-lg shadow-primary/5 backdrop-blur-sm animate-surface-enter">
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="lg:hidden"
                  onClick={() => setMobileNavOpen((prev) => !prev)}
                  aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
                >
                  {mobileNavOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
                  {mobileNavOpen ? "Close" : "Menu"}
                </Button>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary/90">Digest Operations</p>
              </div>
              <h1 className="font-display text-3xl tracking-tight text-foreground md:text-4xl">Control Center</h1>
              <p className="max-w-3xl text-sm text-muted-foreground">
                Route-based operator workspace for onboarding, run control, and long-term maintenance without losing feature coverage.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 xl:justify-end">
              {runStatus?.active ? <Badge variant="warning">Active: {runStatus.active.run_id}</Badge> : <Badge variant="success">No active run</Badge>}
              {runStatus?.latest ? <Badge variant="secondary">Last: {runStatus.latest.status}</Badge> : null}
              {runStatus?.latest_completed && runStatus.latest_completed.source_error_count > 0 ? (
                <Badge variant="warning">Source errors: {runStatus.latest_completed.source_error_count}</Badge>
              ) : null}
              <Button variant="outline" onClick={() => void refreshAll()} disabled={loading || saving}>
                {loading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <RefreshCcw className="h-4 w-4" />}
                {loading ? "Refreshing..." : "Refresh"}
              </Button>
              <div className="min-w-[190px]">
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
              <Button onClick={() => void runNow()} disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id)}>
                {runNowLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
                {runNowLoading ? "Starting..." : "Run now"}
              </Button>
            </div>
          </div>
        </header>

        <section className="console-status-ribbon rounded-2xl px-4 py-3 animate-surface-enter [animation-delay:40ms]" aria-label="Run status ribbon">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={runStatus?.active ? "warning" : "success"}>{runStatus?.active ? "Run active" : "Run idle"}</Badge>
            <Badge variant="secondary">surface: {currentSurface}</Badge>
            <Badge variant="secondary">mode default: {runPolicy.default_mode}</Badge>
            <Badge variant={sourceHealth.length > 0 ? "warning" : "success"}>
              {sourceHealth.length > 0 ? `source issues: ${sourceHealth.length}` : "source health clear"}
            </Badge>
            {runStatus?.latest_completed ? <Badge variant="secondary">latest completed: {runStatus.latest_completed.status}</Badge> : null}
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

        <div className="grid gap-5 lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className={`${mobileNavOpen ? "block" : "hidden"} space-y-4 lg:block`}>
            <Card className="border-border/80 bg-card/95 animate-surface-enter">
              <CardHeader className="pb-3">
                <CardTitle className="font-display text-base">Workspace Navigation</CardTitle>
                <CardDescription>Route-based surfaces for daily operations and advanced controls.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <nav aria-label="Workspace surfaces" className="space-y-2">
                  {navItems.map((item, index) => {
                    const Icon = item.icon
                    const badge =
                      item.id === "onboarding"
                        ? onboardingDone
                          ? "Ready"
                          : `${onboarding?.progress.completed ?? 0}/${onboarding?.progress.total ?? 0}`
                        : undefined
                    return (
                      <NavLink
                        key={item.id}
                        to={surfacePaths[item.id]}
                        className={({ isActive }) =>
                          `group flex min-h-[52px] w-full items-center justify-between rounded-xl border px-3 py-2.5 text-left transition-all duration-200 ${
                            isActive
                              ? "border-primary/40 bg-primary/10 shadow-sm"
                              : "border-border/70 bg-background/60 hover:border-primary/20 hover:bg-primary/5"
                          }`
                        }
                        style={{ animationDelay: `${index * 35}ms` }}
                      >
                        {({ isActive }) => (
                          <>
                            <span className="flex items-center gap-2">
                              <Icon className="h-4 w-4 text-primary" />
                              <span>
                                <span className="block text-sm font-semibold">{item.label}</span>
                                <span className="block text-[11px] text-muted-foreground">{item.hint}</span>
                              </span>
                            </span>
                            {badge ? <Badge variant={item.id === "onboarding" && !onboardingDone ? "warning" : "secondary"}>{badge}</Badge> : isActive ? <Badge variant="secondary">Open</Badge> : null}
                          </>
                        )}
                      </NavLink>
                    )
                  })}
                </nav>
              </CardContent>
            </Card>

            <Card className="border-border/80 bg-card/95 animate-surface-enter [animation-delay:80ms]">
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-base">Digest Health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="space-y-1 rounded-lg border border-border/70 bg-muted/15 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Setup status</p>
                  <div className="flex items-center justify-between">
                    <Badge variant={onboardingDone ? "success" : "warning"}>{onboardingDone ? "Ready" : "In progress"}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {onboarding?.progress.completed ?? 0}/{onboarding?.progress.total ?? 0}
                    </span>
                  </div>
                  <Progress value={setupPercent} className="transition-all duration-500" />
                </div>
                {sourceHealth.length > 0 ? (
                  <div className="rounded-lg border border-amber-300/50 bg-amber-50/60 p-3">
                    <p className="text-xs font-semibold text-amber-900">Source health alerts: {sourceHealth.length}</p>
                    <p className="mt-1 text-xs text-amber-800">Open Sources workspace to inspect diagnostics and apply fixes.</p>
                  </div>
                ) : (
                  <div className="rounded-lg border border-emerald-300/50 bg-emerald-50/60 p-3">
                    <p className="text-xs font-semibold text-emerald-900">No source alerts in recent runs.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </aside>

          <section className="space-y-4 animate-surface-enter" aria-live="polite" aria-label="Console surface content">
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
                    <DashboardPage
                      runStatus={runStatus}
                      sourceHealth={sourceHealth}
                      setupPercent={setupPercent}
                      timelineRuns={timelineRuns}
                      onOpenRun={() => navigateToSurface("run")}
                      onOpenSources={() => navigateToSurface("sources")}
                      onOpenTimeline={() => navigateToSurface("timeline")}
                    />
                  }
                />
                <Route
                  path="/run"
                  element={
                    <RunCenterPage
                      notice={localNotices.run}
                      onDismissNotice={() => clearScopedNotice("run")}
                      runNowModeOverride={runNowModeOverride}
                      setRunNowModeOverride={setRunNowModeOverride}
                      runPolicy={runPolicy}
                      runStatus={runStatus}
                      saving={saving}
                      runNowLoading={runNowLoading}
                      loading={loading}
                      saveAction={saveAction}
                      onRefreshAll={() => void refreshAll()}
                      onRunNow={() => void runNow()}
                      onOpenTimeline={() => navigateToSurface("timeline")}
                    />
                  }
                />
                <Route
                  path="/onboarding"
                  element={
                    <OnboardingPage
                      notice={localNotices.onboarding}
                      onDismissNotice={() => clearScopedNotice("onboarding")}
                      onboarding={onboarding}
                      setupPercent={setupPercent}
                      preflight={preflight}
                      sourcePacks={sourcePacks}
                      previewResult={previewResult}
                      saveAction={saveAction}
                      activeSourcePackId={activeSourcePackId}
                      previewLoading={previewLoading}
                      activateLoading={activateLoading}
                      saving={saving}
                      runStatus={runStatus}
                      onRunPreflight={() => void runOnboardingPreflight()}
                      onApplySourcePack={(packId) => void applySourcePack(packId)}
                      onRunPreview={() => void runOnboardingPreview()}
                      onActivate={() => void activateOnboarding()}
                      renderSetupStepAction={renderSetupStepAction}
                    />
                  }
                />
                <Route
                  path="/sources"
                  element={
                    <SourcesPage
                      notice={localNotices.sources}
                      onDismissNotice={() => clearScopedNotice("sources")}
                      sources={sources}
                      sourceHealth={sourceHealth}
                      sourceType={sourceType}
                      setSourceType={setSourceType}
                      sourceValue={sourceValue}
                      setSourceValue={setSourceValue}
                      sourceTypes={sourceTypes}
                      saving={saving}
                      saveAction={saveAction}
                      onHandleSourceMutation={(action) => void handleSourceMutation(action)}
                      sourceSearch={sourceSearch}
                      setSourceSearch={setSourceSearch}
                      sourceStatusFilter={sourceStatusFilter}
                      setSourceStatusFilter={setSourceStatusFilter}
                      filteredUnifiedSourceRows={filteredUnifiedSourceRows}
                      unifiedRowsVisible={unifiedRowsVisible}
                      showAllUnifiedSources={showAllUnifiedSources}
                      setShowAllUnifiedSources={setShowAllUnifiedSources}
                      onEditUnifiedSourceRow={editUnifiedSourceRow}
                      onDeleteUnifiedSourceRow={(row) => void deleteUnifiedSourceRow(row)}
                    />
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProfilePage
                      notice={localNotices.profile}
                      onDismissNotice={() => clearScopedNotice("profile")}
                      profile={profile}
                      profileJson={profileJson}
                      setProfileJson={setProfileJson}
                      updateProfileField={updateProfileField}
                      runPolicy={runPolicy}
                      setRunPolicy={setRunPolicy}
                      seenResetDays={seenResetDays}
                      setSeenResetDays={setSeenResetDays}
                      seenResetConfirm={seenResetConfirm}
                      setSeenResetConfirm={setSeenResetConfirm}
                      seenResetPreviewCount={seenResetPreviewCount}
                      saveAction={saveAction}
                      saving={saving}
                      onSaveRunPolicy={() => void saveRunPolicy()}
                      onPreviewSeenReset={() => void previewSeenReset()}
                      onApplySeenReset={() => void applySeenReset()}
                    />
                  }
                />
                <Route
                  path="/review"
                  element={
                    <ReviewPage
                      notice={localNotices.review}
                      onDismissNotice={() => clearScopedNotice("review")}
                      saveAction={saveAction}
                      saving={saving}
                      profileJsonParseError={profileJsonParseError}
                      localDiffCount={localDiffCount}
                      localProfileDiff={localProfileDiff}
                      serverDiffCount={serverDiffCount}
                      profileDiff={profileDiff}
                      profileDiffComputedAt={profileDiffComputedAt}
                      onValidateProfile={() => void validateProfile()}
                      onComputeProfileDiff={() => void computeProfileDiff()}
                      onSaveProfile={() => void saveProfile()}
                    />
                  }
                />
                <Route
                  path="/timeline"
                  element={
                    <TimelinePage
                      notice={localNotices.timeline}
                      onDismissNotice={() => clearScopedNotice("timeline")}
                      timelineRunId={timelineRunId}
                      setTimelineRunId={setTimelineRunId}
                      timelineRuns={timelineRuns}
                      timelineStageFilter={timelineStageFilter}
                      setTimelineStageFilter={setTimelineStageFilter}
                      timelineStageOptions={timelineStageOptions}
                      timelineSeverityFilter={timelineSeverityFilter}
                      setTimelineSeverityFilter={setTimelineSeverityFilter}
                      timelineOrder={timelineOrder}
                      setTimelineOrder={setTimelineOrder}
                      timelineLivePaused={timelineLivePaused}
                      setTimelineLivePaused={setTimelineLivePaused}
                      saving={saving}
                      saveAction={saveAction}
                      onRefreshTimeline={() => void refreshTimeline()}
                      onExportTimeline={() => void exportTimeline()}
                      timelineSummary={timelineSummary}
                      timelineEvents={timelineEvents}
                      timelineSelectedEventId={timelineSelectedEventId}
                      setTimelineSelectedEventId={setTimelineSelectedEventId}
                      selectedTimelineEvent={selectedTimelineEvent}
                      timelineNoteAuthor={timelineNoteAuthor}
                      setTimelineNoteAuthor={setTimelineNoteAuthor}
                      timelineNoteText={timelineNoteText}
                      setTimelineNoteText={setTimelineNoteText}
                      onAddTimelineNote={() => void addTimelineNote()}
                      timelineNotes={timelineNotes}
                    />
                  }
                />
                <Route
                  path="/history"
                  element={
                    <HistoryPage
                      notice={localNotices.history}
                      onDismissNotice={() => clearScopedNotice("history")}
                      history={history}
                      saveAction={saveAction}
                      activeRollbackId={activeRollbackId}
                      saving={saving}
                      onRollback={(snapshotId) => void rollback(snapshotId)}
                    />
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            )}
          </section>
        </div>
      </div>
    </main>
  )
}

export default App
