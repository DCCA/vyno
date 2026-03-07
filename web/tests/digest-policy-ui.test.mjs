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

test("profile setup uses guided sections and inline apply actions", () => {
  expectSource(profileSource, /title="Profile Setup"/, "profile setup header missing")
  expectSource(profileSource, /Digest Goal/, "digest goal section missing")
  expectSource(profileSource, /Focus/, "focus section missing")
  expectSource(profileSource, /Quality And Cost/, "quality section missing")
  expectSource(profileSource, /Output/, "output section missing")
  expectSource(profileSource, /Apply Changes/, "compact apply panel missing")
  expectSource(profileSource, /Maintenance tools/, "maintenance utility section missing")
  expectSource(profileSource, /Expert mode/, "expert mode utility section missing")
  expectSource(profileSource, /Fresh only/, "fresh_only guided label missing")
  expectSource(profileSource, /Balanced/, "balanced guided label missing")
  expectSource(profileSource, /Catch up/, "replay_recent guided label missing")
  expectSource(profileSource, /Backfill/, "backfill guided label missing")
  expectSource(profileSource, /Save Changes/, "inline save action missing")
  expectSource(profileSource, /Diff tools/, "profile diff tools missing")
  expectSource(profileSource, /Compute diff/, "profile diff action missing")
  expectSource(profileSource, /Preview Reset/, "seen reset preview action missing")
  expectSource(profileSource, /Apply Reset/, "seen reset apply action missing")
})

test("profile route receives inline profile workflow handlers", () => {
  expectSource(appSource, /runPolicyChangeCount/, "run policy dirty tracking missing")
  expectSource(appSource, /const profileWorkspaceDirty = localDiffCount > 0 \|\| Boolean\(profileJsonParseError\)/, "profile dirty-state guard missing")
  expectSource(appSource, /function saveProfileWorkspace\(\)/, "profile workspace save handler missing")
  expectSource(appSource, /if \(!runPolicyDirty\) \{\s*setRunPolicy\(policyData\.run_policy\)\s*setRunPolicyBaseline\(policyData\.run_policy\)/s, "polling should not clobber dirty run policy state")
  expectSource(appSource, /async function refreshAll\(options\?: \{ preserveProfileWorkspace\?: boolean; preserveRunPolicyWorkspace\?: boolean \}\)/, "refreshAll preserve options missing")
  expectSource(appSource, /if \(!preserveProfileWorkspace \|\| !profileWorkspaceDirty \|\| !profile\) \{\s*setProfile\(profileData\.profile\)/s, "profile refresh dirty-state guard missing")
  expectSource(appSource, /onValidateProfile=\{\(\) => void validateProfile\("profile"\)\}/, "profile validate handler missing")
  expectSource(appSource, /onComputeProfileDiff=\{\(\) => void computeProfileDiff\("profile"\)\}/, "profile diff handler missing")
  expectSource(appSource, /onSaveProfileWorkspace=\{\(\) => void saveProfileWorkspace\(\)\}/, "profile inline save wiring missing")
  expectSource(profileSource, /This replaces the old standalone Review page/, "review removal migration copy missing")
})

test("review route is removed and diff stays inside profile", () => {
  assert.doesNotMatch(appSource, /path="\/review"/, "review route should be removed")
  assert.doesNotMatch(appSource, /ReviewPage/, "review page import should be removed")
  expectSource(profileSource, /Need deeper payload inspection\? Open Expert mode and use the Diff tab\./, "profile diff guidance missing")
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
