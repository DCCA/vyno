import {
  Activity,
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
  timeline: "/timeline",
  history: "/history",
}

export const navItems: Array<{
  id: ConsoleSurface
  label: string
  hint: string
  icon: typeof LayoutDashboard
}> = [
  { id: "dashboard", label: "Dashboard", hint: "status and alerts", icon: LayoutDashboard },
  { id: "run", label: "Run Center", hint: "manual run control", icon: Rocket },
  { id: "onboarding", label: "Onboarding", hint: "preflight and activation", icon: SlidersHorizontal },
  { id: "sources", label: "Sources", hint: "inputs and health", icon: Database },
  { id: "profile", label: "Profile", hint: "guided setup", icon: ShieldCheck },
  { id: "timeline", label: "Timeline", hint: "events and notes", icon: Activity },
  { id: "history", label: "History", hint: "snapshots and rollback", icon: History },
]

export function surfaceForPathname(pathname: string): ConsoleSurface {
  const match = Object.entries(surfacePaths).find(([, path]) => path === pathname)
  return (match?.[0] as ConsoleSurface | undefined) ?? "dashboard"
}
