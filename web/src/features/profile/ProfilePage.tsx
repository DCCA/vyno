import { Loader2, RefreshCcw, Save } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { fromLines, toLines } from "@/lib/console-utils"
import type { Notice, RunPolicy, SaveAction } from "@/app/types"

export function ProfilePage({
  notice,
  onDismissNotice,
  profile,
  profileJson,
  setProfileJson,
  updateProfileField,
  runPolicy,
  setRunPolicy,
  seenResetDays,
  setSeenResetDays,
  seenResetConfirm,
  setSeenResetConfirm,
  seenResetPreviewCount,
  saveAction,
  saving,
  onSaveRunPolicy,
  onPreviewSeenReset,
  onApplySeenReset,
}: {
  notice: Notice | null | undefined
  onDismissNotice: () => void
  profile: Record<string, unknown>
  profileJson: string
  setProfileJson: (value: string) => void
  updateProfileField: (path: string, value: unknown) => void
  runPolicy: RunPolicy
  setRunPolicy: React.Dispatch<React.SetStateAction<RunPolicy>>
  seenResetDays: string
  setSeenResetDays: (value: string) => void
  seenResetConfirm: boolean
  setSeenResetConfirm: (value: boolean) => void
  seenResetPreviewCount: number | null
  saveAction: SaveAction
  saving: boolean
  onSaveRunPolicy: () => void
  onPreviewSeenReset: () => void
  onApplySeenReset: () => void
}) {
  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Profile"
        description="Edit policy and runtime controls here, then use Review to validate and apply changes."
        badges={[
          { label: `default mode: ${runPolicy.default_mode}` },
          { label: runPolicy.allow_run_override ? "override enabled" : "override locked", variant: runPolicy.allow_run_override ? "success" : "warning" },
        ]}
      />

      <InlineNotice notice={notice} onDismiss={onDismissNotice} />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="font-display">Digest Policy</CardTitle>
              <CardDescription>Configure digest strictness and seen-item behavior without editing YAML.</CardDescription>
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
                <p className="text-xs text-muted-foreground">Current default for web-triggered runs. You can still override per run if enabled.</p>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-md border bg-muted/20 p-3">
                  <div>
                    <p className="text-sm font-medium">Allow run override</p>
                    <p className="text-xs text-muted-foreground">Enables one-time mode selection in the Run now control.</p>
                  </div>
                  <Switch
                    aria-label="allow_run_override"
                    checked={runPolicy.allow_run_override}
                    onCheckedChange={(checked) => setRunPolicy((prev) => ({ ...prev, allow_run_override: checked }))}
                  />
                </div>
                <div className="flex items-center justify-between rounded-md border bg-muted/20 p-3">
                  <div>
                    <p className="text-sm font-medium">Seen reset guard</p>
                    <p className="text-xs text-muted-foreground">Require explicit confirmation before clearing seen history.</p>
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
                  <Button onClick={onSaveRunPolicy} disabled={saving}>
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
              <CardTitle className="font-display">Core Runtime Controls</CardTitle>
              <CardDescription>Adjust scoring and online quality-repair behavior.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6 md:grid-cols-2">
              <ToggleField label="LLM Summaries Enabled" checked={Boolean(profile.llm_enabled)} onChange={(value) => updateProfileField("llm_enabled", value)} />
              <ToggleField label="Agent Scoring Enabled" checked={Boolean(profile.agent_scoring_enabled)} onChange={(value) => updateProfileField("agent_scoring_enabled", value)} />
              <NumberField label="Max Agent Items Per Run" value={Number(profile.max_agent_items_per_run ?? 40)} onChange={(value) => updateProfileField("max_agent_items_per_run", value)} />
              <NumberField label="Must-read Max Per Source" value={Number(profile.must_read_max_per_source ?? 2)} onChange={(value) => updateProfileField("must_read_max_per_source", value)} />
              <NumberField label="Quality Repair Threshold" value={Number(profile.quality_repair_threshold ?? 80)} onChange={(value) => updateProfileField("quality_repair_threshold", value)} />
              <ToggleField label="Quality Repair Enabled" checked={Boolean(profile.quality_repair_enabled)} onChange={(value) => updateProfileField("quality_repair_enabled", value)} />
              <ToggleField label="Quality Learning Enabled" checked={Boolean(profile.quality_learning_enabled)} onChange={(value) => updateProfileField("quality_learning_enabled", value)} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-display">Lists and Output</CardTitle>
              <CardDescription>Manage list fields and output settings.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 md:grid-cols-2">
              <ListField label="Topics" value={toLines(profile.topics as string[])} onChange={(value) => updateProfileField("topics", fromLines(value))} />
              <ListField label="Trusted Sources" value={toLines(profile.trusted_sources as string[])} onChange={(value) => updateProfileField("trusted_sources", fromLines(value))} />
              <ListField label="Exclusions" value={toLines(profile.exclusions as string[])} onChange={(value) => updateProfileField("exclusions", fromLines(value))} />
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
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="font-display">Seen History Maintenance</CardTitle>
              <CardDescription>Preview and reset seen keys to reduce over-restrictive runs when content recycles.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 md:grid-cols-[200px,auto,auto,1fr]">
                <div className="space-y-2">
                  <Label htmlFor="seen-reset-days">Older Than (days)</Label>
                  <Input id="seen-reset-days" inputMode="numeric" value={seenResetDays} onChange={(event) => setSeenResetDays(event.target.value)} />
                </div>
                <div className="flex items-end">
                  <Button variant="outline" onClick={onPreviewSeenReset} disabled={saving}>
                    {saveAction === "seen-reset-preview" ? (
                      <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                    ) : (
                      <RefreshCcw className="h-4 w-4" />
                    )}
                    {saveAction === "seen-reset-preview" ? "Previewing..." : "Preview Reset"}
                  </Button>
                </div>
                <div className="flex items-end">
                  <Button variant="outline" onClick={onApplySeenReset} disabled={saving || runPolicy.seen_reset_guard === "confirm" && !seenResetConfirm}>
                    {saveAction === "seen-reset-apply" ? (
                      <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    {saveAction === "seen-reset-apply" ? "Applying..." : "Apply Reset"}
                  </Button>
                </div>
                <div className="flex items-center gap-2 rounded-md border bg-muted/20 px-3">
                  <Switch aria-label="Confirm seen reset" checked={seenResetConfirm} onCheckedChange={setSeenResetConfirm} />
                  <span className="text-xs text-muted-foreground">Confirm seen reset</span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">{seenResetPreviewCount === null ? "No preview yet." : `Preview affected keys: ${seenResetPreviewCount}`}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-display">Advanced Profile JSON</CardTitle>
              <CardDescription>Fine-tune the full profile payload before validation and apply.</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea className="min-h-[460px] font-mono text-xs" value={profileJson} onChange={(event) => setProfileJson(event.target.value)} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
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
      <Switch aria-label={label} checked={checked} onCheckedChange={onChange} />
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
        aria-label={label}
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
      <Textarea aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} className="min-h-[120px]" />
    </div>
  )
}
