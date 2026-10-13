const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface AiInterpretation {
  summary: string
  criticalFindings: string[]
  recommendations: string[]
  confidence: 'high' | 'medium' | 'low'
}

class AiEngine {
  private baseUrl: string

  constructor() {
    this.baseUrl = API_BASE
  }

  async interpret(reportRef: string, language = 'fr'): Promise<AiInterpretation> {
    const res = await fetch(`${this.baseUrl}/reports/${reportRef}/interpret?language=${language}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(body.detail || 'Interpretation failed')
    }
    return res.json()
  }

  async analyze(reportRef: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/reports/${reportRef}/analysis`, {
      headers: { 'Content-Type': 'application/json' },
    })
    if (!res.ok) throw new Error('Analysis failed')
    return res.json()
  }
}

export const aiEngine = new AiEngine()
