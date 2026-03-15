import { cn } from "@/lib/utils"

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("rounded-xl skeleton-shimmer", className)} />
}

export function SkeletonCard({
  rows = 1,
  columns = 4,
  height = "h-20",
}: {
  rows?: number
  columns?: number
  height?: string
}) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }, (_, r) => (
        <div key={r} className={`grid gap-3 md:grid-cols-${columns}`}>
          {Array.from({ length: columns }, (_, c) => (
            <Skeleton key={c} className={height} />
          ))}
        </div>
      ))}
    </div>
  )
}
