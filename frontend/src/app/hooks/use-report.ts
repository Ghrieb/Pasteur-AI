import { useState, useEffect, useCallback } from "react"
import { apiClient } from "../../lib/api-client"
import { notificationCenter } from "../../lib/notification-center"
import { reportToPatientData, historyToTimeline } from "../data/transforms"
import type { ReportJson } from "../../lib/api-types"
import type { PatientData, HistoryEntry } from "../data/mock-data"
import { patientData as fallbackData } from "../data/mock-data"

interface UseReportResult {
  report: ReportJson | null
  patientData: PatientData
  history: HistoryEntry[]
  loading: boolean
  error: string | null
  fetchReport: (ref: string) => Promise<void>
  fetchPatientHistory: (name: string) => Promise<void>
}

export function useReport(): UseReportResult {
  const [report, setReport] = useState<ReportJson | null>(null)
  const [patientData, setPatientData] = useState<PatientData>(fallbackData)
  const [history, setHistory] = useState<HistoryEntry[]>(fallbackData.history)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchReport = useCallback(async (ref: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.getReport(ref)
      setReport(data)
      try {
        const pd = reportToPatientData(data)
        setPatientData(pd)
      } catch (transformErr) {
        console.error('[useReport] reportToPatientData failed:', transformErr)
        setPatientData(fallbackData)
        setError('Erreur de transformation des données')
        return
      }
    } catch (err) {
      const apiErr = err as { detail?: string; status?: number }
      console.error('[useReport] API fetch failed:', apiErr)
      const msg = apiErr?.detail || "Erreur lors du chargement du rapport"
      setError(msg)
      setPatientData(fallbackData)
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchPatientHistory = useCallback(async (name: string) => {
    try {
      const data = await apiClient.getPatientHistory(name)
      if (data.reports?.length) {
        setHistory(historyToTimeline(data.reports))
      }
    } catch {
      /* history is optional — keep fallback */
    }
  }, [])

  return { report, patientData, history, loading, error, fetchReport, fetchPatientHistory }
}
