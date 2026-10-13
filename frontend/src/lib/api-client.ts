import { notificationCenter } from './notification-center'
import type {
  ReportJson, PatientHistoryResponse, AiInterpretRequest, AiInterpretResponse,
  AiAnalysisRequest, AiAnalysisResponse, AiSummaryRequest, AiSummaryResponse,
  BiomarkerEntry, AdminStatus, AdminAiStatus, AdminPrinterStatus, AdminLogsResponse,
  HealthResponse
} from './api-types'

const API_BASE = import.meta.env.VITE_API_URL || ''
const BACKEND_DIRECT = 'http://localhost:8000'

// Self-diagnostic: log how API calls are made
if (typeof window !== 'undefined') {
  const protocol = window.location.protocol
  if (protocol === 'file:') {
    console.error('[API] ERROR: App opened directly from file:///. API calls will fail. Use "npm run dev" and open http://localhost:5173')
  } else {
    console.log(`[API] Base URL: "${API_BASE}" (origin: ${window.location.origin}, protocol: ${protocol})`)
  }
}

export interface ApiError {
  detail: string
  status: number
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '') + '/api'
  }

  private async request<T>(path: string, options?: RequestInit, timeoutMs = 5000): Promise<T> {
    const urls = [`${this.baseUrl}${path}`, `${BACKEND_DIRECT}/api${path}`]
    let lastErr: unknown
    for (const url of urls) {
      if (typeof window !== 'undefined') console.debug(`[API] fetch: ${url}`)
      try {
        const controller = new AbortController()
        const t = setTimeout(() => controller.abort(), timeoutMs)
        try {
          const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...options?.headers },
            signal: controller.signal,
            ...options,
          })
          if (!res.ok) {
            if (typeof window !== 'undefined') console.debug(`[API] HTTP ${res.status} from ${url}`)
            const body = await res.json().catch(() => {
              console.warn(`[API] Non-JSON response from ${url}: status ${res.status}`)
              return { detail: res.statusText }
            })
            throw { detail: body.detail || res.statusText, status: res.status } as ApiError
          }
          if (typeof window !== 'undefined') console.debug(`[API] 200 OK from ${url}`)
          return (await res.json()) as T
        } finally {
          clearTimeout(t)
        }
      } catch (err) {
        lastErr = err
        const apiErr = err as { detail?: string; status?: number }
        if (apiErr?.detail && apiErr.status !== 0) throw err
        console.warn(`[API] Attempt failed for ${url}, trying fallback...`)
      }
    }
    console.error(`[API] All attempts failed for ${path}:`, lastErr)
    notificationCenter.error('Impossible de contacter le serveur', 'API')
    throw { detail: 'Network error', status: 0 } as ApiError
  }

  health() { return this.request<HealthResponse>('/health') }

  getReport(reportRef: string) { return this.request<ReportJson>(`/reports/${reportRef}`) }

  getPatientHistory(name: string) { return this.request<PatientHistoryResponse>(`/patients/${name}/history`) }

  getBiomarker(code: string) { return this.request<BiomarkerEntry>(`/biomarkers/${code}`) }

  interpret(data: AiInterpretRequest) {
    return this.request<AiInterpretResponse>('/interpret', {
      method: 'POST',
      body: JSON.stringify(data),
    }, 30000)
  }

  analyzeReport(data: AiAnalysisRequest) {
    return this.request<AiAnalysisResponse>('/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    }, 30000)
  }

  summarizeDashboard(data: AiSummaryRequest) {
    return this.request<AiSummaryResponse>('/summarize-dashboard', {
      method: 'POST',
      body: JSON.stringify(data),
    }, 30000)
  }

  adminStatus() { return this.request<AdminStatus>('/admin/status') }
  adminAiStatus() { return this.request<AdminAiStatus>('/admin/ai/status') }
  adminPrinterStatus() { return this.request<AdminPrinterStatus>('/admin/printer/status') }
  adminLogs(type?: string) { return this.request<AdminLogsResponse>(`/admin/logs${type ? `?type=${type}` : ''}`) }
  adminExitKiosk() { return this.request<{ status: string }>('/admin/exit-kiosk', { method: 'POST' }) }
  adminRestart() { return this.request<{ status: string }>('/admin/restart', { method: 'POST' }) }
  adminShutdown() { return this.request<{ status: string }>('/admin/shutdown', { method: 'POST' }) }

  adminPrinterConnect() { return this.request<{ status: string }>('/admin/printer/connect', { method: 'POST' }) }
  adminPrinterTest() { return this.request<{ status: string }>('/admin/printer/test', { method: 'POST' }) }
  adminPrinterPrint(data?: Record<string, unknown>) {
    return this.request<{ status: string }>('/admin/printer/print', { method: 'POST', body: JSON.stringify(data || {}) })
  }
  adminPrintSummary(data?: { report?: { report_ref?: string } }) {
    return this.request<{ status: string }>('/admin/printer/print-summary', { method: 'POST', body: JSON.stringify(data || {}) })
  }

  adminClearCache() { return this.request<{ status: string }>('/admin/maintenance/clear-cache', { method: 'POST' }) }
  adminClearPdfs() { return this.request<{ status: string }>('/admin/maintenance/clear-pdfs', { method: 'POST' }) }
}

export const apiClient = new ApiClient(API_BASE)
