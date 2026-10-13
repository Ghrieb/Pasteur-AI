import { useState, useEffect, useRef } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { t } from "../data/translations"
import type { Lang } from "../data/types"
import type { ReportJson } from "../../lib/api-types"
import { Brain, Check, AlertCircle, Loader } from "lucide-react"
import { IpaLogo } from "../components/IpaLogo"

const API_BASE = import.meta.env.VITE_API_URL || ""

const STEPS = [
  { label: "QR détecté", icon: Check, ipa: false },
  { label: "Téléchargement du rapport", sublabel: "Institut Pasteur d'Algérie", icon: Loader, ipa: false },
  { label: "Extraction des biomarqueurs", sublabel: "", icon: Loader, ipa: false },
  { label: "Interprétation IA", sublabel: "Modèle PasteurAI v3.1", icon: Brain, ipa: true },
  { label: "Préparation du tableau de bord", sublabel: "", icon: Loader, ipa: false },
]

export function ProcessingScreen({ onDone, lang, reportRef, qrUrl }: {
  onDone: (summary?: string) => void
  lang: Lang
  reportRef: string
  qrUrl: string
}) {
  const [currentStep, setCurrentStep] = useState(0)
  const [processingError, setProcessingError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [aiSummary, setAiSummary] = useState("")
  const mountedRef = useRef(true)
  const isRtl = lang === "ar"

  const totalSteps = STEPS.length
  const progress = (currentStep / totalSteps) * 100

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  useEffect(() => {
    if (!reportRef) return
    setProcessingError(false)
    setCurrentStep(0)
    setAiSummary("")

    let reportJson: ReportJson | null = null

    async function run() {
      // Step 0 → 1: Start download
      if (!mountedRef.current) return
      setCurrentStep(1)

      // Step 1: POST /api/reports/process (download + parse PDF)
      const processRes = await fetch(`${API_BASE}/api/reports/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: qrUrl, report_ref: reportRef }),
      })
      if (!processRes.ok) throw new Error("Processing failed")
      if (!mountedRef.current) return
      reportJson = await processRes.json() as ReportJson

      // Step 1 → 2: Extraction complete
      setCurrentStep(2)

      // Step 2 → 3: Start AI interpretation
      await new Promise(r => setTimeout(r, 300))
      if (!mountedRef.current) return
      setCurrentStep(3)

      // Step 3: Call AI summary
      const summaryRes = await fetch(`${API_BASE}/api/summarize-dashboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reportJson, language: lang }),
      })
      if (!summaryRes.ok) throw new Error("AI summary failed")
      if (!mountedRef.current) return
      const summaryData = await summaryRes.json()
      const summary = summaryData.summary || ""

      setAiSummary(summary)

      // Step 3 → 4: Complete
      setCurrentStep(4)

      // Brief delay then navigate
      await new Promise(r => setTimeout(r, 500))
      if (!mountedRef.current) return
      onDone(summary)
    }

    run().catch(() => {
      if (mountedRef.current) {
        setProcessingError(true)
        setCurrentStep(totalSteps)
      }
    })
  }, [qrUrl, reportRef, retryCount])

  return (
    <div
      className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden"
      style={{
        background: "var(--background)",
        fontFamily: "var(--font-family-sans)",
        direction: isRtl ? "rtl" : "ltr",
      }}
    >
      <style>{`
        @keyframes breathe {
          0%, 100% { box-shadow: 0 0 40px var(--primary), 0 0 80px var(--primary) / 20%; }
          50% { box-shadow: 0 0 60px var(--primary), 0 0 100px var(--primary) / 30%; }
        }
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @keyframes scaleIn {
          0% { transform: scale(0) rotate(-90deg); opacity: 0; }
          60% { transform: scale(1.2) rotate(5deg); }
          100% { transform: scale(1) rotate(0deg); opacity: 1; }
        }
      `}</style>
      <ParticleField />
      <div className="relative z-10 w-full max-w-2xl px-6 md:px-8">
        {/* Header */}
        <div className="text-center mb-10 md:mb-12 animate-fade-in">
          <div
            className="w-24 h-24 rounded-3xl flex items-center justify-center mx-auto mb-8"
            style={{
              background: processingError
                ? "var(--danger-subtle)"
                : "linear-gradient(135deg, var(--primary), var(--secondary))",
              boxShadow: processingError
                ? "0 0 40px var(--danger)"
                : "0 0 40px var(--primary), 0 0 80px var(--primary) / 20%",
              animation: processingError ? "none" : "breathe 3s ease-in-out infinite",
            }}
          >
            {processingError ? (
              <AlertCircle className="w-12 h-12" style={{ color: "var(--danger)" }} />
            ) : (
              <IpaLogo variant="white" size="sm" />
            )}
          </div>
          <h2 style={{
            fontSize: "var(--text-3xl)",
            fontWeight: "var(--font-weight-extrabold)",
            color: processingError ? "var(--danger)" : "var(--foreground)",
            letterSpacing: "var(--tracking-tight)",
            marginBottom: "var(--space-3)",
          }}>
            {processingError ? "Erreur de traitement" : t[lang].processing}
          </h2>
          <p style={{
            fontSize: "var(--text-lg)",
            color: processingError ? "var(--danger)" : "var(--foreground-muted)",
            lineHeight: "var(--leading-relaxed)",
          }}>
            {processingError
              ? "Le rapport sera chargé à partir des données disponibles"
              : currentStep >= totalSteps && !processingError
                ? "Analyse terminée"
                : "Analyse par intelligence artificielle médicale"}
          </p>
          {processingError && (
            <button onClick={() => setRetryCount(c => c + 1)} className="btn-primary mt-6">
              Réessayer
            </button>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-10 md:mb-12 animate-slide-up" style={{ animationDelay: "100ms" }}>
          <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--background-input)" }}>
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${progress}%`,
                background: "linear-gradient(90deg, var(--primary), var(--secondary), var(--primary))",
                backgroundSize: "200% 100%",
                boxShadow: "0 0 16px var(--primary)",
                animation: processingError ? "none" : "shimmer 2s linear infinite",
              }}
            />
          </div>
          <div className="flex justify-between mt-3">
            <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground-subtle)" }}>0%</span>
            <span style={{ fontSize: "var(--text-sm)", color: "var(--primary)", fontFamily: "var(--font-family-mono)", fontWeight: "var(--font-weight-semibold)" }}>
              {Math.round(progress)}%
            </span>
            <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground-subtle)" }}>100%</span>
          </div>
        </div>

        {/* Steps List */}
        <GlassCard className="p-6 md:p-8 animate-slide-up" style={{ animationDelay: "200ms" }}>
          <div className="relative">
            {/* Completed connector */}
            <div className="absolute left-5 top-0 w-px transition-all duration-700 z-0"
              style={{
                height: `${(currentStep / totalSteps) * 100}%`,
                background: "var(--success)",
              }}
            />
            {/* Remaining connector */}
            <div className="absolute left-5 top-0 w-px h-full z-0"
              style={{ background: "var(--border)" }}
            />

            {STEPS.map((step, i) => (
              <div key={i} className="flex items-start gap-4 py-3 relative">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-500 relative z-10"
                  style={{
                    background:
                      i < currentStep
                        ? "var(--success-subtle)"
                        : i === currentStep
                          ? "var(--primary-subtle)"
                          : "var(--background-input)",
                    border: `2px solid ${
                      i < currentStep
                        ? "var(--success)"
                        : i === currentStep
                          ? "var(--primary)"
                          : "var(--border)"
                    }`,
                    boxShadow: i === currentStep ? "0 0 16px var(--primary) / 40%" : "none",
                  }}
                >
                  {i < currentStep ? (
                    <Check className="w-5 h-5" style={{ color: "var(--success)", animation: "scaleIn 0.4s ease-out forwards" }} />
                  ) : i === currentStep ? (
                    processingError ? (
                      <AlertCircle className="w-5 h-5" style={{ color: "var(--danger)" }} />
                    ) : step.ipa ? (
                      <img src="/logo-ipa-white-processed.png" alt="IPA" className="w-5 h-5 object-contain" />
                    ) : (
                      <step.icon className="w-5 h-5 text-primary animate-pulse" />
                    )
                  ) : (
                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: "var(--foreground-subtle)", opacity: 0.4 }} />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div style={{
                    fontSize: "var(--text-base)",
                    fontWeight: i <= currentStep ? "var(--font-weight-semibold)" : "var(--font-weight-normal)",
                    color:
                      i < currentStep
                        ? "var(--success)"
                        : i === currentStep
                          ? "var(--foreground)"
                          : "var(--foreground-muted)",
                  }}>
                    {step.label}
                  </div>
                  {i <= currentStep && (step as any).sublabel && (
                    <div style={{
                      fontSize: "var(--text-sm)",
                      color: "var(--foreground-subtle)",
                      marginTop: "var(--space-1)",
                      fontFamily: i <= currentStep ? "var(--font-family-mono)" : undefined,
                    }}>
                      {(step as any).sublabel}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {processingError && currentStep >= totalSteps && (
            <div className="text-center py-3 mt-2 animate-fade-in" style={{ color: "var(--warning)", fontSize: "var(--text-sm)" }}>
              Le rapport sera chargé en mode dégradé
            </div>
          )}
        </GlassCard>

        {/* Reference Display */}
        <div className="mt-8 text-center animate-fade-in" style={{ animationDelay: "300ms" }}>
          <p style={{
            fontSize: "var(--text-sm)",
            color: "var(--foreground-subtle)",
            marginBottom: "var(--space-2)",
          }}>
            Référence du rapport
          </p>
          <p style={{
            fontSize: "var(--text-xl)",
            fontWeight: "var(--font-weight-bold)",
            color: "var(--foreground)",
            fontFamily: "var(--font-family-mono)",
          }}>
            {reportRef}
          </p>
        </div>
      </div>
    </div>
  )
}
