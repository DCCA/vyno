import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const appSource = readFileSync(resolve(here, "../src/App.tsx"), "utf8")
const typesSource = readFileSync(resolve(here, "../src/app/types.ts"), "utf8")
const noticeSource = readFileSync(resolve(here, "../src/components/system/notice.tsx"), "utf8")
const runSource = readFileSync(resolve(here, "../src/features/run-center/RunCenterPage.tsx"), "utf8")
const onboardingSource = readFileSync(resolve(here, "../src/features/onboarding/OnboardingPage.tsx"), "utf8")
const sourcesSource = readFileSync(resolve(here, "../src/features/sources/SourcesPage.tsx"), "utf8")
const profileSource = readFileSync(resolve(here, "../src/features/profile/ProfilePage.tsx"), "utf8")
const reviewSource = readFileSync(resolve(here, "../src/features/review/ReviewPage.tsx"), "utf8")
const timelineSource = readFileSync(resolve(here, "../src/features/timeline/TimelinePage.tsx"), "utf8")
const historySource = readFileSync(resolve(here, "../src/features/history/HistoryPage.tsx"), "utf8")

function expectSource(source, pattern, message) {
  assert.match(source, pattern, message)
}

test("feedback uses scoped channels instead of a single global action banner", () => {
  expectSource(typesSource, /type NoticeScope = "global" \| "run" \| "onboarding" \| "sources" \| "profile" \| "review" \| "timeline" \| "history"/, "notice scope union missing")
  expectSource(appSource, /function setScopedNotice\(scope: NoticeScope, kind: Notice\["kind"\], text: string\)/, "scoped notice setter missing")
  expectSource(noticeSource, /export function InlineNotice/, "scoped notice renderer missing")
})

test("each major surface renders local feedback near actions", () => {
  expectSource(runSource, /<InlineNotice notice=\{notice\}/, "run scoped notice render missing")
  expectSource(onboardingSource, /<InlineNotice notice=\{notice\}/, "onboarding scoped notice render missing")
  expectSource(sourcesSource, /<InlineNotice notice=\{notice\}/, "sources scoped notice render missing")
  expectSource(profileSource, /<InlineNotice notice=\{notice\}/, "profile scoped notice render missing")
  expectSource(reviewSource, /<InlineNotice notice=\{notice\}/, "review scoped notice render missing")
  expectSource(timelineSource, /<InlineNotice notice=\{notice\}/, "timeline scoped notice render missing")
  expectSource(historySource, /<InlineNotice notice=\{notice\}/, "history scoped notice render missing")
})

test("success messages auto-dismiss while errors stay actionable", () => {
  expectSource(appSource, /globalNotice\.kind !== "ok"/, "global success auto-dismiss guard missing")
  expectSource(appSource, /notice\.kind !== "ok"/, "local success auto-dismiss guard missing")
  expectSource(noticeSource, /Dismiss/, "dismiss control missing")
  expectSource(noticeSource, /aria-live=\{notice\.kind === "error" \? "assertive" : "polite"\}/, "aria-live severity behavior missing")
})
