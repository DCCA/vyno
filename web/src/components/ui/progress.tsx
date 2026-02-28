import * as React from "react"

import { cn } from "@/lib/utils"

type ProgressProps = React.HTMLAttributes<HTMLDivElement> & {
  value?: number
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(({ className, value, ...props }, ref) => {
  const clamped = Math.max(0, Math.min(100, Number.isFinite(value) ? Number(value) : 0))

  return (
    <div
      ref={ref}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-muted", className)}
      {...props}
    >
      <div
        className="h-full w-full flex-1 bg-primary transition-transform motion-reduce:transition-none"
        style={{ transform: `translateX(-${100 - clamped}%)` }}
      />
    </div>
  )
})
Progress.displayName = "Progress"

export { Progress }
