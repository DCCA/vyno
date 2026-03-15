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
    return (
      <div className={cn("flex items-center justify-between rounded-lg border border-border bg-muted/30 px-4 py-3", className)}>
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="text-sm font-semibold text-foreground">{value}</span>
      </div>
    )
  }

  return (
    <Card className={cn(metricVariants({ variant }), className)}>
      <CardHeader className="pb-4">
        <CardDescription className="text-[11px] uppercase tracking-[0.06em]">{label}</CardDescription>
        <CardTitle className="font-display text-2xl">{value}</CardTitle>
        {detail ? <p className="text-sm text-muted-foreground">{detail}</p> : null}
      </CardHeader>
    </Card>
  )
}
