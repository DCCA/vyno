import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const appSource = readFileSync(resolve(here, "../src/App.tsx"), "utf8")
const cssSource = readFileSync(resolve(here, "../src/index.css"), "utf8")

function expectApp(pattern, message) {
  assert.match(appSource, pattern, message)
}

function expectCss(pattern, message) {
  assert.match(cssSource, pattern, message)
}

test("redesign exposes focused navigation surfaces", () => {
  expectApp(/Workspace Navigation/, "navigation panel title missing")
  expectApp(/label: "Dashboard"/, "dashboard surface missing")
  expectApp(/label: "Run Center"/, "run center surface missing")
  expectApp(/label: "Onboarding"/, "onboarding surface missing")
  expectApp(/label: "Sources"/, "sources surface missing")
  expectApp(/label: "Profile"/, "profile surface missing")
  expectApp(/label: "Review"/, "review surface missing")
  expectApp(/label: "Timeline"/, "timeline surface missing")
  expectApp(/label: "History"/, "history surface missing")
})

test("redesign includes responsive nav shell and animation hooks", () => {
  expectApp(/setMobileNavOpen/, "mobile nav state missing")
  expectApp(/lg:hidden/, "mobile menu button style missing")
  expectApp(/animate-surface-enter/, "surface animation class missing")

  expectCss(/@keyframes surface-enter/, "surface-enter keyframe missing")
  expectCss(/\.animate-surface-enter\s*\{/, "surface animation utility missing")
  expectCss(/prefers-reduced-motion: reduce/, "reduced motion fallback missing")
})
