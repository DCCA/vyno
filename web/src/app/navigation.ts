import {
  Activity,
  Clock3,
  Database,
  History,
  LayoutDashboard,
  Rocket,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react"

import type { ConsoleSurface } from "@/app/types"

export const surfacePaths: Record<ConsoleSurface, string> = {
  dashboard: "/",
  run: "/run",
  onboarding: "/onboarding",
  sources: "/sources",
  profile: "/profile",
  schedule: "/schedule",
  timeline: "/timeline",
  history: "/history",
}

type NavItem = {
  id: ConsoleSurface
  label: string
  hint: string
  icon: typeof LayoutDashboard
}

export function navItemsForLifecycle(lifecycle: "needs_setup" | "ready"): NavItem[] {
  if (lifecycle === "needs_setup") {
    return [
      { id: "onboarding", label: "Setup", hint: "activation guide", icon: SlidersHorizontal },
      { id: "sources", label: "Sources", hint: "starter inputs", icon: Database },
      { id: "profile", label: "Profile", hint: "preferences", icon: ShieldCheck },
    ]
  }

  return [
    { id: "dashboard", label: "Dashboard", hint: "status and alerts", icon: LayoutDashboard },
    { id: "schedule", label: "Schedule", hint: "automation control", icon: Clock3 },
    { id: "run", label: "Run Center", hint: "manual run control", icon: Rocket },
    { id: "sources", label: "Sources", hint: "inputs and health", icon: Database },
    { id: "profile", label: "Profile", hint: "preferences and maintenance", icon: ShieldCheck },
    { id: "timeline", label: "Timeline", hint: "events and notes", icon: Activity },
    { id: "history", label: "History", hint: "snapshots and rollback", icon: History },
  ]
}

export function surfaceForPathname(pathname: string): ConsoleSurface {
  const match = Object.entries(surfacePaths).find(([, path]) => path === pathname)
  return (match?.[0] as ConsoleSurface | undefined) ?? "dashboard"
}
