import { useState, useEffect, useRef } from "react"
import { GlassCard } from "../GlassCard"
import { Sparkles, Send, Loader2, CheckCircle } from "lucide-react"
import { apiClient } from "../../../lib/api-client"
import type { ReportJson } from "../../../lib/api-types"

export function AiInsightCard({ reportJson, language, prefillQuestion, initialSummary, initialRecommendations }: {
  reportJson: ReportJson
  language: string
  prefillQuestion?: string
  initialSummary?: string
  initialRecommendations?: string[]
}) {
  const [query, setQuery] = useState("")
  const [answer, setAnswer] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const prevPrefill = useRef(prefillQuestion)

  useEffect(() => {
    if (prefillQuestion && prefillQuestion !== prevPrefill.current) {
      prevPrefill.current = prefillQuestion
      handleAsk(prefillQuestion)
    }
  }, [prefillQuestion])

  const handleAsk = async (q?: string) => {
    const question = q || query
    if (!question.trim()) return
    setLoading(true)
    try {
      const res = await apiClient.interpret({ reportJson, query: question, language })
      setAnswer(res.answer)
    } catch {
      setAnswer("Désolé, l'assistant IA est temporairement indisponible.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <GlassCard className="p-6 w-full" style={{ borderColor: "rgba(26,127,212,0.25)" }}>
      <div className="flex items-center gap-3 mb-6">
        <Sparkles size={24} style={{ color: "#1A7FD4" }} />
        <h3 style={{ fontSize: 22, fontWeight: 600, color: "#E8F4FD" }}>Assistant IA · Institut Pasteur</h3>
      </div>

      {/* Patient-specific initial analysis */}
      {initialSummary && (
        <div className="mb-6 p-6 rounded-xl" style={{ background: "rgba(255,255,255,0.03)" }}>
          <p style={{ fontSize: 16, color: "#C5DFF0", lineHeight: 1.7 }}>{initialSummary}</p>
          {initialRecommendations && initialRecommendations.length > 0 && (
            <div className="mt-5 pt-5" style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#14B8A6", letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 12 }}>
                Recommandations
              </div>
              <div className="flex flex-col gap-2">
                {initialRecommendations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <CheckCircle size={16} style={{ color: "#14B8A6", flexShrink: 0, marginTop: 2 }} />
                    <span style={{ fontSize: 15, color: "#C5DFF0", lineHeight: 1.6 }}>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Q&A answers */}
      {answer && (
        <div className="mb-6 p-6 rounded-xl" style={{ background: "rgba(255,255,255,0.03)" }}>
          <p style={{ fontSize: 16, color: "#C5DFF0", lineHeight: 1.7 }}>{answer}</p>
        </div>
      )}

      {/* Q&A Input */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          placeholder={language === "fr" ? "Posez une question sur votre analyse..." : language === "ar" ? "اطرح سؤالاً حول تحليلك..." : "Ask a question about your analysis..."}
          className="flex-1 px-6 py-4 text-base outline-none rounded-xl"
          style={{ color: "#E8F4FD", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)" }}
        />
        <button
          className="p-4 rounded-xl flex items-center justify-center"
          style={{ background: "linear-gradient(135deg,#1A7FD4,#14B8A6)" }}
          onClick={() => handleAsk()}
          disabled={loading}
        >
          {loading ? <Loader2 size={20} className="animate-spin text-white" /> : <Send size={20} className="text-white" />}
        </button>
      </div>
    </GlassCard>
  )
}
