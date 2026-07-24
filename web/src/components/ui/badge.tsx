import type React from "react"

import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[13px] font-semibold uppercase tracking-[0.04em] transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-border bg-secondary text-secondary-foreground",
        outline: "border-border bg-background text-foreground",
        // State voices: tinted surface + ink, tuned to >=7:1 in both themes.
        success: "border-transparent bg-success-surface text-success-ink",
        warning: "border-transparent bg-warning-surface text-warning-ink",
        destructive: "border-transparent bg-destructive-surface text-destructive-ink",
        accent: "border-transparent gradient-accent text-accent-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}
