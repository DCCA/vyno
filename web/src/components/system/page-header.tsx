import type { ReactNode } from "react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

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
      <CardHeader className="gap-5 bg-gradient-to-br from-white/95 via-white/90 to-secondary/45 pb-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary/80">{eyebrow}</p>
          <div className="space-y-2">
            <CardTitle className="font-display text-2xl md:text-[2rem]">{title}</CardTitle>
            <CardDescription className="max-w-3xl text-[0.95rem] leading-7">{description}</CardDescription>
          </div>
          {badges && badges.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {badges.map((badge) => (
                <Badge key={`${badge.label}:${badge.variant ?? "default"}`} variant={badge.variant ?? "secondary"}>
                  {badge.label}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
        {actions ? (
          <CardContent className="rounded-[1.35rem] border border-border/80 bg-white/85 p-2 shadow-[0_18px_32px_-28px_rgba(15,23,42,0.5)]">
            {actions}
          </CardContent>
        ) : null}
      </CardHeader>
    </Card>
  )
}
