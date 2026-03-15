import { useState } from "react"
import { AlertTriangle, ArrowUpRight, ChevronDown, ChevronUp, Clock3, ImageOff, Loader2, MoreHorizontal, Plus, Search } from "lucide-react"

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
  const [lastFeedbackKey, setLastFeedbackKey] = useState("")
  const [studioOpen, setStudioOpen] = useState(false)
  const sortedSourceRows = Object.entries(sources).sort((a, b) => a[0].localeCompare(b[0]))
  const totalSourceCount = sortedSourceRows.reduce((sum, [, values]) => sum + values.length, 0)

  function handleSourceFeedback(row: UnifiedSourceRow, label: "prefer_source" | "less_source" | "mute_source") {
    setLastFeedbackKey(row.key)
    onSourceFeedback(row, label)
    setTimeout(() => setLastFeedbackKey(""), 2000)
  }

  const previewRows = unifiedRowsVisible.filter((row) => row.preview_status === "ready")
  const compactRows = unifiedRowsVisible.filter((row) => row.preview_status !== "ready")

  return (
    <div className="space-y-4">
      <WorkspaceHeader
        title="Sources"
        description="Curate the signal library, keep ingestion healthy, and manage source quality from one structured workspace."
        badges={[
          { label: `${sortedSourceRows.length} types` },
          { label: `${totalSourceCount} sources` },
          { label: sourceHealth.length > 0 ? `${sourceHealth.length} failing` : "all healthy", variant: sourceHealth.length > 0 ? "warning" : "success" },
        ]}
      />

      {/* Filter bar — top-level, always visible */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[240px] flex-1 space-y-1">
          <Label htmlFor="unified-source-search" className="sr-only">Filter sources</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="unified-source-search"
              placeholder="Search sources..."
              value={sourceSearch}
              onChange={(event) => setSourceSearch(event.target.value)}
              className="pl-9"
            />
          </div>
        </div>
        <div className="w-[140px]">
          <Select value={sourceStatusFilter} onValueChange={(value) => setSourceStatusFilter(value === "failing" ? "failing" : value === "healthy" ? "healthy" : "all")}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All status</SelectItem>
              <SelectItem value="healthy">Healthy</SelectItem>
              <SelectItem value="failing">Failing</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Badge variant="outline">{filteredUnifiedSourceRows.length} cards</Badge>
      </div>

      {/* Source Studio — collapsible */}
      {studioOpen ? (
        <Card>
          <CardHeader className="flex-row items-center justify-between gap-3 space-y-0 pb-3">
            <div>
              <CardTitle className="font-display text-base">Add or remove source</CardTitle>
              <CardDescription>One source at a time without leaving the library.</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setStudioOpen(false)}>
              <ChevronUp className="h-4 w-4" />
              Close
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 md:grid-cols-[200px_1fr_auto]">
              <Select value={sourceType} onValueChange={setSourceType}>
                <SelectTrigger>
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  {sourceTypes.map((type) => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                placeholder={sourceValuePlaceholderForType(sourceType)}
                value={sourceValue}
                onChange={(event) => setSourceValue(event.target.value)}
              />
              <div className="flex gap-2">
                <Button onClick={() => onHandleSourceMutation("add")} disabled={saving}>
                  {saveAction === "source-add" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin" /> : null}
                  {saveAction === "source-add" ? "Adding..." : "Add"}
                </Button>
                <Button variant="outline" onClick={() => onHandleSourceMutation("remove")} disabled={saving}>
                  {saveAction === "source-remove" ? <Loader2 className="h-4 w-4 motion-safe:animate-spin" /> : null}
                  {saveAction === "source-remove" ? "Removing..." : "Remove"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Button variant="outline" onClick={() => setStudioOpen(true)}>
          <Plus className="h-4 w-4" />
          Add or remove source
        </Button>
      )}

      <InlineNotice notice={notice} onDismiss={() => clearScopedNotice("sources")} />

      {/* Compact cards — sources without items */}
      {compactRows.length > 0 ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Waiting for items
            </p>
            <Badge variant="secondary" className="text-[10px]">{compactRows.length}</Badge>
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {compactRows.map((row) => (
              <CompactSourceCard
                key={row.key}
                row={row}
                saving={saving}
                highlighted={lastFeedbackKey === row.key}
                onSourceFeedback={handleSourceFeedback}
                onEditUnifiedSourceRow={onEditUnifiedSourceRow}
                onDeleteUnifiedSourceRow={onDeleteUnifiedSourceRow}
              />
            ))}
          </div>
        </div>
      ) : null}

      {/* Preview cards — sources with items */}
      {previewRows.length > 0 ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Preview ready
            </p>
            <Badge variant="success" className="text-[10px]">{previewRows.length}</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {previewRows.map((row) => (
              <SourcePreviewCard
                key={row.key}
                row={row}
                saving={saving}
                highlighted={lastFeedbackKey === row.key}
                onSourceFeedback={handleSourceFeedback}
                onEditUnifiedSourceRow={onEditUnifiedSourceRow}
                onDeleteUnifiedSourceRow={onDeleteUnifiedSourceRow}
              />
            ))}
          </div>
        </div>
      ) : null}

      {unifiedRowsVisible.length === 0 ? (
        <EmptyState
          title="No sources match"
          description="Try adjusting your search or status filter."
        />
      ) : null}

      {filteredUnifiedSourceRows.length > 12 ? (
        <div className="flex justify-center">
          <Button variant="outline" size="sm" onClick={() => setShowAllUnifiedSources(!showAllUnifiedSources)}>
            {showAllUnifiedSources ? (
              <>Show less <ChevronUp className="h-3.5 w-3.5" /></>
            ) : (
              <>Show {filteredUnifiedSourceRows.length - 12} more <ChevronDown className="h-3.5 w-3.5" /></>
            )}
          </Button>
        </div>
      ) : null}
    </div>
  )
}

/* ── Compact card for sources without preview items ── */

function CompactSourceCard({
  row,
  saving,
  highlighted,
  onSourceFeedback,
  onEditUnifiedSourceRow,
  onDeleteUnifiedSourceRow,
}: {
  row: UnifiedSourceRow
  saving: boolean
  highlighted: boolean
  onSourceFeedback: (row: UnifiedSourceRow, label: "prefer_source" | "less_source" | "mute_source") => void
  onEditUnifiedSourceRow: (row: UnifiedSourceRow) => void
  onDeleteUnifiedSourceRow: (row: UnifiedSourceRow) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const isFailing = row.health === "failing"

  return (
    <div className={`animate-surface-enter rounded-lg border border-border bg-card p-4 transition-colors duration-150 hover:bg-muted/30 ${highlighted ? "ring-2 ring-accent/40" : ""}`}>
      {/* Header: badges + overflow */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Badge variant="outline" className="text-[10px]">{row.type_label}</Badge>
          <Badge variant={isFailing ? "warning" : "secondary"} className="text-[10px]">
            {isFailing ? "failing" : "waiting"}
          </Badge>
        </div>
        <Button variant="ghost" size="sm" className="h-6 w-6 shrink-0 rounded-full p-0 text-muted-foreground hover:text-foreground" onClick={() => setExpanded(!expanded)} aria-label="More actions">
          <MoreHorizontal className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Identity */}
      <div className="mt-2.5">
        <p className="truncate text-sm font-semibold leading-tight" title={row.identity_title}>{row.identity_title}</p>
        <p className="mt-0.5 truncate text-xs text-muted-foreground" title={row.source}>
          {row.identity_subtitle || truncateText(row.source, 50)}
        </p>
      </div>

      {/* Failing detail */}
      {isFailing ? (
        <div className="mt-2 rounded-lg bg-amber-50/60 px-2.5 py-1.5 dark:bg-amber-950/20">
          <p className="flex items-center gap-1 text-[11px] font-medium text-amber-800 dark:text-amber-300">
            <AlertTriangle className="h-3 w-3 shrink-0" />
            {truncateText(row.last_error, 60)}
          </p>
        </div>
      ) : null}

      {/* Actions */}
      <div className="mt-3 flex items-center gap-1.5 border-t border-border/50 pt-3">
        <Button variant="outline" size="sm" className="h-7 rounded-lg text-xs" onClick={() => onSourceFeedback(row, "prefer_source")} disabled={saving}>Prefer</Button>
        <Button variant="outline" size="sm" className="h-7 rounded-lg text-xs" onClick={() => onSourceFeedback(row, "less_source")} disabled={saving}>Less</Button>
        <div className="flex-1" />
        {expanded ? (
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" className="h-7 rounded-lg text-xs text-destructive" onClick={() => onSourceFeedback(row, "mute_source")} disabled={saving}>Mute</Button>
            {row.can_edit ? <Button variant="ghost" size="sm" className="h-7 rounded-lg text-xs" onClick={() => onEditUnifiedSourceRow(row)} disabled={saving}>Edit</Button> : null}
            {row.can_delete ? <Button variant="ghost" size="sm" className="h-7 rounded-lg text-xs text-destructive" onClick={() => onDeleteUnifiedSourceRow(row)} disabled={saving}>Delete</Button> : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}

/* ── Full preview card for sources with items ── */

function SourcePreviewCard({
  row,
  saving,
  highlighted,
  onSourceFeedback,
  onEditUnifiedSourceRow,
  onDeleteUnifiedSourceRow,
}: {
  row: UnifiedSourceRow
  saving: boolean
  highlighted: boolean
  onSourceFeedback: (row: UnifiedSourceRow, label: "prefer_source" | "less_source" | "mute_source") => void
  onEditUnifiedSourceRow: (row: UnifiedSourceRow) => void
  onDeleteUnifiedSourceRow: (row: UnifiedSourceRow) => void
}) {
  const [imageFailed, setImageFailed] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const isFailing = row.health === "failing"
  const hasPreviewImage = Boolean(row.preview_image_url && !imageFailed)
  const hasPreviewLink = Boolean(row.preview_url)
  const metaLine = [row.preview_host || row.type_label, row.preview_published_at ? formatPreviewDate(row.preview_published_at) : ""]
    .filter(Boolean)
    .join(" · ")

  return (
    <Card className={`animate-surface-enter overflow-hidden transition-[box-shadow,border-color] duration-150 hover:shadow-panel-lg ${highlighted ? "ring-2 ring-accent/40" : ""}`}>
      <div className="flex h-full flex-col">
        {/* Media area */}
        <div className="source-card-media">
          {hasPreviewImage ? (
            hasPreviewLink ? (
              <a href={row.preview_url ?? undefined} target="_blank" rel="noreferrer" className="group block">
                <img
                  src={row.preview_image_url ?? undefined}
                  alt={row.preview_title}
                  width={620}
                  height={400}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.015]"
                  loading="lazy"
                  onError={() => setImageFailed(true)}
                />
                <div className="source-card-media-overlay" aria-hidden="true" />
              </a>
            ) : (
              <>
                <img
                  src={row.preview_image_url ?? undefined}
                  alt={row.preview_title}
                  width={620}
                  height={400}
                  className="h-full w-full object-cover"
                  loading="lazy"
                  onError={() => setImageFailed(true)}
                />
                <div className="source-card-media-overlay" aria-hidden="true" />
              </>
            )
          ) : (
            <div className="source-card-placeholder flex h-full w-full items-end justify-between p-4">
              <Badge variant="secondary">
                {row.type_label}
              </Badge>
              <div className="rounded-full border border-border bg-card p-2 text-muted-foreground">
                <ImageOff className="h-4 w-4" aria-hidden="true" />
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3 p-4">
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge variant="outline" className="text-[10px]">{row.type_label}</Badge>
            <Badge variant={isFailing ? "warning" : "success"} className="text-[10px]">
              {isFailing ? `failing (${row.count})` : "ready"}
            </Badge>
          </div>
          <div className="min-w-0 space-y-1">
            <div className="text-xs text-muted-foreground">{metaLine}</div>
            {hasPreviewLink ? (
              <a href={row.preview_url ?? undefined} target="_blank" rel="noreferrer" className="block hover:underline">
                <h3 className="source-card-title-clamp font-display text-[1.05rem] leading-tight tracking-[-0.02em] text-foreground">
                  {row.preview_title}
                </h3>
              </a>
            ) : (
              <h3 className="source-card-title-clamp font-display text-[1.05rem] leading-tight tracking-[-0.02em] text-foreground">
                {row.preview_title}
              </h3>
            )}
            <p className="source-card-description-clamp text-sm leading-relaxed text-muted-foreground">
              {row.preview_description}
            </p>
          </div>
          <div className="flex min-w-0 items-center gap-2 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">{row.identity_title}</span>
            <span className="truncate" title={row.source}>{truncateText(row.source, 40)}</span>
          </div>
        </div>

        {/* Error detail */}
        {isFailing ? (
          <div className="mx-4 mb-3 rounded-lg border border-amber-300/40 bg-amber-50/50 px-3 py-2 text-xs dark:border-amber-700/30 dark:bg-amber-950/20">
            <div className="flex items-center gap-1.5 font-semibold text-amber-800 dark:text-amber-300">
              <AlertTriangle className="h-3.5 w-3.5" />
              Ingestion issue
            </div>
            <p className="mt-1 text-amber-700 dark:text-amber-400" title={row.last_error}>{truncateText(row.last_error, 100)}</p>
          </div>
        ) : null}

        {/* Action footer */}
        <div className="flex items-center gap-1.5 border-t border-border/60 px-4 py-2.5">
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => onSourceFeedback(row, "prefer_source")} disabled={saving}>Prefer</Button>
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => onSourceFeedback(row, "less_source")} disabled={saving}>Less</Button>
          <div className="flex-1" />
          {expanded ? (
            <>
              <Button variant="ghost" size="sm" className="h-7 text-xs border-destructive/40 text-destructive" onClick={() => onSourceFeedback(row, "mute_source")} disabled={saving}>Mute</Button>
              {row.can_edit ? <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => onEditUnifiedSourceRow(row)} disabled={saving}>Edit</Button> : null}
              {row.can_delete ? <Button variant="ghost" size="sm" className="h-7 text-xs text-destructive" onClick={() => onDeleteUnifiedSourceRow(row)} disabled={saving}>Delete</Button> : null}
            </>
          ) : null}
          <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setExpanded(!expanded)} aria-label="More actions">
            <MoreHorizontal className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </Card>
  )
}

function formatPreviewDate(value: string): string {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}
