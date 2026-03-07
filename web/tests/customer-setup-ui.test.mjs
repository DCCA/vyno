import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { test } from "node:test"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const appSource = readFileSync(resolve(here, "../src/App.tsx"), "utf8")
const navigationSource = readFileSync(resolve(here, "../src/app/navigation.ts"), "utf8")
const onboardingSource = readFileSync(resolve(here, "../src/features/onboarding/OnboardingPage.tsx"), "utf8")
const dashboardSource = readFileSync(resolve(here, "../src/features/dashboard/DashboardPage.tsx"), "utf8")
const profileSource = readFileSync(resolve(here, "../src/features/profile/ProfilePage.tsx"), "utf8")
const apiSource = readFileSync(resolve(here, "../src/lib/api.ts"), "utf8")
const startAppSource = readFileSync(resolve(here, "../../scripts/start-app.sh"), "utf8")

function expectSource(source, pattern, message) {
  assert.match(source, pattern, message)
}

test("onboarding is a guided first-run setup flow", () => {
  expectSource(onboardingSource, /title=\{revisitMode \? "Setup Guide" : "Guided Setup"\}/, "guided setup header missing")
  expectSource(onboardingSource, /Activation Milestones/, "activation milestone summary missing")
  expectSource(onboardingSource, /Connect at least one output/, "output step missing")
  expectSource(onboardingSource, /Choose starter sources/, "source pack step missing")
  expectSource(onboardingSource, /Set digest preferences/, "preferences step missing")
  expectSource(onboardingSource, /Enable daily automation/, "schedule step missing")
  expectSource(onboardingSource, /Preview the digest/, "preview step missing")
  expectSource(onboardingSource, /Start the first live digest/, "live run step missing")
  expectSource(onboardingSource, /Save schedule/, "schedule save action missing")
})

test("app routes incomplete setups into onboarding", () => {
  expectSource(appSource, /<Navigate to=\{surfacePaths\.onboarding\} replace \/>/, "incomplete setup redirect missing")
  expectSource(appSource, /api<\{ schedule_status: ScheduleStatus \}>\("\/api\/schedule\/status"\)/, "schedule status fetch missing")
  expectSource(appSource, /const onboardingLifecycle = onboarding\?\.lifecycle \?\? "needs_setup"/, "app should read onboarding lifecycle")
  expectSource(navigationSource, /navItemsForLifecycle/, "navigation should be lifecycle aware")
  expectSource(navigationSource, /label: "Setup"/, "setup nav label missing")
})

test("dashboard and profile expose automation status after setup", () => {
  expectSource(dashboardSource, /Automation Control/, "dashboard automation control module missing")
  expectSource(dashboardSource, /Current Posture/, "dashboard posture module missing")
  expectSource(dashboardSource, /Automation enabled|Automation not enabled/, "dashboard automation messaging missing")
  expectSource(profileSource, /title="Automation"/, "profile automation section missing")
  expectSource(profileSource, /Enable daily automation/, "profile schedule toggle missing")
  expectSource(profileSource, /Revisit setup guide/, "profile revisit setup action missing")
  expectSource(onboardingSource, /Active workspace/, "onboarding revisit banner missing")
})

test("local app startup uses proxied api calls and blocks port conflicts", () => {
  expectSource(apiSource, /const target = API_BASE \? `\$\{API_BASE\}\$\{path\}` : path/, "api client should support relative paths when no base is set")
  expectSource(startAppSource, /VITE_API_BASE=\$\{VITE_API_BASE:-\}/, "start-app should not force a browser api base by default")
  expectSource(startAppSource, /ensure_port_available "\$\{API_PORT\}" "API"/, "start-app should guard the API port")
  expectSource(startAppSource, /ensure_port_available "\$\{UI_PORT\}" "UI"/, "start-app should guard the UI port")
})
