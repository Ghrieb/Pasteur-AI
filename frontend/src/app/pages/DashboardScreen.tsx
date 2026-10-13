import { useState, useEffect } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { HealthScoreRing } from "../components/HealthScoreRing"
import { CategoryCard } from "../components/CategoryCard"
import { apiClient } from "../../lib/api-client"
import { getCachedSummary, setCachedSummary } from "../../lib/ai-cache"
import type { Lang, Screen } from "../data/types"
import type { ReportJson } from "../../lib/api-types"
import type { PatientData, HistoryEntry } from "../data/mock-data"
import { Activity, Brain, Clock, Printer, Mic, User, Calendar, Sparkles, AlertTriangle, TrendingUp, ChevronLeft, ChevronRight, Droplets, FlaskConical, Heart, Zap, Thermometer, Star, BarChart3 } from "lucide-react"
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, LineChart, Line, ReferenceLine } from "recharts"
import { HealthRadarChart } from "../components/charts/HealthRadarChart"
import { t } from "../data/translations"
import { categoryStatus, statusColor, statusBg } from "../data/utils"
import { CATEGORY_LABELS } from "../data/transforms"
import { IpaLogo } from "../components/IpaLogo"

export function DashboardScreen({ reportRef, lang, onNav, onCategory, report, patientData: p, history, loading, error, fetchReport, initialAiSummary }: { reportRef: string; lang: Lang; onNav: (s: Screen) => void; onCategory: (k: string) => void; report: ReportJson | null; patientData: PatientData; history: HistoryEntry[]; loading: boolean; error: string | null; fetchReport: (ref: string) => Promise<void>; initialAiSummary?: string }) {
  const [activeTab, setActiveTab] = useState<"overview" | "charts">("overview")
  const [aiSummary, setAiSummary] = useState(initialAiSummary || p.aiSummary)

  useEffect(() => {
    if (!report) return
    if (initialAiSummary) {
      setCachedSummary(reportRef, initialAiSummary)
      return
    }
    const cached = getCachedSummary(reportRef)
    if (cached) { setAiSummary(cached); return }
    let cancelled = false
    apiClient.summarizeDashboard({ reportJson: report, language: lang })
      .then(res => { if (!cancelled) { setAiSummary(res.summary); setCachedSummary(reportRef, res.summary) } })
      .catch(() => { /* keep fallback */ })
    return () => { cancelled = true }
  }, [report, lang, initialAiSummary, reportRef])
  const isRtl = lang === "ar"

  const navItems = [
    { id: "insights", icon: Brain, label: t[lang].insights },
    { id: "history", icon: Clock, label: t[lang].history },
    { id: "anomalies", icon: AlertTriangle, label: t[lang].anomalies },
    { id: "print", icon: Printer, label: t[lang].print },
    { id: "voice", icon: Mic, label: t[lang].voice },
  ] as const

  if (error) {
    return (
      <div className="min-h-screen" style={{ background: "var(--background)", fontFamily: "var(--font-family-sans)", direction: isRtl ? "rtl" : "ltr" }}>
        <ParticleField />
        <div className="relative z-10 flex items-center justify-center min-h-screen px-6">
          <GlassCard className="p-8 max-w-md w-full text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
              style={{ background: "var(--danger-subtle)", border: "1px solid var(--danger-border)" }}>
              <AlertTriangle className="w-8 h-8" style={{ color: "var(--danger)" }} />
            </div>
            <h3 style={{ fontSize: "var(--text-xl)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)", marginBottom: "var(--space-2)" }}>
              Erreur de chargement
            </h3>
            <p style={{ color: "var(--foreground-muted)", fontSize: "var(--text-base)", marginBottom: "var(--space-6)" }}>
              {error}
            </p>
            <button onClick={() => reportRef && fetchReport(reportRef)} className="btn-primary w-full">
              Réessayer
            </button>
          </GlassCard>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen" style={{ background: "var(--background)", fontFamily: "var(--font-family-sans)", direction: isRtl ? "rtl" : "ltr" }}>
        <ParticleField />
        <div className="relative z-10 flex items-center justify-center min-h-screen px-6">
          <div className="flex flex-col items-center gap-6 animate-fade-in">
            <div className="w-14 h-14 rounded-full border-3 border-primary border-t-transparent animate-spin" />
            <p style={{ color: "var(--foreground-muted)", fontSize: "var(--text-lg)" }}>Chargement du rapport...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className="min-h-screen"
      style={{ background: "var(--background)", fontFamily: "var(--font-family-sans)", direction: isRtl ? "rtl" : "ltr", overflowY: "auto", overflowX: "visible" }}
    >
      <ParticleField />

      {/* Sticky Header */}
      <header className="sticky top-0 z-50"
        style={{
          background: "rgba(6, 18, 32, 0.85)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div className="max-w-7xl mx-auto px-6 md:px-8">
          <div className="flex items-center justify-between h-16 md:h-18">
            {/* Left: Brand + Title */}
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0"
                style={{ background: "var(--primary-subtle)", border: "1px solid var(--primary-border)", boxShadow: "0 0 20px var(--primary) / 25%" }}>
                <IpaLogo variant="white" size="sm" />
              </div>
              <div className="hidden sm:block">
                <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-extrabold)", color: "var(--foreground)", letterSpacing: "var(--tracking-tight)" }}>PasteurAI</div>
                <div style={{ fontSize: "var(--text-xs)", color: "var(--foreground-muted)", letterSpacing: "var(--tracking-widest)", textTransform: "uppercase" }}>Tableau de Bord Médical</div>
              </div>
            </div>

            {/* Right: Navigation */}
            <nav className="flex items-center gap-2 shrink-0" aria-label="Navigation principale">
              {navItems.map(({ id, icon: Icon, label }) => (
                <button
                  key={id}
                  onClick={() => onNav(id as Screen)}
                  className="btn-icon-nav"
                  aria-label={label}
                  title={label}
                >
                  <Icon className="w-5 h-5" />
                  <span className="hidden md:inline" style={{ fontSize: "var(--text-sm)" }}>{label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-8 py-8 pb-16">
        {/* Patient Header Card */}
        <GlassCard className="mb-8 animate-fade-in">
          <div className="p-6 md:p-8">
            <div className="flex flex-col md:flex-row md:items-start gap-6 md:gap-8">
              <div className="w-20 h-20 md:w-24 md:h-24 rounded-2xl flex items-center justify-center flex-shrink-0"
                style={{ background: "linear-gradient(135deg, var(--primary-subtle), var(--secondary-subtle))", border: "1px solid var(--primary-border)" }}>
                <User className="w-11 h-11 md:w-12 md:h-12" style={{ color: "var(--primary)" }} />
              </div>

              <div className="flex-1 min-w-0">
                <div style={{ fontSize: "var(--text-3xl)", fontWeight: "var(--font-weight-extrabold)", color: "var(--foreground)", letterSpacing: "var(--tracking-tight)", marginBottom: "var(--space-2)" }}>
                  {p.name}
                </div>
                <div className="flex flex-wrap items-center gap-4 md:gap-6" style={{ fontSize: "var(--text-base)", color: "var(--foreground-muted)" }}>
                  <span>{p.age} ans · {p.gender}</span>
                  <span className="px-3 py-1 rounded-full font-mono" style={{ fontSize: "var(--text-sm)", background: "var(--primary-subtle)", color: "var(--primary)", border: "1px solid var(--primary-border)" }}>
                    {p.refNumber}
                  </span>
                  <span className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Rapport du {p.reportDate}
                  </span>
                </div>
              </div>

              <div className="flex-1 md:w-auto">
                <div className="p-4 md:p-6 rounded-2xl"
                  style={{ background: "var(--primary-subtle)", border: "1px solid var(--primary-border)" }}>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                      style={{ background: "var(--primary)", boxShadow: "0 0 16px var(--primary) / 30%" }}>
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div className="min-w-0">
                      <div style={{ fontSize: "var(--text-sm)", color: "var(--primary)", letterSpacing: "var(--tracking-wider)", textTransform: "uppercase", fontWeight: "var(--font-weight-semibold)", marginBottom: "var(--space-2)" }}>
                        Résumé IA
                      </div>
                      <p style={{ fontSize: "var(--text-base)", color: "var(--foreground)", lineHeight: "var(--leading-relaxed)" }}>
                        {aiSummary}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Score + Categories Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Health Score Card */}
          <GlassCard className="lg:col-span-1 animate-slide-up" style={{ animationDelay: "100ms" }}>
            <div className="p-6 md:p-8 flex flex-col items-center justify-center gap-6 text-center">
              <div style={{ fontSize: "var(--text-sm)", color: "var(--foreground-subtle)", letterSpacing: "var(--tracking-wider)", textTransform: "uppercase", fontWeight: "var(--font-weight-semibold)" }}>
                Score Global de Santé
              </div>
              <HealthScoreRing score={p.healthScore} size={160} strokeWidth={10} />
              <div>
                <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: p.healthScore >= 80 ? "var(--success)" : p.healthScore >= 60 ? "var(--warning)" : "var(--danger)" }}>
                  {p.healthScore >= 80 ? "Excellent" : p.healthScore >= 60 ? "Satisfaisant" : "À surveiller"}
                </div>
                <div style={{ fontSize: "var(--text-sm)", color: "var(--foreground-subtle)", marginTop: "var(--space-1)" }}>
                  Basé sur {Object.values(p.biomarkers).flat().length} biomarqueurs
                </div>
              </div>
            </div>
          </GlassCard>

          {/* System Health Dot-Matrix */}
          <div className="lg:col-span-2 animate-slide-up" style={{ animationDelay: "200ms" }}>
            <GlassCard className="p-0 overflow-hidden">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-px p-3 md:p-4">
                {(Object.keys(p.biomarkers) as (keyof typeof p.biomarkers)[]).map((k) => {
                  const markers = p.biomarkers[k]
                  const s = categoryStatus(markers)
                  const color = statusColor(s)
                  const bg = statusBg(s)
                  const abnormal = markers.filter(m => m.status !== "normal").length
                  const score = Math.round(Math.max(0, 100 - (abnormal / markers.length) * 100))
                  const filledDots = Math.round(score / 10)
                  const dotColor = score >= 80 ? "#22C55E" : score >= 50 ? "#F59E0B" : "#EF4444"
                  const icons: Record<string, JSX.Element> = {
                    blood: <Droplets className="w-4 h-4" />,
                    liver: <Activity className="w-4 h-4" />,
                    kidney: <FlaskConical className="w-4 h-4" />,
                    heart: <Heart className="w-4 h-4" />,
                    hormones: <Zap className="w-4 h-4" />,
                    inflammation: <Thermometer className="w-4 h-4" />,
                    vitamins: <Star className="w-4 h-4" />,
                    lipids: <BarChart3 className="w-4 h-4" />,
                  }
                  return (
                    <button key={k} onClick={() => onCategory(k)}
                      className="flex items-center gap-3 px-3 py-4 rounded-xl text-left transition-all duration-150 active:scale-[0.98] hover:bg-white/[0.04] group"
                      style={{ borderLeft: `2px solid ${color}60` }}>
                      <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                        style={{ background: bg, color }}>
                        {icons[k] || <Activity className="w-4 h-4" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>
                            {CATEGORY_LABELS[k] || k}
                          </span>
                          <span style={{ fontSize: 10, color: "var(--foreground-subtle)", fontFamily: "JetBrains Mono" }}>
                            {markers.length}p
                          </span>
                        </div>
                        <div className="flex items-center gap-[3px]">
                          {Array.from({ length: 10 }).map((_, i) => (
                            <div key={i}
                              className="w-[7px] h-[7px] rounded-sm transition-all duration-300"
                              style={{
                                background: i < filledDots ? dotColor : "transparent",
                                border: i < filledDots ? "none" : "1px solid rgba(255,255,255,0.12)",
                                boxShadow: i < filledDots ? `0 0 4px ${dotColor}60` : "none",
                              }}
                            />
                          ))}
                        </div>
                      </div>
                      <div className="flex-shrink-0 text-right min-w-[42px]">
                        <div style={{ fontSize: 14, fontWeight: 700, color: dotColor, fontFamily: "DM Sans" }}>
                          {score}
                        </div>
                        <div style={{ fontSize: 10, color: abnormal > 0 ? color : "#22C55E", marginTop: 1, fontWeight: 500 }}>
                          {abnormal > 0 ? `${abnormal} anom.` : "OK"}
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </GlassCard>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 animate-slide-up" style={{ animationDelay: "300ms" }} role="tablist" aria-label="Vues du tableau de bord">
          {(["overview", "charts"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              role="tab"
              aria-selected={activeTab === tab}
              className={`flex-1 ${activeTab === tab ? "tab-active" : "tab"}`}
              style={{ minHeight: "var(--touch-target-lg)" }}
            >
              {tab === "overview" ? "Vue d'ensemble" : "Graphiques"}
            </button>
          ))}
        </div>

        {/* Tab Panels */}
        {activeTab === "overview" ? (
          <div className="animate-fade-in" role="tabpanel" aria-label="Vue d'ensemble">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {(Object.keys(p.biomarkers) as (keyof typeof p.biomarkers)[]).map((k) => (
                <CategoryCard key={k} catKey={k} markers={p.biomarkers[k]} lang={lang} onClick={() => onCategory(k)} />
              ))}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in" role="tabpanel" aria-label="Graphiques">
            {/* Systemic View */}
            <GlassCard className="p-6 lg:col-span-1">
              <div className="flex items-center justify-between mb-6">
                <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>
                  Vue systémique
                </h3>
                <span className="badge-primary" style={{ fontSize: "var(--text-xs)" }}>
                  Radar Chart
                </span>
              </div>
              <HealthRadarChart tests={report?.tests ?? []} />
            </GlassCard>

            {/* Health Score History */}
            <GlassCard className="p-6 lg:col-span-1">
              <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)", marginBottom: "var(--space-6)" }}>
                Évolution du score de santé
              </h3>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={history.length ? history : p.history}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                    <XAxis dataKey="date" tick={{ fill: "var(--foreground-muted)", fontSize: 12, dy: 8 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: "var(--foreground-muted)", fontSize: 12, dx: -8 }} axisLine={false} tickLine={false} domain={[50, 100]} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--background-elevated)",
                      border: "1px solid var(--primary-border)",
                      borderRadius: 12,
                      color: "var(--foreground)",
                      boxShadow: "var(--shadow-xl)",
                    }}
                    formatter={(value: number) => [`${value}/100`, "Score de santé"]}
                  />
                  <Area type="monotone" dataKey="healthScore" stroke="var(--primary)" fill="url(#scoreGrad)" strokeWidth={2} dot={{ fill: "var(--primary)", r: 5, stroke: "var(--background)", strokeWidth: 2 }} />
                </AreaChart>
              </ResponsiveContainer>
            </GlassCard>

            {/* Cholesterol Trend */}
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>
                  Cholestérol Total
                </h3>
                <span className="badge-warning" style={{ fontSize: "var(--text-xs)" }}>
                  Attention
                </span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={history.length ? history : p.history}>
                    <XAxis dataKey="date" tick={{ fill: "var(--foreground-muted)", fontSize: 12, dy: 8 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: "var(--foreground-muted)", fontSize: 12, dx: -8 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "var(--background-elevated)",
                        border: "1px solid var(--warning-border)",
                        borderRadius: 12,
                        color: "var(--foreground)",
                      }}
                      formatter={(value: number) => [`${value} mg/dL`, "Cholestérol"]}
                  />
                  <ReferenceLine y={200} stroke="var(--success)" strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: "Seuil normal (200)", fill: "var(--success)", fontSize: 11, dy: -8 }} />
                  <Line type="monotone" dataKey="cholesterol" stroke="var(--warning)" strokeWidth={2} dot={{ fill: "var(--warning)", r: 5, stroke: "var(--background)", strokeWidth: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </GlassCard>

            {/* ALT Trend */}
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>
                  ALT (Foie)
                </h3>
                <span className="badge-warning" style={{ fontSize: "var(--text-xs)" }}>
                  Surveillez
                </span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={history.length ? history : p.history}>
                    <XAxis dataKey="date" tick={{ fill: "var(--foreground-muted)", fontSize: 12, dy: 8 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: "var(--foreground-muted)", fontSize: 12, dx: -8 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "var(--background-elevated)",
                        border: "1px solid var(--warning-border)",
                        borderRadius: 12,
                        color: "var(--foreground)",
                      }}
                      formatter={(value: number) => [`${value} U/L`, "ALT"]}
                  />
                  <ReferenceLine y={45} stroke="var(--success)" strokeDasharray="4 4" strokeOpacity={0.5} label={{ value: "Max normal (45)", fill: "var(--success)", fontSize: 11, dy: -8 }} />
                  <Line type="monotone" dataKey="alt" stroke="var(--warning)" strokeWidth={2} dot={{ fill: "var(--warning)", r: 5, stroke: "var(--background)", strokeWidth: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </GlassCard>
          </div>
        )}
      </main>
    </div>
  )
}