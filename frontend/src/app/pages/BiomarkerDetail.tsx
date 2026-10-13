import { useState } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { BiomarkerGauge } from "../components/BiomarkerGauge"
import { statusColor, statusBg, statusLabel } from "../data/utils"
import type { Lang } from "../data/types"
import type { ReportJson } from "../../lib/api-types"
import type { PatientData, BiomarkerEntry } from "../data/mock-data"
import { ChevronLeft, Brain, Info } from "lucide-react"
import { IpaLogo } from "../components/IpaLogo"
import { CategoryBarChart } from "../components/charts/CategoryBarChart"
import { CATEGORY_KEY_MAP, CATEGORY_LABELS } from "../data/transforms"
import { t } from "../data/translations"

export function BiomarkerDetail({ catKey, lang, onBack, report, patientData: p }: { catKey: string; lang: Lang; onBack: () => void; report: ReportJson | null; patientData: PatientData }) {
  const markers = (p.biomarkers[catKey as keyof typeof p.biomarkers] ?? []) as BiomarkerEntry[]
  const [selected, setSelected] = useState(0)
  const isRtl = lang === "ar"

  const m = markers[selected]

  const aiInsights: Record<string, { text: string; rec: string }> = {
    elevated: { text: "Cette valeur est légèrement au-dessus de la normale. Cela peut indiquer une surcharge ou une inflammation de l'organe concerné.", rec: "Consultez votre médecin pour un suivi adapté et évitez les facteurs aggravants." },
    low: { text: "Cette valeur est en dessous du seuil recommandé. Une supplémentation ou une adaptation alimentaire peut être nécessaire.", rec: "Discutez d'une supplémentation avec votre médecin et réévaluez dans 4 à 6 semaines." },
    normal: { text: "Cette valeur se situe dans les normes de référence internationales. Aucune action immédiate n'est requise.", rec: "Maintenez vos habitudes actuelles et continuez les contrôles périodiques." },
    critical: { text: "Valeur critique nécessitant une attention médicale immédiate. Ne tardez pas à consulter.", rec: "Consultez un médecin en urgence." },
  }

  const matchingGroups = Object.entries(CATEGORY_KEY_MAP)
    .filter(([, v]) => v === catKey)
    .map(([k]) => k)

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
            <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>
              Détail des biomarqueurs
            </div>
            <div className="ml-auto opacity-60">
              <IpaLogo variant="white" size="sm" />
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-8 py-8 pb-16">
        {!m ? (
          <div className="flex flex-col items-center justify-center py-24 animate-fade-in">
            <ParticleField />
            <p style={{ color: "var(--foreground-muted)", fontSize: "var(--text-lg)" }}>Aucun biomarqueur dans cette catégorie.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Sidebar — marker list */}
            <div className="flex flex-col gap-3 animate-fade-in">
              {markers.map((mk, i) => (
                <button key={mk.name} onClick={() => setSelected(i)}
                  className="flex items-center gap-3 p-4 rounded-xl text-left transition-all duration-300"
                  style={{
                    background: selected === i ? "var(--primary-subtle)" : "var(--background-input)",
                    border: selected === i ? "1px solid var(--primary-border)" : "1px solid var(--border)",
                  }}>
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: statusColor(mk.status) }} />
                  <div className="flex-1 min-w-0">
                    <div style={{ fontSize: "var(--text-base)", fontWeight: "var(--font-weight-semibold)", color: selected === i ? "var(--foreground)" : "var(--foreground-muted)" }}>{mk.name}</div>
                    <div style={{ fontSize: "var(--text-base)", color: statusColor(mk.status), fontFamily: "var(--font-family-mono)" }}>{mk.value} {mk.unit}</div>
                  </div>
                </button>
              ))}
            </div>

            {/* Main content */}
            <div className="lg:col-span-2 flex flex-col gap-5 animate-slide-up" style={{ animationDelay: "100ms" }}>
              <GlassCard className="p-6 md:p-8">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
                  <div>
                    <div style={{ fontSize: "var(--text-3xl)", fontWeight: "var(--font-weight-extrabold)", color: "var(--foreground)", letterSpacing: "var(--tracking-tight)" }}>{m.name}</div>
                    <div style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)", marginTop: "var(--space-1)" }}>Biomarqueur · {CATEGORY_LABELS[catKey] || catKey}</div>
                  </div>
                  <div className="text-right">
                    <div style={{ fontSize: 52, fontWeight: 800, color: statusColor(m.status), letterSpacing: "-0.02em" }}>{m.value}</div>
                    <div style={{ fontSize: "var(--text-base)", color: "var(--foreground-muted)", fontFamily: "var(--font-family-mono)" }}>{m.unit}</div>
                  </div>
                </div>
                <div className="mb-4">
                  <div className="flex justify-between mb-2">
                    <span style={{ fontSize: "var(--text-base)", color: "var(--foreground-muted)" }}>Plage de référence: {m.min} – {m.max} {m.unit}</span>
                    <span className="px-3 py-0.5 rounded-full font-semibold" style={{ fontSize: "var(--text-sm)", background: statusBg(m.status), color: statusColor(m.status) }}>
                      {statusLabel[lang][m.status]}
                    </span>
                  </div>
                  <BiomarkerGauge value={m.value} min={m.min} max={m.max} status={m.status} />
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)", marginBottom: "var(--space-4)" }}>Vue d'ensemble — {CATEGORY_LABELS[catKey] || catKey}</div>
                <CategoryBarChart category={catKey} tests={report?.tests?.filter(t => matchingGroups.includes(t.dashboard_group) || t.category === catKey) ?? []} />
              </GlassCard>

              <GlassCard className="p-6" style={{ border: "1px solid var(--primary-border)" }}>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "var(--primary-subtle)" }}>
                    <Brain className="w-5 h-5" style={{ color: "var(--primary)" }} />
                  </div>
                  <div>
                    <div style={{ fontSize: "var(--text-base)", fontWeight: "var(--font-weight-bold)", color: "var(--foreground)" }}>Interprétation IA</div>
                    <div style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)" }}>Confiance : 94%</div>
                  </div>
                  <div className="ml-auto px-3 py-1 rounded-full" style={{ background: "var(--success-subtle)", border: "1px solid var(--success-border)" }}>
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--success)", fontWeight: "var(--font-weight-semibold)" }}>94% confiance</span>
                  </div>
                </div>
                <p style={{ fontSize: "var(--text-base)", color: "var(--foreground)", lineHeight: "var(--leading-relaxed)", marginBottom: "var(--space-3)" }}>
                  {m && aiInsights[m.status]?.text || aiInsights.normal.text}
                </p>
                <div className="p-3 rounded-xl flex items-start gap-2" style={{ background: "var(--secondary-subtle)", border: "1px solid var(--secondary-border)" }}>
                  <Info className="w-4 h-4" style={{ color: "var(--secondary)", flexShrink: 0, marginTop: 2 }} />
                  <p style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)", lineHeight: "var(--leading-relaxed)" }}>
                    {m && aiInsights[m.status]?.rec || aiInsights.normal.rec}
                  </p>
                </div>
              </GlassCard>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
