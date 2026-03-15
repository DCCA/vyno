import { useMemo, type ReactNode } from "react"
import { Loader2, Play, ShieldCheck } from "lucide-react"
import { useLocation } from "react-router-dom"

import { useNavActions, useOnboardingState, useProfileState, useRunState, useScheduleState, useUiState } from "@/app/console-context"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Textarea } from "@/components/ui/textarea"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { fromLines, toLines } from "@/lib/console-utils"
import type { OnboardingStatus } from "@/app/types"

export function OnboardingPage() {
  const location = useLocation()
  const { saving, saveAction, localNotices, clearScopedNotice } = useUiState()
  const { runStatus, runPolicy, setRunPolicy } = useRunState()
  const { scheduleStatus } = useScheduleState()
  const { navigateToSurface } = useNavActions()
  const { profile, updateProfileField, onSaveProfileWorkspace } = useProfileState()
  const {
    onboarding, setupPercent, preflight, sourcePacks, previewResult,
    previewLoading, activateLoading, activeSourcePackId,
    onRunPreflight, onApplySourcePack, onRunPreview, onActivate,
  } = useOnboardingState()
  const notice = localNotices.onboarding
  const revisitMode = useMemo(
    () => new URLSearchParams(location.search).get("mode") === "revisit",
    [location.search],
  )
  const output = asRecord(profile?.output)
  const schedule = asRecord(profile?.schedule)
  const topics = asStringArray(profile?.topics)
  const obsidianFolder = asString(output.obsidian_folder, "AI Digest")
  const milestoneRows = milestoneSummaries(onboarding?.steps ?? [])
  const firstPendingMilestone = milestoneRows.find((row) => row.status !== "complete")?.id || "prepare"
  const firstPendingMilestoneLabel = milestoneRows.find((row) => row.id === firstPendingMilestone)?.label || "Prepare workspace"

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title={revisitMode ? "Setup Guide" : "Guided Setup"}
        description={
          revisitMode
            ? "Review or adjust your activation choices without resetting the workspace."
            : "Move from zero setup to an automated digest schedule without editing files or learning the whole console first."
        }
        badges={[
          { label: onboarding?.preflight.ok ? "preflight ready" : "preflight needs attention", variant: onboarding?.preflight.ok ? "success" : "warning" },
          { label: `${onboarding?.progress.completed ?? 0}/${onboarding?.progress.total ?? 0} steps` },
          { label: scheduleStatus?.enabled ? "automation on" : "automation off", variant: scheduleStatus?.enabled ? "success" : "warning" },
        ]}
        actions={
          <Button
            onClick={onActivate}
            disabled={saving || previewLoading || activateLoading || Boolean(runStatus?.active?.run_id)}
          >
            {activateLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
            {activateLoading ? "Starting..." : "Start first live digest"}
          </Button>
        }
      />

      <InlineNotice notice={notice} onDismiss={() => clearScopedNotice("onboarding")} />

      {revisitMode ? (
        <Alert>
          <AlertTitle>Active workspace</AlertTitle>
          <AlertDescription>
            Your digest is already configured. Use this guide to review setup decisions or change them without resetting the workspace.
          </AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Activation Milestones</CardTitle>
          <CardDescription>
            Keep setup focused on the few actions that unlock a useful recurring digest. Detailed controls stay below.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">Current focus: {firstPendingMilestoneLabel}</Badge>
            <Badge variant={scheduleStatus?.enabled ? "success" : "warning"}>
              {scheduleStatus?.enabled ? "Automation configured" : "Automation required"}
            </Badge>
          </div>
          <Progress value={setupPercent} />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {milestoneRows.map((step, index) => (
              <div key={step.id} className="rounded-xl border bg-muted/15 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Milestone {index + 1}</p>
                <div className="mt-2 flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold leading-tight">{step.label}</p>
                  <Badge variant={step.status === "complete" ? "success" : step.id === firstPendingMilestone ? "warning" : "secondary"}>{step.status}</Badge>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">{step.detail}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <StepCard
        number={1}
        title="Run preflight checks"
        detail="Verify keys, writable paths, and runtime prerequisites before continuing."
        status={stepStatus(onboarding, "preflight")}
      >
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="outline" onClick={onRunPreflight} disabled={saving}>
            {saveAction === "onboarding-preflight" ? (
              <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
            ) : (
              <ShieldCheck className="h-4 w-4" />
            )}
            {saveAction === "onboarding-preflight" ? "Running..." : "Run preflight"}
          </Button>
          {preflight ? (
            <div className="flex flex-wrap gap-2">
              <Badge variant={preflight.ok ? "success" : "warning"}>{preflight.ok ? "Ready" : "Needs fixes"}</Badge>
              <Badge variant="secondary">pass: {preflight.pass_count}</Badge>
              <Badge variant="secondary">warn: {preflight.warn_count}</Badge>
              <Badge variant={preflight.fail_count > 0 ? "warning" : "secondary"}>fail: {preflight.fail_count}</Badge>
            </div>
          ) : null}
        </div>
      </StepCard>

      <StepCard
        number={2}
        title="Connect at least one output"
        detail="A daily digest needs somewhere to go. Telegram and Obsidian are both supported."
        status={stepStatus(onboarding, "outputs")}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 rounded-xl border p-4">
            <p className="text-sm font-semibold">Telegram delivery</p>
            <p className="text-xs text-muted-foreground">Use Telegram if you want the digest pushed to a chat automatically.</p>
            <div className="space-y-2">
              <Label htmlFor="telegram-bot-token">Bot token</Label>
              <Input
                id="telegram-bot-token"
                value={asString(output.telegram_bot_token)}
                onChange={(event) => updateProfileField("output.telegram_bot_token", event.target.value)}
                placeholder="Paste bot token"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="telegram-chat-id">Chat id</Label>
              <Input
                id="telegram-chat-id"
                value={asString(output.telegram_chat_id)}
                onChange={(event) => updateProfileField("output.telegram_chat_id", event.target.value)}
                placeholder="123456789"
              />
            </div>
          </div>
          <div className="space-y-2 rounded-xl border p-4">
            <p className="text-sm font-semibold">Obsidian delivery</p>
            <p className="text-xs text-muted-foreground">Use Obsidian if you want each digest saved as a note for later retrieval.</p>
            <div className="space-y-2">
              <Label htmlFor="obsidian-vault-path">Vault path</Label>
              <Input
                id="obsidian-vault-path"
                value={asString(output.obsidian_vault_path)}
                onChange={(event) => updateProfileField("output.obsidian_vault_path", event.target.value)}
                placeholder="/path/to/vault"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="obsidian-folder">Digest folder</Label>
              <Input
                id="obsidian-folder"
                value={obsidianFolder}
                onChange={(event) => updateProfileField("output.obsidian_folder", event.target.value)}
                placeholder="AI Digest"
              />
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={onSaveProfileWorkspace} disabled={saving}>
            {saveAction === "profile-save" || saveAction === "run-policy-save" ? (
              <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
            ) : null}
            {saveAction === "profile-save" || saveAction === "run-policy-save" ? "Saving..." : "Save output settings"}
          </Button>
          <p className="text-sm text-muted-foreground">At least one valid output is required before launch.</p>
        </div>
      </StepCard>

      <StepCard
        number={3}
        title="Choose starter sources"
        detail="Begin with a curated pack so the first digest is useful without manual source editing."
        status={stepStatus(onboarding, "sources")}
      >
        <div className="grid gap-3 md:grid-cols-2">
          {sourcePacks.map((pack) => (
            <div key={pack.id} className="rounded-xl border bg-muted/15 p-4">
              <p className="text-sm font-semibold">{pack.name}</p>
              <p className="mt-1 text-xs text-muted-foreground">{pack.description}</p>
              <p className="mt-2 text-xs text-muted-foreground">{pack.item_count} sources</p>
              <Button className="mt-4" variant="outline" onClick={() => onApplySourcePack(pack.id)} disabled={saving}>
                {saveAction === "source-pack" && activeSourcePackId === pack.id ? (
                  <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                ) : null}
                {saveAction === "source-pack" && activeSourcePackId === pack.id ? "Applying..." : "Apply pack"}
              </Button>
            </div>
          ))}
        </div>
      </StepCard>

      <StepCard
        number={4}
        title="Set digest preferences"
        detail="Pick how strict the digest should be and what topics you want it to emphasize."
        status={stepStatus(onboarding, "profile")}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 rounded-xl border p-4">
            <Label>Default digest mode</Label>
            <div className="grid gap-2">
              <ModeButton active={runPolicy.default_mode === "fresh_only"} label="Fresh only" onClick={() => setRunPolicy((prev) => ({ ...prev, default_mode: "fresh_only" }))} />
              <ModeButton active={runPolicy.default_mode === "balanced"} label="Balanced" onClick={() => setRunPolicy((prev) => ({ ...prev, default_mode: "balanced" }))} />
              <ModeButton active={runPolicy.default_mode === "replay_recent"} label="Catch up" onClick={() => setRunPolicy((prev) => ({ ...prev, default_mode: "replay_recent" }))} />
              <ModeButton active={runPolicy.default_mode === "backfill"} label="Backfill" onClick={() => setRunPolicy((prev) => ({ ...prev, default_mode: "backfill" }))} />
            </div>
          </div>
          <div className="space-y-2 rounded-xl border p-4">
            <Label htmlFor="topics">Topics to prioritize</Label>
            <Textarea
              id="topics"
              value={toLines(topics)}
              onChange={(event) => updateProfileField("topics", fromLines(event.target.value))}
              className="min-h-[160px]"
              placeholder="ai agents&#10;evals&#10;coding assistants"
            />
            <p className="text-xs text-muted-foreground">One topic per line. You can refine this later in Profile Setup.</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={onSaveProfileWorkspace} disabled={saving}>
            {saveAction === "profile-save" || saveAction === "run-policy-save" ? (
              <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
            ) : null}
            {saveAction === "profile-save" || saveAction === "run-policy-save" ? "Saving..." : "Save preferences"}
          </Button>
          <p className="text-sm text-muted-foreground">This keeps the first digest useful without forcing advanced tuning.</p>
        </div>
      </StepCard>

      <StepCard
        number={5}
        title="Configure scheduled automation"
        detail="This product is not considered fully set up until an automation cadence is configured."
        status={stepStatus(onboarding, "schedule")}
      >
        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2 rounded-xl border p-4">
            <p className="text-sm font-semibold">Automation</p>
            <p className="text-xs text-muted-foreground">
              {asBoolean(schedule.enabled, false) ? "Enabled" : "Paused"}
            </p>
          </div>
          <div className="space-y-2 rounded-xl border p-4">
            <p className="text-sm font-semibold">Cadence</p>
            <p className="text-xs text-muted-foreground">{asString(schedule.cadence, "daily")}</p>
          </div>
          <div className="space-y-2 rounded-xl border p-4">
            <p className="text-sm font-semibold">Timezone</p>
            <p className="text-xs text-muted-foreground">{asString(schedule.timezone, "UTC")}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => navigateToSurface("schedule")} disabled={saving}>
            Open schedule controls
          </Button>
          <div className="text-sm text-muted-foreground">
            {scheduleStatus?.enabled && scheduleStatus.next_run_at
              ? `Next scheduled run: ${scheduleStatus.next_run_at}`
              : "Open the schedule workspace to enable automation and set the cadence, quiet hours, and timezone."}
          </div>
        </div>
      </StepCard>

      <StepCard
        number={6}
        title="Preview the digest"
        detail="Check a safe, non-delivering preview before your first live run."
        status={stepStatus(onboarding, "preview")}
      >
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" onClick={onRunPreview} disabled={previewLoading || saving}>
            {previewLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
            {previewLoading ? "Running..." : "Run preview"}
          </Button>
        </div>
        {previewResult ? (
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2 rounded-xl border p-4">
              <p className="text-sm font-semibold">Preview summary</p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">status: {previewResult.status}</Badge>
                <Badge variant="secondary">must-read: {previewResult.must_read_count}</Badge>
                <Badge variant="secondary">skim: {previewResult.skim_count}</Badge>
                <Badge variant="secondary">videos: {previewResult.video_count}</Badge>
              </div>
            </div>
            <div className="space-y-2 rounded-xl border p-4">
              <p className="text-sm font-semibold">Obsidian preview</p>
              <pre className="max-h-[220px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                {previewResult.obsidian_note || "-"}
              </pre>
            </div>
          </div>
        ) : null}
      </StepCard>

      <StepCard
        number={7}
        title="Start the first live digest"
        detail="Launch one real run now so you can confirm the product works before relying on the saved schedule."
        status={stepStatus(onboarding, "activate")}
      >
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={onActivate} disabled={saving || previewLoading || activateLoading || Boolean(runStatus?.active?.run_id)}>
            {activateLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
            {activateLoading ? "Starting..." : "Start first live digest"}
          </Button>
          <p className="text-sm text-muted-foreground">Daily automation handles later runs. This first launch proves the setup works.</p>
        </div>
      </StepCard>

      <StepCard
        number={8}
        title="Confirm health"
        detail="Make sure the first completed run is healthy enough to trust scheduled automation."
        status={stepStatus(onboarding, "health")}
      >
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">latest run: {onboarding?.latest_completed?.run_id ?? "-"}</Badge>
          <Badge variant={onboarding?.latest_completed?.status === "success" ? "success" : "warning"}>
            status: {onboarding?.latest_completed?.status ?? "n/a"}
          </Badge>
          <Badge variant="secondary">source errors: {onboarding?.latest_completed?.source_error_count ?? 0}</Badge>
          <Badge variant="secondary">summary errors: {onboarding?.latest_completed?.summary_error_count ?? 0}</Badge>
        </div>
      </StepCard>
    </div>
  )
}

function StepCard({
  number,
  title,
  detail,
  status,
  children,
}: {
  number: number
  title: string
  detail: string
  status: "complete" | "pending"
  children: ReactNode
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="font-display">{number}. {title}</CardTitle>
            <CardDescription>{detail}</CardDescription>
          </div>
          <Badge variant={status === "complete" ? "success" : "warning"}>{status}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">{children}</CardContent>
    </Card>
  )
}

function ModeButton({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md border px-3 py-2 text-left text-sm ${active ? "border-primary bg-primary/10" : "border-border bg-background"}`}
    >
      {label}
    </button>
  )
}

function stepStatus(onboarding: OnboardingStatus | null, stepId: string): "complete" | "pending" {
  const row = onboarding?.steps.find((step) => step.id === stepId)
  return row?.status === "complete" ? "complete" : "pending"
}

function milestoneSummaries(steps: OnboardingStatus["steps"]): Array<{
  id: string
  label: string
  status: "complete" | "pending"
  detail: string
}> {
  const byId = new Map(steps.map((step) => [step.id, step]))
  const groups = [
    {
      id: "prepare",
      label: "Prepare workspace",
      detail: "Preflight checks and at least one delivery target must be ready.",
      stepIds: ["preflight", "outputs"],
    },
    {
      id: "sources",
      label: "Choose sources",
      detail: "Add a starter source set so the first digest is useful immediately.",
      stepIds: ["sources"],
    },
    {
      id: "preferences",
      label: "Set preferences and schedule",
      detail: "Save digest preferences and choose the cadence, quiet hours, and timezone.",
      stepIds: ["profile", "schedule"],
    },
    {
      id: "launch",
      label: "Preview and launch",
      detail: "Preview safely, then run the first live digest and confirm health.",
      stepIds: ["preview", "activate", "health"],
    },
  ] as const

  return groups.map((group) => {
    const status = group.stepIds.every((stepId) => byId.get(stepId)?.status === "complete") ? "complete" : "pending"
    return {
      id: group.id,
      label: group.label,
      status,
      detail: group.detail,
    }
  })
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}
}

function asString(value: unknown, fallback = ""): string {
  const text = String(value ?? "").trim()
  return text || fallback
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value.map((item) => String(item ?? "").trim()).filter(Boolean)
}

function asBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback
}

export function ProfileJsonError({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertTitle>Profile JSON is invalid</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  )
}
