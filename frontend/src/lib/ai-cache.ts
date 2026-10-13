import type { AiAnalysisResponse } from "./api-types"

const PREFIX = "ai_"

export function getCachedSummary(ref: string): string | null {
  try { return sessionStorage.getItem(`${PREFIX}summary_${ref}`) } catch { return null }
}
export function setCachedSummary(ref: string, summary: string) {
  try { sessionStorage.setItem(`${PREFIX}summary_${ref}`, summary) } catch {}
}
export function getCachedInsights(ref: string): AiAnalysisResponse | null {
  try {
    const raw = sessionStorage.getItem(`${PREFIX}insights_${ref}`)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}
export function setCachedInsights(ref: string, insights: AiAnalysisResponse) {
  try { sessionStorage.setItem(`${PREFIX}insights_${ref}`, JSON.stringify(insights)) } catch {}
}
export function clearCache(ref: string) {
  try {
    sessionStorage.removeItem(`${PREFIX}summary_${ref}`)
    sessionStorage.removeItem(`${PREFIX}insights_${ref}`)
  } catch {}
}
