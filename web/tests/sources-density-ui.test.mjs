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

test("sources workspace exposes density-focused sub-surfaces", () => {
  expectSource(/Sources Workspace/, "sources workspace heading missing")
  expectSource(/<TabsTrigger value="overview">Overview<\/TabsTrigger>/, "overview tab missing")
  expectSource(/<TabsTrigger value="effective">Effective Sources<\/TabsTrigger>/, "effective sources tab missing")
  expectSource(/<TabsTrigger value="health">Source Health<\/TabsTrigger>/, "source health tab missing")
})

test("effective sources view includes search, truncation reveal, and row expansion", () => {
  expectSource(/Filter effective sources/, "effective source search label missing")
  expectSource(/effective-source-search/, "effective source search input missing")
  expectSource(/View full values/, "full source value reveal missing")
  expectSource(/Show more \(\$\{filteredSourceRows\.length - 12\}\)/, "effective source show more control missing")
})

test("source health view includes compact triage controls", () => {
  expectSource(/Filter failing sources/, "source health search label missing")
  expectSource(/source-health-search/, "source health search input missing")
  expectSource(/failing sources: \{sourceHealth\.length\}/, "source health summary metric missing")
  expectSource(/Show more \(\$\{filteredSourceHealth\.length - 12\}\)/, "source health show more control missing")
})
