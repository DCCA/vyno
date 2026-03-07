import type { ConsoleSurface, SourceHealthItem, UnifiedSourceRow } from "@/app/types"

const CONSOLE_SURFACES: ConsoleSurface[] = [
  "dashboard",
  "run",
  "onboarding",
  "sources",
  "profile",
  "timeline",
  "history",
]

export function toLines(values: string[] | undefined): string {
  return (values ?? []).join("\n")
}

export function fromLines(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

export function diffObjects(base: Record<string, unknown>, target: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const keys = new Set([...Object.keys(base), ...Object.keys(target)])
  for (const key of keys) {
    const left = base[key]
    const right = target[key]
    if (isRecord(left) && isRecord(right)) {
      const nested = diffObjects(left, right)
      if (Object.keys(nested).length > 0) {
        out[key] = nested
      }
      continue
    }
    if (JSON.stringify(left) !== JSON.stringify(right)) {
      out[key] = right
    }
  }
  return out
}

export function parseProfilePayload(value: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(value)
  if (!isRecord(parsed)) {
    throw new Error("Profile JSON must be an object.")
  }
  return parsed
}

export function formatElapsed(seconds: number | undefined): string {
  const total = Math.max(0, Math.floor(seconds ?? 0))
  const mins = Math.floor(total / 60)
  const secs = total % 60
  if (mins <= 0) return `${secs}s`
  return `${mins}m ${secs}s`
}

export function toInt(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return Math.trunc(value)
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

export function truncateText(value: string, maxChars = 92): string {
  const source = (value ?? "").trim()
  if (source.length <= maxChars) return source
  return `${source.slice(0, Math.max(0, maxChars - 1)).trimEnd()}…`
}

export function statusHoverDetail(row: UnifiedSourceRow): string {
  const details = [
    `Type: ${row.type || "-"}`,
    `Source: ${row.source || "-"}`,
    `Last seen: ${row.last_seen || "-"}`,
    `Last error: ${row.last_error || "-"}`,
    `Hint: ${row.hint || "-"}`,
  ]
  return details.join("\n")
}

export function sourceValuePlaceholderForType(sourceType: string): string {
  const st = (sourceType || "").trim().toLowerCase()
  if (st === "rss") return "https://news.ycombinator.com/rss"
  if (st === "youtube_channel") return "UC_x5XG1OV2P6uZZ5FSM9Ttw"
  if (st === "youtube_query") return "llm evals"
  if (st === "x_author") return "@thdxr or https://x.com/thdxr"
  if (st === "x_theme") return "ai agents"
  if (st === "github_repo") return "openai/openai-cookbook"
  if (st === "github_topic") return "llm-evals"
  if (st === "github_query") return "agentic eval framework"
  if (st === "github_org") return "vercel-labs or https://github.com/vercel-labs"
  return "Enter source value"
}

export function sourceHealthMatches(type: string, source: string, item: SourceHealthItem): boolean {
  const t = (type || "").trim().toLowerCase()
  const s = (source || "").trim().toLowerCase()
  const k = (item.kind || "").trim().toLowerCase()
  const src = (item.source || "").trim().toLowerCase()
  if (!s) return false
  if (t === "rss") return k === "rss" && src === s
  if (t === "youtube_channel") return k === "youtube_channel" && src === s
  if (t === "youtube_query") return k === "youtube_query" && src === s
  if (t === "x_author") return k === "x_author" && src === s
  if (t === "x_theme") return k === "x_theme" && src === s
  if (t.startsWith("github_")) return k === "github" && src.includes(s)
  return k === t && src === s
}

export function surfaceFromLegacyQuery(search: string): ConsoleSurface | null {
  const params = new URLSearchParams(search)
  const value = (params.get("surface") || "").trim()
  return CONSOLE_SURFACES.includes(value as ConsoleSurface) ? (value as ConsoleSurface) : null
}
