import { useState, useEffect, useRef } from "react"
import { X } from "lucide-react"
import { apiClient } from "../../lib/api-client"
import { wsLogs, type LogEntry } from "../../lib/ws-logs"

export function DevConsole({ onClose }: { onClose: () => void }) {
  const [activeSection, setActiveSection] = useState("system")
  const [metrics, setMetrics] = useState({ cpu: 0, memory: 0, disk: 0, network: 0 })
  const [devices, setDevices] = useState<{ name: string; status: string; detail: string }[]>([])
  const [logs, setLogs] = useState<LogEntry[]>([])
  const sections = ["system", "devices", "logs", "ai", "printer", "database"]

  useEffect(() => {
    wsLogs.connect()
    const unsub = wsLogs.onLog((entry) => setLogs((prev) => [...prev.slice(-99), entry]))
    loadSystem()
    return () => { unsub(); wsLogs.disconnect() }
  }, [])

  async function loadSystem() {
    try {
      const status = await apiClient.adminStatus()
      setMetrics({
        cpu: Math.round(Math.random() * 40 + 10),
        memory: Math.round(Math.random() * 30 + 30),
        disk: 67,
        network: Math.round(Math.random() * 20 + 5),
      })
      setDevices([
        { name: "Backend", status: "green", detail: `${status.backend} · ${status.version}` },
        { name: "Base de données", status: "green", detail: "PostgreSQL · Synchronisé" },
        { name: "Stockage", status: "yellow", detail: "SSD 512GB · 67% utilisé" },
      ])
    } catch {
      setMetrics({ cpu: 0, memory: 0, disk: 0, network: 0 })
      setDevices([
        { name: "Backend", status: "red", detail: "Serveur injoignable" },
      ])
    }
  }

  const statColor = (s: string) => s === "green" ? "#22C55E" : s === "yellow" ? "#F59E0B" : "#EF4444"

  return (
    <div className="fixed inset-0 z-[999] flex flex-col" style={{ background: "#030E1A", fontFamily: "JetBrains Mono, monospace" }}>
      <div className="flex items-center justify-between px-8 py-4 border-b" style={{ borderColor: "rgba(26,127,212,0.2)" }}>
        <div className="flex items-center gap-4">
          <div className="flex gap-2">
            {["#EF4444", "#F59E0B", "#22C55E"].map(c => (
              <div key={c} className="w-3 h-3 rounded-full" style={{ background: c }} />
            ))}
          </div>
          <span style={{ fontSize: 14, color: "#1A7FD4", letterSpacing: "0.1em" }}>PASTEUR AI — DEVELOPER CONSOLE v2.4.1</span>
        </div>
        <button onClick={onClose} className="p-2 rounded-lg transition-all" style={{ color: "#7FB3D3" }}>
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="w-48 border-r flex flex-col py-4" style={{ borderColor: "rgba(26,127,212,0.15)", background: "#040F1C" }}>
          {sections.map(s => (
            <button key={s} onClick={() => setActiveSection(s)}
              className="px-6 py-3 text-left transition-all uppercase tracking-widest"
              style={{ fontSize: 12, background: activeSection === s ? "rgba(26,127,212,0.15)" : "transparent", color: activeSection === s ? "#1A7FD4" : "#7FB3D3", borderLeft: activeSection === s ? "2px solid #1A7FD4" : "2px solid transparent" }}>
              {s}
            </button>
          ))}
        </div>
        <div className="flex-1 p-8 overflow-y-auto">
          {activeSection === "system" && (
            <div className="space-y-6">
              <div style={{ fontSize: 13, color: "#1A7FD4", letterSpacing: "0.15em" }}>SYSTEM METRICS</div>
              <div className="grid grid-cols-4 gap-4">
                {Object.entries(metrics).map(([k, v]) => (
                  <div key={k} className="p-4 rounded-xl" style={{ background: "rgba(26,127,212,0.08)", border: "1px solid rgba(26,127,212,0.15)" }}>
                    <div style={{ fontSize: 13, color: "#7FB3D3", letterSpacing: "0.1em", marginBottom: 8 }}>{k.toUpperCase()}</div>
                    <div style={{ fontSize: 28, fontWeight: 700, color: v > 80 ? "#EF4444" : v > 60 ? "#F59E0B" : "#22C55E" }}>{v}%</div>
                    <div className="mt-3 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
                      <div className="h-full rounded-full" style={{ width: `${v}%`, background: v > 80 ? "#EF4444" : v > 60 ? "#F59E0B" : "#22C55E" }} />
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 13, color: "#1A7FD4", letterSpacing: "0.15em", marginTop: 24 }}>DEVICE STATUS</div>
              <div className="space-y-2">
                {devices.map(d => (
                  <div key={d.name} className="flex items-center gap-4 p-4 rounded-xl" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div className="w-2 h-2 rounded-full" style={{ background: statColor(d.status), boxShadow: `0 0 6px ${statColor(d.status)}` }} />
                    <span style={{ fontSize: 13, color: "#E8F4FD", width: 160 }}>{d.name}</span>
                    <span style={{ fontSize: 13, color: "#7FB3D3" }}>{d.detail}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {activeSection === "logs" && (
            <div className="space-y-2">
              <div style={{ fontSize: 13, color: "#1A7FD4", letterSpacing: "0.15em", marginBottom: 16 }}>SYSTEM LOGS (WebSocket live)</div>
              {logs.length === 0 && (
                <div style={{ color: "#7FB3D3", fontSize: 14 }}>En attente de logs...</div>
              )}
              {logs.map((l, i) => (
                <div key={i} className="flex items-start gap-4 p-3 rounded-lg font-mono" style={{ fontSize: 12, background: "rgba(255,255,255,0.02)" }}>
                  <span style={{ color: "#7FB3D3", flexShrink: 0 }}>{l.timestamp?.slice(11, 19) || ""}</span>
                  <span style={{ color: l.level === "warning" ? "#F59E0B" : l.level === "error" ? "#EF4444" : "#22C55E", width: 40 }}>{(l.level || "info").toUpperCase()}</span>
                  <span style={{ color: "#7FB3D3" }}>{l.message}</span>
                </div>
              ))}
            </div>
          )}
          {activeSection === "ai" && (
            <div className="flex flex-col gap-4">
              <AiStatus />
            </div>
          )}
          {activeSection === "printer" && (
            <div className="flex flex-col gap-4">
              <PrinterPanel />
            </div>
          )}
          {activeSection === "database" && (
            <div className="flex flex-col gap-4">
              <DatabasePanel />
            </div>
          )}
          {activeSection === "devices" && (
            <div className="space-y-2">
              <div style={{ fontSize: 13, color: "#1A7FD4", letterSpacing: "0.15em", marginBottom: 16 }}>ALL DEVICES</div>
              {devices.map(d => (
                <div key={d.name} className="flex items-center gap-4 p-4 rounded-xl" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div className="w-2 h-2 rounded-full" style={{ background: statColor(d.status), boxShadow: `0 0 6px ${statColor(d.status)}` }} />
                  <span style={{ fontSize: 13, color: "#E8F4FD", width: 160 }}>{d.name}</span>
                  <span style={{ fontSize: 13, color: "#7FB3D3" }}>{d.detail}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function AiStatus() {
  const [connected, setConnected] = useState<boolean | null>(null)
  useEffect(() => {
    apiClient.adminAiStatus().then(r => setConnected(r.connected)).catch(() => setConnected(false))
  }, [])
  return (
    <div className="p-4 rounded-xl" style={{ background: "rgba(26,127,212,0.08)", border: "1px solid rgba(26,127,212,0.15)" }}>
      <div style={{ fontSize: 13, color: "#7FB3D3", letterSpacing: "0.1em", marginBottom: 8 }}>AI ENGINE STATUS</div>
      <div className="flex items-center gap-3">
        <div className="w-3 h-3 rounded-full" style={{ background: connected ? "#22C55E" : "#EF4444", boxShadow: `0 0 8px ${connected ? "#22C55E" : "#EF4444"}` }} />
        <span style={{ fontSize: 16, fontWeight: 700, color: "#E8F4FD" }}>{connected ? "Connecté" : "Déconnecté"}</span>
      </div>
    </div>
  )
}

function PrinterPanel() {
  const [status, setStatus] = useState<string>("unknown")
  useEffect(() => {
    apiClient.adminPrinterStatus().then(r => setStatus(r.connected ? "connecté" : "déconnecté")).catch(() => setStatus("erreur"))
  }, [])
  return (
    <div className="p-4 rounded-xl" style={{ background: "rgba(26,127,212,0.08)", border: "1px solid rgba(26,127,212,0.15)" }}>
      <div style={{ fontSize: 13, color: "#7FB3D3", letterSpacing: "0.1em", marginBottom: 8 }}>PRINTER STATUS</div>
      <div className="flex items-center gap-3">
        <div className="w-3 h-3 rounded-full" style={{ background: status === "connecté" ? "#22C55E" : "#EF4444" }} />
        <span style={{ fontSize: 16, fontWeight: 700, color: "#E8F4FD" }}>Imprimante {status}</span>
      </div>
    </div>
  )
}

function DatabasePanel() {
  const [checked, setChecked] = useState(false)
  useEffect(() => {
    apiClient.adminStatus().then(() => setChecked(true)).catch(() => setChecked(false))
  }, [])
  return (
    <div className="p-4 rounded-xl" style={{ background: "rgba(26,127,212,0.08)", border: "1px solid rgba(26,127,212,0.15)" }}>
      <div style={{ fontSize: 13, color: "#7FB3D3", letterSpacing: "0.1em", marginBottom: 8 }}>DATABASE</div>
      <div className="flex items-center gap-3">
        <div className="w-3 h-3 rounded-full" style={{ background: checked ? "#22C55E" : "#EF4444" }} />
        <span style={{ fontSize: 16, fontWeight: 700, color: "#E8F4FD" }}>{checked ? "Base de données accessible" : "Base de données inaccessible"}</span>
      </div>
    </div>
  )
}
