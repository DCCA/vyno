import { useEffect, useMemo, useState } from "react"
import {
  Activity,
  CheckCircle2,
  Clock3,
  Database,
  History,
  LayoutDashboard,
  Loader2,
  Menu,
  Play,
  RefreshCcw,
  Rocket,
  Save,
  ScrollText,
  ShieldCheck,
  SlidersHorizontal,
  Undo2,
  X,
} from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"

type SourceMap = Record<string, string[]>

type SourceErrorDetail = {
  kind: string
  source: string
  error: string
  hint: string
}

type SourceHealthItem = {
  kind: string
  source: string
  count: number
  last_seen: string
  last_run_id: string
  last_error: string
  hint: string
}

type RunStatus = {
  active: { run_id: string; started_at: string } | null
  latest: {
    run_id: string
    status: string
    started_at: string
    source_error_count: number
    summary_error_count: number
  } | null
  latest_completed: {
    run_id: string
    status: string
    started_at: string
    source_error_count: number
    summary_error_count: number
    source_errors: SourceErrorDetail[]
  } | null
}

type RunProgress = {
  available: boolean
  run_id: string
  pipeline_run_id: string
  mode: string
  stage: string
  stage_label: string
  message: string
  stage_detail: string
  elapsed_s: number
  percent: number | null
  status: string
  is_active: boolean
  started_at: string
  updated_at: string
  details: Record<string, unknown>
  event_index: number
}

type HistoryItem = {
  id: string
  created_at: string
  action: string
  details: Record<string, unknown>
}

type PreflightCheck = {
  id: string
  label: string
  status: "pass" | "warn" | "fail"
  detail: string
  hint: string
  required: boolean
}

type PreflightReport = {
  generated_at_utc: string
  ok: boolean
  pass_count: number
  warn_count: number
  fail_count: number
  checks: PreflightCheck[]
}

type OnboardingStep = {
  id: string
  label: string
  status: "complete" | "pending"
  completed_at: string
  detail: string
}

type OnboardingStatus = {
  generated_at_utc: string
  steps: OnboardingStep[]
  progress: { completed: number; total: number }
  preflight: {
    ok: boolean
    pass_count: number
    warn_count: number
    fail_count: number
  }
  latest_completed: {
    run_id: string
    status: string
    started_at: string
    source_error_count: number
    summary_error_count: number
  } | null
}

type SourcePack = {
  id: string
  name: string
  description: string
  item_count: number
}

type PreviewResult = {
  run_id: string
  status: string
  source_error_count: number
  summary_error_count: number
  source_errors: string[]
  summary_errors: string[]
  source_count: number
  must_read_count: number
  skim_count: number
  video_count: number
  telegram_messages: string[]
  obsidian_note: string
}

type TimelineRun = {
  run_id: string
  status: string
  started_at: string
  window_start: string
  window_end: string
  event_count: number
}

type TimelineEvent = {
  id: number
  run_id: string
  event_index: number
  ts_utc: string
  stage: string
  severity: "info" | "warn" | "error"
  message: string
  elapsed_s: number
  details: Record<string, unknown>
}

type TimelineSummary = {
  run_id: string
  status: string
  started_at: string
  event_count: number
  error_event_count: number
  warn_event_count: number
  duration_s: number
  last_stage: string
  last_message: string
  final_item_count: number
  must_read_count: number
  skim_count: number
  video_count: number
  source_error_count: number
  summary_error_count: number
  mode?: {
    name: string
    use_last_completed_window: boolean
    only_new: boolean
    allow_seen_fallback: boolean
  }
  filter_funnel?: {
    fetched: number
    post_window: number
    post_seen: number
    post_block: number
    selected: number
  }
  strictness_score?: number
  strictness_level?: "low" | "medium" | "high" | string
  restriction_reasons?: Array<{
    key: string
    label: string
    dropped: number
    ratio_pct: number
  }>
  recommendations?: string[]
}

type TimelineNote = {
  id: number
  run_id: string
  created_at_utc: string
  author: string
  note: string
  labels: string[]
  actions: string[]
}

type RunPolicy = {
  default_mode: "fresh_only" | "balanced" | "replay_recent" | "backfill"
  allow_run_override: boolean
  seen_reset_guard: "confirm" | "disabled"
}

type SaveAction =
  | ""
  | "source-add"
  | "source-remove"
  | "onboarding-preflight"
  | "source-pack"
  | "profile-validate"
  | "profile-diff"
  | "profile-save"
  | "run-policy-save"
  | "timeline-refresh"
  | "timeline-export"
  | "timeline-note"
  | "seen-reset-preview"
  | "seen-reset-apply"
  | "rollback"

type ConsoleSurface = "dashboard" | "run" | "onboarding" | "sources" | "profile" | "review" | "timeline" | "history"

const API_BASE = (import.meta.env.VITE_API_BASE ?? "").trim().replace(/\/$/, "")
const API_TOKEN = import.meta.env.VITE_WEB_API_TOKEN ?? ""
const API_TOKEN_HEADER = import.meta.env.VITE_WEB_API_TOKEN_HEADER ?? "X-Digest-Api-Token"

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? undefined)
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  if (API_TOKEN) {
    headers.set(API_TOKEN_HEADER, API_TOKEN)
  }

  const target = API_BASE ? `${API_BASE}${path}` : path
  const response = await fetch(target, {
    ...init,
    headers,
  })
  if (!response.ok) {
    const body = await response.text()
    throw new Error(body || `request failed (${response.status})`)
  }
  return (await response.json()) as T
}

function toLines(values: string[] | undefined): string {
  return (values ?? []).join("\n")
}

function fromLines(value: string): string[] {
  return value
    .split("\n")
    .map((v) => v.trim())
    .filter(Boolean)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function diffObjects(base: Record<string, unknown>, target: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const keys = new Set([...Object.keys(base), ...Object.keys(target)])
  for (const key of keys) {
    const left = base[key]
    const right = target[key]
    if (isRecord(left) && isRecord(right)) {
      const nested = diffObjects(left, right)
      if (Object.keys(nested).length > 0) {
        out[key] = nested
      }
      continue
    }
    if (JSON.stringify(left) !== JSON.stringify(right)) {
      out[key] = right
    }
  }
  return out
}

function parseProfilePayload(value: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(value)
  if (!isRecord(parsed)) {
    throw new Error("Profile JSON must be an object.")
  }
  return parsed
}

function formatElapsed(seconds: number | undefined): string {
  const total = Math.max(0, Math.floor(seconds ?? 0))
  const mins = Math.floor(total / 60)
  const secs = total % 60
  if (mins <= 0) return `${secs}s`
  return `${mins}m ${secs}s`
}

function toInt(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return Math.trunc(value)
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

export default function App() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [sourceTypes, setSourceTypes] = useState<string[]>([])
  const [sources, setSources] = useState<SourceMap>({})
  const [sourceType, setSourceType] = useState("rss")
  const [sourceValue, setSourceValue] = useState("")
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
  const [notice, setNotice] = useState<{ kind: "ok" | "error"; text: string } | null>(null)
  const [surface, setSurface] = useState<ConsoleSurface>("dashboard")
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [consoleModeOverride, setConsoleModeOverride] = useState<"setup" | "manage" | null>(null)
  const [manageTab, setManageTab] = useState("sources")

  const sortedSourceRows = useMemo(
    () => Object.entries(sources).sort((a, b) => a[0].localeCompare(b[0])),
    [sources],
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
  const consoleMode = consoleModeOverride ?? (onboardingDone ? "manage" : "setup")
  const manageSurfaceToTab: Partial<Record<ConsoleSurface, string>> = {
    sources: "sources",
    profile: "profile",
    review: "review",
    timeline: "timeline",
    history: "history",
  }
  const activeManageTab = manageSurfaceToTab[surface] ?? "sources"
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
      ] =
        await Promise.all([
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
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({ kind: "error", text: "Select a source type and enter a value." })
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
      setNotice({ kind: "ok", text: `Source ${action} completed.` })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
        setNotice({ kind: "ok", text: `Run started: ${result.run_id}${modeText}` })
      } else {
        setNotice({ kind: "error", text: `Run already active: ${result.active_run_id}` })
      }
      const [status, progress] = await Promise.all([
        api<RunStatus>("/api/run-status"),
        api<RunProgress>(
          `/api/run-progress${result.run_id ? `?run_id=${encodeURIComponent(result.run_id)}` : ""}`,
        ),
      ])
      setRunStatus(status)
      setRunProgress(progress.available ? progress : null)
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({
        kind: result.ok ? "ok" : "error",
        text: result.ok
          ? `Preflight passed (${result.pass_count} checks).`
          : `Preflight found ${result.fail_count} failing checks.`,
      })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({
        kind: result.error_count > 0 ? "error" : "ok",
        text: `Source pack applied: added=${result.added_count}, existing=${result.existing_count}, errors=${result.error_count}.`,
      })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({ kind: "ok", text: `Preview run completed (${result.status}).` })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
    } finally {
      setPreviewLoading(false)
    }
  }

  async function activateOnboarding() {
    setActivateLoading(true)
    setSaving(true)
    try {
      const result = await api<{ started: boolean; run_id?: string; active_run_id?: string }>(
        "/api/onboarding/activate",
        {
          method: "POST",
        },
      )
      const [status, progress, onboardingStatus] = await Promise.all([
        api<RunStatus>("/api/run-status"),
        api<RunProgress>(
          `/api/run-progress${result.run_id ? `?run_id=${encodeURIComponent(result.run_id)}` : ""}`,
        ),
        api<OnboardingStatus>("/api/onboarding/status"),
      ])
      setRunStatus(status)
      setRunProgress(progress.available ? progress : null)
      setOnboarding(onboardingStatus)
      setNotice({
        kind: result.started ? "ok" : "error",
        text: result.started
          ? `Live run started: ${result.run_id}`
          : `Run already active: ${result.active_run_id}`,
      })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({ kind: "ok", text: "Profile validated." })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({ kind: "ok", text: "Diff updated." })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({ kind: "ok", text: "Profile overlay saved." })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({ kind: "ok", text: "Run policy saved." })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      const result = await api<{ affected_count: number; scope: string; older_than_days: number | null }>(
        "/api/seen/reset/preview",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      )
      setSeenResetPreviewCount(result.affected_count)
      setNotice({ kind: "ok", text: `Preview complete: ${result.affected_count} seen keys affected.` })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({ kind: "ok", text: `Seen reset applied: ${result.deleted_count} keys removed.` })
      await refreshAll()
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      setNotice({ kind: "ok", text: `Rolled back to ${snapshotId}.` })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
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
      const severityQuery =
        timelineSeverityFilter === "all" ? "" : `&severity=${encodeURIComponent(timelineSeverityFilter)}`
      const orderQuery = `&order=${encodeURIComponent(timelineOrder)}`

      const [eventsResult, notesResult, summaryResult] = await Promise.all([
        api<{ events: TimelineEvent[] }>(
          `/api/timeline/events?run_id=${runIdQuery}&limit=400${stageQuery}${severityQuery}${orderQuery}`,
        ),
        api<{ notes: TimelineNote[] }>(`/api/timeline/notes?run_id=${runIdQuery}&limit=200`),
        api<{ summary: TimelineSummary }>(`/api/timeline/summary?run_id=${runIdQuery}`).catch(() => ({ summary: null })),
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
      setNotice({ kind: "error", text: String(error) })
    } finally {
      if (!options?.silent) {
        setSaveAction("")
        setSaving(false)
      }
    }
  }

  async function addTimelineNote() {
    if (!timelineRunId || !timelineNoteText.trim()) {
      setNotice({ kind: "error", text: "Select a run and enter a note." })
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
      setNotice({ kind: "ok", text: "Timeline note saved." })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  useEffect(() => {
    if (surface === "onboarding") {
      setConsoleModeOverride("setup")
      return
    }
    if (surface === "dashboard" || surface === "run") {
      return
    }
    setConsoleModeOverride("manage")
    setManageTab(activeManageTab)
  }, [activeManageTab, surface])

  useEffect(() => {
    setMobileNavOpen(false)
  }, [surface])

  useEffect(() => {
    if (!timelineRunId) return
    void refreshTimeline({ silent: true })
  }, [timelineRunId, timelineStageFilter, timelineSeverityFilter, timelineOrder])

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
      setNotice({ kind: "ok", text: "Timeline JSON exported." })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
    } finally {
      setSaveAction("")
      setSaving(false)
    }
  }

  useEffect(() => {
    if (surface !== "timeline" || !timelineRunId) return
    if (timelineLivePaused) return
    const activeRunId = runStatus?.active?.run_id ?? ""
    const isLive = activeRunId !== "" && activeRunId === timelineRunId
    if (!isLive) return
    const timer = setInterval(() => {
      void refreshTimeline({ silent: true })
    }, 2500)
    return () => clearInterval(timer)
  }, [runStatus?.active?.run_id, surface, timelineLivePaused, timelineOrder, timelineRunId, timelineSeverityFilter, timelineStageFilter])

  function renderSetupStepAction(stepId: string) {
    if (stepId === "preflight") {
      return (
        <Button variant="outline" size="sm" onClick={() => void runOnboardingPreflight()} disabled={saving}>
          {saveAction === "onboarding-preflight" ? (
            <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" />
          ) : (
            <ShieldCheck className="h-3.5 w-3.5" />
          )}
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
      return (
        <Button variant="outline" size="sm" onClick={() => setSurface("sources")}>
          Open sources
        </Button>
      )
    }
    if (stepId === "outputs" || stepId === "profile") {
      return (
        <Button variant="outline" size="sm" onClick={() => setSurface("profile")}>
          Open profile
        </Button>
      )
    }
    if (stepId === "preview") {
      return (
        <Button variant="outline" size="sm" onClick={() => void runOnboardingPreview()} disabled={previewLoading || saving}>
          {previewLoading ? (
            <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" />
          ) : (
            <Play className="h-3.5 w-3.5" />
          )}
          {previewLoading ? "Running..." : "Run preview"}
        </Button>
      )
    }
    if (stepId === "activate") {
      return (
        <Button
          size="sm"
          onClick={() => void activateOnboarding()}
          disabled={saving || previewLoading || activateLoading || Boolean(runStatus?.active?.run_id)}
        >
          {activateLoading ? (
            <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" />
          ) : (
            <Play className="h-3.5 w-3.5" />
          )}
          {activateLoading ? "Starting..." : "Activate"}
        </Button>
      )
    }
    if (stepId === "health") {
      return (
        <Button
          variant="outline"
          size="sm"
          onClick={() => void runNow()}
          disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id)}
        >
          {runNowLoading ? (
            <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" />
          ) : (
            <RefreshCcw className="h-3.5 w-3.5" />
          )}
          Re-check with run
        </Button>
      )
    }
    return null
  }

  const navItems: Array<{
    id: ConsoleSurface
    label: string
    hint: string
    icon: typeof LayoutDashboard
    badge?: string
  }> = [
    { id: "dashboard", label: "Dashboard", hint: "status and alerts", icon: LayoutDashboard },
    { id: "run", label: "Run Center", hint: "manual run control", icon: Rocket },
    {
      id: "onboarding",
      label: "Onboarding",
      hint: "preflight and activation",
      icon: SlidersHorizontal,
      badge: onboardingDone ? "Ready" : `${onboarding?.progress.completed ?? 0}/${onboarding?.progress.total ?? 0}`,
    },
    { id: "sources", label: "Sources", hint: "inputs and health", icon: Database },
    { id: "profile", label: "Profile", hint: "policy and runtime", icon: ShieldCheck },
    { id: "review", label: "Review", hint: "validate and apply", icon: ScrollText },
    { id: "timeline", label: "Timeline", hint: "events and notes", icon: Activity },
    { id: "history", label: "History", hint: "snapshots and rollback", icon: History },
  ]

  const isManageSurface = surface === "sources" || surface === "profile" || surface === "review" || surface === "timeline" || surface === "history"

  return (
    <main className="min-h-screen bg-console-canvas">
      <div className="mx-auto flex w-full max-w-[1380px] flex-col gap-5 px-4 py-6 md:px-6 lg:px-8 lg:py-8">
        <header className="rounded-2xl border border-border/80 bg-card/90 p-5 shadow-lg shadow-primary/5 backdrop-blur-sm">
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
                Status-first workspace for daily operations, onboarding, and advanced maintenance without losing feature coverage.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 xl:justify-end">
              {runStatus?.active ? (
                <Badge variant="warning">Active: {runStatus.active.run_id}</Badge>
              ) : (
                <Badge variant="success">No active run</Badge>
              )}
              {runStatus?.latest ? <Badge variant="secondary">Last: {runStatus.latest.status}</Badge> : null}
              {runStatus?.latest_completed && runStatus.latest_completed.source_error_count > 0 ? (
                <Badge variant="warning">Source errors: {runStatus.latest_completed.source_error_count}</Badge>
              ) : null}
              <Button variant="outline" onClick={() => void refreshAll()} disabled={loading || saving}>
                {loading ? (
                  <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                ) : (
                  <RefreshCcw className="h-4 w-4" />
                )}
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
                {runNowLoading ? (
                  <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {runNowLoading ? "Starting..." : "Run now"}
              </Button>
            </div>
          </div>
        </header>

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
                  <Badge variant={digestBusy ? "warning" : "success"}>
                    {digestBusy ? "Running" : "Completed"}
                  </Badge>
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

        {notice ? (
          <Alert variant={notice.kind === "error" ? "destructive" : "default"}>
            <AlertTitle>{notice.kind === "error" ? "Action failed" : "Action completed"}</AlertTitle>
            <AlertDescription>{notice.text}</AlertDescription>
          </Alert>
        ) : null}

        <div className="grid gap-5 lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className={`${mobileNavOpen ? "block" : "hidden"} space-y-4 lg:block`}>
            <Card className="border-border/80 bg-card/95 animate-surface-enter">
              <CardHeader className="pb-3">
                <CardTitle className="font-display text-base">Workspace Navigation</CardTitle>
                <CardDescription>Focused surfaces for daily operations and advanced controls.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {navItems.map((item, index) => {
                  const Icon = item.icon
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSurface(item.id)}
                      className={`group flex w-full items-center justify-between rounded-xl border px-3 py-2.5 text-left transition-all duration-200 ${
                        surface === item.id
                          ? "border-primary/40 bg-primary/10 shadow-sm"
                          : "border-border/70 bg-background/60 hover:border-primary/20 hover:bg-primary/5"
                      }`}
                      style={{ animationDelay: `${index * 35}ms` }}
                    >
                      <span className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-primary" />
                        <span>
                          <span className="block text-sm font-semibold">{item.label}</span>
                          <span className="block text-[11px] text-muted-foreground">{item.hint}</span>
                        </span>
                      </span>
                      {item.badge ? (
                        <Badge variant={item.id === "onboarding" && !onboardingDone ? "warning" : "secondary"}>{item.badge}</Badge>
                      ) : null}
                    </button>
                  )
                })}
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
                    <p className="mt-1 text-xs text-amber-800">Open Sources page to inspect diagnostics and apply fixes.</p>
                  </div>
                ) : (
                  <div className="rounded-lg border border-emerald-300/50 bg-emerald-50/60 p-3">
                    <p className="text-xs font-semibold text-emerald-900">No source alerts in recent runs.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </aside>

          <section className="space-y-4 animate-surface-enter">
            {loading || !profile ? (
              <Card>
                <CardContent className="flex items-center gap-3 p-6">
                  <Loader2 className="h-5 w-5 animate-spin" /> Loading configuration...
                </CardContent>
              </Card>
            ) : surface === "dashboard" ? (
              <>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <Card className="border-border/80 bg-card/95">
                    <CardHeader className="pb-2">
                      <CardDescription>Latest run</CardDescription>
                      <CardTitle className="font-display text-2xl">{runStatus?.latest?.status ?? "n/a"}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card className="border-border/80 bg-card/95">
                    <CardHeader className="pb-2">
                      <CardDescription>Source alerts</CardDescription>
                      <CardTitle className="font-display text-2xl">{sourceHealth.length}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card className="border-border/80 bg-card/95">
                    <CardHeader className="pb-2">
                      <CardDescription>Setup completion</CardDescription>
                      <CardTitle className="font-display text-2xl">{setupPercent}%</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card className="border-border/80 bg-card/95">
                    <CardHeader className="pb-2">
                      <CardDescription>Timeline runs</CardDescription>
                      <CardTitle className="font-display text-2xl">{timelineRuns.length}</CardTitle>
                    </CardHeader>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle className="font-display">Operational Focus</CardTitle>
                    <CardDescription>Start with status and move into focused workflows.</CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    <Button className="justify-between" onClick={() => setSurface("run")}>
                      Open Run Center
                      <Rocket className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" className="justify-between" onClick={() => setSurface("sources")}>
                      Open Sources
                      <Database className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" className="justify-between" onClick={() => setSurface("timeline")}>
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
                        <div key={`${item.kind}:${item.source}`} className="rounded-lg border border-amber-300/40 bg-amber-50/30 p-2.5">
                          <p className="truncate font-mono text-[11px]">{item.source}</p>
                          <p className="text-xs text-muted-foreground">{item.count} failures in recent runs</p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ) : null}
              </>
            ) : surface === "run" ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="font-display">Run Center</CardTitle>
                    <CardDescription>Manual runs, mode overrides, and live progress visibility.</CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-4 md:grid-cols-[1fr,auto,auto]">
                    <div className="space-y-2">
                      <Label>One-time mode override</Label>
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
                    <div className="flex items-end">
                      <Button variant="outline" onClick={() => void refreshAll()} disabled={loading || saving}>
                        {loading ? (
                          <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                        ) : (
                          <RefreshCcw className="h-4 w-4" />
                        )}
                        {loading ? "Refreshing..." : "Refresh"}
                      </Button>
                    </div>
                    <div className="flex items-end">
                      <Button onClick={() => void runNow()} disabled={saving || runNowLoading || Boolean(runStatus?.active?.run_id)}>
                        {runNowLoading ? (
                          <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                        {runNowLoading ? "Starting..." : "Run now"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="font-display">Latest Completion Snapshot</CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-wrap gap-2">
                    <Badge variant="secondary">run_id: {runStatus?.latest_completed?.run_id ?? "-"}</Badge>
                    <Badge variant="secondary">status: {runStatus?.latest_completed?.status ?? "-"}</Badge>
                    <Badge variant="secondary">
                      source errors: {runStatus?.latest_completed?.source_error_count ?? 0}
                    </Badge>
                    <Badge variant="secondary">
                      summary errors: {runStatus?.latest_completed?.summary_error_count ?? 0}
                    </Badge>
                    <Button variant="outline" size="sm" onClick={() => setSurface("timeline")}>
                      Open timeline details
                    </Button>
                  </CardContent>
                </Card>
              </>
            ) : surface === "onboarding" ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="font-display">Setup Journey</CardTitle>
                    <CardDescription>Move from preflight to first healthy run using guided actions.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={onboarding?.preflight.ok ? "success" : "warning"}>
                        Preflight {onboarding?.preflight.ok ? "ready" : "needs attention"}
                      </Badge>
                      <Badge variant="secondary">
                        Steps {onboarding?.progress.completed ?? 0}/{onboarding?.progress.total ?? 0}
                      </Badge>
                    </div>
                    <Progress value={setupPercent} />
                    <div className="grid gap-3 md:grid-cols-2">
                      {(onboarding?.steps ?? []).map((step) => (
                        <div key={step.id} className="space-y-2 rounded-xl border bg-muted/20 p-3">
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-semibold leading-tight">{step.label}</p>
                            <Badge variant={step.status === "complete" ? "success" : "warning"}>
                              {step.status === "complete" ? <CheckCircle2 className="h-3 w-3" /> : null}
                              {step.status}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground">{step.detail}</p>
                          <p className="text-[11px] text-muted-foreground">
                            {step.completed_at ? `Completed at ${step.completed_at}` : "Not completed yet"}
                          </p>
                          <div>{renderSetupStepAction(step.id)}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="font-display">Preflight Checks</CardTitle>
                    <CardDescription>Validate environment, config, and writable paths before activation.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {preflight ? (
                      <>
                        <div className="mb-3 flex flex-wrap items-center gap-2">
                          <Badge variant={preflight.ok ? "success" : "warning"}>
                            {preflight.ok ? "Ready to activate" : "Fix required items"}
                          </Badge>
                          <Badge variant="secondary">pass: {preflight.pass_count}</Badge>
                          <Badge variant="secondary">warn: {preflight.warn_count}</Badge>
                          <Badge variant={preflight.fail_count > 0 ? "warning" : "secondary"}>fail: {preflight.fail_count}</Badge>
                        </div>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Check</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Detail</TableHead>
                              <TableHead>Hint</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {preflight.checks.map((check) => (
                              <TableRow key={check.id}>
                                <TableCell className="font-medium">{check.label}</TableCell>
                                <TableCell>
                                  <Badge
                                    variant={
                                      check.status === "pass"
                                        ? "success"
                                        : check.status === "warn"
                                          ? "warning"
                                          : "secondary"
                                    }
                                  >
                                    {check.status}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-xs text-muted-foreground">{check.detail}</TableCell>
                                <TableCell className="text-xs">{check.hint || "-"}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </>
                    ) : (
                      <div className="flex flex-wrap items-center gap-3">
                        <p className="text-sm text-muted-foreground">Run preflight to load checks for this environment.</p>
                        <Button variant="outline" onClick={() => void runOnboardingPreflight()} disabled={saving}>
                          {saveAction === "onboarding-preflight" ? (
                            <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                          ) : (
                            <ShieldCheck className="h-4 w-4" />
                          )}
                          {saveAction === "onboarding-preflight" ? "Running..." : "Run preflight"}
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="font-display">Source Packs</CardTitle>
                    <CardDescription>Apply curated source bundles to bootstrap ingestion quickly.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {sourcePacks.map((pack) => (
                      <div
                        key={pack.id}
                        className="flex flex-col gap-2 rounded-xl border bg-muted/15 p-3 md:flex-row md:items-center md:justify-between"
                      >
                        <div className="space-y-1">
                          <p className="text-sm font-semibold">{pack.name}</p>
                          <p className="text-xs text-muted-foreground">{pack.description}</p>
                          <p className="text-xs text-muted-foreground">{pack.item_count} sources</p>
                        </div>
                        <Button variant="outline" onClick={() => void applySourcePack(pack.id)} disabled={saving}>
                          {saveAction === "source-pack" && activeSourcePackId === pack.id ? (
                            <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                          ) : null}
                          {saveAction === "source-pack" && activeSourcePackId === pack.id ? "Applying..." : "Apply pack"}
                        </Button>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                {previewResult ? (
                  <Card>
                    <CardHeader>
                      <CardTitle className="font-display">Preview Result</CardTitle>
                      <CardDescription>Non-delivering output from the latest onboarding preview run.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="secondary">run_id: {previewResult.run_id}</Badge>
                        <Badge variant={previewResult.status === "success" ? "success" : "warning"}>
                          status: {previewResult.status}
                        </Badge>
                        <Badge variant="secondary">must-read: {previewResult.must_read_count}</Badge>
                        <Badge variant="secondary">skim: {previewResult.skim_count}</Badge>
                        <Badge variant="secondary">videos: {previewResult.video_count}</Badge>
                      </div>
                      <div className="grid gap-3 md:grid-cols-2">
                        <div>
                          <Label>Telegram Preview</Label>
                          <pre className="max-h-[260px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                            {(previewResult.telegram_messages ?? []).join("\n\n") || "-"}
                          </pre>
                        </div>
                        <div>
                          <Label>Obsidian Preview</Label>
                          <pre className="max-h-[260px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                            {previewResult.obsidian_note || "-"}
                          </pre>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ) : null}
              </>
            ) : isManageSurface ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="font-display">
                      {surface === "sources"
                        ? "Sources"
                        : surface === "profile"
                          ? "Profile"
                          : surface === "review"
                            ? "Review"
                            : surface === "timeline"
                              ? "Timeline"
                              : "History"}
                    </CardTitle>
                    <CardDescription>
                      {surface === "sources"
                        ? "Manage ingestion inputs and inspect source health."
                        : surface === "profile"
                          ? "Tune policy and runtime behavior with full parity."
                          : surface === "review"
                            ? "Validate, diff, and apply profile payload changes."
                            : surface === "timeline"
                              ? "Inspect live and historical run events."
                              : "Review and rollback saved snapshots."}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-wrap items-center gap-2">
                    <Badge variant={onboardingDone ? "success" : "warning"}>
                      {onboardingDone ? "Setup complete" : "Setup incomplete"}
                    </Badge>
                    <Badge variant="secondary">
                      Steps {onboarding?.progress.completed ?? 0}/{onboarding?.progress.total ?? 0}
                    </Badge>
                    {!onboardingDone ? <Button variant="outline" size="sm" onClick={() => setSurface("onboarding")}>Return to setup journey</Button> : null}
                  </CardContent>
                </Card>

                <Tabs value={manageTab} onValueChange={setManageTab} className="w-full">
                  <div className="sr-only">
                    <TabsList>
                      <TabsTrigger value="sources">Sources</TabsTrigger>
                      <TabsTrigger value="profile">Profile</TabsTrigger>
                      <TabsTrigger value="review">Review</TabsTrigger>
                      <TabsTrigger value="timeline">Timeline</TabsTrigger>
                      <TabsTrigger value="history">History</TabsTrigger>
                    </TabsList>
                  </div>

                  <TabsContent value="sources" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Source Management</CardTitle>
                        <CardDescription>
                          Add or remove tracked sources using canonicalized values saved in overlay.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="grid gap-4 md:grid-cols-[1fr,2fr,auto,auto]">
                        <div className="space-y-2">
                          <Label>Source Type</Label>
                          <Select value={sourceType} onValueChange={setSourceType}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select type" />
                            </SelectTrigger>
                            <SelectContent>
                              {sourceTypes.map((type) => (
                                <SelectItem key={type} value={type}>
                                  {type}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Value</Label>
                          <Input
                            placeholder="https://github.com/vercel-labs or owner/repo"
                            value={sourceValue}
                            onChange={(event) => setSourceValue(event.target.value)}
                          />
                        </div>
                        <div className="flex items-end">
                          <Button onClick={() => void handleSourceMutation("add")} disabled={saving}>
                            {saveAction === "source-add" ? (
                              <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                            ) : null}
                            {saveAction === "source-add" ? "Adding..." : "Add"}
                          </Button>
                        </div>
                        <div className="flex items-end">
                          <Button variant="outline" onClick={() => void handleSourceMutation("remove")} disabled={saving}>
                            {saveAction === "source-remove" ? (
                              <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                            ) : null}
                            {saveAction === "source-remove" ? "Removing..." : "Remove"}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Effective Sources</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Type</TableHead>
                              <TableHead>Count</TableHead>
                              <TableHead>Values</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {sortedSourceRows.map(([type, values]) => (
                              <TableRow key={type}>
                                <TableCell className="font-semibold">{type}</TableCell>
                                <TableCell>{values.length}</TableCell>
                                <TableCell className="font-mono text-xs text-muted-foreground">
                                  {values.slice(0, 5).join("\n") || "-"}
                                  {values.length > 5 ? `\n... (+${values.length - 5})` : ""}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>

                    {sourceHealth.length > 0 ? (
                      <Card>
                        <CardHeader>
                          <CardTitle className="font-display">Source Health</CardTitle>
                          <CardDescription>
                            Broken sources detected in recent runs. Fix these to improve source coverage.
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Source</TableHead>
                                <TableHead>Failures (20 runs)</TableHead>
                                <TableHead>Last Error</TableHead>
                                <TableHead>Suggested Fix</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {sourceHealth.slice(0, 12).map((item) => (
                                <TableRow key={`${item.kind}:${item.source}`}>
                                  <TableCell className="font-mono text-xs">{item.source}</TableCell>
                                  <TableCell>{item.count}</TableCell>
                                  <TableCell className="text-xs text-muted-foreground">{item.last_error}</TableCell>
                                  <TableCell className="text-xs">{item.hint}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </CardContent>
                      </Card>
                    ) : null}
                  </TabsContent>

                  <TabsContent value="profile" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Digest Policy</CardTitle>
                        <CardDescription>
                          Configure digest strictness and seen-item behavior without editing YAML.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label>Default Mode</Label>
                          <Select
                            value={runPolicy.default_mode}
                            onValueChange={(value) =>
                              setRunPolicy((prev) => ({
                                ...prev,
                                default_mode: (value as RunPolicy["default_mode"]) || "fresh_only",
                              }))
                            }
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="fresh_only">fresh_only (strict new)</SelectItem>
                              <SelectItem value="balanced">balanced (recommended)</SelectItem>
                              <SelectItem value="replay_recent">replay_recent</SelectItem>
                              <SelectItem value="backfill">backfill (advanced)</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-xs text-muted-foreground">
                            Current default for web-triggered runs. You can still override per run if enabled.
                          </p>
                        </div>
                        <div className="space-y-4">
                          <div className="flex items-center justify-between rounded-md border bg-muted/20 p-3">
                            <div>
                              <p className="text-sm font-medium">Allow run override</p>
                              <p className="text-xs text-muted-foreground">
                                Enables one-time mode selection in the Run now control.
                              </p>
                            </div>
                            <Switch
                              checked={runPolicy.allow_run_override}
                              onCheckedChange={(checked) =>
                                setRunPolicy((prev) => ({ ...prev, allow_run_override: checked }))
                              }
                            />
                          </div>
                          <div className="flex items-center justify-between rounded-md border bg-muted/20 p-3">
                            <div>
                              <p className="text-sm font-medium">Seen reset guard</p>
                              <p className="text-xs text-muted-foreground">
                                Require explicit confirmation before clearing seen history.
                              </p>
                            </div>
                            <Select
                              value={runPolicy.seen_reset_guard}
                              onValueChange={(value) =>
                                setRunPolicy((prev) => ({
                                  ...prev,
                                  seen_reset_guard: (value as RunPolicy["seen_reset_guard"]) || "confirm",
                                }))
                              }
                            >
                              <SelectTrigger className="w-[150px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="confirm">confirm</SelectItem>
                                <SelectItem value="disabled">disabled</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="flex justify-end">
                            <Button onClick={() => void saveRunPolicy()} disabled={saving}>
                              {saveAction === "run-policy-save" ? (
                                <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                              ) : (
                                <Save className="h-4 w-4" />
                              )}
                              {saveAction === "run-policy-save" ? "Saving..." : "Save Policy"}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Seen History Maintenance</CardTitle>
                        <CardDescription>
                          Preview and reset seen keys to reduce over-restrictive runs when content recycles.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="grid gap-3 md:grid-cols-[200px,auto,auto,1fr]">
                          <div className="space-y-2">
                            <Label>Older Than (days)</Label>
                            <Input value={seenResetDays} onChange={(event) => setSeenResetDays(event.target.value)} />
                          </div>
                          <div className="flex items-end">
                            <Button variant="outline" onClick={() => void previewSeenReset()} disabled={saving}>
                              {saveAction === "seen-reset-preview" ? (
                                <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                              ) : (
                                <RefreshCcw className="h-4 w-4" />
                              )}
                              {saveAction === "seen-reset-preview" ? "Previewing..." : "Preview Reset"}
                            </Button>
                          </div>
                          <div className="flex items-end">
                            <Button
                              variant="outline"
                              onClick={() => void applySeenReset()}
                              disabled={saving || runPolicy.seen_reset_guard === "confirm" && !seenResetConfirm}
                            >
                              {saveAction === "seen-reset-apply" ? (
                                <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                              ) : (
                                <Save className="h-4 w-4" />
                              )}
                              {saveAction === "seen-reset-apply" ? "Applying..." : "Apply Reset"}
                            </Button>
                          </div>
                          <div className="flex items-center gap-2 rounded-md border bg-muted/20 px-3">
                            <Switch checked={seenResetConfirm} onCheckedChange={setSeenResetConfirm} />
                            <span className="text-xs text-muted-foreground">
                              Confirm seen reset
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {seenResetPreviewCount === null
                            ? "No preview yet."
                            : `Preview affected keys: ${seenResetPreviewCount}`}
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Core Runtime Controls</CardTitle>
                        <CardDescription>Adjust scoring and online quality-repair behavior.</CardDescription>
                      </CardHeader>
                      <CardContent className="grid gap-6 md:grid-cols-2">
                        <ToggleField
                          label="LLM Summaries Enabled"
                          checked={Boolean(profile.llm_enabled)}
                          onChange={(value) => updateProfileField("llm_enabled", value)}
                        />
                        <ToggleField
                          label="Agent Scoring Enabled"
                          checked={Boolean(profile.agent_scoring_enabled)}
                          onChange={(value) => updateProfileField("agent_scoring_enabled", value)}
                        />
                        <NumberField
                          label="Max Agent Items Per Run"
                          value={Number(profile.max_agent_items_per_run ?? 40)}
                          onChange={(value) => updateProfileField("max_agent_items_per_run", value)}
                        />
                        <NumberField
                          label="Must-read Max Per Source"
                          value={Number(profile.must_read_max_per_source ?? 2)}
                          onChange={(value) => updateProfileField("must_read_max_per_source", value)}
                        />
                        <NumberField
                          label="Quality Repair Threshold"
                          value={Number(profile.quality_repair_threshold ?? 80)}
                          onChange={(value) => updateProfileField("quality_repair_threshold", value)}
                        />
                        <ToggleField
                          label="Quality Repair Enabled"
                          checked={Boolean(profile.quality_repair_enabled)}
                          onChange={(value) => updateProfileField("quality_repair_enabled", value)}
                        />
                        <ToggleField
                          label="Quality Learning Enabled"
                          checked={Boolean(profile.quality_learning_enabled)}
                          onChange={(value) => updateProfileField("quality_learning_enabled", value)}
                        />
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Lists and Output</CardTitle>
                        <CardDescription>Manage list fields and output settings.</CardDescription>
                      </CardHeader>
                      <CardContent className="grid gap-5 md:grid-cols-2">
                        <ListField
                          label="Topics"
                          value={toLines(profile.topics as string[])}
                          onChange={(value) => updateProfileField("topics", fromLines(value))}
                        />
                        <ListField
                          label="Trusted Sources"
                          value={toLines(profile.trusted_sources as string[])}
                          onChange={(value) => updateProfileField("trusted_sources", fromLines(value))}
                        />
                        <ListField
                          label="Exclusions"
                          value={toLines(profile.exclusions as string[])}
                          onChange={(value) => updateProfileField("exclusions", fromLines(value))}
                        />
                        <div className="space-y-2">
                          <Label>Obsidian Folder</Label>
                          <Input
                            value={String(((profile.output as Record<string, unknown>)?.obsidian_folder as string) ?? "")}
                            onChange={(event) => updateProfileField("output.obsidian_folder", event.target.value)}
                          />
                          <Label className="pt-2">Render Mode</Label>
                          <Select
                            value={String(((profile.output as Record<string, unknown>)?.render_mode as string) ?? "sectioned")}
                            onValueChange={(value) => updateProfileField("output.render_mode", value)}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="sectioned">sectioned</SelectItem>
                              <SelectItem value="source_segmented">source_segmented</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Advanced Profile JSON</CardTitle>
                        <CardDescription>Fine-tune full profile payload before validation and apply.</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Textarea
                          className="min-h-[280px] font-mono text-xs"
                          value={profileJson}
                          onChange={(event) => setProfileJson(event.target.value)}
                        />
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="review" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Review and Apply</CardTitle>
                        <CardDescription>
                          Validate changes, inspect local/server diff views, and apply overlay updates atomically.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          onClick={() => void validateProfile()}
                          disabled={saving || Boolean(profileJsonParseError)}
                        >
                          {saveAction === "profile-validate" ? (
                            <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                          ) : (
                            <ShieldCheck className="h-4 w-4" />
                          )}
                          {saveAction === "profile-validate" ? "Validating..." : "Validate"}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => void computeProfileDiff()}
                          disabled={saving || Boolean(profileJsonParseError)}
                        >
                          {saveAction === "profile-diff" ? (
                            <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                          ) : (
                            <RefreshCcw className="h-4 w-4" />
                          )}
                          {saveAction === "profile-diff" ? "Computing..." : "Compute Diff"}
                        </Button>
                        <Button onClick={() => void saveProfile()} disabled={saving || Boolean(profileJsonParseError)}>
                          {saveAction === "profile-save" ? (
                            <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                          ) : (
                            <Save className="h-4 w-4" />
                          )}
                          {saveAction === "profile-save" ? "Saving..." : "Save Overlay"}
                        </Button>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Pending Local Diff</CardTitle>
                        <CardDescription>
                          Live diff between the editor payload and the last loaded effective profile.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant={localDiffCount > 0 ? "warning" : "success"}>
                            local changes: {localDiffCount}
                          </Badge>
                          {profileJsonParseError ? <Badge variant="warning">invalid JSON</Badge> : null}
                        </div>
                        {profileJsonParseError ? (
                          <Alert variant="destructive">
                            <AlertTitle>Profile JSON is invalid</AlertTitle>
                            <AlertDescription>{profileJsonParseError}</AlertDescription>
                          </Alert>
                        ) : localDiffCount === 0 ? (
                          <p className="text-sm text-muted-foreground">No pending local changes.</p>
                        ) : (
                          <pre className="max-h-[340px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                            {JSON.stringify(localProfileDiff, null, 2)}
                          </pre>
                        )}
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Server Canonical Diff</CardTitle>
                        <CardDescription>
                          Result from <span className="font-semibold">Compute Diff</span> after server-side validation and
                          redaction handling.
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        {serverDiffCount === 0 ? (
                          <p className="text-sm text-muted-foreground">
                            {profileDiffComputedAt
                              ? "No server-side diff. The editor payload matches the current effective profile."
                              : "No computed diff yet. Click Compute Diff to generate a canonical server diff."}
                          </p>
                        ) : (
                          <pre className="max-h-[340px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                            {JSON.stringify(profileDiff, null, 2)}
                          </pre>
                        )}
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="timeline" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Run Timeline</CardTitle>
                        <CardDescription>
                          Monitor active run events and review historical timeline details after completion.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="grid gap-3 md:grid-cols-[2fr,1fr,1fr,1fr,auto]">
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
                          <Select
                            value={timelineOrder}
                            onValueChange={(value) => setTimelineOrder(value === "asc" ? "asc" : "desc")}
                          >
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
                          <Button variant="outline" onClick={() => void refreshTimeline()} disabled={saving || !timelineRunId}>
                            {saveAction === "timeline-refresh" ? (
                              <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                            ) : (
                              <RefreshCcw className="h-4 w-4" />
                            )}
                            {saveAction === "timeline-refresh" ? "Refreshing..." : "Refresh"}
                          </Button>
                          <Button variant="outline" onClick={() => void exportTimeline()} disabled={saving || !timelineRunId}>
                            {saveAction === "timeline-export" ? (
                              <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                            ) : (
                              <Save className="h-4 w-4" />
                            )}
                            {saveAction === "timeline-export" ? "Exporting..." : "Export JSON"}
                          </Button>
                        </div>
                        <div className="col-span-full flex items-center justify-between rounded-md border bg-muted/20 p-3">
                          <div>
                            <p className="text-sm font-medium">Live polling</p>
                            <p className="text-xs text-muted-foreground">
                              Automatic refresh for active runs while Timeline is open.
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">{timelineLivePaused ? "Paused" : "Live"}</span>
                            <Switch checked={!timelineLivePaused} onCheckedChange={(checked) => setTimelineLivePaused(!checked)} />
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Timeline Summary</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {timelineSummary ? (
                          <div className="space-y-3">
                            <div className="flex flex-wrap gap-2">
                              <Badge
                                variant={
                                  timelineSummary.status === "success"
                                    ? "success"
                                    : timelineSummary.status === "partial"
                                      ? "warning"
                                      : "outline"
                                }
                              >
                                status: {timelineSummary.status}
                              </Badge>
                              <Badge variant="secondary">events: {timelineSummary.event_count}</Badge>
                              <Badge variant="secondary">errors: {timelineSummary.error_event_count}</Badge>
                              <Badge variant="secondary">warnings: {timelineSummary.warn_event_count}</Badge>
                              <Badge variant="secondary">duration: {formatElapsed(timelineSummary.duration_s)}</Badge>
                              <Badge variant="secondary">
                                M/S/V: {timelineSummary.must_read_count}/{timelineSummary.skim_count}/{timelineSummary.video_count}
                              </Badge>
                              {timelineSummary.mode?.name ? (
                                <Badge variant="secondary">mode: {timelineSummary.mode.name}</Badge>
                              ) : null}
                              {timelineSummary.strictness_level ? (
                                <Badge
                                  variant={
                                    timelineSummary.strictness_level === "high"
                                      ? "warning"
                                      : timelineSummary.strictness_level === "medium"
                                        ? "outline"
                                        : "success"
                                  }
                                >
                                  strictness: {timelineSummary.strictness_level}
                                  {typeof timelineSummary.strictness_score === "number"
                                    ? ` (${timelineSummary.strictness_score})`
                                    : ""}
                                </Badge>
                              ) : null}
                            </div>

                            {timelineSummary.filter_funnel ? (
                              <div className="rounded-md border bg-muted/20 p-3 text-xs">
                                <p className="mb-1 font-semibold text-foreground">Filter funnel</p>
                                <p className="font-mono text-muted-foreground">
                                  fetched={timelineSummary.filter_funnel.fetched} -{" "}
                                  post_window={timelineSummary.filter_funnel.post_window} -{" "}
                                  post_seen={timelineSummary.filter_funnel.post_seen} -{" "}
                                  post_block={timelineSummary.filter_funnel.post_block} -{" "}
                                  selected={timelineSummary.filter_funnel.selected}
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
                        <CardTitle className="font-display">Timeline Events</CardTitle>
                      </CardHeader>
                      <CardContent>
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
                            {timelineEvents.length > 0 ? (
                              timelineEvents.map((row) => (
                                <TableRow
                                  key={`${row.run_id}:${row.id}`}
                                  className="cursor-pointer"
                                  data-state={row.id === timelineSelectedEventId ? "selected" : undefined}
                                  onClick={() => setTimelineSelectedEventId(row.id)}
                                >
                                  <TableCell>{row.event_index}</TableCell>
                                  <TableCell className="font-mono text-xs">{row.ts_utc}</TableCell>
                                  <TableCell className="font-mono text-xs">{row.stage}</TableCell>
                                  <TableCell>
                                    <Badge
                                      variant={
                                        row.severity === "error"
                                          ? "warning"
                                          : row.severity === "warn"
                                            ? "outline"
                                            : "secondary"
                                      }
                                    >
                                      {row.severity}
                                    </Badge>
                                  </TableCell>
                                  <TableCell className="text-xs">{row.message}</TableCell>
                                  <TableCell>{formatElapsed(row.elapsed_s)}</TableCell>
                                </TableRow>
                              ))
                            ) : (
                              <TableRow>
                                <TableCell colSpan={6} className="text-center text-sm text-muted-foreground">
                                  No events for selected filters/run.
                                </TableCell>
                              </TableRow>
                            )}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>

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
                          <Input value={timelineNoteAuthor} onChange={(event) => setTimelineNoteAuthor(event.target.value)} />
                          <Input
                            placeholder="Add note about this run..."
                            value={timelineNoteText}
                            onChange={(event) => setTimelineNoteText(event.target.value)}
                          />
                          <Button onClick={() => void addTimelineNote()} disabled={saving || !timelineRunId || !timelineNoteText.trim()}>
                            {saveAction === "timeline-note" ? (
                              <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                            ) : (
                              <Save className="h-4 w-4" />
                            )}
                            {saveAction === "timeline-note" ? "Saving..." : "Add Note"}
                          </Button>
                        </div>
                        <div className="space-y-2">
                          {timelineNotes.length > 0 ? (
                            timelineNotes.map((row) => (
                              <div key={row.id} className="rounded-md border bg-muted/20 p-3">
                                <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                  <span className="font-semibold text-foreground">{row.author || "admin"}</span>
                                  <span>{row.created_at_utc}</span>
                                </div>
                                <p className="text-sm">{row.note}</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-sm text-muted-foreground">No notes for this run yet.</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="history">
                    <Card>
                      <CardHeader>
                        <CardTitle className="font-display">Snapshot History</CardTitle>
                        <CardDescription>Rollback overlay state to a previous snapshot when needed.</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Created</TableHead>
                              <TableHead>Action</TableHead>
                              <TableHead>Snapshot</TableHead>
                              <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {history.map((row) => (
                              <TableRow key={row.id}>
                                <TableCell>{row.created_at}</TableCell>
                                <TableCell>{row.action}</TableCell>
                                <TableCell className="font-mono text-xs">{row.id}</TableCell>
                                <TableCell className="text-right">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => void rollback(row.id)}
                                    disabled={saving}
                                  >
                                    {saveAction === "rollback" && activeRollbackId === row.id ? (
                                      <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin motion-reduce:animate-none" />
                                    ) : (
                                      <Undo2 className="h-3.5 w-3.5" />
                                    )}
                                    {saveAction === "rollback" && activeRollbackId === row.id ? "Rolling back..." : "Rollback"}
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>
              </>
            ) : null}
          </section>
        </div>
      </div>
    </main>
  )
}

function ToggleField({
  label,
  checked,
  onChange,
}: {
  label: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-3">
      <Label>{label}</Label>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  )
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (value: number) => void
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input
        type="number"
        value={Number.isFinite(value) ? String(value) : "0"}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </div>
  )
}

function ListField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Textarea value={value} onChange={(event) => onChange(event.target.value)} className="min-h-[120px]" />
    </div>
  )
}
