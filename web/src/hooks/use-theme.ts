import { useCallback, useEffect, useSyncExternalStore } from "react"

type Theme = "light" | "dark" | "system"

const STORAGE_KEY = "digest-theme"

function getSystemPreference(): "light" | "dark" {
  if (typeof window === "undefined") return "light"
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

function getStoredTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === "light" || stored === "dark" || stored === "system") return stored
  } catch {}
  return "system"
}

function applyTheme(theme: Theme) {
  const resolved = theme === "system" ? getSystemPreference() : theme
  document.documentElement.classList.toggle("dark", resolved === "dark")
}

let currentTheme: Theme = getStoredTheme()
applyTheme(currentTheme)

const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((fn) => fn())
}

function subscribe(cb: () => void) {
  listeners.add(cb)
  return () => { listeners.delete(cb) }
}

function getSnapshot(): Theme {
  return currentTheme
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)

  const setTheme = useCallback((next: Theme) => {
    currentTheme = next
    try { localStorage.setItem(STORAGE_KEY, next) } catch {}
    applyTheme(next)
    emit()
  }, [])

  const toggle = useCallback(() => {
    const resolved = currentTheme === "system" ? getSystemPreference() : currentTheme
    setTheme(resolved === "dark" ? "light" : "dark")
  }, [setTheme])

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)")
    const handler = () => {
      if (currentTheme === "system") applyTheme("system")
    }
    mq.addEventListener("change", handler)
    return () => mq.removeEventListener("change", handler)
  }, [])

  return { theme, setTheme, toggle }
}
