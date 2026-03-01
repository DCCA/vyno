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

test("digest policy panel exposes required controls", () => {
  expectSource(/Digest Policy/, "Digest policy panel title missing")
  expectSource(/Configure digest strictness and seen-item behavior/, "Digest policy description missing")

  expectSource(/<SelectItem value="fresh_only">fresh_only \(strict new\)<\/SelectItem>/, "fresh_only mode option missing")
  expectSource(/<SelectItem value="balanced">balanced \(recommended\)<\/SelectItem>/, "balanced mode option missing")
  expectSource(/<SelectItem value="replay_recent">replay_recent<\/SelectItem>/, "replay_recent mode option missing")
  expectSource(/<SelectItem value="backfill">backfill \(advanced\)<\/SelectItem>/, "backfill mode option missing")

  expectSource(/allow_run_override/, "run override toggle wiring missing")
  expectSource(/seen_reset_guard/, "seen reset guard wiring missing")
  expectSource(/Confirm seen reset/, "seen reset confirmation control missing")
  expectSource(/Preview Reset/, "seen reset preview action missing")
  expectSource(/Apply Reset/, "seen reset apply action missing")
})

test("policy and run-now API contracts are wired", () => {
  expectSource(/\/api\/config\/run-policy/, "run-policy API endpoint missing")
  expectSource(
    /JSON\.stringify\(\{\s*default_mode: runPolicy\.default_mode,\s*allow_run_override: runPolicy\.allow_run_override,\s*seen_reset_guard: runPolicy\.seen_reset_guard,\s*\}\)/s,
    "run-policy save payload missing expected fields",
  )

  expectSource(/\/api\/run-now/, "run-now API endpoint missing")
  expectSource(
    /body: JSON\.stringify\(selectedMode \? \{ mode: selectedMode \} : \{\}\)/,
    "run-now mode override payload missing",
  )
})
