import { useEffect, useMemo, useState } from "react"
import { Activity, Clock3, Loader2, Play, RefreshCcw, Save, ShieldCheck, Undo2 } from "lucide-react"

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

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8787"

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
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
  const [profileJson, setProfileJson] = useState("")
  const [profileDiff, setProfileDiff] = useState<Record<string, unknown>>({})
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
  const [notice, setNotice] = useState<{ kind: "ok" | "error"; text: string } | null>(null)

  const sortedSourceRows = useMemo(
    () => Object.entries(sources).sort((a, b) => a[0].localeCompare(b[0])),
    [sources],
  )

  const showRunActivity = Boolean(runProgress && (runProgress.is_active || runStatus?.active?.run_id))

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

  useEffect(() => {
    void refreshAll()
    const timer = setInterval(() => {
      void Promise.all([
        api<RunStatus>("/api/run-status"),
        api<RunProgress>("/api/run-progress"),
        api<{ items: SourceHealthItem[] }>("/api/source-health"),
        api<OnboardingStatus>("/api/onboarding/status"),
      ])
        .then(([status, progress, health, onboardingStatus]) => {
          setRunStatus(status)
          setRunProgress(progress.available ? progress : null)
          setSourceHealth(health.items)
          setOnboarding(onboardingStatus)
        })
        .catch(() => undefined)
    }, 8000)
    return () => clearInterval(timer)
  }, [])

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
      ])
      setSourceTypes(typeData.types)
      setSources(sourceData.sources)
      setProfile(profileData.profile)
      setProfileJson(JSON.stringify(profileData.profile, null, 2))
      setHistory(historyData.snapshots)
      setRunStatus(statusData)
      setRunProgress(progressData.available ? progressData : null)
      setSourceHealth(healthData.items)
      setOnboarding(onboardingData)
      setSourcePacks(sourcePackData.packs)
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
      setSaving(false)
    }
  }

  async function runNow() {
    setRunNowLoading(true)
    setSaving(true)
    try {
      const result = await api<{ started: boolean; run_id?: string; active_run_id?: string }>("/api/run-now", {
        method: "POST",
      })
      if (result.started) {
        setNotice({ kind: "ok", text: `Run started: ${result.run_id}` })
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
      setSaving(false)
    }
  }

  async function applySourcePack(packId: string) {
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
    setSaving(true)
    try {
      const parsed = JSON.parse(profileJson) as Record<string, unknown>
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
      setSaving(false)
    }
  }

  async function computeProfileDiff() {
    setSaving(true)
    try {
      const parsed = JSON.parse(profileJson) as Record<string, unknown>
      const result = await api<{ diff: Record<string, unknown> }>("/api/config/profile/diff", {
        method: "POST",
        body: JSON.stringify({ profile: parsed }),
      })
      setProfileDiff(result.diff)
      setNotice({ kind: "ok", text: "Diff updated." })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
    } finally {
      setSaving(false)
    }
  }

  async function saveProfile() {
    setSaving(true)
    try {
      const parsed = JSON.parse(profileJson) as Record<string, unknown>
      await api("/api/config/profile/save", {
        method: "POST",
        body: JSON.stringify({ profile: parsed }),
      })
      await refreshAll()
      setNotice({ kind: "ok", text: "Profile overlay saved." })
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
    } finally {
      setSaving(false)
    }
  }

  async function rollback(snapshotId: string) {
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
      setSaving(false)
    }
  }

  return (
    <main className="min-h-screen bg-soft-grid bg-grid-size">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-6 md:px-8">
        <header className="rounded-xl border bg-card/95 p-4 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Digest Config Console</h1>
              <p className="text-sm text-muted-foreground">
                shadcn + Tailwind UI for source/profile management with overlay-safe writes.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {runStatus?.active ? (
                <Badge variant="warning">Active: {runStatus.active.run_id}</Badge>
              ) : (
                <Badge variant="success">No active run</Badge>
              )}
              {runStatus?.latest ? (
                <Badge variant="secondary">Last: {runStatus.latest.status}</Badge>
              ) : null}
              {runStatus?.latest_completed && runStatus.latest_completed.source_error_count > 0 ? (
                <Badge variant="warning">
                  Source errors: {runStatus.latest_completed.source_error_count}
                </Badge>
              ) : null}
              <Button variant="outline" onClick={() => void refreshAll()} disabled={loading || saving}>
                <RefreshCcw className="h-4 w-4" /> Refresh
              </Button>
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

        {showRunActivity && runProgress ? (
          <Card aria-live="polite" aria-busy={runProgress.is_active}>
            <CardHeader className="pb-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  <CardTitle className="text-base">Digest Activity</CardTitle>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={runProgress.is_active ? "warning" : "success"}>
                    {runProgress.is_active ? "Running" : "Completed"}
                  </Badge>
                  <Badge variant="secondary">run_id: {runProgress.run_id}</Badge>
                </div>
              </div>
              <CardDescription className="text-xs">
                {runProgress.stage_label}: {runProgress.stage_detail || runProgress.message}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {typeof runProgress.percent === "number" ? (
                <div className="space-y-1">
                  <Progress value={runProgress.percent} />
                  <p className="text-xs text-muted-foreground">{Math.round(runProgress.percent)}% complete</p>
                </div>
              ) : (
                <div className="space-y-1">
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div className="h-full w-1/3 bg-primary motion-safe:animate-pulse motion-reduce:animate-none" />
                  </div>
                  <p className="text-xs text-muted-foreground">Progress is active. Waiting for next stage update.</p>
                </div>
              )}

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
            </CardContent>
          </Card>
        ) : null}

        {notice ? (
          <Alert variant={notice.kind === "error" ? "destructive" : "default"}>
            <AlertTitle>{notice.kind === "error" ? "Action failed" : "Action completed"}</AlertTitle>
            <AlertDescription>{notice.text}</AlertDescription>
          </Alert>
        ) : null}

        {sourceHealth.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Source Health</CardTitle>
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
                  {sourceHealth.slice(0, 6).map((item) => (
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

        {loading || !profile ? (
          <Card>
            <CardContent className="flex items-center gap-3 p-6">
              <Loader2 className="h-5 w-5 animate-spin" /> Loading configuration...
            </CardContent>
          </Card>
        ) : (
          <Tabs defaultValue="onboarding" className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="onboarding">Onboarding</TabsTrigger>
              <TabsTrigger value="sources">Sources</TabsTrigger>
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="review">Review</TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
            </TabsList>

            <TabsContent value="onboarding" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Setup Progress</CardTitle>
                  <CardDescription>
                    Move from preflight to first healthy run with a guided checklist.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={onboarding?.preflight.ok ? "success" : "warning"}>
                      Preflight: {onboarding?.preflight.ok ? "ready" : "needs attention"}
                    </Badge>
                    <Badge variant="secondary">
                      Steps: {onboarding?.progress.completed ?? 0}/{onboarding?.progress.total ?? 0}
                    </Badge>
                    <Button variant="outline" onClick={() => void runOnboardingPreflight()} disabled={saving}>
                      <ShieldCheck className="h-4 w-4" /> Run preflight
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => void runOnboardingPreview()}
                      disabled={previewLoading || saving}
                    >
                      {previewLoading ? (
                        <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      {previewLoading ? "Running preview..." : "Preview"}
                    </Button>
                    <Button
                      onClick={() => void activateOnboarding()}
                      disabled={saving || previewLoading || activateLoading || Boolean(runStatus?.active?.run_id)}
                    >
                      {activateLoading ? (
                        <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      {activateLoading ? "Starting live run..." : "Activate"}
                    </Button>
                  </div>

                  {previewLoading ? (
                    <p className="text-xs text-muted-foreground">
                      Preview is running. The app is fetching sources, scoring items, and building output artifacts.
                    </p>
                  ) : null}

                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Step</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Detail</TableHead>
                        <TableHead>Completed At</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(onboarding?.steps ?? []).map((step) => (
                        <TableRow key={step.id}>
                          <TableCell className="font-medium">{step.label}</TableCell>
                          <TableCell>
                            <Badge variant={step.status === "complete" ? "success" : "warning"}>{step.status}</Badge>
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">{step.detail}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{step.completed_at || "-"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Preflight Checks</CardTitle>
                  <CardDescription>
                    Validate environment, config, and writable paths before activation.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {preflight ? (
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
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Run preflight to load checks for this environment.
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Source Packs</CardTitle>
                  <CardDescription>
                    Apply curated source bundles to bootstrap ingestion quickly.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {sourcePacks.map((pack) => (
                    <div key={pack.id} className="flex flex-col gap-2 rounded-lg border p-3 md:flex-row md:items-center md:justify-between">
                      <div>
                        <p className="text-sm font-semibold">{pack.name}</p>
                        <p className="text-xs text-muted-foreground">{pack.description}</p>
                        <p className="text-xs text-muted-foreground">{pack.item_count} sources</p>
                      </div>
                      <Button variant="outline" onClick={() => void applySourcePack(pack.id)} disabled={saving}>
                        Apply pack
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {previewResult ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Preview Result</CardTitle>
                    <CardDescription>
                      Non-delivering preview output from the latest onboarding preview run.
                    </CardDescription>
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
            </TabsContent>

            <TabsContent value="sources" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Source Management</CardTitle>
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
                      Add
                    </Button>
                  </div>
                  <div className="flex items-end">
                    <Button variant="outline" onClick={() => void handleSourceMutation("remove")} disabled={saving}>
                      Remove
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Effective Sources</CardTitle>
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
            </TabsContent>

            <TabsContent value="profile" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Core Runtime Controls</CardTitle>
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
                  <CardTitle>Lists and Output</CardTitle>
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
                  <CardTitle>Advanced Profile JSON</CardTitle>
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
                  <CardTitle>Review and Apply</CardTitle>
                  <CardDescription>
                    Validate changes, inspect diff, and apply overlay updates atomically.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={() => void validateProfile()} disabled={saving}>
                    <ShieldCheck className="h-4 w-4" /> Validate
                  </Button>
                  <Button variant="outline" onClick={() => void computeProfileDiff()} disabled={saving}>
                    <RefreshCcw className="h-4 w-4" /> Compute Diff
                  </Button>
                  <Button onClick={() => void saveProfile()} disabled={saving}>
                    <Save className="h-4 w-4" /> Save Overlay
                  </Button>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Profile Diff</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="max-h-[340px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                    {JSON.stringify(profileDiff, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="history">
              <Card>
                <CardHeader>
                  <CardTitle>Snapshot History</CardTitle>
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
                              <Undo2 className="h-3.5 w-3.5" /> Rollback
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
        )}
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
