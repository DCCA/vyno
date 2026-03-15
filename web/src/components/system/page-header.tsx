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
  return (
    <Card>
      <CardHeader className="gap-4 lg:grid lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start lg:gap-6">
        <div className="min-w-0 max-w-[72ch] space-y-2">
          <div className="space-y-1">
            <CardTitle className="font-display text-xl md:text-2xl">{title}</CardTitle>
            <CardDescription className="max-w-[68ch] text-balance">{description}</CardDescription>
          </div>
          {badges && badges.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {badges.map((badge) => (
                <Badge key={`${badge.label}:${badge.variant ?? "default"}`} variant={badge.variant ?? "secondary"}>
                  {badge.label}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
        {actions ? (
          <div className="flex flex-wrap items-center gap-2 lg:justify-self-end lg:self-start">
            {actions}
          </div>
        ) : null}
      </CardHeader>
    </Card>
  )
}
