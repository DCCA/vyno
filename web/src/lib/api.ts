const API_BASE = (import.meta.env.VITE_API_BASE ?? "").trim().replace(/\/$/, "")
const API_TOKEN = import.meta.env.VITE_WEB_API_TOKEN ?? ""
const API_TOKEN_HEADER = import.meta.env.VITE_WEB_API_TOKEN_HEADER ?? "X-Digest-Api-Token"

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? undefined)
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  if (API_TOKEN) {
    headers.set(API_TOKEN_HEADER, API_TOKEN)
  }

  const target = API_BASE ? `${API_BASE}${path}` : path
  let response: Response
  try {
    response = await fetch(target, {
      ...init,
      headers,
    })
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error)
    throw new Error(`Network error calling ${target}. Check that API is running and reachable. (${reason})`)
  }
  if (!response.ok) {
    const body = await response.text()
    throw new Error(body || `request failed (${response.status})`)
  }
  return (await response.json()) as T
}
