import type { ReactNode } from "react"

import { Badge } from "@/components/ui/badge"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function WorkspaceHeader({
  title,
  description,
  badges,
  actions,
}: {
  title: string
  description: string
  badges?: Array<{ label: string; variant?: "default" | "secondary" | "outline" | "success" | "warning" }>
  actions?: ReactNode
}) {
  const eyebrow = title === "Dashboard" ? "Overview" : "Workspace"

  return (
    <Card className="overflow-hidden border-border/80">
      <CardHeader className="gap-5 bg-gradient-to-br from-white/96 via-white/92 to-accent/10 pb-5 lg:grid lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start lg:gap-6">
        <div className="min-w-0 max-w-[72ch] space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary/72">{eyebrow}</p>
          <div className="space-y-2">
            <CardTitle className="font-display text-2xl md:text-[2rem]">{title}</CardTitle>
            <CardDescription className="max-w-[68ch] text-[0.98rem] leading-7 text-balance">{description}</CardDescription>
          </div>
          {badges && badges.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {badges.map((badge) => (
                <Badge key={`${badge.label}:${badge.variant ?? "default"}`} variant={badge.variant ?? "secondary"}>
                  {badge.label}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
        {actions ? (
          <div className="w-full rounded-[1.35rem] border border-border/80 bg-background/86 p-2 shadow-[0_18px_32px_-28px_rgba(19,23,30,0.24)] lg:w-auto lg:justify-self-end lg:self-start">
            {actions}
          </div>
        ) : null}
      </CardHeader>
    </Card>
  )
}
