import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const appSource = readFileSync(resolve(here, "../src/App.tsx"), "utf8")
const navSource = readFileSync(resolve(here, "../src/app/navigation.ts"), "utf8")
const scheduleSource = readFileSync(resolve(here, "../src/features/schedule/SchedulePage.tsx"), "utf8")
const headerSource = readFileSync(resolve(here, "../src/components/system/page-header.tsx"), "utf8")
const onboardingSource = readFileSync(resolve(here, "../src/features/onboarding/OnboardingPage.tsx"), "utf8")
const profileSource = readFileSync(resolve(here, "../src/features/profile/ProfilePage.tsx"), "utf8")

function expectSource(source, pattern, message) {
  assert.match(source, pattern, message)
}

test("schedule is a dedicated workspace with its own route and save flow", () => {
  expectSource(navSource, /schedule: "\/schedule"/, "schedule route path missing")
  expectSource(appSource, /async function saveSchedule\(scope: "schedule" = "schedule"\)/, "schedule save handler missing")
  expectSource(appSource, /\/api\/config\/schedule/, "schedule config save endpoint missing")
  expectSource(appSource, /path="\/schedule"/, "schedule route missing")
  expectSource(scheduleSource, /title="Schedule"/, "schedule page header missing")
  expectSource(scheduleSource, /cadence: \${scheduleDraft\.cadence}/, "schedule header should show cadence")
  expectSource(scheduleSource, /formatTimestampBadge/, "schedule header should use a compact next-run label")
  expectSource(scheduleSource, /Schedule Controls/, "schedule controls section missing")
  expectSource(scheduleSource, /Quiet hours/, "schedule quiet-hours controls missing")
  expectSource(scheduleSource, /What Happens Next/, "schedule preview section missing")
  expectSource(scheduleSource, /Issues And Recovery/, "schedule recovery section missing")
})

test("setup and profile link into schedule controls instead of duplicating the full editor", () => {
  expectSource(onboardingSource, /Open schedule controls/, "onboarding schedule entry point missing")
  expectSource(profileSource, /Open schedule controls/, "profile schedule entry point missing")
  assert.doesNotMatch(profileSource, /Enable daily automation/, "profile should not keep the old embedded schedule toggle")
})

test("workspace header keeps a stable content column when actions are present", () => {
  expectSource(headerSource, /lg:grid-cols-\[minmax\(0,1fr\)_auto\]/, "workspace header should use a stable desktop grid")
  expectSource(headerSource, /max-w-\[68ch\]/, "workspace description should keep a readable measure without over-constraining")
  expectSource(headerSource, /text-balance/, "workspace description should balance headline copy")
})
