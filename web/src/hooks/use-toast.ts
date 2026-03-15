import { useCallback, useSyncExternalStore } from "react"

export type Toast = {
  id: number
  kind: "ok" | "error"
  text: string
  createdAt: number
}

let nextId = 1
let toasts: Toast[] = []
const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((fn) => fn())
}

function addToast(kind: Toast["kind"], text: string) {
  const id = nextId++
  toasts = [...toasts, { id, kind, text, createdAt: Date.now() }]
  emit()
  setTimeout(() => dismissToast(id), 5000)
}

function dismissToast(id: number) {
  const prev = toasts
  toasts = toasts.filter((t) => t.id !== id)
  if (toasts !== prev) emit()
}

function subscribe(cb: () => void) {
  listeners.add(cb)
  return () => {
    listeners.delete(cb)
  }
}

function getSnapshot() {
  return toasts
}

export function useToast() {
  const items = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
  const toast = useCallback((kind: Toast["kind"], text: string) => addToast(kind, text), [])
  const dismiss = useCallback((id: number) => dismissToast(id), [])
  return { toasts: items, toast, dismiss }
}
