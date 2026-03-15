import { useState } from "react"
import { AlertTriangle, ArrowUpRight, Clock3, ImageOff, Loader2 } from "lucide-react"

import { useSourceState, useUiState } from "@/app/console-context"
import type { UnifiedSourceRow } from "@/app/types"
import { EmptyState } from "@/components/ui/empty-state"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MetricCard } from "@/components/ui/metric-card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { sourceValuePlaceholderForType, truncateText } from "@/lib/console-utils"

export function SourcesPage() {
  const { saving, saveAction, localNotices, clearScopedNotice } = useUiState()
  const {
    sources, sourceHealth, sourceType, setSourceType, sourceValue, setSourceValue,
    sourceTypes, sourceSearch, setSourceSearch, sourceStatusFilter, setSourceStatusFilter,
    filteredUnifiedSourceRows, unifiedRowsVisible, showAllUnifiedSources, setShowAllUnifiedSources,
    onHandleSourceMutation, onEditUnifiedSourceRow, onDeleteUnifiedSourceRow, onSourceFeedback,
  } = useSourceState()
  const notice = localNotices.sources
  const sortedSourceRows = Object.entries(sources).sort((a, b) => a[0].localeCompare(b[0]))
  const totalSourceCount = sortedSourceRows.reduce((sum, [, values]) => sum + values.length, 0)

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Sources"
        description="Curate the signal library, keep ingestion healthy, and manage source quality from one structured workspace."
        badges={[
          { label: `types: ${sortedSourceRows.length}` },
          { label: `total sources: ${totalSourceCount}` },
          { label: `failing sources: ${sourceHealth.length}`, variant: sourceHealth.length > 0 ? "warning" : "success" },
        ]}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard variant="compact" label="Library size" value={String(totalSourceCount)} detail="Tracked source entries" />
        <MetricCard variant="compact" label="Active types" value={String(sortedSourceRows.length)} detail="Distinct connectors in use" />
        <MetricCard variant="compact" label="Health posture" value={sourceHealth.length > 0 ? "Watch" : "Clear"} detail={sourceHealth.length > 0 ? `${sourceHealth.length} sources need attention` : "No current failures"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="font-display">Source Studio</CardTitle>
            <CardDescription>Add or remove one source at a time without leaving the library.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
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
                placeholder={sourceValuePlaceholderForType(sourceType)}
                value={sourceValue}
                onChange={(event) => setSourceValue(event.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={() => onHandleSourceMutation("add")} disabled={saving} className="flex-1">
                {saveAction === "source-add" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : null}
                {saveAction === "source-add" ? "Adding..." : "Add"}
              </Button>
              <Button variant="outline" onClick={() => onHandleSourceMutation("remove")} disabled={saving} className="flex-1">
                {saveAction === "source-remove" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin motion-reduce:animate-none" /> : null}
                {saveAction === "source-remove" ? "Removing..." : "Remove"}
              </Button>
            </div>
            <InlineNotice notice={notice} onDismiss={() => clearScopedNotice("sources")} />
          </CardContent>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="font-display">Source Library</CardTitle>
            <CardDescription>Browse sources as latest-item link cards with clearer preview hierarchy and calmer source context.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-[1.35rem] border border-border/80 bg-secondary/30 p-4">
              <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_170px_auto] md:items-end">
                <div className="min-w-[240px] flex-1 space-y-2">
                  <Label htmlFor="unified-source-search">Filter sources</Label>
                  <Input
                    id="unified-source-search"
                    placeholder="Search preview title, source, host, error, or hint"
                    value={sourceSearch}
                    onChange={(event) => setSourceSearch(event.target.value)}
                  />
                </div>
                <div className="min-w-[170px] space-y-2">
                  <Label>Status</Label>
                  <Select value={sourceStatusFilter} onValueChange={(value) => setSourceStatusFilter(value === "failing" ? "failing" : value === "healthy" ? "healthy" : "all")}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">all</SelectItem>
                      <SelectItem value="healthy">healthy</SelectItem>
                      <SelectItem value="failing">failing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Badge variant="outline" className="justify-self-start md:justify-self-end">cards {filteredUnifiedSourceRows.length}</Badge>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
              {unifiedRowsVisible.length > 0 ? (
                unifiedRowsVisible.map((row) => (
                  <SourcePreviewCard
                    key={row.key}
                    row={row}
                    saving={saving}
                    onEditUnifiedSourceRow={onEditUnifiedSourceRow}
                    onDeleteUnifiedSourceRow={onDeleteUnifiedSourceRow}
                    onSourceFeedback={onSourceFeedback}
                  />
                ))
              ) : (
                <div className="md:col-span-2 2xl:col-span-3">
                  <EmptyState
                    title="No sources match"
                    description="Try adjusting your search or status filter."
                  />
                </div>
              )}
            </div>

            {filteredUnifiedSourceRows.length > 12 ? (
              <div className="flex justify-end">
                <Button variant="outline" size="sm" onClick={() => setShowAllUnifiedSources(!showAllUnifiedSources)}>
                  {showAllUnifiedSources ? "Show less" : `Show more (${filteredUnifiedSourceRows.length - 12})`}
                </Button>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


function SourcePreviewCard({
  row,
  saving,
  onEditUnifiedSourceRow,
  onDeleteUnifiedSourceRow,
  onSourceFeedback,
}: {
  row: UnifiedSourceRow
  saving: boolean
  onEditUnifiedSourceRow: (row: UnifiedSourceRow) => void
  onDeleteUnifiedSourceRow: (row: UnifiedSourceRow) => void
  onSourceFeedback: (row: UnifiedSourceRow, label: "prefer_source" | "less_source" | "mute_source") => void
}) {
  const [imageFailed, setImageFailed] = useState(false)
  const isFailing = row.health === "failing"
  const hasPreviewImage = Boolean(row.preview_image_url && row.preview_status === "ready" && !imageFailed)
  const isEmpty = row.preview_status === "no_items"
  const hasPreviewLink = Boolean(row.preview_url)
  const metaLine = [row.preview_host || row.type_label, row.preview_published_at ? formatPreviewDate(row.preview_published_at) : ""]
    .filter(Boolean)
    .join(" · ")

  const previewBody = (
    <div className="space-y-0">
      <div className="source-card-media">
        {hasPreviewImage ? (
          <img
            src={row.preview_image_url ?? undefined}
            alt={row.preview_title}
            width={620}
            height={400}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.015]"
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="source-card-placeholder flex h-full w-full items-end justify-between p-5">
            <div className="max-w-[82%] space-y-2">
              <Badge variant="secondary" className="border-white/40 bg-white/70 text-foreground shadow-sm">
                {row.type_label}
              </Badge>
              <p className="font-display text-[1.14rem] leading-tight tracking-[-0.03em] text-foreground">
                {isEmpty ? row.identity_title : row.preview_title}
              </p>
            </div>
            <div className="rounded-full border border-foreground/10 bg-white/72 p-2 text-muted-foreground shadow-sm">
              <ImageOff className="h-4 w-4" aria-hidden="true" />
            </div>
          </div>
        )}
        {hasPreviewImage ? (
          <div className="source-card-media-overlay" aria-hidden="true" />
        ) : null}
      </div>

      <div className="space-y-4 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{row.type_label}</Badge>
          <Badge variant={isFailing ? "warning" : isEmpty ? "secondary" : "success"}>
            {isFailing ? `needs attention (${row.count})` : isEmpty ? "waiting for first item" : "preview ready"}
          </Badge>
        </div>

        <div className="min-w-0 space-y-2">
          <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-xs font-medium text-muted-foreground">
            <span>{metaLine}</span>
            {row.preview_published_at ? <Clock3 className="h-3.5 w-3.5" aria-hidden="true" /> : null}
          </div>
          <h3 className="source-card-title-clamp text-pretty font-display text-[1.18rem] leading-tight tracking-[-0.03em] text-foreground">
            {row.preview_title}
          </h3>
          <p className="source-card-description-clamp text-[0.95rem] leading-6 text-muted-foreground">
            {row.preview_description}
          </p>
        </div>

        <div className="flex min-w-0 flex-wrap items-center gap-2 rounded-[1rem] border border-border/70 bg-background/72 px-3 py-2.5 text-sm">
          <span className="font-medium text-foreground">{row.identity_title}</span>
          <span className="text-muted-foreground">{row.identity_subtitle}</span>
          <span className="min-w-0 break-all font-mono text-[11px] text-muted-foreground/90" title={row.source}>
            {truncateText(row.source, 72)}
          </span>
        </div>
      </div>
    </div>
  )

  return (
    <Card className="animate-surface-enter overflow-hidden border-border/90 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(247,242,237,0.94))] transition-[transform,box-shadow,border-color] duration-200 hover:-translate-y-0.5 hover:border-border hover:shadow-panel">
      <div className="flex h-full flex-col">
        {hasPreviewLink ? (
          <a
            href={row.preview_url ?? undefined}
            target="_blank"
            rel="noreferrer"
            className="group block cursor-pointer transition-transform duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            aria-label={`Visit source item ${row.preview_title}`}
          >
            {previewBody}
          </a>
        ) : (
          <div>{previewBody}</div>
        )}

        <CardContent className="mt-auto space-y-3 p-5 pt-0">
          {isFailing ? (
            <div className="rounded-[1rem] border border-[hsl(25_71%_40%_/_0.18)] bg-[hsl(25_71%_97%)] px-3 py-2.5 text-sm">
              <div className="flex items-center gap-2 font-semibold text-[hsl(25_71%_28%)]">
                <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                <span>Ingestion issue detected</span>
              </div>
              <p className="mt-1.5 text-[13px] text-[hsl(25_44%_26%)]" title={row.last_error}>
                {truncateText(row.last_error, 132)}
              </p>
              <p className="mt-1 text-xs text-[hsl(25_34%_30%)]" title={row.hint}>
                Hint: {truncateText(row.hint, 116)}
              </p>
              <p className="mt-1 text-xs text-[hsl(25_34%_30%)]">Last seen: {row.last_seen}</p>
            </div>
          ) : isEmpty ? (
            <div className="rounded-[1rem] border border-border/60 bg-muted/15 px-3 py-2.5 text-sm text-muted-foreground">
              <div className="flex items-center gap-2 font-semibold text-foreground">
                <ImageOff className="h-4 w-4" aria-hidden="true" />
                <span>Preview not ready yet</span>
              </div>
              <p className="mt-1.5 text-[13px]">The card will switch to a live preview after the first stored item arrives.</p>
            </div>
          ) : !hasPreviewImage ? (
            <div className="rounded-[1rem] border border-border/60 bg-muted/15 px-3 py-2.5 text-sm text-muted-foreground">
              <div className="flex items-center gap-2 font-semibold text-foreground">
                <ImageOff className="h-4 w-4" aria-hidden="true" />
                <span>Preview image unavailable</span>
              </div>
              <p className="mt-1.5 text-[13px]">{truncateText(row.preview_description, 120)}</p>
            </div>
          ) : null}

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border/70 pt-3">
            <div className="text-xs text-muted-foreground">
              {hasPreviewLink ? (
                <span className="inline-flex items-center gap-1 font-medium text-foreground/85">
                  Primary action opens preview
                  <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
                </span>
              ) : (
                <span>Preview will activate after the first stored item arrives.</span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => onSourceFeedback(row, "prefer_source")} disabled={saving}>
                Prefer
              </Button>
              <Button variant="outline" size="sm" onClick={() => onSourceFeedback(row, "less_source")} disabled={saving}>
                Less
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSourceFeedback(row, "mute_source")}
                disabled={saving}
                className="border-destructive/40 text-destructive hover:bg-destructive/10"
              >
                Mute
              </Button>
              {row.can_edit ? (
                <Button variant="outline" size="sm" onClick={() => onEditUnifiedSourceRow(row)} disabled={saving}>
                  Edit
                </Button>
              ) : (
                <Badge variant="outline">managed in config</Badge>
              )}
              {row.can_delete ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDeleteUnifiedSourceRow(row)}
                  disabled={saving}
                  className="border-destructive/40 text-destructive hover:bg-destructive/10"
                >
                  Delete
                </Button>
              ) : null}
            </div>
          </div>
        </CardContent>
      </div>
    </Card>
  )
}

function formatPreviewDate(value: string): string {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}
