import { X } from "lucide-react"

import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"

export function Toaster() {
  const { toasts, dismiss } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" aria-live="polite">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "animate-surface-enter flex min-w-[280px] max-w-[420px] items-start gap-2 rounded-xl border px-4 py-3 shadow-panel",
            t.kind === "error"
              ? "border-destructive/40 bg-destructive/5 text-destructive"
              : "border-border bg-card text-foreground",
          )}
        >
          <p className="flex-1 text-sm">{t.text}</p>
          <button
            onClick={() => dismiss(t.id)}
            className="shrink-0 rounded-md p-0.5 text-muted-foreground hover:text-foreground"
            aria-label="Dismiss"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}
