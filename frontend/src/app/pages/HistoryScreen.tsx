import { useEffect } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { useReport } from "../hooks/use-report"
import { t } from "../data/translations"
import type { Lang } from "../data/types"
import { ChevronLeft, Clock, TrendingUp } from "lucide-react"
import { IpaLogo } from "../components/IpaLogo"
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"

export function HistoryScreen({ reportRef, lang, onBack }: { reportRef: string; lang: Lang; onBack: () => void }) {
  const { patientData: p, history, fetchPatientHistory } = useReport()
  const isRtl = lang === "ar"

  useEffect(() => {
    if (reportRef) fetchPatientHistory(reportRef)
  }, [reportRef, fetchPatientHistory])

  const displayHistory = history.length ? history : p.history
  const first = displayHistory[0]
  const last = displayHistory[displayHistory.length - 1]
  const diff = last && first ? last.healthScore - first.healthScore : 0

  const reports = displayHistory.map((h, i) => ({
    date: h.date,
    ref: i === displayHistory.length - 1 ? p.refNumber : `HIST-${String(i + 1).padStart(4, "0")}`,
    score: h.healthScore,
    flags: 0,
    status: i === displayHistory.length - 1 ? "current" : "past" as const,
  }))

  const TooltipCard = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null
    return (
      <div className="px-4 py-3 rounded-xl" style={{ background: "var(--background)", border: "1px solid var(--primary-border)", boxShadow: "0 8px 32px var(--background-input)" }}>
        <p style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)", marginBottom: "var(--space-1)" }}>{label}</p>
        <p style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--primary)", fontFamily: "var(--font-family-mono)" }}>{payload[0].value}</p>
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
            <Clock className="w-6 h-6" style={{ color: "var(--primary)" }} />
            <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>
              Historique médical · {p.name}
            </div>
            <div className="ml-auto opacity-60">
              <IpaLogo variant="white" size="sm" />
            </div>
          </div>
        </div>
      </header>
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-8 py-8 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8 animate-fade-in">
          <GlassCard className="p-6">
            <div style={{ fontSize: "var(--text-sm)", color: "var(--foreground-subtle)", marginBottom: "var(--space-3)", letterSpacing: "var(--tracking-wider)", textTransform: "uppercase" }}>Évolution du score</div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={displayHistory}>
                <defs>
                  <linearGradient id="hGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: "var(--foreground-muted)", fontSize: 13 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "var(--foreground-muted)", fontSize: 13 }} axisLine={false} tickLine={false} domain={[60, 80]} />
                <Tooltip content={<TooltipCard />} />
                <Area type="monotone" dataKey="healthScore" stroke="var(--primary)" fill="url(#hGrad)" strokeWidth={2} dot={{ fill: "var(--primary)", r: 4 }} />
              </AreaChart>
            </ResponsiveContainer>
          </GlassCard>
          <GlassCard className="p-6 flex flex-col justify-center items-center gap-4">
            <div style={{ fontSize: 56, fontWeight: 800, color: diff >= 0 ? "var(--success)" : "var(--danger)" }}>{diff >= 0 ? "+" : ""}{diff}</div>
            <div style={{ fontSize: "var(--text-base)", color: "var(--foreground-muted)", textAlign: "center" }}>Points depuis le premier rapport</div>
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl" style={{ background: diff >= 0 ? "var(--success-subtle)" : "var(--danger-subtle)", border: `1px solid ${diff >= 0 ? "var(--success-border)" : "var(--danger-border)"}` }}>
              <TrendingUp className="w-4 h-4" style={{ color: diff >= 0 ? "var(--success)" : "var(--danger)" }} />
              <span style={{ fontSize: "var(--text-sm)", color: diff >= 0 ? "var(--success)" : "var(--danger)", fontWeight: "var(--font-weight-semibold)" }}>
                {diff >= 0 ? "Amélioration" : "Détérioration"}
              </span>
            </div>
          </GlassCard>
        </div>
        <div className="relative animate-slide-up" style={{ animationDelay: "100ms" }}>
          <div className="absolute left-6 top-0 bottom-0 w-px" style={{ background: "var(--primary-border)" }} />
          <div className="space-y-6">
            {reports.map((r) => (
              <div key={r.ref} className="flex gap-8 pl-16 relative">
                <div className="absolute left-3.5 w-5 h-5 rounded-full flex items-center justify-center"
                  style={{ background: r.status === "current" ? "var(--primary)" : "var(--background)", border: "2px solid var(--primary)", top: 24 }}>
                  {r.status === "current" && <div className="w-2 h-2 rounded-full" style={{ background: "var(--foreground)" }} />}
                </div>
                <GlassCard className="flex-1 p-4 md:p-6 flex items-center justify-between"
                  style={{ borderColor: r.status === "current" ? "var(--primary-border)" : "var(--border)" }}>
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <span style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>{r.date}</span>
                      {r.status === "current" && (
                        <span className="px-2 py-0.5 rounded-full font-semibold" style={{ fontSize: "var(--text-sm)", background: "var(--primary-subtle)", color: "var(--primary)" }}>Actuel</span>
                      )}
                    </div>
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)", fontFamily: "var(--font-family-mono)" }}>{r.ref}</span>
                  </div>
                  <div className="text-center">
                    <div style={{ fontSize: 40, fontWeight: 800, color: r.score >= 72 ? "var(--success)" : "var(--warning)" }}>{r.score}</div>
                    <div style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)" }}>/ 100</div>
                  </div>
                </GlassCard>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
