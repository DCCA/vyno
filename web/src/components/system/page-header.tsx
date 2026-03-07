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
  return (
    <Card className="border-border/80 bg-card/95">
      <CardHeader className="gap-3 pb-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <CardTitle className="font-display text-2xl">{title}</CardTitle>
          <CardDescription className="max-w-3xl">{description}</CardDescription>
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
        {actions ? <CardContent className="p-0">{actions}</CardContent> : null}
      </CardHeader>
    </Card>
  )
}
