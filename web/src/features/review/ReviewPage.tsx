import { Loader2, RefreshCcw, Save, ShieldCheck } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { ProfileJsonError } from "@/features/onboarding/OnboardingPage"
import type { Notice, SaveAction } from "@/app/types"

export function ReviewPage({
  notice,
  onDismissNotice,
  saveAction,
  saving,
  profileJsonParseError,
  localDiffCount,
  localProfileDiff,
  serverDiffCount,
  profileDiff,
  profileDiffComputedAt,
  onValidateProfile,
  onComputeProfileDiff,
  onSaveProfile,
}: {
  notice: Notice | null | undefined
  onDismissNotice: () => void
  saveAction: SaveAction
  saving: boolean
  profileJsonParseError: string
  localDiffCount: number
  localProfileDiff: Record<string, unknown>
  serverDiffCount: number
  profileDiff: Record<string, unknown>
  profileDiffComputedAt: string
  onValidateProfile: () => void
  onComputeProfileDiff: () => void
  onSaveProfile: () => void
}) {
  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Review"
        description="Validate changes, inspect local and server-side diffs, then save the overlay once the payload is ready."
        badges={[
          { label: `local changes: ${localDiffCount}`, variant: localDiffCount > 0 ? "warning" : "success" },
          { label: profileJsonParseError ? "invalid JSON" : "json valid", variant: profileJsonParseError ? "warning" : "success" },
          { label: `server diff: ${serverDiffCount}` },
        ]}
      />

      <InlineNotice notice={notice} onDismiss={onDismissNotice} />

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Review and Apply</CardTitle>
          <CardDescription>Validation and diff actions are isolated here so editing and committing are separate jobs.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={onValidateProfile} disabled={saving || Boolean(profileJsonParseError)}>
            {saveAction === "profile-validate" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <ShieldCheck className="h-4 w-4" />}
            {saveAction === "profile-validate" ? "Validating..." : "Validate"}
          </Button>
          <Button variant="outline" onClick={onComputeProfileDiff} disabled={saving || Boolean(profileJsonParseError)}>
            {saveAction === "profile-diff" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <RefreshCcw className="h-4 w-4" />}
            {saveAction === "profile-diff" ? "Computing..." : "Compute Diff"}
          </Button>
          <Button onClick={onSaveProfile} disabled={saving || Boolean(profileJsonParseError)}>
            {saveAction === "profile-save" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Save className="h-4 w-4" />}
            {saveAction === "profile-save" ? "Saving..." : "Save Overlay"}
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="font-display">Pending Local Diff</CardTitle>
            <CardDescription>Live diff between the editor payload and the last loaded effective profile.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={localDiffCount > 0 ? "warning" : "success"}>local changes: {localDiffCount}</Badge>
              {profileJsonParseError ? <Badge variant="warning">invalid JSON</Badge> : null}
            </div>
            {profileJsonParseError ? (
              <ProfileJsonError message={profileJsonParseError} />
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
            <CardDescription>Result from Compute Diff after server-side validation and redaction handling.</CardDescription>
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
      </div>
    </div>
  )
}
