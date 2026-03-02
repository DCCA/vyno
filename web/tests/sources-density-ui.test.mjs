import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const appSource = readFileSync(resolve(here, "../src/App.tsx"), "utf8")

function expectSource(pattern, message) {
  assert.match(appSource, pattern, message)
}

test("sources workspace merges management and triage into one surface", () => {
  expectSource(/CardTitle className="font-display">Sources<\/CardTitle>/, "sources unified heading missing")
  expectSource(/Manage inputs and triage source health in one unified workspace/, "sources unified description missing")
  expectSource(/Label htmlFor="unified-source-search">Filter sources<\/Label>/, "unified source filter missing")
})

test("unified sources view includes filter controls and merged columns", () => {
  expectSource(/Filter sources/, "unified source search label missing")
  expectSource(/unified-source-search/, "unified source search input missing")
  expectSource(/<TableHead className="w-\[140px\]">Type<\/TableHead>/, "type column missing")
  expectSource(/<TableHead className="w-\[320px\]">Source<\/TableHead>/, "source column missing")
  expectSource(/<TableHead className="w-\[160px\]">Status<\/TableHead>/, "status column missing")
  expectSource(/<TableHead className="sticky right-0 w-\[160px\] bg-card">Actions<\/TableHead>/, "actions column missing")
  expectSource(/Show more \(\$\{filteredUnifiedSourceRows\.length - 12\}\)/, "unified source show more control missing")
})

test("unified rows expose per-line edit and delete actions", () => {
  expectSource(/onClick=\{\(\) => editUnifiedSourceRow\(row\)\}/, "row edit action missing")
  expectSource(/onClick=\{\(\) => void deleteUnifiedSourceRow\(row\)\}/, "row delete action missing")
  expectSource(/Delete \$\{row\.type\} source\?/, "delete confirmation prompt missing")
  expectSource(/failing sources: \{sourceHealth\.length\}/, "source health summary metric missing")
})
