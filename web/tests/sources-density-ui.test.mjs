import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const sourcesSource = readFileSync(resolve(here, "../src/features/sources/SourcesPage.tsx"), "utf8")
const utilsSource = readFileSync(resolve(here, "../src/lib/console-utils.ts"), "utf8")
const appSource = readFileSync(resolve(here, "../src/App.tsx"), "utf8")

function expectSource(source, pattern, message) {
  assert.match(source, pattern, message)
}

test("sources workspace merges management and triage into one surface", () => {
  expectSource(sourcesSource, /WorkspaceHeader/, "sources workspace header missing")
  expectSource(sourcesSource, /Curate the signal library, keep ingestion healthy/, "sources unified description missing")
  expectSource(sourcesSource, /Source Studio/, "source studio module missing")
  expectSource(sourcesSource, /Source Library/, "source library module missing")
  expectSource(sourcesSource, /Label htmlFor="unified-source-search">Filter sources<\/Label>/, "unified source filter missing")
  expectSource(sourcesSource, /Browse sources as latest-item link cards with clearer preview hierarchy/, "source library preview description missing")
})

test("unified sources view is card-first with preview metadata", () => {
  expectSource(sourcesSource, /Filter sources/, "unified source search label missing")
  expectSource(sourcesSource, /unified-source-search/, "unified source search input missing")
  expectSource(sourcesSource, /Search preview title, source, host, error, or hint/, "preview search placeholder missing")
  expectSource(sourcesSource, /cards \{filteredUnifiedSourceRows\.length\}/, "card count badge missing")
  expectSource(sourcesSource, /function SourcePreviewCard/, "source preview card component missing")
  expectSource(sourcesSource, /Preview not ready yet/, "preview fallback message missing")
  expectSource(sourcesSource, /Primary action opens preview/, "single primary action hint missing")
  expectSource(sourcesSource, /row\.preview_image_url/, "preview image binding missing")
  expectSource(sourcesSource, /row\.preview_title/, "preview title binding missing")
  expectSource(sourcesSource, /row\.preview_host/, "preview host binding missing")
  expectSource(sourcesSource, /source-card-title-clamp/, "title clamp class missing")
  expectSource(sourcesSource, /source-card-description-clamp/, "description clamp class missing")
  expectSource(sourcesSource, /Ingestion issue detected/, "inline failing-state message missing")
  expectSource(sourcesSource, /Show more \(\$\{filteredUnifiedSourceRows\.length - 12\}\)/, "unified source show more control missing")
})

test("unified rows expose local actions and config-only handling", () => {
  expectSource(sourcesSource, /onClick=\{\(\) => onEditUnifiedSourceRow\(row\)\}/, "row edit action missing")
  expectSource(sourcesSource, /onClick=\{\(\) => onDeleteUnifiedSourceRow\(row\)\}/, "row delete action missing")
  expectSource(sourcesSource, /managed in config/, "config-only source handling missing")
  expectSource(appSource, /Delete \$\{row\.type\} source\?/, "delete confirmation prompt missing")
  expectSource(appSource, /if \(!row\.can_delete\) return/, "delete guard missing")
  expectSource(sourcesSource, /label: `failing sources: \$\{sourceHealth\.length\}`/, "source health summary metric missing")
  assert.doesNotMatch(sourcesSource, /Open preview/, "duplicate footer preview button should be removed")
})

test("source value placeholder adapts to selected source type", () => {
  expectSource(utilsSource, /function sourceValuePlaceholderForType\(sourceType: string\)/, "placeholder helper missing")
  expectSource(utilsSource, /if \(st === "x_author"\) return "@thdxr or https:\/\/x\.com\/thdxr"/, "x_author placeholder missing")
  expectSource(utilsSource, /if \(st === "github_org"\) return "vercel-labs or https:\/\/github\.com\/vercel-labs"/, "github_org placeholder missing")
  expectSource(sourcesSource, /placeholder=\{sourceValuePlaceholderForType\(sourceType\)\}/, "dynamic source placeholder binding missing")
})

test("sources app reads preview rows from the API and filters against preview fields", () => {
  expectSource(appSource, /api<\{ items: UnifiedSourceRow\[\] \}>\("\/api\/source-previews"\)/, "source previews API call missing")
  expectSource(appSource, /setUnifiedSourceRows\(sourcePreviewData\.items\)/, "source previews state assignment missing")
  expectSource(appSource, /row\.preview_title\.toLowerCase\(\)\.includes\(query\)/, "preview title filtering missing")
  expectSource(appSource, /row\.preview_description\.toLowerCase\(\)\.includes\(query\)/, "preview description filtering missing")
  expectSource(appSource, /row\.preview_host\.toLowerCase\(\)\.includes\(query\)/, "preview host filtering missing")
})
