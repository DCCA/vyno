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
})

test("unified sources view includes filter controls and merged columns", () => {
  expectSource(sourcesSource, /Filter sources/, "unified source search label missing")
  expectSource(sourcesSource, /unified-source-search/, "unified source search input missing")
  expectSource(sourcesSource, /<TableHead className="w-\[140px\]">Type<\/TableHead>/, "type column missing")
  expectSource(sourcesSource, /<TableHead>Source<\/TableHead>/, "source column missing")
  expectSource(sourcesSource, /<TableHead className="w-\[150px\]">Status<\/TableHead>/, "status column missing")
  expectSource(sourcesSource, /<TableHead className="w-\[180px\] text-right">Actions<\/TableHead>/, "actions column missing")
  expectSource(sourcesSource, /title=\{statusHoverDetail\(row\)\}/, "status hover detail tooltip missing")
  expectSource(sourcesSource, /Show more \(\$\{filteredUnifiedSourceRows\.length - 12\}\)/, "unified source show more control missing")
})

test("unified rows expose per-line edit and delete actions", () => {
  expectSource(sourcesSource, /onClick=\{\(\) => onEditUnifiedSourceRow\(row\)\}/, "row edit action missing")
  expectSource(sourcesSource, /onClick=\{\(\) => onDeleteUnifiedSourceRow\(row\)\}/, "row delete action missing")
  expectSource(appSource, /Delete \$\{row\.type\} source\?/, "delete confirmation prompt missing")
  expectSource(sourcesSource, /label: `failing sources: \$\{sourceHealth\.length\}`/, "source health summary metric missing")
})

test("source value placeholder adapts to selected source type", () => {
  expectSource(utilsSource, /function sourceValuePlaceholderForType\(sourceType: string\)/, "placeholder helper missing")
  expectSource(utilsSource, /if \(st === "x_author"\) return "@thdxr or https:\/\/x\.com\/thdxr"/, "x_author placeholder missing")
  expectSource(utilsSource, /if \(st === "github_org"\) return "vercel-labs or https:\/\/github\.com\/vercel-labs"/, "github_org placeholder missing")
  expectSource(sourcesSource, /placeholder=\{sourceValuePlaceholderForType\(sourceType\)\}/, "dynamic source placeholder binding missing")
})
