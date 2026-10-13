import { useState, useEffect, useRef } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { useReport } from "../hooks/use-report"
import { PrinterService } from "../../lib/devices/printer"
import { notificationCenter } from "../../lib/notification-center"
import { t } from "../data/translations"
import type { Lang } from "../data/types"
import { ChevronLeft, Printer, Download, Check, Loader2 } from "lucide-react"

export function PrintScreen({ reportRef, lang, onBack }: { reportRef: string; lang: Lang; onBack: () => void }) {
  const [printing, setPrinting] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [printed, setPrinted] = useState(false)
  const { patientData: p, fetchReport } = useReport()
  const printer = useRef(new PrinterService())
  const isRtl = lang === "ar"

  useEffect(() => {
    if (reportRef) fetchReport(reportRef)
  }, [reportRef, fetchReport])

  const handlePrint = async () => {
    setPrinting(true)
    try {
      await printer.current.print(reportRef)
      setPrinted(true)
      notificationCenter.success("Rapport imprimé avec succès", "Print")
    } catch {
      notificationCenter.error("Échec de l'impression", "Print")
    } finally {
      setPrinting(false)
    }
  }

  const handleDownloadPdf = async () => {
    setDownloading(true)
    try {
      const blob = await printer.current.downloadPdf(reportRef)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `rapport-${reportRef}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 1500)
      notificationCenter.success("PDF téléchargé avec succès", "PDF")
    } catch {
      notificationCenter.error("Échec de la génération PDF", "PDF")
    } finally {
      setDownloading(false)
    }
  }

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
              Imprimer / Télécharger
            </div>
          </div>
        </div>
      </header>
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 md:px-8 py-8">
        <div className="w-full max-w-2xl flex flex-col items-center gap-8">
          {/* Print Preview card */}
          <div className="w-80 rounded-2xl overflow-hidden shadow-2xl animate-fade-in"
            style={{ background: "#F5F5F0", color: "#1A1A1A", fontFamily: "var(--font-family-sans)" }}>
            <div className="p-6 text-center border-b border-gray-200">
              <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: "0.1em", color: "#1e88e5" }}>PASTEUR AI</div>
              <div style={{ fontSize: "var(--text-sm)", color: "#666", marginTop: 2 }}>Institut Pasteur d'Algérie</div>
            </div>
            <div className="p-6 space-y-2">
              <div style={{ fontSize: "var(--text-sm)" }}>Patient: {p.name}</div>
              <div style={{ fontSize: "var(--text-sm)" }}>Ref: {p.refNumber || reportRef}</div>
              <div style={{ fontSize: "var(--text-sm)" }}>Date: {p.reportDate}</div>
              <div className="border-t border-dashed border-gray-300 my-3" />
              <div style={{ fontSize: "var(--text-lg)", fontWeight: 700 }}>Score Santé: {p.healthScore}/100</div>
              <div style={{ fontSize: "var(--text-sm)", color: "#666" }}>Analyse IA disponible</div>
              <div className="border-t border-dashed border-gray-300 my-3" />
              <div style={{ fontSize: 11, color: "#666", lineHeight: 1.6 }}>Résultat non contractuel.</div>
              <div style={{ fontSize: 11, color: "#666" }}>Consultez votre médecin.</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 animate-slide-up" style={{ animationDelay: "150ms" }}>
            <button onClick={handlePrint} disabled={printing}
              className="btn-primary btn-lg flex items-center gap-3"
              style={{ boxShadow: printed ? "none" : "0 0 30px var(--primary)" }}>
              {printing ? <Loader2 className="w-5 h-5 animate-spin" /> : printed ? <Check className="w-5 h-5" /> : <Printer className="w-5 h-5" />}
              {printing ? "Impression..." : printed ? "Imprimé !" : "Imprimer"}
            </button>
            <button onClick={handleDownloadPdf} disabled={downloading}
              className={downloading ? "btn-outline btn-lg flex items-center gap-3 opacity-60" : "btn-outline btn-lg flex items-center gap-3"}>
              {downloading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
              {downloading ? "Génération..." : "PDF"}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
