import { type ReactNode, useCallback, useRef, useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

type ConfirmOptions = {
  title: string
  description: string
  confirmLabel?: string
  variant?: "default" | "destructive"
}

type ConfirmDialogState = ConfirmOptions & {
  resolve: (confirmed: boolean) => void
}

export function useConfirm() {
  const [state, setState] = useState<ConfirmDialogState | null>(null)

  const confirm = useCallback(
    (options: ConfirmOptions): Promise<boolean> =>
      new Promise((resolve) => {
        setState({ ...options, resolve })
      }),
    [],
  )

  const handleClose = useCallback(
    (confirmed: boolean) => {
      state?.resolve(confirmed)
      setState(null)
    },
    [state],
  )

  return { confirmState: state, confirm, handleClose }
}

export function ConfirmDialog({
  state,
  onClose,
}: {
  state: ConfirmDialogState | null
  onClose: (confirmed: boolean) => void
}) {
  const overlayRef = useRef<HTMLDivElement>(null)

  if (!state) return null

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose(false)
      }}
    >
      <Card className="mx-4 w-full max-w-md animate-surface-enter shadow-panel">
        <CardHeader>
          <CardTitle className="font-display">{state.title}</CardTitle>
          <CardDescription>{state.description}</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onClose(false)}>
            Cancel
          </Button>
          <Button
            variant={state.variant === "destructive" ? "destructive" : "default"}
            onClick={() => onClose(true)}
          >
            {state.confirmLabel ?? "Confirm"}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
