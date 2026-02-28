import { useEffect, useMemo, useState } from "react"
import { Loader2, Play, RefreshCcw, Save, ShieldCheck, Undo2 } from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"

type SourceMap = Record<string, string[]>

type RunStatus = {
  active: { run_id: string; started_at: string } | null
  latest: {
    run_id: string
    status: string
    started_at: string
    source_errors: number
    summary_errors: number
  } | null
}

type HistoryItem = {
  id: string
  created_at: string
  action: string
  details: Record<string, unknown>
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
  const [notice, setNotice] = useState<{ kind: "ok" | "error"; text: string } | null>(null)

  const sortedSourceRows = useMemo(
    () => Object.entries(sources).sort((a, b) => a[0].localeCompare(b[0])),
    [sources],
  )

  useEffect(() => {
    void refreshAll()
    const timer = setInterval(() => {
      void api<RunStatus>("/api/run-status").then(setRunStatus).catch(() => undefined)
    }, 8000)
    return () => clearInterval(timer)
  }, [])

  async function refreshAll() {
    setLoading(true)
    try {
      const [typeData, sourceData, profileData, historyData, statusData] = await Promise.all([
        api<{ types: string[] }>("/api/config/source-types"),
        api<{ sources: SourceMap }>("/api/config/sources"),
        api<{ profile: Record<string, unknown> }>("/api/config/profile"),
        api<{ snapshots: HistoryItem[] }>("/api/config/history"),
        api<RunStatus>("/api/run-status"),
      ])
      setSourceTypes(typeData.types)
      setSources(sourceData.sources)
      setProfile(profileData.profile)
      setProfileJson(JSON.stringify(profileData.profile, null, 2))
      setHistory(historyData.snapshots)
      setRunStatus(statusData)
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
      const status = await api<RunStatus>("/api/run-status")
      setRunStatus(status)
    } catch (error) {
      setNotice({ kind: "error", text: String(error) })
    } finally {
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
              <Button variant="outline" onClick={() => void refreshAll()} disabled={loading || saving}>
                <RefreshCcw className="h-4 w-4" /> Refresh
              </Button>
              <Button onClick={() => void runNow()} disabled={saving}>
                <Play className="h-4 w-4" /> Run now
              </Button>
            </div>
          </div>
        </header>

        {notice ? (
          <Alert variant={notice.kind === "error" ? "destructive" : "default"}>
            <AlertTitle>{notice.kind === "error" ? "Action failed" : "Action completed"}</AlertTitle>
            <AlertDescription>{notice.text}</AlertDescription>
          </Alert>
        ) : null}

        {loading || !profile ? (
          <Card>
            <CardContent className="flex items-center gap-3 p-6">
              <Loader2 className="h-5 w-5 animate-spin" /> Loading configuration...
            </CardContent>
          </Card>
        ) : (
          <Tabs defaultValue="sources" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="sources">Sources</TabsTrigger>
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="review">Review</TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
            </TabsList>

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
