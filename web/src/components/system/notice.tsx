import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

import type { Notice } from "@/app/types"

export function InlineNotice({
  notice,
  onDismiss,
}: {
  notice: Notice | null | undefined
  onDismiss: () => void
}) {
  if (!notice) return null
  return (
    <Alert variant={notice.kind === "error" ? "destructive" : "default"} role="status" aria-live={notice.kind === "error" ? "assertive" : "polite"}>
      <AlertTitle>{notice.kind === "error" ? "Action failed" : "Action completed"}</AlertTitle>
      <AlertDescription className="flex items-start justify-between gap-3">
        <span>{notice.text}</span>
        <Button variant="ghost" size="sm" onClick={onDismiss}>
          Dismiss
        </Button>
      </AlertDescription>
    </Alert>
  )
}
