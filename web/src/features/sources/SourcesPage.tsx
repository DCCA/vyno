import { Loader2 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { InlineNotice } from "@/components/system/notice"
import { WorkspaceHeader } from "@/components/system/page-header"
import { sourceValuePlaceholderForType, statusHoverDetail, truncateText } from "@/lib/console-utils"
import type { Notice, SaveAction, SourceHealthItem, SourceMap, UnifiedSourceRow } from "@/app/types"

export function SourcesPage({
  notice,
  onDismissNotice,
  sources,
  sourceHealth,
  sourceType,
  setSourceType,
  sourceValue,
  setSourceValue,
  sourceTypes,
  saving,
  saveAction,
  onHandleSourceMutation,
  sourceSearch,
  setSourceSearch,
  sourceStatusFilter,
  setSourceStatusFilter,
  filteredUnifiedSourceRows,
  unifiedRowsVisible,
  showAllUnifiedSources,
  setShowAllUnifiedSources,
  onEditUnifiedSourceRow,
  onDeleteUnifiedSourceRow,
}: {
  notice: Notice | null | undefined
  onDismissNotice: () => void
  sources: SourceMap
  sourceHealth: SourceHealthItem[]
  sourceType: string
  setSourceType: (value: string) => void
  sourceValue: string
  setSourceValue: (value: string) => void
  sourceTypes: string[]
  saving: boolean
  saveAction: SaveAction
  onHandleSourceMutation: (action: "add" | "remove") => void
  sourceSearch: string
  setSourceSearch: (value: string) => void
  sourceStatusFilter: "all" | "healthy" | "failing"
  setSourceStatusFilter: (value: "all" | "healthy" | "failing") => void
  filteredUnifiedSourceRows: UnifiedSourceRow[]
  unifiedRowsVisible: UnifiedSourceRow[]
  showAllUnifiedSources: boolean
  setShowAllUnifiedSources: (value: boolean | ((prev: boolean) => boolean)) => void
  onEditUnifiedSourceRow: (row: UnifiedSourceRow) => void
  onDeleteUnifiedSourceRow: (row: UnifiedSourceRow) => void
}) {
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
        <MetricTile label="Library size" value={String(totalSourceCount)} detail="Tracked source entries" />
        <MetricTile label="Active types" value={String(sortedSourceRows.length)} detail="Distinct connectors in use" />
        <MetricTile label="Health posture" value={sourceHealth.length > 0 ? "Watch" : "Clear"} detail={sourceHealth.length > 0 ? `${sourceHealth.length} sources need attention` : "No current failures"} />
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
            <InlineNotice notice={notice} onDismiss={onDismissNotice} />
          </CardContent>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="font-display">Source Library</CardTitle>
            <CardDescription>Filter sources, inspect health posture, and take row-level actions without leaving context.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-[1.35rem] border border-border/80 bg-secondary/30 p-4">
              <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_170px_auto] md:items-end">
              <div className="min-w-[240px] flex-1 space-y-2">
                <Label htmlFor="unified-source-search">Filter sources</Label>
                <Input
                  id="unified-source-search"
                  placeholder="Search type, source, error, or hint"
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
              <Badge variant="outline" className="justify-self-start md:justify-self-end">rows {filteredUnifiedSourceRows.length}</Badge>
              </div>
            </div>

            <div className="hidden overflow-y-auto rounded-md border md:block md:max-h-[620px]">
              <Table className="w-full table-fixed">
                <TableHeader className="sticky top-0 z-10 bg-card">
                  <TableRow>
                    <TableHead className="w-[140px]">Type</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead className="w-[150px]">Status</TableHead>
                    <TableHead className="w-[180px] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {unifiedRowsVisible.map((row) => (
                    <TableRow key={row.key} className="align-top">
                      <TableCell className="font-semibold">{row.type}</TableCell>
                      <TableCell className="font-mono text-xs" title={row.source}>
                        {truncateText(row.source, 96)}
                      </TableCell>
                      <TableCell>
                        <span tabIndex={0} title={statusHoverDetail(row)} className="inline-flex cursor-help">
                          <Badge variant={row.health === "failing" ? "warning" : "success"}>
                            {row.health === "failing" ? `failing (${row.count})` : "healthy"}
                          </Badge>
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="outline" size="sm" onClick={() => onEditUnifiedSourceRow(row)} disabled={saving}>
                            Edit
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onDeleteUnifiedSourceRow(row)}
                            disabled={saving}
                            className="border-destructive/40 text-destructive hover:bg-destructive/10"
                          >
                            Delete
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  {unifiedRowsVisible.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-sm text-muted-foreground">
                        No sources match the current filters.
                      </TableCell>
                    </TableRow>
                  ) : null}
                </TableBody>
              </Table>
            </div>

            <div className="space-y-2 md:hidden">
              {unifiedRowsVisible.length > 0 ? (
                unifiedRowsVisible.map((row) => (
                  <div key={`mobile:${row.key}`} className="rounded-lg border bg-muted/10 p-3">
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold">{row.type}</p>
                      <Badge variant={row.health === "failing" ? "warning" : "success"}>
                        {row.health === "failing" ? `failing (${row.count})` : "healthy"}
                      </Badge>
                    </div>
                    <p className="font-mono text-xs text-muted-foreground" title={row.source}>
                      {truncateText(row.source, 150)}
                    </p>
                    <p className="text-xs text-muted-foreground" title={row.last_error}>
                      error: {truncateText(row.last_error, 120)}
                    </p>
                    <p className="text-xs text-muted-foreground">last seen: {row.last_seen}</p>
                    <p className="text-xs" title={row.hint}>
                      hint: {truncateText(row.hint, 120)}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={() => onEditUnifiedSourceRow(row)} disabled={saving}>
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDeleteUnifiedSourceRow(row)}
                        disabled={saving}
                        className="border-destructive/40 text-destructive hover:bg-destructive/10"
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No sources match the current filters.</p>
              )}
            </div>

            {filteredUnifiedSourceRows.length > 12 ? (
              <div className="flex justify-end">
                <Button variant="outline" size="sm" onClick={() => setShowAllUnifiedSources((prev) => !prev)}>
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

function MetricTile({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <Card>
      <CardHeader className="pb-4">
        <CardDescription className="text-[11px] uppercase tracking-[0.14em]">{label}</CardDescription>
        <CardTitle className="font-display text-[1.8rem]">{value}</CardTitle>
        <p className="text-sm text-muted-foreground">{detail}</p>
      </CardHeader>
    </Card>
  )
}
