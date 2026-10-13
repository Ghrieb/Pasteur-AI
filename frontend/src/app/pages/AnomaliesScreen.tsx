import { useState } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { t } from "../data/translations"
import type { Lang } from "../data/types"
import type { ReportJson } from "../../lib/api-types"
import { ChevronLeft, AlertTriangle } from "lucide-react"
import { IpaLogo } from "../components/IpaLogo"
import { AbnormalAlertCard } from "../components/charts/AbnormalAlertCard"
import { HealthRadarChart } from "../components/charts/HealthRadarChart"
import { CATEGORY_KEY_MAP } from "../data/transforms"

export function AnomaliesScreen({ lang, onBack, report, onCategory }: { lang: Lang; onBack: () => void; report: ReportJson | null; onCategory: (k: string) => void }) {
  const [activeTab, setActiveTab] = useState<"overview" | "charts">("overview")
  const isRtl = lang === "ar"

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
            <AlertTriangle className="w-6 h-6" style={{ color: "var(--danger)" }} />
            <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>
              {t[lang].anomalies}
            </div>
            <div className="ml-auto opacity-60">
              <IpaLogo variant="white" size="sm" />
            </div>
          </div>
        </div>
      </header>
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-8 py-8 pb-16">
        <div className="flex gap-2 mb-8 animate-fade-in" role="tablist">
          {(["overview", "charts"] as const).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              role="tab"
              aria-selected={activeTab === tab}
              className={`flex-1 ${activeTab === tab ? "tab-active" : "tab"}`}
              style={{ minHeight: "var(--touch-target-lg)" }}>
              {tab === "overview" ? "Vue d'ensemble" : "Graphiques"}
            </button>
          ))}
        </div>
        {activeTab === "overview" ? (
          <div className="animate-fade-in">
            {report?.tests?.some(t => t.abnormal) ? (
              <GlassCard className="p-6">
                <AbnormalAlertCard
                  tests={report.tests}
                  onSelectCategory={(rawKey) => onCategory(CATEGORY_KEY_MAP[rawKey] || rawKey || "liver")}
                />
              </GlassCard>
            ) : (
              <div className="py-16 text-center">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4" style={{ background: "var(--success-subtle)", border: "1px solid var(--success-border)" }}>
                  <span style={{ fontSize: 32, color: "var(--success)" }}>✓</span>
                </div>
                <p className="text-xl font-bold" style={{ color: "var(--foreground)", marginBottom: "var(--space-2)" }}>Aucune anomalie détectée</p>
                <p className="text-base" style={{ color: "var(--foreground-muted)" }}>Tous les biomarqueurs sont dans les normes.</p>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-slide-up" style={{ animationDelay: "100ms" }}>
            <GlassCard className="p-6">
              <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)", marginBottom: "var(--space-4)" }}>Vue systémique des anomalies</div>
              <HealthRadarChart tests={report?.tests ?? []} />
            </GlassCard>
            <GlassCard className="p-6">
              <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)", marginBottom: "var(--space-4)" }}>Répartition par sévérité</div>
              <div className="flex flex-col gap-4">
                {[["Critique", report?.tests?.filter(t => t.abnormal && t.value != null && t.range?.max != null && t.value > t.range.max * 1.5).length || 0, "var(--danger)"],
                  ["Anormal", report?.tests?.filter(t => t.abnormal && t.value != null && t.range?.max != null && t.value > t.range.max && t.value <= t.range.max * 1.5).length || 0, "var(--warning)"],
                  ["Alerte", report?.tests?.filter(t => t.abnormal && !(t.value != null && t.range?.max != null && t.value > t.range.max)).length || 0, "var(--primary)"],
                ].map(([label, count, color]) => (
                  <div key={label} className="flex items-center gap-4">
                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: color }} />
                    <span style={{ fontSize: "var(--text-base)", color: "var(--foreground)", flex: 1 }}>{label}</span>
                    <span style={{ fontSize: "var(--text-2xl)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)", fontFamily: "var(--font-family-mono)" }}>{count}</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        )}
      </main>
    </div>
  )
}
