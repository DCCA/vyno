import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const appSource = readFileSync(resolve(here, "../src/App.tsx"), "utf8")
const profileSource = readFileSync(resolve(here, "../src/features/profile/ProfilePage.tsx"), "utf8")

function expectSource(source, pattern, message) {
  assert.match(source, pattern, message)
}

test("digest policy panel exposes required controls", () => {
  expectSource(profileSource, /Digest Policy/, "Digest policy panel title missing")
  expectSource(profileSource, /Configure digest strictness and seen-item behavior/, "Digest policy description missing")
  expectSource(profileSource, /<SelectItem value="fresh_only">fresh_only \(strict new\)<\/SelectItem>/, "fresh_only mode option missing")
  expectSource(profileSource, /<SelectItem value="balanced">balanced \(recommended\)<\/SelectItem>/, "balanced mode option missing")
  expectSource(profileSource, /<SelectItem value="replay_recent">replay_recent<\/SelectItem>/, "replay_recent mode option missing")
  expectSource(profileSource, /<SelectItem value="backfill">backfill \(advanced\)<\/SelectItem>/, "backfill mode option missing")
  expectSource(profileSource, /allow_run_override/, "run override toggle wiring missing")
  expectSource(profileSource, /seen_reset_guard/, "seen reset guard wiring missing")
  expectSource(profileSource, /Confirm seen reset/, "seen reset confirmation control missing")
  expectSource(profileSource, /Preview Reset/, "seen reset preview action missing")
  expectSource(profileSource, /Apply Reset/, "seen reset apply action missing")
})

test("policy and run-now API contracts are wired", () => {
  expectSource(appSource, /\/api\/config\/run-policy/, "run-policy API endpoint missing")
  expectSource(
    appSource,
    /JSON\.stringify\(\{\s*default_mode: runPolicy\.default_mode,\s*allow_run_override: runPolicy\.allow_run_override,\s*seen_reset_guard: runPolicy\.seen_reset_guard,\s*\}\)/s,
    "run-policy save payload missing expected fields",
  )
  expectSource(appSource, /\/api\/run-now/, "run-now API endpoint missing")
  expectSource(
    appSource,
    /body: JSON\.stringify\(selectedMode \? \{ mode: selectedMode \} : \{\}\)/,
    "run-now mode override payload missing",
  )
})
