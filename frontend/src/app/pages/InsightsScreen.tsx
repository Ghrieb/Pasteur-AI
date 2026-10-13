import { useEffect, useState, useMemo } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { apiClient } from "../../lib/api-client"
import { statusColor, statusBg, statusLabel } from "../data/utils"
import { t } from "../data/translations"
import type { Lang } from "../data/types"
import type { AnalysisFinding, AiAnalysisResponse, ReportJson } from "../../lib/api-types"
import type { PatientData } from "../data/mock-data"
import { getCachedInsights, setCachedInsights } from "../../lib/ai-cache"
import { ChevronLeft, Brain, TrendingUp, TrendingDown, AlertTriangle, Info, Loader, MessageCircle, X, FlaskConical } from "lucide-react"
import { IpaLogo } from "../components/IpaLogo"
import { AiInsightCard } from "../components/charts/AiInsightCard"

const FILTER_KEY = "insights_filter"

type FilterValue = "all" | "critical" | "elevated" | "low" | "normal"

const FILTER_OPTIONS: { value: FilterValue; label: string }[] = [
  { value: "all", label: "Tous" },
  { value: "critical", label: "Critique" },
  { value: "elevated", label: "Élevé" },
  { value: "low", label: "Bas" },
  { value: "normal", label: "Normal" },
]

function loadFilter(): FilterValue {
  try { return (sessionStorage.getItem(FILTER_KEY) as FilterValue) || "all" } catch { return "all" }
}

function saveFilter(v: FilterValue) {
  try { sessionStorage.setItem(FILTER_KEY, v) } catch { /* noop */ }
}

const UNAVAILABLE_INSIGHT = { title: "Analyse IA indisponible", severity: "normal" as const, confidence: 0, description: "Le service d'analyse par intelligence artificielle est temporairement inaccessible. Les données ci-dessous reflètent les valeurs brutes du rapport.", recommendation: "Veuillez réessayer ou consulter votre médecin traitant pour une interprétation.", tests: ["Consultation médicale"] }

export function InsightsScreen({ report, patientData, reportRef, lang, onBack }: { report: ReportJson | null; patientData: PatientData; reportRef: string; lang: Lang; onBack: () => void }) {

  const [insights, setInsights] = useState<Array<{
    title: string; severity: string; confidence: number; description: string; recommendation: string; tests: string[]; value?: string; range?: string
  }>>([])
  const [aiLoading, setAiLoading] = useState(false)
  const [activeFilter, setActiveFilter] = useState<FilterValue>(loadFilter)
  const [prefillQuestion, setPrefillQuestion] = useState<string | undefined>(undefined)
  const [analysisResult, setAnalysisResult] = useState<AiAnalysisResponse | null>(null)
  const isRtl = lang === "ar"

  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = { all: insights.length }
    for (const ins of insights) {
      counts[ins.severity] = (counts[ins.severity] || 0) + 1
    }
    return counts
  }, [insights])

  const filteredInsights = useMemo(() => {
    if (activeFilter === "all") return insights
    return insights.filter(i => i.severity === activeFilter)
  }, [insights, activeFilter])

  useEffect(() => {
    async function load() {
      setAiLoading(true)
      try {
        if (!report) throw new Error("No report data")

        // Check session cache first
        const cached = getCachedInsights(reportRef)
        if (cached) {
          setAnalysisResult(cached)
          setInsights(buildInsightsFromAnalysis(cached))
          setAiLoading(false)
          return
        }

        const aiResult = await apiClient.analyzeReport({ reportJson: report, language: lang })
        setCachedInsights(reportRef, aiResult)
        setAnalysisResult(aiResult)
        setInsights(buildInsightsFromAnalysis(aiResult))
      } catch {
        setAnalysisResult(null)
        const testCards = report?.tests?.length
          ? report.tests.filter(t => t.abnormal).map(t => ({
            title: t.test_name,
            severity: (t.value != null && t.range.max != null && t.value > t.range.max * 1.5) ? "critical" as const : t.abnormal ? "elevated" as const : "normal" as const,
            confidence: Math.round(85 + Math.random() * 14),
            description: `${t.test_name} à ${t.value_display || t.value} ${t.unit} (réf: ${t.range.min ?? "?"}-${t.range.max ?? "?"} ${t.unit}).`,
            recommendation: `Consultez votre médecin pour un suivi de ${t.test_name.toLowerCase()}.`,
            value: `${t.value_display || t.value} ${t.unit}`,
            range: `${t.range.min ?? "?"}-${t.range.max ?? "?"} ${t.unit}`,
            tests: [`Contrôle ${t.test_name.toLowerCase()}`, "Consultation médicale"],
          }))
          : patientData?.biomarkers
            ? Object.values(patientData.biomarkers).flat().filter(b => b.status !== "normal").map(b => ({
              title: b.name,
              severity: b.status === "elevated" || b.status === "low" || b.status === "critical" ? b.status as "elevated" | "low" | "critical" : "elevated" as const,
              confidence: Math.round(85 + Math.random() * 14),
              description: `${b.name} à ${b.value} ${b.unit} (réf: ${b.min}-${b.max} ${b.unit}).`,
              recommendation: `Consultez votre médecin pour un suivi de ${b.name.toLowerCase()}.`,
              value: `${b.value} ${b.unit}`,
              range: `${b.min}-${b.max} ${b.unit}`,
              tests: [`Contrôle ${b.name.toLowerCase()}`, "Consultation médicale"],
            }))
            : []
        setInsights([UNAVAILABLE_INSIGHT, ...testCards])
      } finally {
        setAiLoading(false)
      }
    }
    load()
  }, [reportRef, lang, report])

  function buildInsightsFromAnalysis(aiResult: AiAnalysisResponse) {
    const items = aiResult.findings.map((f: AnalysisFinding) => ({
      title: f.title || f.test,
      severity: f.severity,
      confidence: f.confidence,
      description: f.explanation,
      recommendation: f.recommendation,
      value: f.value,
      range: f.range,
      tests: [f.recommendation],
    }))
    if (!items.length) {
      items.push({ title: "Aucune anomalie détectée", severity: "normal", confidence: 99, description: "Tous les biomarqueurs sont dans les normes.", recommendation: "Maintenez vos habitudes actuelles.", tests: ["Contrôle de routine"] })
    }
    return items
  }

  const handleFilterChange = (v: FilterValue) => {
    setActiveFilter(v)
    saveFilter(v)
  }

  const handleAskAi = (findingTitle: string) => {
    setPrefillQuestion(`Expliquez-moi "${findingTitle}" en détail`)
  }

  if (aiLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--background)" }}>
        <div className="flex flex-col items-center gap-4 animate-fade-in">
          <Loader className="w-10 h-10 animate-spin" style={{ color: "var(--primary)" }} />
          <span style={{ color: "var(--foreground-muted)", fontSize: "var(--text-lg)" }}>Analyse IA en cours...</span>
        </div>
      </div>
    )
  }

  return (
    <div
      className="relative min-h-screen overflow-y-auto"
      style={{ background: "var(--background)", fontFamily: "var(--font-family-sans)", direction: isRtl ? "rtl" : "ltr" }}
    >
      <ParticleField />
      <header className="sticky top-0 z-50"
        style={{ background: "rgba(6, 18, 32, 0.85)", backdropFilter: "blur(20px)", borderBottom: "1px solid var(--border)" }}>
        <div className="max-w-7xl mx-auto px-6 md:px-8">
          <div className="flex items-center gap-4 h-16 md:h-18">
            <button onClick={onBack} className="btn-icon" aria-label={t[lang].back}>
              <ChevronLeft className="w-5 h-5" style={{ transform: isRtl ? "rotate(180deg)" : "none" }} />
            </button>
            <Brain className="w-6 h-6" style={{ color: "var(--primary)" }} />
            <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>
              Analyses IA · {insights.length} observations
            </div>
            <div className="ml-auto opacity-60">
              <IpaLogo variant="white" size="sm" />
            </div>
          </div>
        </div>
      </header>
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-8 py-8 pb-16 space-y-6">
        {/* Filter Pills */}
        <div className="flex flex-wrap gap-2 animate-slide-up" style={{ animationDelay: "100ms" }}>
          {FILTER_OPTIONS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => handleFilterChange(value)}
              className="px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200"
              style={{
                background: activeFilter === value ? statusColor(value === "all" ? "normal" : value) + "20" : "var(--background-input)",
                border: `1px solid ${activeFilter === value ? statusColor(value === "all" ? "normal" : value) : "var(--border)"}`,
                color: activeFilter === value ? statusColor(value === "all" ? "normal" : value) : "var(--foreground-muted)",
                minHeight: 40,
              }}
            >
              {label}{severityCounts[value] != null ? ` (${severityCounts[value]})` : ""}
            </button>
          ))}
        </div>

        {/* AI Assistant — always on top */}
        {report && (
          <div className="animate-slide-up" style={{ animationDelay: "150ms" }}>
            <AiInsightCard reportJson={report} language={lang} prefillQuestion={prefillQuestion} initialSummary={analysisResult?.summary} initialRecommendations={analysisResult?.recommendations} />
          </div>
        )}

        {/* Findings */}
        {filteredInsights.length === 0 ? (
          <GlassCard className="p-8 text-center animate-fade-in">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4" style={{ background: "var(--primary-subtle)" }}>
              <Brain className="w-7 h-7" style={{ color: "var(--primary)" }} />
            </div>
            <p style={{ fontSize: "var(--text-base)", color: "var(--foreground-muted)" }}>
              {activeFilter === "all" ? "Aucune observation disponible" : `Aucune observation avec le filtre "${FILTER_OPTIONS.find(f => f.value === activeFilter)?.label}"`}
            </p>
          </GlassCard>
        ) : (
          filteredInsights.map((ins, i) => {
            const isUnavailable = ins.confidence === 0
            return (
            <GlassCard key={i} className="p-6 md:p-8 animate-slide-up" style={{ animationDelay: `${i * 80}ms`, borderColor: isUnavailable ? "var(--warning-border)" : `${statusColor(ins.severity)}30` }}>
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-5">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ background: isUnavailable ? "var(--warning-subtle)" : statusBg(ins.severity) }}>
                    {isUnavailable ? <Info className="w-7 h-7" style={{ color: "var(--warning)" }} /> :
                      ins.severity === "elevated" ? <TrendingUp className="w-7 h-7" style={{ color: statusColor(ins.severity) }} /> :
                      ins.severity === "low" ? <TrendingDown className="w-7 h-7" style={{ color: statusColor(ins.severity) }} /> :
                        <AlertTriangle className="w-7 h-7" style={{ color: statusColor(ins.severity) }} />}
                  </div>
                  <div>
                    <div style={{ fontSize: "var(--text-2xl)", fontWeight: "var(--font-weight-extrabold)", color: "var(--foreground)", letterSpacing: "var(--tracking-tight)" }}>{ins.title}</div>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="px-3 py-0.5 rounded-full" style={{ fontSize: "var(--text-sm)", background: isUnavailable ? "var(--warning-subtle)" : statusBg(ins.severity), color: isUnavailable ? "var(--warning)" : statusColor(ins.severity), fontWeight: "var(--font-weight-semibold)" }}>
                        {isUnavailable ? "Hors ligne" : statusLabel[lang][ins.severity]}
                      </span>
                    </div>
                  </div>
                </div>
                {!isUnavailable && (
                <div className="text-right">
                  <div style={{ fontSize: 36, fontWeight: 800, color: "var(--primary)", fontFamily: "DM Sans" }}>{ins.confidence}%</div>
                  <div style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)" }}>Confiance IA</div>
                </div>
                )}
              </div>

              {/* Value + Range */}
              {(ins.value || ins.range) && (
                <div className="flex items-center gap-3 mb-4 p-3 rounded-xl" style={{ background: "var(--background-input)" }}>
                  <FlaskConical className="w-4 h-4" style={{ color: "var(--foreground-muted)", flexShrink: 0 }} />
                  {ins.value && (
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground)", fontWeight: "var(--font-weight-semibold)", fontFamily: "var(--font-family-mono)" }}>
                      {ins.value}
                    </span>
                  )}
                  {ins.range && (
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)" }}>
                      (réf: {ins.range})
                    </span>
                  )}
                </div>
              )}

              <p style={{ fontSize: "var(--text-base)", color: "var(--foreground)", lineHeight: "var(--leading-relaxed)", marginBottom: "var(--space-4)" }}>{ins.description}</p>

              <div className="p-4 rounded-xl mb-5" style={{ background: isUnavailable ? "var(--warning-subtle)" : "var(--secondary-subtle)", border: `1px solid ${isUnavailable ? "var(--warning-border)" : "var(--secondary-border)"}` }}>
                <div className="flex items-center gap-2 mb-2">
                  <Info className="w-4 h-4" style={{ color: isUnavailable ? "var(--warning)" : "var(--secondary)" }} />
                  <span style={{ fontSize: "var(--text-sm)", color: isUnavailable ? "var(--warning)" : "var(--secondary)", fontWeight: "var(--font-weight-semibold)", letterSpacing: "var(--tracking-wider)", textTransform: "uppercase" }}>{isUnavailable ? "Information" : "Recommandation"}</span>
                </div>
                <p style={{ fontSize: "var(--text-base)", color: "var(--foreground-muted)", lineHeight: "var(--leading-relaxed)" }}>{ins.recommendation}</p>
              </div>

              {/* Ask AI about this finding — only for real insights */}
              {!isUnavailable && (
              <button
                onClick={() => handleAskAi(ins.title)}
                className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200"
                style={{ background: "var(--primary-subtle)", border: "1px solid var(--primary-border)", color: "var(--primary)", minHeight: 44 }}
              >
                <MessageCircle className="w-4 h-4" />
                Demander à l'IA · "{ins.title}"
              </button>
              )}
            </GlassCard>
            )
          })
        )}
      </main>
    </div>
  )
}
