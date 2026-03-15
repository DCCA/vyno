import { useCallback, useEffect, useState } from "react"
import { Command } from "cmdk"
import * as Dialog from "@radix-ui/react-dialog"
import { useNavigate } from "react-router-dom"
import {
  Activity,
  Clock3,
  Database,
  History,
  LayoutDashboard,
  Moon,
  Play,
  Rocket,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sun,
} from "lucide-react"

import { useTheme } from "@/hooks/use-theme"

const pages = [
  { id: "dashboard", label: "Dashboard", hint: "Status and alerts", path: "/", icon: LayoutDashboard },
  { id: "schedule", label: "Schedule", hint: "Automation control", path: "/schedule", icon: Clock3 },
  { id: "run", label: "Run Center", hint: "Manual run control", path: "/run", icon: Rocket },
  { id: "sources", label: "Sources", hint: "Inputs and health", path: "/sources", icon: Database },
  { id: "profile", label: "Profile", hint: "Preferences", path: "/profile", icon: ShieldCheck },
  { id: "timeline", label: "Timeline", hint: "Events and notes", path: "/timeline", icon: Activity },
  { id: "history", label: "History", hint: "Snapshots and rollback", path: "/history", icon: History },
  { id: "onboarding", label: "Setup", hint: "Activation guide", path: "/onboarding", icon: SlidersHorizontal },
]

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [])

  const goTo = useCallback(
    (path: string) => {
      navigate(path)
      setOpen(false)
    },
    [navigate],
  )

  const resolvedTheme = theme === "system"
    ? (document.documentElement.classList.contains("dark") ? "dark" : "light")
    : theme

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 animate-fade-in" />
        <Dialog.Content
          className="fixed left-1/2 top-[20%] z-50 w-full max-w-[540px] -translate-x-1/2 rounded-xl border border-border bg-card shadow-lg animate-scale-in overflow-hidden"
          aria-label="Command palette"
        >
          <Command loop>
            <div className="flex items-center gap-2 border-b border-border px-4">
              <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
              <Command.Input placeholder="Type a command or search..." />
            </div>
            <Command.List>
              <Command.Empty>No results found.</Command.Empty>
              <Command.Group heading="Pages">
                {pages.map((page) => {
                  const Icon = page.icon
                  return (
                    <Command.Item
                      key={page.id}
                      value={`${page.label} ${page.hint}`}
                      onSelect={() => goTo(page.path)}
                    >
                      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="flex-1">
                        <span className="font-medium">{page.label}</span>
                        <span className="ml-2 text-muted-foreground text-[13px]">{page.hint}</span>
                      </span>
                    </Command.Item>
                  )
                })}
              </Command.Group>
              <Command.Separator />
              <Command.Group heading="Actions">
                <Command.Item
                  value="Run digest now"
                  onSelect={() => {
                    goTo("/run")
                  }}
                >
                  <Play className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="font-medium">Run digest now</span>
                </Command.Item>
                <Command.Item
                  value="Toggle theme dark light"
                  onSelect={() => {
                    toggle()
                    setOpen(false)
                  }}
                >
                  {resolvedTheme === "dark" ? (
                    <Sun className="h-4 w-4 shrink-0 text-muted-foreground" />
                  ) : (
                    <Moon className="h-4 w-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className="font-medium">
                    Switch to {resolvedTheme === "dark" ? "light" : "dark"} mode
                  </span>
                </Command.Item>
              </Command.Group>
            </Command.List>
            <div className="border-t border-border px-4 py-2 text-[12px] text-muted-foreground flex items-center gap-3">
              <span className="flex items-center gap-1">
                <kbd className="inline-flex h-5 items-center rounded border border-border bg-muted px-1.5 text-[11px] font-mono">↑↓</kbd>
                navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="inline-flex h-5 items-center rounded border border-border bg-muted px-1.5 text-[11px] font-mono">↵</kbd>
                select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="inline-flex h-5 items-center rounded border border-border bg-muted px-1.5 text-[11px] font-mono">esc</kbd>
                close
              </span>
            </div>
          </Command>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
