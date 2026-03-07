import { useState, type Dispatch, type ReactNode, type SetStateAction } from "react"
import { Loader2, RefreshCcw, Save, ShieldCheck } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { fromLines, toLines } from "@/lib/console-utils"
import type { Notice, RunPolicy, SaveAction, ScheduleStatus } from "@/app/types"

type ProfileRecord = Record<string, unknown>
type ProfileSectionId = "goal" | "focus" | "quality" | "output" | "automation"

export function ProfilePage({
  notice,
  onDismissNotice,
  profile,
  scheduleStatus,
  onboardingLifecycle,
  profileJson,
  setProfileJson,
  updateProfileField,
  runPolicy,
  setRunPolicy,
  runPolicyDirty,
  runPolicyChangeCount,
  profileJsonParseError,
  profileWorkspaceChangeCount,
  localProfileDiff,
  profileDiff,
  profileDiffComputedAt,
  seenResetDays,
  setSeenResetDays,
  seenResetConfirm,
  setSeenResetConfirm,
  seenResetPreviewCount,
  saveAction,
  saving,
  onValidateProfile,
  onComputeProfileDiff,
  onSaveProfileWorkspace,
  onRevisitSetupGuide,
  onOpenSchedule,
  onPreviewSeenReset,
  onApplySeenReset,
}: {
  notice: Notice | null | undefined
  onDismissNotice: () => void
  profile: Record<string, unknown> | null
  scheduleStatus: ScheduleStatus | null
  onboardingLifecycle: "needs_setup" | "ready"
  profileJson: string
  setProfileJson: (value: string) => void
  updateProfileField: (path: string, value: unknown) => void
  runPolicy: RunPolicy
  setRunPolicy: Dispatch<SetStateAction<RunPolicy>>
  runPolicyDirty: boolean
  runPolicyChangeCount: number
  profileJsonParseError: string
  profileWorkspaceChangeCount: number
  localProfileDiff: Record<string, unknown>
  profileDiff: Record<string, unknown>
  profileDiffComputedAt: string
  seenResetDays: string
  setSeenResetDays: (value: string) => void
  seenResetConfirm: boolean
  setSeenResetConfirm: (value: boolean) => void
  seenResetPreviewCount: number | null
  saveAction: SaveAction
  saving: boolean
  onValidateProfile: () => void
  onComputeProfileDiff: () => void
  onSaveProfileWorkspace: () => void
  onRevisitSetupGuide: () => void
  onOpenSchedule: () => void
  onPreviewSeenReset: () => void
  onApplySeenReset: () => void
}) {
  const [openSection, setOpenSection] = useState<ProfileSectionId>("goal")
  const [showMaintenance, setShowMaintenance] = useState(false)
  const [showExpert, setShowExpert] = useState(false)

  if (!profile) return null

  const topics = asStringArray(profile.topics)
  const trustedSources = asStringArray(profile.trusted_sources)
  const exclusions = asStringArray(profile.exclusions)
  const blockedSources = asStringArray(profile.blocked_sources)
  const trustedAuthorsX = asStringArray(profile.trusted_authors_x)
  const blockedAuthorsX = asStringArray(profile.blocked_authors_x)
  const trustedGithubOrgs = asStringArray(profile.trusted_orgs_github)
  const blockedGithubOrgs = asStringArray(profile.blocked_orgs_github)
  const output = asRecord(profile.output)
  const schedule = asRecord(profile.schedule)
  const obsidianFolder = asString(output.obsidian_folder, "AI Digest")
  const renderMode = asString(output.render_mode, "sectioned")
  const scheduleEnabled = asBoolean(schedule.enabled, false)
  const scheduleTime = asString(schedule.time_local, "09:00")
  const scheduleTimezone = asString(schedule.timezone, "UTC")
  const selectionMode = asBoolean(profile.agent_scoring_enabled, true) ? "smart" : "basic"
  const summaryMode = asBoolean(profile.llm_enabled, false) ? "standard" : "lightweight"
  const qualityRepairEnabled = asBoolean(profile.quality_repair_enabled, false)
  const diversityMode = diversityModeFromValue(asNumber(profile.must_read_max_per_source, 2))
  const localDiffCount = Object.keys(localProfileDiff).length
  const serverDiffCount = Object.keys(profileDiff).length

  const goalSummary = describeGoal(runPolicy.default_mode)
  const focusSummary = `${topics.length} topics, ${trustedSources.length} trusted, ${exclusions.length} excluded`
  const qualitySummary = describeQuality(selectionMode, summaryMode, diversityMode, qualityRepairEnabled)
  const outputSummary = renderMode === "source_segmented" ? `Source-grouped notes in ${obsidianFolder}` : `Sectioned digest in ${obsidianFolder}`
  const automationSummary = scheduleEnabled ? `Daily at ${scheduleTime} (${scheduleTimezone})` : "Daily automation is off"
  const setupFacts = [
    `Mode: ${titleForMode(runPolicy.default_mode)}`,
    `Focus: ${focusSummary}`,
    `Output: ${renderMode === "source_segmented" ? "Grouped by source" : "Sectioned digest"}`,
    `Automation: ${automationSummary}`,
  ]

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Profile Setup"
        description="Use compact guided controls first. Open deeper tuning only when you need it."
        badges={[
          { label: `${profileWorkspaceChangeCount} pending`, variant: profileWorkspaceChangeCount > 0 ? "warning" : "success" },
          { label: profileJsonParseError ? "expert json needs attention" : "profile ready", variant: profileJsonParseError ? "warning" : "secondary" },
        ]}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-3">
          <InlineNotice notice={notice} onDismiss={onDismissNotice} />

          <SectionCard
            title="Digest Goal"
            summary={goalSummary}
            description="Set the default run behavior first."
            open={openSection === "goal"}
            onToggle={() => setOpenSection((current) => (current === "goal" ? "focus" : "goal"))}
            actionLabel={openSection === "goal" ? "Next section" : "Edit"}
          >
            <div className="grid gap-3 md:grid-cols-2">
              <ChoiceCard
                active={runPolicy.default_mode === "fresh_only"}
                title="Fresh only"
                description="Strict novelty. Great when you read every run."
                detail="Older missed items stay hidden unless you override the mode."
                onClick={() => setRunPolicy((prev) => ({ ...prev, default_mode: "fresh_only" }))}
              />
              <ChoiceCard
                active={runPolicy.default_mode === "balanced"}
                title="Balanced"
                description="Best everyday default for fresh content with light catch-up."
                detail="Good default for most operators."
                badge="Recommended"
                onClick={() => setRunPolicy((prev) => ({ ...prev, default_mode: "balanced" }))}
              />
              <ChoiceCard
                active={runPolicy.default_mode === "replay_recent"}
                title="Catch up"
                description="Brings recent missed items back more often."
                detail="Useful when you do not read every run."
                onClick={() => setRunPolicy((prev) => ({ ...prev, default_mode: "replay_recent" }))}
              />
              <ChoiceCard
                active={runPolicy.default_mode === "backfill"}
                title="Backfill"
                description="Reopens older unseen content aggressively."
                detail="Best for cleanup mode, not daily use."
                onClick={() => setRunPolicy((prev) => ({ ...prev, default_mode: "backfill" }))}
              />
            </div>
            <ToggleRow
              label="Allow one-time run override"
              description="Lets Run Center temporarily use a different mode without changing this default."
              checked={runPolicy.allow_run_override}
              onChange={(checked) => setRunPolicy((prev) => ({ ...prev, allow_run_override: checked }))}
            />
            <InlineEffect title="Current effect" text={goalSummary} />
          </SectionCard>

          <SectionCard
            title="Focus"
            summary={focusSummary}
            description="Prioritize themes and trusted inputs."
            open={openSection === "focus"}
            onToggle={() => setOpenSection((current) => (current === "focus" ? "quality" : "focus"))}
            actionLabel={openSection === "focus" ? "Next section" : "Edit"}
          >
            <TokenEditor
              label="Topics"
              description="Add themes you want the digest to notice faster."
              placeholder="Add a topic like ai agents"
              values={topics}
              emptyHint="No topic guidance yet."
              onChange={(next) => updateProfileField("topics", next)}
            />
            <TokenEditor
              label="Trusted sources"
              description="Trusted sources carry more weight during ranking."
              placeholder="Add a source like simonwillison.net"
              values={trustedSources}
              emptyHint="No trusted sources configured."
              onChange={(next) => updateProfileField("trusted_sources", next)}
            />
            <TokenEditor
              label="Avoid or exclude"
              description="Exclude noisy themes or recurring low-value content."
              placeholder="Add an exclusion like crypto"
              values={exclusions}
              emptyHint="No exclusions configured."
              onChange={(next) => updateProfileField("exclusions", next)}
            />
            <InlineEffect
              title="Current effect"
              text={
                topics.length > 0 || trustedSources.length > 0 || exclusions.length > 0
                  ? `Priority guidance is active across ${topics.length} topic${topics.length === 1 ? "" : "s"} and ${trustedSources.length} trusted source${trustedSources.length === 1 ? "" : "s"}.`
                  : "Selection is currently driven mostly by source quality and ranking rules."
              }
            />
          </SectionCard>

          <SectionCard
            title="Quality And Cost"
            summary={qualitySummary}
            description="Tune this only if the default balance is not right."
            open={openSection === "quality"}
            onToggle={() => setOpenSection((current) => (current === "quality" ? "output" : "quality"))}
            actionLabel={openSection === "quality" ? "Next section" : "Tune"}
          >
            <div className="space-y-4">
              <CompactChoiceGroup label="Selection intelligence">
                <ChoiceCard
                  active={selectionMode === "basic"}
                  title="Basic rules"
                  description="Lower cost and faster ranking."
                  detail="Relies more on source and keyword rules."
                  onClick={() => updateProfileField("agent_scoring_enabled", false)}
                />
                <ChoiceCard
                  active={selectionMode === "smart"}
                  title="Smart ranking"
                  description="Uses AI scoring to help rank stronger items."
                  detail="Better selection quality with some extra cost."
                  badge="Recommended"
                  onClick={() => updateProfileField("agent_scoring_enabled", true)}
                />
              </CompactChoiceGroup>

              <CompactChoiceGroup label="Summary style">
                <ChoiceCard
                  active={summaryMode === "lightweight"}
                  title="Lightweight digest"
                  description="Minimal summary generation."
                  detail="Best when you mostly scan titles."
                  onClick={() => updateProfileField("llm_enabled", false)}
                />
                <ChoiceCard
                  active={summaryMode === "standard"}
                  title="AI summaries"
                  description="Easier reading with fuller summaries."
                  detail="Recommended when readability matters."
                  badge="Recommended"
                  onClick={() => updateProfileField("llm_enabled", true)}
                />
              </CompactChoiceGroup>

              <CompactChoiceGroup label="Must-read diversity" columns="3">
                <ChoiceCard
                  active={diversityMode === "source_heavy"}
                  title="Source heavy"
                  description="Allows strong sources to dominate more."
                  detail="Depth over variety."
                  onClick={() => updateProfileField("must_read_max_per_source", 4)}
                />
                <ChoiceCard
                  active={diversityMode === "balanced"}
                  title="Balanced"
                  description="Keeps must-read reasonably diverse."
                  detail="Best default."
                  badge="Recommended"
                  onClick={() => updateProfileField("must_read_max_per_source", 2)}
                />
                <ChoiceCard
                  active={diversityMode === "high"}
                  title="High variety"
                  description="Spreads must-read across more sources."
                  detail="Variety over depth."
                  onClick={() => updateProfileField("must_read_max_per_source", 1)}
                />
              </CompactChoiceGroup>

              <ToggleRow
                label="Auto-fix weak summaries"
                description="Repairs low-quality summaries before delivery."
                checked={qualityRepairEnabled}
                onChange={(checked) => updateProfileField("quality_repair_enabled", checked)}
              />
            </div>
            <InlineEffect title="Current effect" text={qualitySummary} />
          </SectionCard>

          <SectionCard
            title="Output"
            summary={outputSummary}
            description="Keep this small: folder and layout only."
            open={openSection === "output"}
            onToggle={() => setOpenSection((current) => (current === "output" ? "automation" : "output"))}
            actionLabel={openSection === "output" ? "Next section" : "Edit"}
          >
            <div className="space-y-2">
              <Label htmlFor="obsidian-folder">Obsidian folder</Label>
              <Input
                id="obsidian-folder"
                value={obsidianFolder}
                onChange={(event) => updateProfileField("output.obsidian_folder", event.target.value)}
              />
              <p className="text-xs text-muted-foreground">Digest notes are written into this vault folder.</p>
            </div>
            <CompactChoiceGroup label="Digest format">
              <ChoiceCard
                active={renderMode === "sectioned"}
                title="Sectioned digest"
                description="Must-read, skim, and videos grouped by section."
                detail="Best for quick daily reading."
                badge="Recommended"
                onClick={() => updateProfileField("output.render_mode", "sectioned")}
              />
              <ChoiceCard
                active={renderMode === "source_segmented"}
                title="Group by source"
                description="Digest content grouped by source instead of rank bucket."
                detail="Best when source context matters more."
                onClick={() => updateProfileField("output.render_mode", "source_segmented")}
              />
            </CompactChoiceGroup>
            <InlineEffect title="Current effect" text={renderMode === "source_segmented" ? "Delivered notes will group items by source." : "Delivered notes will stay grouped by digest sections."} />
          </SectionCard>

          <SectionCard
            title="Automation"
            summary={automationSummary}
            description="Manage daily automation from the dedicated schedule workspace."
            open={openSection === "automation"}
            onToggle={() => setOpenSection("automation")}
            actionLabel="Edit"
          >
            <div className="grid gap-3 md:grid-cols-3">
              <div className="space-y-2 rounded-xl border p-4">
                <p className="text-sm font-semibold">Automation</p>
                <p className="text-xs text-muted-foreground">{scheduleEnabled ? "Enabled" : "Paused"}</p>
              </div>
              <div className="space-y-2 rounded-xl border p-4">
                <p className="text-sm font-semibold">Daily time</p>
                <p className="text-xs text-muted-foreground">{scheduleTime}</p>
              </div>
              <div className="space-y-2 rounded-xl border p-4">
                <p className="text-sm font-semibold">Timezone</p>
                <p className="text-xs text-muted-foreground">{scheduleTimezone}</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button type="button" variant="outline" onClick={onOpenSchedule}>
                Open schedule controls
              </Button>
              <p className="text-sm text-muted-foreground">Use the dedicated schedule page to save, pause, resume, or inspect automation.</p>
            </div>
            <InlineEffect
              title="Current effect"
              text={
                scheduleStatus?.enabled && scheduleStatus.next_run_at
                  ? `The next scheduled run is ${scheduleStatus.next_run_at}.`
                  : "No automated daily run is active yet."
              }
            />
          </SectionCard>

          <UtilityCard
            title="Maintenance tools"
            description="Hidden by default so cleanup tools do not crowd the main setup."
            open={showMaintenance}
            onToggle={() => setShowMaintenance((current) => !current)}
          >
            <div className="space-y-4">
              {onboardingLifecycle === "ready" ? (
                <div className="rounded-xl border bg-muted/20 p-4">
                  <p className="text-sm font-medium">Setup guide</p>
                  <p className="mt-1 text-xs text-muted-foreground">Reopen the guided setup without resetting the workspace or restoring setup to the main menu.</p>
                  <div className="mt-4">
                    <Button type="button" variant="outline" onClick={onRevisitSetupGuide} disabled={saving}>
                      Revisit setup guide
                    </Button>
                  </div>
                </div>
              ) : null}

              <div className="space-y-2">
                <Label>Seen reset protection</Label>
                <Select
                  value={runPolicy.seen_reset_guard}
                  onValueChange={(value) =>
                    setRunPolicy((prev) => ({
                      ...prev,
                      seen_reset_guard: (value as RunPolicy["seen_reset_guard"]) || "confirm",
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="confirm">Require confirmation</SelectItem>
                    <SelectItem value="disabled">Allow immediate reset</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="rounded-xl border bg-muted/20 p-4">
                <p className="text-sm font-medium">Seen history cleanup</p>
                <p className="mt-1 text-xs text-muted-foreground">Preview how many old seen keys would be cleared before applying a reset.</p>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="seen-reset-days">Older than (days)</Label>
                    <Input id="seen-reset-days" inputMode="numeric" value={seenResetDays} onChange={(event) => setSeenResetDays(event.target.value)} />
                  </div>
                  <label className="flex items-center gap-2 rounded-lg border bg-background px-3 py-3 text-sm text-muted-foreground">
                    <Switch aria-label="Confirm seen reset" checked={seenResetConfirm} onCheckedChange={setSeenResetConfirm} />
                    Confirm seen reset
                  </label>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button type="button" variant="outline" onClick={onPreviewSeenReset} disabled={saving}>
                    {saveAction === "seen-reset-preview" ? (
                      <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                    ) : (
                      <RefreshCcw className="h-4 w-4" />
                    )}
                    {saveAction === "seen-reset-preview" ? "Previewing..." : "Preview Reset"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={onApplySeenReset}
                    disabled={saving || (runPolicy.seen_reset_guard === "confirm" && !seenResetConfirm)}
                  >
                    {saveAction === "seen-reset-apply" ? (
                      <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    {saveAction === "seen-reset-apply" ? "Applying..." : "Apply Reset"}
                  </Button>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">
                  {seenResetPreviewCount === null ? "No preview yet." : `Preview affected keys: ${seenResetPreviewCount}`}
                </p>
              </div>
            </div>
          </UtilityCard>

          <UtilityCard
            title="Expert mode"
            description="Advanced controls and raw JSON stay available without dominating the desktop view."
            open={showExpert}
            onToggle={() => setShowExpert((current) => !current)}
          >
            <Tabs defaultValue="controls" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="controls">Advanced controls</TabsTrigger>
                <TabsTrigger value="diff">Diff</TabsTrigger>
                <TabsTrigger value="json">Raw JSON</TabsTrigger>
              </TabsList>
              <TabsContent value="controls" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <NumberField
                    label="Max agent-scored items"
                    description="Caps how many items are sent through AI ranking."
                    value={asNumber(profile.max_agent_items_per_run, 40)}
                    onChange={(value) => updateProfileField("max_agent_items_per_run", value)}
                  />
                  <NumberField
                    label="Quality repair threshold"
                    description="Lower scores than this are candidates for repair."
                    value={asNumber(profile.quality_repair_threshold, 80)}
                    onChange={(value) => updateProfileField("quality_repair_threshold", value)}
                  />
                  <NumberField
                    label="GitHub minimum stars"
                    description="Filters low-signal repositories."
                    value={asNumber(profile.github_min_stars, 0)}
                    onChange={(value) => updateProfileField("github_min_stars", value)}
                  />
                  <NumberField
                    label="GitHub repo max age (days)"
                    description="Drops repositories inactive for too long."
                    value={asNumber(profile.github_repo_max_age_days, 30)}
                    onChange={(value) => updateProfileField("github_repo_max_age_days", value)}
                  />
                  <ToggleRow
                    label="Quality learning"
                    description="Lets the system adapt scoring offsets over time."
                    checked={asBoolean(profile.quality_learning_enabled, true)}
                    onChange={(value) => updateProfileField("quality_learning_enabled", value)}
                  />
                  <ToggleRow
                    label="Include archived GitHub repos"
                    description="Archived repos are usually low-signal."
                    checked={asBoolean(profile.github_include_archived, false)}
                    onChange={(value) => updateProfileField("github_include_archived", value)}
                  />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <ListAreaField
                    label="Blocked sources"
                    description="Sources that should always be filtered out."
                    value={toLines(blockedSources)}
                    onChange={(value) => updateProfileField("blocked_sources", fromLines(value))}
                  />
                  <ListAreaField
                    label="Trusted X authors"
                    description="Extra X authors to boost even if they are not in your sources list."
                    value={toLines(trustedAuthorsX)}
                    onChange={(value) => updateProfileField("trusted_authors_x", fromLines(value))}
                  />
                  <ListAreaField
                    label="Blocked X authors"
                    description="X authors that should be excluded even if they appear in search results."
                    value={toLines(blockedAuthorsX)}
                    onChange={(value) => updateProfileField("blocked_authors_x", fromLines(value))}
                  />
                  <ListAreaField
                    label="Trusted GitHub owners"
                    description="GitHub owners that should carry extra trust during scoring."
                    value={toLines(trustedGithubOrgs)}
                    onChange={(value) => updateProfileField("trusted_orgs_github", fromLines(value))}
                  />
                  <ListAreaField
                    label="Blocked GitHub owners"
                    description="GitHub owners that should be filtered out during selection."
                    value={toLines(blockedGithubOrgs)}
                    onChange={(value) => updateProfileField("blocked_orgs_github", fromLines(value))}
                  />
                </div>
              </TabsContent>
              <TabsContent value="diff" className="space-y-4">
                <div className="rounded-xl border bg-muted/20 p-4">
                  <p className="text-sm font-medium">Diff tools</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Use this for deeper inspection when the guided setup is not enough. This replaces the old standalone Review page.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button type="button" variant="outline" onClick={onValidateProfile} disabled={saving || Boolean(profileJsonParseError)}>
                    {saveAction === "profile-validate" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <ShieldCheck className="h-4 w-4" />}
                    {saveAction === "profile-validate" ? "Validating..." : "Validate"}
                  </Button>
                  <Button type="button" variant="outline" onClick={onComputeProfileDiff} disabled={saving || Boolean(profileJsonParseError)}>
                    {saveAction === "profile-diff" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <RefreshCcw className="h-4 w-4" />}
                    {saveAction === "profile-diff" ? "Computing..." : "Compute diff"}
                  </Button>
                </div>
                {profileJsonParseError ? (
                  <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-950 dark:text-amber-100">
                    <p className="font-medium">Expert JSON needs attention</p>
                    <p className="mt-1 text-xs">Fix JSON errors before validating or computing diffs.</p>
                  </div>
                ) : null}
                <div className="grid gap-4 xl:grid-cols-2">
                  <div className="space-y-3 rounded-xl border p-4">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium">Pending local diff</p>
                      <Badge variant={localDiffCount > 0 ? "warning" : "success"}>local changes: {localDiffCount}</Badge>
                    </div>
                    {profileJsonParseError ? (
                      <p className="text-sm text-muted-foreground">Local diff is unavailable until the expert JSON is valid again.</p>
                    ) : localDiffCount === 0 ? (
                      <p className="text-sm text-muted-foreground">No pending local changes.</p>
                    ) : (
                      <pre className="max-h-[280px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                        {JSON.stringify(localProfileDiff, null, 2)}
                      </pre>
                    )}
                  </div>
                  <div className="space-y-3 rounded-xl border p-4">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium">Canonical server diff</p>
                      <Badge variant={serverDiffCount > 0 ? "warning" : "secondary"}>server diff: {serverDiffCount}</Badge>
                    </div>
                    {serverDiffCount === 0 ? (
                      <p className="text-sm text-muted-foreground">
                        {profileDiffComputedAt
                          ? "No server-side diff. The current payload matches the effective profile."
                          : "No computed diff yet. Use Compute diff to generate a canonical server diff."}
                      </p>
                    ) : (
                      <pre className="max-h-[280px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
                        {JSON.stringify(profileDiff, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="json" className="space-y-3">
                <div className="rounded-xl border bg-muted/20 p-4">
                  <p className="text-sm font-medium">Raw profile payload</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Use this only when the guided setup does not cover a field. Invalid JSON blocks validation and save.
                  </p>
                </div>
                <Textarea
                  className="min-h-[420px] font-mono text-xs"
                  value={profileJson}
                  onChange={(event) => setProfileJson(event.target.value)}
                />
                {profileJsonParseError ? (
                  <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-950 dark:text-amber-100">
                    <p className="font-medium">Expert JSON needs attention</p>
                    <p className="mt-1 text-xs">{profileJsonParseError}</p>
                  </div>
                ) : null}
              </TabsContent>
            </Tabs>
          </UtilityCard>
        </div>

        <div className="xl:sticky xl:top-4 xl:self-start">
          <Card>
            <CardHeader>
              <CardTitle className="font-display">Apply Changes</CardTitle>
              <CardDescription>Keep this panel small: save, validate, and open diff tools only when needed.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Badge variant={profileWorkspaceChangeCount > 0 ? "warning" : "success"}>
                  {profileWorkspaceChangeCount > 0 ? `${profileWorkspaceChangeCount} pending` : "No pending changes"}
                </Badge>
                {runPolicyDirty ? <Badge variant="warning">{runPolicyChangeCount} policy change{runPolicyChangeCount === 1 ? "" : "s"}</Badge> : null}
                {profileJsonParseError ? <Badge variant="warning">Expert JSON invalid</Badge> : null}
              </div>

              <div className="rounded-xl border bg-muted/20 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">Current setup</p>
                <div className="mt-3 space-y-2 text-sm text-muted-foreground">
                  {setupFacts.map((fact) => (
                    <p key={fact}>{fact}</p>
                  ))}
                </div>
              </div>

              <div className="grid gap-2">
                <Button type="button" onClick={onSaveProfileWorkspace} disabled={saving || Boolean(profileJsonParseError)}>
                  {saveAction === "profile-save" || saveAction === "run-policy-save" ? (
                    <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  {saveAction === "profile-save" || saveAction === "run-policy-save" ? "Saving..." : "Save Changes"}
                </Button>
                <Button type="button" variant="outline" onClick={onValidateProfile} disabled={saving || Boolean(profileJsonParseError)}>
                  {saveAction === "profile-validate" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <ShieldCheck className="h-4 w-4" />}
                  {saveAction === "profile-validate" ? "Validating..." : "Validate"}
                </Button>
              </div>
              <p className="text-xs leading-5 text-muted-foreground">
                Need deeper payload inspection? Open Expert mode and use the Diff tab.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function SectionCard({
  title,
  summary,
  description,
  open,
  onToggle,
  actionLabel,
  children,
}: {
  title: string
  summary: string
  description: string
  open: boolean
  onToggle: () => void
  actionLabel: string
  children: ReactNode
}) {
  return (
    <Card>
      <CardHeader className="gap-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1">
            <CardTitle className="font-display">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={onToggle}>
            {actionLabel}
          </Button>
        </div>
        <div className="rounded-xl border bg-muted/20 px-3 py-2 text-sm text-muted-foreground">{summary}</div>
      </CardHeader>
      {open ? <CardContent className="space-y-4">{children}</CardContent> : null}
    </Card>
  )
}

function UtilityCard({
  title,
  description,
  open,
  onToggle,
  children,
}: {
  title: string
  description: string
  open: boolean
  onToggle: () => void
  children: ReactNode
}) {
  return (
    <Card>
      <CardHeader className="gap-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1">
            <CardTitle className="font-display">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={onToggle}>
            {open ? "Hide" : "Show"}
          </Button>
        </div>
      </CardHeader>
      {open ? <CardContent className="space-y-4">{children}</CardContent> : null}
    </Card>
  )
}

function CompactChoiceGroup({
  label,
  columns = "2",
  children,
}: {
  label: string
  columns?: "2" | "3"
  children: ReactNode
}) {
  const columnClass = columns === "3" ? "md:grid-cols-3" : "md:grid-cols-2"
  return (
    <div className="space-y-3">
      <SectionLabel>{label}</SectionLabel>
      <div className={`grid gap-3 ${columnClass}`}>{children}</div>
    </div>
  )
}

function InlineEffect({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-xl border bg-primary/5 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary/80">{title}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{text}</p>
    </div>
  )
}

function SectionLabel({ children }: { children: ReactNode }) {
  return <p className="text-sm font-medium">{children}</p>
}

function ChoiceCard({
  active,
  title,
  description,
  detail,
  onClick,
  badge,
}: {
  active: boolean
  title: string
  description: string
  detail: string
  onClick: () => void
  badge?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-xl border p-4 text-left transition-colors ${
        active ? "border-primary bg-primary/5 shadow-sm" : "border-border bg-background hover:border-primary/40 hover:bg-muted/20"
      }`}
    >
      <div className="space-y-2">
        <p className="text-sm font-semibold">{title}</p>
        {badge ? <Badge variant="secondary">{badge}</Badge> : null}
        <p className="text-sm leading-6 text-muted-foreground">{description}</p>
        {active ? <p className="text-xs leading-5 text-muted-foreground">{detail}</p> : null}
      </div>
    </button>
  )
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border p-4 md:flex-row md:items-start md:justify-between">
      <div className="space-y-1">
        <Label>{label}</Label>
        <p className="text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      <Switch aria-label={label} checked={checked} onCheckedChange={onChange} />
    </div>
  )
}

function NumberField({
  label,
  description,
  value,
  onChange,
}: {
  label: string
  description: string
  value: number
  onChange: (value: number) => void
}) {
  return (
    <div className="space-y-2 rounded-xl border p-4">
      <Label>{label}</Label>
      <p className="text-xs leading-5 text-muted-foreground">{description}</p>
      <Input
        aria-label={label}
        type="number"
        value={Number.isFinite(value) ? String(value) : "0"}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </div>
  )
}

function ListAreaField({
  label,
  description,
  value,
  onChange,
}: {
  label: string
  description: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="space-y-2 rounded-xl border p-4">
      <Label>{label}</Label>
      <p className="text-xs leading-5 text-muted-foreground">{description}</p>
      <Textarea aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} className="min-h-[120px]" />
    </div>
  )
}

function TokenEditor({
  label,
  description,
  placeholder,
  values,
  emptyHint,
  onChange,
}: {
  label: string
  description: string
  placeholder: string
  values: string[]
  emptyHint: string
  onChange: (next: string[]) => void
}) {
  const [draft, setDraft] = useState("")

  function commitDraft() {
    const next = draft.trim()
    if (!next) return
    const deduped = new Set(values.map((value) => value.trim()).filter(Boolean))
    deduped.add(next)
    onChange(Array.from(deduped))
    setDraft("")
  }

  function removeValue(value: string) {
    onChange(values.filter((item) => item !== value))
  }

  return (
    <div className="rounded-xl border p-4">
      <div className="space-y-1">
        <Label>{label}</Label>
        <p className="text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {values.length > 0 ? (
          values.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => removeValue(value)}
              className="rounded-full border bg-muted/30 px-3 py-1 text-sm text-foreground transition-colors hover:border-destructive/40 hover:bg-destructive/10"
            >
              {value}
            </button>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">{emptyHint}</p>
        )}
      </div>
      <div className="mt-4 flex flex-col gap-2 md:flex-row">
        <Input
          value={draft}
          placeholder={placeholder}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault()
              commitDraft()
            }
          }}
        />
        <Button type="button" variant="outline" onClick={commitDraft}>
          Add
        </Button>
      </div>
    </div>
  )
}

function asRecord(value: unknown): ProfileRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as ProfileRecord) : {}
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => String(item ?? "").trim())
    .filter(Boolean)
}

function asString(value: unknown, fallback = ""): string {
  const text = String(value ?? "").trim()
  return text || fallback
}

function asBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback
}

function asNumber(value: unknown, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) return parsed
  }
  return fallback
}

function diversityModeFromValue(value: number): "source_heavy" | "balanced" | "high" {
  if (value <= 1) return "high"
  if (value <= 2) return "balanced"
  return "source_heavy"
}

function titleForMode(mode: RunPolicy["default_mode"]): string {
  if (mode === "fresh_only") return "Fresh only"
  if (mode === "balanced") return "Balanced"
  if (mode === "replay_recent") return "Catch up"
  return "Backfill"
}

function describeGoal(mode: RunPolicy["default_mode"]): string {
  if (mode === "fresh_only") return "Runs stay strict about novelty and hide older missed items."
  if (mode === "balanced") return "Runs favor fresh items while allowing a small amount of recent catch-up."
  if (mode === "replay_recent") return "Recent missed items can reappear more often so you can catch up."
  return "Older unseen content can return more aggressively during runs."
}

function describeQuality(
  selectionMode: "basic" | "smart",
  summaryMode: "lightweight" | "standard",
  diversityMode: "source_heavy" | "balanced" | "high",
  qualityRepairEnabled: boolean,
): string {
  const ranking = selectionMode === "smart" ? "smart ranking" : "basic rules"
  const summaries = summaryMode === "standard" ? "AI summaries" : "lightweight summaries"
  const diversity =
    diversityMode === "high" ? "high variety" : diversityMode === "balanced" ? "balanced variety" : "source-heavy must-read"
  const repair = qualityRepairEnabled ? "with auto-fix enabled" : "with auto-fix off"
  return `${ranking}, ${summaries}, ${diversity}, ${repair}.`
}
