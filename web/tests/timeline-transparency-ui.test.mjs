import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const timelineSource = readFileSync(resolve(here, "../src/features/timeline/TimelinePage.tsx"), "utf8")

function expectSource(pattern, message) {
  assert.match(timelineSource, pattern, message)
}

test("timeline summary includes strictness transparency", () => {
  expectSource(/strictness: \{timelineSummary\.strictness_level\}/, "strictness badge text missing")
  expectSource(/timelineSummary\.strictness_score/, "strictness score rendering missing")
  expectSource(/mode: \{timelineSummary\.mode\.name\}/, "mode badge rendering missing")
})

test("timeline summary includes filter funnel and restriction reasons", () => {
  expectSource(/Filter funnel/, "filter funnel heading missing")
  expectSource(/funnel\.fetched/, "filter funnel fetched count missing")
  expectSource(/funnel\.post_window/, "filter funnel window count missing")
  expectSource(/funnel\.post_seen/, "filter funnel seen count missing")
  expectSource(/funnel\.post_block/, "filter funnel block count missing")
  expectSource(/funnel\.selected/, "filter funnel selected count missing")
  expectSource(/FunnelBar/, "FunnelBar component usage missing")
  expectSource(/Top restriction reasons/, "restriction reason heading missing")
  expectSource(/timelineSummary\.restriction_reasons/, "restriction reason list wiring missing")
})

test("timeline summary exposes actionable recommendations", () => {
  expectSource(/Recommended actions/, "recommendations heading missing")
  expectSource(/timelineSummary\.recommendations/, "recommendations list wiring missing")
})
