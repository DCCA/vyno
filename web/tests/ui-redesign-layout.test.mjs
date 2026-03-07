import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const appSource = readFileSync(resolve(here, "../src/App.tsx"), "utf8")
const navSource = readFileSync(resolve(here, "../src/app/navigation.ts"), "utf8")
const cssSource = readFileSync(resolve(here, "../src/index.css"), "utf8")

function expectSource(source, pattern, message) {
  assert.match(source, pattern, message)
}

test("redesign exposes focused navigation surfaces", () => {
  expectSource(appSource, /Workspace Navigation/, "navigation panel title missing")
  expectSource(navSource, /label: "Dashboard"/, "dashboard surface missing")
  expectSource(navSource, /label: "Run Center"/, "run center surface missing")
  expectSource(navSource, /label: "Onboarding"/, "onboarding surface missing")
  expectSource(navSource, /label: "Sources"/, "sources surface missing")
  expectSource(navSource, /label: "Profile"/, "profile surface missing")
  expectSource(navSource, /label: "Review"/, "review surface missing")
  expectSource(navSource, /label: "Timeline"/, "timeline surface missing")
  expectSource(navSource, /label: "History"/, "history surface missing")
  expectSource(navSource, /dashboard: "\/"/, "dashboard route missing")
  expectSource(navSource, /run: "\/run"/, "run route missing")
  expectSource(navSource, /timeline: "\/timeline"/, "timeline route missing")
})

test("redesign includes responsive nav shell and animation hooks", () => {
  expectSource(appSource, /setMobileNavOpen/, "mobile nav state missing")
  expectSource(appSource, /lg:hidden/, "mobile menu button style missing")
  expectSource(appSource, /animate-surface-enter/, "surface animation class missing")
  expectSource(appSource, /NavLink/, "route-aware navigation missing")
  expectSource(appSource, /<Routes>/, "route shell missing")

  expectSource(cssSource, /@keyframes surface-enter/, "surface-enter keyframe missing")
  expectSource(cssSource, /\.animate-surface-enter\s*\{/, "surface animation utility missing")
  expectSource(cssSource, /prefers-reduced-motion: reduce/, "reduced motion fallback missing")
})
