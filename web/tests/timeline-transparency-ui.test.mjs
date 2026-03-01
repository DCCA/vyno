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

test("timeline summary includes strictness transparency", () => {
  expectSource(/strictness: \{timelineSummary\.strictness_level\}/, "strictness badge text missing")
  expectSource(/timelineSummary\.strictness_score/, "strictness score rendering missing")
  expectSource(/mode: \{timelineSummary\.mode\.name\}/, "mode badge rendering missing")
})

test("timeline summary includes filter funnel and restriction reasons", () => {
  expectSource(/Filter funnel/, "filter funnel heading missing")
  expectSource(/fetched=\{timelineSummary\.filter_funnel\.fetched\}/, "filter funnel fetched count missing")
  expectSource(/post_window=\{timelineSummary\.filter_funnel\.post_window\}/, "filter funnel window count missing")
  expectSource(/post_seen=\{timelineSummary\.filter_funnel\.post_seen\}/, "filter funnel seen count missing")
  expectSource(/post_block=\{timelineSummary\.filter_funnel\.post_block\}/, "filter funnel block count missing")
  expectSource(/selected=\{timelineSummary\.filter_funnel\.selected\}/, "filter funnel selected count missing")

  expectSource(/Top restriction reasons/, "restriction reason heading missing")
  expectSource(/timelineSummary\.restriction_reasons/, "restriction reason list wiring missing")
})

test("timeline summary exposes actionable recommendations", () => {
  expectSource(/Recommended actions/, "recommendations heading missing")
  expectSource(/timelineSummary\.recommendations/, "recommendations list wiring missing")
})
