import { useState, useRef, useEffect } from "react"
import type { Screen, Lang } from "./data/types"
import { HomeScreen, ScanScreen, ProcessingScreen, DashboardScreen, BiomarkerDetail, InsightsScreen, HistoryScreen, VoiceScreen, PrintScreen, DevConsole, AnomaliesScreen } from "./pages"
import { ErrorBoundary } from "./components/ErrorBoundary"
import { eventBus } from "../lib/event-bus"
import { sessionManager } from "../lib/session-manager"
import { notificationCenter } from "../lib/notification-center"
import { themeEngine } from "../lib/theme-engine"
import { useReport } from "./hooks/use-report"
import type { Notification } from "../lib/notification-center"

export default function App() {
  const [screen, setScreen] = useState<Screen>("home")
  const [lang, setLang] = useState<Lang>("fr")
  const [selectedCategory, setSelectedCategory] = useState<string>("liver")
  const [reportRef, setReportRef] = useState<string>("")
  const [qrUrl, setQrUrl] = useState<string>("")
  const [showDevConsole, setShowDevConsole] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [tapCount, setTapCount] = useState(0)
  const [initialAiSummary, setInitialAiSummary] = useState("")
  const tapTimer = useRef<ReturnType<typeof setTimeout>>()

  const { report, patientData, history, loading, error, fetchReport, fetchPatientHistory } = useReport()

  useEffect(() => {
    if (reportRef) {
      fetchReport(reportRef)
        .then(() => {
          if (reportRef) fetchPatientHistory(reportRef)
        })
    }
  }, [reportRef])

  useEffect(() => {
    themeEngine.get()
    sessionManager.start()
    notificationCenter.info("Système prêt", "PasteurAI")
    const unsub = notificationCenter.onNotification((n) => {
      setNotifications((prev) => [...prev.slice(-4), n])
      setTimeout(() => setNotifications((prev) => prev.filter((x) => x.id !== n.id)), 4000)
    })
    return () => { unsub(); sessionManager.end("app_quit") }
  }, [])

  const navigate = (s: Screen) => {
    eventBus.emit({ type: "session:updated", payload: { sessionId: sessionManager.getCurrent()?.id || "", status: s } })
    if (s === "home" || s === "scan") { setReportRef(""); setQrUrl("") }
    setScreen(s)
  }

  const handleLogoTap = () => {
    setTapCount(c => c + 1)
    clearTimeout(tapTimer.current)
    tapTimer.current = setTimeout(() => setTapCount(0), 2000)
    if (tapCount >= 4) { setShowDevConsole(true); setTapCount(0) }
  }

  return (
    <div className="relative w-full min-h-screen" style={{ fontFamily: "DM Sans, sans-serif" }} onDoubleClick={handleLogoTap}>
      <style>{`
        * { scrollbar-width: none; }
        *::-webkit-scrollbar { display: none; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        .screen-enter { animation: fadeIn 0.5s ease forwards; }
      `}</style>
      <div className="screen-enter" key={screen}>
        <ErrorBoundary>
          {screen === "home" && <HomeScreen onStart={() => navigate("scan")} lang={lang} setLang={setLang} />}
          {screen === "scan" && (
            <ScanScreen onScan={(ref, url) => { setReportRef(ref); setQrUrl(url || ""); navigate("processing") }} lang={lang} onBack={() => navigate("home")} />
          )}
          {screen === "processing" && <ProcessingScreen reportRef={reportRef} qrUrl={qrUrl} onDone={(summary) => { setInitialAiSummary(summary || ""); navigate("dashboard") }} lang={lang} />}
          {screen === "dashboard" && (
            <DashboardScreen reportRef={reportRef} lang={lang} report={report} patientData={patientData} history={history} loading={loading} error={error} fetchReport={fetchReport} onNav={(s) => navigate(s)} onCategory={(k) => { setSelectedCategory(k); navigate("biomarker") }} initialAiSummary={initialAiSummary} />
          )}
          {screen === "biomarker" && <BiomarkerDetail catKey={selectedCategory} lang={lang} report={report} patientData={patientData} onBack={() => navigate("dashboard")} />}
          {screen === "insights" && <InsightsScreen report={report} patientData={patientData} reportRef={reportRef} lang={lang} onBack={() => navigate("dashboard")} />}
          {screen === "history" && <HistoryScreen reportRef={reportRef} lang={lang} onBack={() => navigate("dashboard")} />}
          {screen === "print" && <PrintScreen reportRef={reportRef} lang={lang} onBack={() => navigate("dashboard")} />}
          {screen === "voice" && <VoiceScreen reportRef={reportRef} lang={lang} onBack={() => navigate("dashboard")} />}
          {screen === "anomalies" && <AnomaliesScreen lang={lang} report={report} onBack={() => navigate("dashboard")} onCategory={(k) => { setSelectedCategory(k); navigate("biomarker") }} />}
        </ErrorBoundary>
      </div>
      {showDevConsole && <DevConsole onClose={() => setShowDevConsole(false)} />}

      {/* Notification toasts */}
      <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
        {notifications.map((n) => (
          <div key={n.id}
            className="pointer-events-auto cursor-pointer px-6 py-4 rounded-xl backdrop-blur-xl"
            style={{
              background: n.level === "error" ? "rgba(239,68,68,0.2)" : n.level === "warning" ? "rgba(245,158,11,0.2)" : n.level === "success" ? "rgba(34,197,94,0.2)" : "rgba(26,127,212,0.2)",
              border: `1px solid ${n.level === "error" ? "#EF4444" : n.level === "warning" ? "#F59E0B" : n.level === "success" ? "#22C55E" : "#1A7FD4"}`,
              borderLeft: `4px solid ${n.level === "error" ? "#EF4444" : n.level === "warning" ? "#F59E0B" : n.level === "success" ? "#22C55E" : "#1A7FD4"}`,
              minWidth: 320, maxWidth: 480,
            }}
            onClick={() => setNotifications((prev) => prev.filter((x) => x.id !== n.id))}>
            <div className="flex items-center gap-3">
              <span style={{ fontSize: 20, color: n.level === "error" ? "#EF4444" : n.level === "warning" ? "#F59E0B" : n.level === "success" ? "#22C55E" : "#1A7FD4" }}>
                {n.level === "success" ? "✓" : n.level === "warning" ? "⚠" : n.level === "error" ? "✕" : "ℹ"}
              </span>
              <span style={{ color: "#E8F4FD", fontSize: 15 }}>{n.message}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
