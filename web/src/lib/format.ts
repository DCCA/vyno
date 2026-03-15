const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" })

const UNITS: Array<[Intl.RelativeTimeFormatUnit, number]> = [
  ["year", 365 * 24 * 60 * 60 * 1000],
  ["month", 30 * 24 * 60 * 60 * 1000],
  ["week", 7 * 24 * 60 * 60 * 1000],
  ["day", 24 * 60 * 60 * 1000],
  ["hour", 60 * 60 * 1000],
  ["minute", 60 * 1000],
]

export function formatTimestamp(
  iso: string | null | undefined,
  style: "relative" | "short" | "full" = "short",
): string {
  if (!iso) return "n/a"
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso

  if (style === "full") {
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  }

  if (style === "short") {
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  // relative
  const diff = date.getTime() - Date.now()
  for (const [unit, ms] of UNITS) {
    if (Math.abs(diff) >= ms) {
      return rtf.format(Math.round(diff / ms), unit)
    }
  }
  return rtf.format(Math.round(diff / 1000), "second")
}

export function formatStatus(value: string | null | undefined): string {
  if (!value) return "n/a"
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase().replace(/_/g, " ")
}
