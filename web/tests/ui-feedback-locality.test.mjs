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

test("feedback uses scoped channels instead of a single global action banner", () => {
  expectSource(/type NoticeScope = "global" \| "run" \| "onboarding" \| "sources" \| "profile" \| "review" \| "timeline" \| "history"/, "notice scope union missing")
  expectSource(/function setScopedNotice\(scope: NoticeScope, kind: Notice\["kind"\], text: string\)/, "scoped notice setter missing")
  expectSource(/function renderScopedNotice\(scope: NoticeScope\)/, "scoped notice renderer missing")
})

test("each major surface renders local feedback near actions", () => {
  expectSource(/\{renderScopedNotice\("run"\)\}/, "run scoped notice render missing")
  expectSource(/\{renderScopedNotice\("onboarding"\)\}/, "onboarding scoped notice render missing")
  expectSource(/\{renderScopedNotice\("sources"\)\}/, "sources scoped notice render missing")
  expectSource(/\{renderScopedNotice\("profile"\)\}/, "profile scoped notice render missing")
  expectSource(/\{renderScopedNotice\("review"\)\}/, "review scoped notice render missing")
  expectSource(/\{renderScopedNotice\("timeline"\)\}/, "timeline scoped notice render missing")
  expectSource(/\{renderScopedNotice\("history"\)\}/, "history scoped notice render missing")
})

test("success messages auto-dismiss while errors stay actionable", () => {
  expectSource(/globalNotice\.kind !== "ok"/, "global success auto-dismiss guard missing")
  expectSource(/notice\.kind !== "ok"/, "local success auto-dismiss guard missing")
  expectSource(/Dismiss/, "dismiss control missing")
  expectSource(/aria-live=\{notice\.kind === "error" \? "assertive" : "polite"\}/, "aria-live severity behavior missing")
})
