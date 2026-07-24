import { cva, type VariantProps } from "class-variance-authority"

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

const metricVariants = cva("", {
  variants: {
    variant: {
      stat: "",
      compact: "",
      inline: "",
    },
  },
  defaultVariants: {
    variant: "stat",
  },
})

export function MetricCard({
  label,
  value,
  detail,
  variant = "stat",
  className,
}: {
  label: string
  value: string
  detail?: string
  className?: string
} & VariantProps<typeof metricVariants>) {
  if (variant === "inline") {
    // Flat row, not a boxed card-in-card: values read as typeset data.
    return (
      <div className={cn("flex items-center justify-between gap-3 border-b border-border/70 pb-2 last:border-0 last:pb-0", className)}>
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="font-mono text-sm font-medium tabular-nums text-foreground">{value}</span>
      </div>
    )
  }

  return (
    <Card className={cn(metricVariants({ variant }), className)}>
      <CardHeader className="pb-4">
        <CardDescription className="text-[13px] uppercase tracking-[0.06em]">{label}</CardDescription>
        <CardTitle className="font-display text-2xl tabular-nums">{value}</CardTitle>
        {detail ? <p className="text-sm text-muted-foreground">{detail}</p> : null}
      </CardHeader>
    </Card>
  )
}
