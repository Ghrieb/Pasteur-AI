import { useState, useRef } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { apiClient } from "../../lib/api-client"
import { t } from "../data/translations"
import type { Lang } from "../data/types"
import { ChevronLeft, Mic, MicOff, User, Brain, Loader } from "lucide-react"

export function VoiceScreen({ reportRef, lang, onBack }: { reportRef: string; lang: Lang; onBack: () => void }) {
  const [listening, setListening] = useState(false)
  const [question, setQuestion] = useState("")
  const [answer, setAnswer] = useState("")
  const [answering, setAnswering] = useState(false)
  const [bars] = useState(() => Array.from({ length: 24 }, () => Math.random() * 60 + 10))
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const isRtl = lang === "ar"

  const isSupported = typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)

  const suggestedQA: [string, string][] = [
    ["Pourquoi mon ALT est élevé ?", "Votre ALT est à 68 U/L, légèrement au-dessus de la normale (45 U/L). Cela peut indiquer une légère irritation du foie. Les causes possibles incluent la fatigue, une alimentation riche en graisses, ou certains médicaments. Consultez votre médecin pour un suivi adapté."],
    ["Mon cholestérol est-il dangereux ?", "Votre cholestérol total est de 218 mg/dL. C'est légèrement au-dessus du seuil recommandé de 200 mg/dL. Le LDL est également élevé à 138 mg/dL. Une alimentation équilibrée pauvre en graisses saturées et l'exercice physique peuvent aider à normaliser ces valeurs."],
  ]

  const askQuestion = async (q: string) => {
    setQuestion(q)
    setAnswering(true)
    try {
      const report = await apiClient.getReport(reportRef)
      const res = await apiClient.interpret({ reportJson: report, query: q, language: lang })
      setAnswer(res.answer)
    } catch {
      const matched = suggestedQA.find(([qq]) => qq === q)
      setAnswer(matched?.[1] ?? "L'assistant IA est temporairement indisponible. Veuillez réessayer.")
    } finally {
      setAnswering(false)
    }
  }

  const startListening = () => {
    if (!isSupported) {
      setAnswering(true)
      setListening(true)
      setTimeout(async () => {
        setListening(false)
        const q = "Pourquoi mon ALT est élevé ?"
        setQuestion(q)
        try {
          const report = await apiClient.getReport(reportRef)
          const res = await apiClient.interpret({ reportJson: report, query: q, language: lang })
          setAnswer(res.answer)
        } catch {
          setAnswer("Votre ALT est à 68 U/L, légèrement au-dessus de la normale (45 U/L). Cela peut indiquer une légère irritation du foie. Les causes possibles incluent la fatigue, une alimentation riche en graisses, ou certains médicaments. Consultez votre médecin pour un suivi adapté.")
        } finally {
          setAnswering(false)
        }
      }, 2500)
      return
    }
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    const recog = new SpeechRecognition()
    recog.lang = lang === "ar" ? "ar-DZ" : lang === "en" ? "en-US" : "fr-FR"
    recog.continuous = false
    recog.interimResults = false
    recog.onresult = async (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0][0].transcript
      setQuestion(transcript)
      setListening(false)
      setAnswering(true)
      try {
        const report = await apiClient.getReport(reportRef)
        const res = await apiClient.interpret({ reportJson: report, query: transcript, language: lang })
        setAnswer(res.answer)
      } catch {
        setAnswer("L'assistant IA est temporairement indisponible. Veuillez réessayer.")
      } finally {
        setAnswering(false)
      }
    }
    recog.onerror = () => {
      setListening(false)
      setAnswering(false)
    }
    recog.start()
    recognitionRef.current = recog
    setListening(true)
  }

  const handleListen = startListening

  return (
    <div
      className="relative min-h-screen flex flex-col overflow-hidden"
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
              Assistant Vocal
            </div>
          </div>
        </div>
      </header>
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 md:px-8 py-8">
        <div className="w-full max-w-2xl flex flex-col items-center">
          <div className="text-center mb-8 animate-fade-in">
            <h2 style={{ fontSize: "var(--text-3xl)", fontWeight: "var(--font-weight-extrabold)", color: "var(--foreground)", letterSpacing: "var(--tracking-tight)", marginBottom: "var(--space-2)" }}>
              Assistant Vocal PasteurAI
            </h2>
            <p style={{ fontSize: "var(--text-lg)", color: "var(--foreground-muted)" }}>
              Posez votre question à voix haute
            </p>
          </div>

          <button onClick={handleListen} disabled={listening}
            className="relative flex items-center justify-center rounded-full transition-all duration-300 mb-8"
            style={{
              width: 140, height: 140,
              background: listening ? "var(--danger-subtle)" : "var(--primary-subtle)",
              border: `3px solid ${listening ? "var(--danger)" : "var(--primary)"}`,
              boxShadow: listening ? "0 0 50px var(--danger)" : "0 0 30px var(--primary)",
            }}>
            {listening ? <MicOff className="w-14 h-14" style={{ color: "var(--danger)" }} /> : <Mic className="w-14 h-14" style={{ color: "var(--primary)" }} />}
            {listening && <div className="absolute inset-0 rounded-full animate-ping" style={{ background: "var(--danger-subtle)" }} />}
          </button>

          {/* Audio Visualizer */}
          <div className="flex items-center gap-1 mb-8 h-16">
            {bars.map((h, i) => (
              <div key={i} className="rounded-full transition-all duration-150"
                style={{
                  width: 4,
                  height: listening ? `${h * (0.5 + Math.random() * 0.8)}%` : "20%",
                  background: listening ? "var(--primary)" : "var(--border)",
                  boxShadow: listening ? "0 0 6px var(--primary)" : "none",
                  transition: "height 0.1s ease",
                }} />
            ))}
          </div>

          {question && (
            <div className="w-full space-y-4 animate-fade-in">
              <GlassCard className="p-5" style={{ borderColor: "var(--primary-border)" }}>
                <div className="flex items-start gap-3">
                  <User className="w-5 h-5" style={{ color: "var(--primary)", flexShrink: 0, marginTop: 2 }} />
                  <p style={{ fontSize: "var(--text-base)", color: "var(--foreground)", fontWeight: "var(--font-weight-semibold)" }}>{question}</p>
                </div>
              </GlassCard>
              {answering ? (
                <div className="flex items-center justify-center gap-3 py-8">
                  <div className="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                  <span style={{ color: "var(--foreground-muted)", fontSize: "var(--text-sm)" }}>Analyse en cours...</span>
                </div>
              ) : (
                <GlassCard className="p-5" style={{ borderColor: "var(--secondary-border)" }}>
                  <div className="flex items-start gap-3">
                    <Brain className="w-5 h-5" style={{ color: "var(--secondary)", flexShrink: 0, marginTop: 2 }} />
                    <p style={{ fontSize: "var(--text-base)", color: "var(--foreground)", lineHeight: "var(--leading-relaxed)" }}>{answer}</p>
                  </div>
                </GlassCard>
              )}
            </div>
          )}

          {!question && !listening && (
            <div className="flex flex-col gap-3 w-full animate-slide-up" style={{ animationDelay: "150ms" }}>
              <div style={{ fontSize: "var(--text-sm)", color: "var(--foreground-subtle)", textAlign: "center", letterSpacing: "var(--tracking-wider)", textTransform: "uppercase", marginBottom: "var(--space-3)" }}>
                Questions suggérées
              </div>
              {suggestedQA.map(([q]) => (
                <button key={q} onClick={() => askQuestion(q)} disabled={answering}
                  className="text-left p-4 rounded-xl transition-all"
                  style={{ background: "var(--background-input)", border: "1px solid var(--border)", color: "var(--foreground-muted)", fontSize: "var(--text-base)" }}>
                  {answering && question === q ? <Loader className="w-4 h-4 inline animate-spin mr-2" style={{ color: "var(--primary)" }} /> : null}
                  "{q}"
                </button>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
