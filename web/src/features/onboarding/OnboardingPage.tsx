import { CheckCircle2, Loader2, Play, ShieldCheck } from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import type {
  Notice,
  OnboardingStatus,
  PreviewResult,
  PreflightReport,
  RunStatus,
  SaveAction,
  SourcePack,
} from "@/app/types"

export function OnboardingPage({
  notice,
  onDismissNotice,
  onboarding,
  setupPercent,
  preflight,
  sourcePacks,
  previewResult,
  saveAction,
  activeSourcePackId,
  previewLoading,
  activateLoading,
  saving,
  runStatus,
  onRunPreflight,
  onApplySourcePack,
  onRunPreview,
  onActivate,
  renderSetupStepAction,
}: {
  notice: Notice | null | undefined
  onDismissNotice: () => void
  onboarding: OnboardingStatus | null
  setupPercent: number
  preflight: PreflightReport | null
  sourcePacks: SourcePack[]
  previewResult: PreviewResult | null
  saveAction: SaveAction
  activeSourcePackId: string
  previewLoading: boolean
  activateLoading: boolean
  saving: boolean
  runStatus: RunStatus | null
  onRunPreflight: () => void
  onApplySourcePack: (packId: string) => void
  onRunPreview: () => void
  onActivate: () => void
  renderSetupStepAction: (stepId: string) => React.ReactNode
}) {
  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Onboarding"
        description="Dedicated setup journey from preflight through first healthy live run."
        badges={[
          { label: onboarding?.preflight.ok ? "preflight ready" : "preflight needs attention", variant: onboarding?.preflight.ok ? "success" : "warning" },
          { label: `steps ${onboarding?.progress.completed ?? 0}/${onboarding?.progress.total ?? 0}` },
        ]}
        actions={
          <Button
            onClick={onActivate}
            disabled={saving || previewLoading || activateLoading || Boolean(runStatus?.active?.run_id)}
          >
            {activateLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
            {activateLoading ? "Starting..." : "Activate"}
          </Button>
        }
      />

      <InlineNotice notice={notice} onDismiss={onDismissNotice} />

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
            <Badge variant="secondary">Steps {onboarding?.progress.completed ?? 0}/{onboarding?.progress.total ?? 0}</Badge>
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
                        <Badge variant={check.status === "pass" ? "success" : check.status === "warn" ? "warning" : "secondary"}>
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
              <Button variant="outline" onClick={onRunPreflight} disabled={saving}>
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
            <div key={pack.id} className="flex flex-col gap-2 rounded-xl border bg-muted/15 p-3 md:flex-row md:items-center md:justify-between">
              <div className="space-y-1">
                <p className="text-sm font-semibold">{pack.name}</p>
                <p className="text-xs text-muted-foreground">{pack.description}</p>
                <p className="text-xs text-muted-foreground">{pack.item_count} sources</p>
              </div>
              <Button variant="outline" onClick={() => onApplySourcePack(pack.id)} disabled={saving}>
                {saveAction === "source-pack" && activeSourcePackId === pack.id ? (
                  <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" />
                ) : null}
                {saveAction === "source-pack" && activeSourcePackId === pack.id ? "Applying..." : "Apply pack"}
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Preview and Activation</CardTitle>
          <CardDescription>Verify a safe preview before launching the first live run.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button variant="outline" onClick={onRunPreview} disabled={previewLoading || saving}>
            {previewLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
            {previewLoading ? "Running..." : "Run preview"}
          </Button>
          <Button onClick={onActivate} disabled={saving || previewLoading || activateLoading || Boolean(runStatus?.active?.run_id)}>
            {activateLoading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : <Play className="h-4 w-4" />}
            {activateLoading ? "Starting..." : "Activate"}
          </Button>
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
              <Badge variant={previewResult.status === "success" ? "success" : "warning"}>status: {previewResult.status}</Badge>
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
    </div>
  )
}

export function ProfileJsonError({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertTitle>Profile JSON is invalid</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  )
}
