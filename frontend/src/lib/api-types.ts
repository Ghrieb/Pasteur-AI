export interface ReportPatient {
  name: string
  age: number | null
  sex: string
}

export interface ReportDates {
  demande: string
  edition: string
}

export interface TestRange {
  comparator: string
  min: number | null
  max: number | null
}

export interface TestAnteriority {
  value: number | null
  date: string | null
}

export interface ReportTest {
  test_name: string
  value: number | null
  value_display: string
  unit: string
  abnormal: boolean
  section: string
  sub_section: string
  methodology: string
  range: TestRange
  secondary_range: TestRange
  anteriority: TestAnteriority | null
  test_date: string
  code: string
  biomarker: string
  normalization_confidence: number
  category: string
  dashboard_group: string
}

export interface Interpretation {
  severity: string
  unit: string
  min: number | null
  max: number | null
  comparator: string
  value: number | null
  raw: string | null
}

export interface ReportMeta {
  pdf_source: string
  parsed_at: string
}

export interface ReportJson {
  report_ref: string
  demande_id: string
  patient: ReportPatient
  dates: ReportDates
  tests: ReportTest[]
  interpretations: Interpretation[]
  meta: ReportMeta
}

export interface PatientHistoryEntry {
  id: number
  report_ref: string
  date_edition: string
  raw_json: ReportJson
}

export interface PatientHistoryResponse {
  reports: PatientHistoryEntry[]
}

export interface AiInterpretResponse {
  answer: string
  provider: string
  model: string
}

export interface AiInterpretRequest {
  reportJson: ReportJson
  query?: string
  language?: string
  provider?: string
  model?: string
}

export interface AnalysisFinding {
  title?: string
  test: string
  value: string
  range: string
  severity: string
  explanation: string
  recommendation: string
  confidence: number
}

export interface AiAnalysisRequest {
  reportJson: ReportJson
  language?: string
}

export interface AiAnalysisResponse {
  summary: string
  findings: AnalysisFinding[]
  recommendations: string[]
  confidence: string
}

export interface AiSummaryRequest {
  reportJson: ReportJson
  language?: string
}

export interface AiSummaryResponse {
  summary: string
}

export interface BiomarkerEntry {
  code: string
  name_fr: string
  name_en: string
  unit: string
  category: string
  system: string
  dashboard_group: string
  description: string
}

export interface AdminStatus {
  backend: string
  version: string
  uptime: string
}

export interface AdminAiStatus {
  connected: boolean
}

export interface AdminPrinterStatus {
  connected: boolean
  paper: string
  model: string
}

export interface AdminLogsResponse {
  logs: string[]
}

export interface HealthResponse {
  status: string
  timestamp: string
}
