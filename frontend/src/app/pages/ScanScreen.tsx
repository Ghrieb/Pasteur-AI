import { useState, useEffect, useRef, useCallback } from "react"
import { ParticleField } from "../components/ParticleField"
import { GlassCard } from "../components/GlassCard"
import { useQrScanner } from "../hooks/use-qr-scanner"
import { t } from "../data/translations"
import type { Lang } from "../data/types"
import { ChevronLeft, Camera, Check, Key, RefreshCw, X } from "lucide-react"
import { IpaLogo } from "../components/IpaLogo"

export function ScanScreen({ onScan, lang, onBack }: { onScan: (ref: string, url?: string) => void; lang: Lang; onBack: () => void }) {
  const [anim, setAnim] = useState(0)
  const [manualRef, setManualRef] = useState("")
  const [showManual, setShowManual] = useState(false)
  const [camTimeout, setCamTimeout] = useState(false)
  const mountedRef = useRef(true)
  const { videoRef, status, detectedCode, rawData, errorMsg, start, stop, reset } = useQrScanner()

  useEffect(() => {
    mountedRef.current = true
    const i = setInterval(() => setAnim((a) => (a + 1) % 100), 50)
    start()
    const timer = setTimeout(() => {
      if (mountedRef.current && status !== "detected") setCamTimeout(true)
    }, 50000)
    return () => {
      mountedRef.current = false
      clearInterval(i)
      clearTimeout(timer)
      stop()
    }
  }, [])

  useEffect(() => {
    if (status === "detected" || detectedCode) {
      setCamTimeout(false)
    }
  }, [status, detectedCode])

  useEffect(() => {
    if (detectedCode) {
      const t = setTimeout(() => onScan(detectedCode, rawData || undefined), 800)
      return () => clearTimeout(t)
    }
  }, [detectedCode, rawData, onScan])

  const handleRetry = useCallback(() => {
    setCamTimeout(false)
    setShowManual(false)
    stop()
    setTimeout(() => start(), 300)
  }, [stop, start])

  const handleManualScan = () => {
    const ref = manualRef.trim()
    if (ref) onScan(ref)
  }

  const scanning = status === "scanning"
  const detected = status === "detected"
  const hasError = status === "error"
  const isRtl = lang === "ar"

  return (
    <div
      className="relative min-h-screen flex flex-col overflow-hidden"
      style={{
        background: "var(--background)",
        fontFamily: "var(--font-family-sans)",
        direction: isRtl ? "rtl" : "ltr",
      }}
    >
      <ParticleField />

      {/* Floating controls */}
      <button onClick={onBack} className="absolute top-4 left-6 md:left-8 z-50 btn-icon" aria-label={t[lang].back}>
        <ChevronLeft className="w-5 h-5" style={{ transform: isRtl ? "rotate(180deg)" : "none" }} />
      </button>
      <div className="absolute top-4 right-6 md:right-8 z-50 opacity-60">
        <IpaLogo variant="white" size="sm" />
      </div>

      <div className="relative z-10 w-full max-w-3xl px-6 md:px-8 mx-auto flex-1 flex flex-col items-center justify-center">

        {/* Scan Frame */}
        <div className="relative mx-auto" style={{ width: "min(100%, 440px)", aspectRatio: "1 / 1" }}>
          {/* Scan overlay text */}
          {scanning && !detected && !camTimeout && !showManual && (
            <div className="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 text-center z-10 pointer-events-none whitespace-nowrap">
              <h2 style={{
                fontSize: "var(--text-2xl)",
                fontWeight: "var(--font-weight-extrabold)",
                color: "var(--foreground)",
                textShadow: "0 2px 12px rgba(0,0,0,0.6)",
              }}>
                {t[lang].scanTitle}
              </h2>
              <p style={{
                fontSize: "var(--text-sm)",
                color: "var(--foreground-muted)",
                marginTop: "var(--space-2)",
                textShadow: "0 1px 6px rgba(0,0,0,0.5)",
              }}>
                {t[lang].scanInstr}
              </p>
            </div>
          )}
          {/* Error / Timeout State */}
          {(hasError || camTimeout) && !showManual && (
            <GlassCard className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center animate-fade-in" role="alert">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
                style={{
                  background: camTimeout ? "var(--warning-subtle)" : "var(--danger-subtle)",
                  border: camTimeout ? "1px solid var(--warning-border)" : "1px solid var(--danger-border)",
                }}
              >
                <Camera className="w-8 h-8" style={{ color: camTimeout ? "var(--warning)" : "var(--danger)" }} />
              </div>

              <p style={{
                color: camTimeout ? "var(--warning)" : "var(--danger)",
                fontSize: "var(--text-xl)",
                fontWeight: "var(--font-weight-bold)",
                marginBottom: "var(--space-3)",
              }}>
                {camTimeout ? "Caméra lente à répondre" : errorMsg || "Caméra non disponible"}
              </p>

              <p style={{
                color: "var(--foreground-muted)",
                fontSize: "var(--text-base)",
                marginBottom: "var(--space-6)",
                lineHeight: "var(--leading-relaxed)",
                maxWidth: 280,
              }}>
                {camTimeout
                  ? "Le flux caméra prend du temps. Passez en saisie manuelle."
                  : errorMsg?.includes("Permission") || errorMsg?.includes("permission")
                    ? "Cliquez sur l'icône du cadenas dans la barre d'adresse et autorisez la caméra."
                    : errorMsg || "Vérifiez les permissions caméra dans votre navigateur."}
              </p>

              <div className="flex flex-col sm:flex-row gap-3 w-full max-w-xs">
                <button
                  onClick={handleRetry}
                  className="btn-primary flex-1"
                  style={{ minHeight: "var(--touch-target-lg)" }}
                >
                  <RefreshCw className="w-5 h-5" />
                  Réessayer
                </button>
                <button
                  onClick={() => setShowManual(true)}
                  className="btn-outline flex-1"
                  style={{ minHeight: "var(--touch-target-lg)" }}
                >
                  <Key className="w-5 h-5" />
                  Saisie Manuelle
                </button>
              </div>
            </GlassCard>
          )}

          {/* Camera View */}
          {!hasError && !camTimeout && (
            <GlassCard className="absolute inset-0 animate-fade-in">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="absolute inset-0 w-full h-full object-cover"
                style={{ opacity: detected ? 0.3 : 1 }}
              />

              {/* Scanning Line */}
              {scanning && (
                <div
                  className="absolute left-8 right-8 h-1 pointer-events-none"
                  style={{
                    top: `${20 + (anim / 100) * 60}%`,
                    background: "linear-gradient(90deg, transparent, var(--primary), transparent)",
                    boxShadow: "0 0 16px var(--primary)",
                    transition: "top 0.05s linear",
                  }}
                  aria-hidden="true"
                />
              )}

              {/* Corner Brackets */}
              {[["top-4 left-4", "border-t border-l"], ["top-4 right-4", "border-t border-r"], ["bottom-4 left-4", "border-b border-l"], ["bottom-4 right-4", "border-b border-r"]].map(([pos, border], i) => (
                <div
                  key={i}
                  className={`absolute w-12 h-12 ${pos} ${border}`}
                  style={{
                    borderColor: detected ? "var(--success)" : "var(--primary)",
                    borderWidth: 3,
                    borderRadius: 12,
                    boxShadow: `0 0 16px ${detected ? "var(--success)" : "var(--primary)"}`,
                    transition: "all 0.5s ease-out",
                  }}
                  aria-hidden="true"
                />
              ))}

              {/* Detected Overlay */}
              {detected && (
                <div
                  className="absolute inset-0 flex flex-col items-center justify-center animate-scale-in"
                  style={{ background: "var(--success-subtle)", backdropFilter: "blur(12px)" }}
                  role="status"
                  aria-live="polite"
                >
                  <div
                    className="w-20 h-20 rounded-full flex items-center justify-center mb-4"
                    style={{
                      background: "var(--success-subtle)",
                      border: "2px solid var(--success)",
                      boxShadow: "0 0 40px var(--success)",
                    }}
                  >
                    <Check className="w-10 h-10" style={{ color: "var(--success)" }} />
                  </div>
                  <span style={{
                    color: "var(--success)",
                    fontSize: "var(--text-xl)",
                    fontWeight: "var(--font-weight-bold)",
                  }}>
                    QR Code Détecté
                  </span>
                  <span style={{
                    color: "var(--foreground-muted)",
                    fontSize: "var(--text-sm)",
                    marginTop: "var(--space-2)",
                    fontFamily: "var(--font-family-mono)",
                  }}>
                    Réf: {detectedCode}
                  </span>
                </div>
              )}
            </GlassCard>
          )}

          {/* Pulse Rings */}
          {scanning && !detected && [1, 2, 3].map((n) => (
            <div
              key={n}
              className="absolute rounded-full border pointer-events-none"
              style={{
                inset: -n * 24,
                borderColor: "var(--primary)",
                borderWidth: 1,
                opacity: 0.3,
                animation: `pulse ${n * 0.8 + 1}s ease-out infinite`,
                animationDelay: `${n * 0.3}s`,
              }}
              aria-hidden="true"
            />
          ))}

          <style>{`
            @keyframes pulse {
              0% { opacity: 0.4; transform: scale(1); }
              100% { opacity: 0; transform: scale(1.15); }
            }
          `}</style>
        </div>

        {/* Status Indicator */}
        <div className="mt-8 text-center">
          <div className="flex items-center justify-center gap-3" role="status" aria-live="polite">
            {hasError ? (
              <span style={{ color: "var(--danger)", fontSize: "var(--text-base)", fontWeight: "var(--font-weight-medium)" }}>
                Caméra inaccessible
              </span>
            ) : camTimeout ? (
              <span style={{ color: "var(--warning)", fontSize: "var(--text-base)", fontWeight: "var(--font-weight-medium)" }}>
                La caméra ne répond pas
              </span>
            ) : detected ? (
              <>
                <div className="w-3 h-3 rounded-full" style={{ background: "var(--success)", boxShadow: "0 0 10px var(--success)" }} />
                <span style={{ color: "var(--success)", fontSize: "var(--text-base)", fontWeight: "var(--font-weight-semibold)" }}>
                  QR code reconnu · Traitement...
                </span>
              </>
            ) : (
              <>
                <div className="w-3 h-3 rounded-full animate-pulse" style={{ background: "var(--primary)", boxShadow: "0 0 10px var(--primary)" }} />
                <span style={{ color: "var(--foreground-muted)", fontSize: "var(--text-base)" }}>
                  Recherche de QR code...
                </span>
              </>
            )}
          </div>
        </div>

        {/* Manual Entry Toggle */}
        {!showManual && !hasError && !camTimeout && (
          <div className="mt-6 text-center">
            <button
              onClick={() => { stop(); setShowManual(true) }}
              className="btn-ghost"
              style={{ minWidth: 280 }}
            >
              <Key className="w-4 h-4" />
              Saisir manuellement le numéro de référence
            </button>
          </div>
        )}

        {/* Manual Entry Form */}
        {showManual && (
          <GlassCard className="mt-8 p-6 max-w-md mx-auto animate-slide-up" style={{ borderColor: "var(--primary-border)" }}>
            <div className="flex items-center justify-between mb-6">
              <h3 style={{
                fontSize: "var(--text-lg)",
                fontWeight: "var(--font-weight-bold)",
                color: "var(--foreground)",
              }}>
                Saisie Manuelle
              </h3>
              <button
                onClick={() => { setShowManual(false); handleRetry() }}
                className="btn-ghost btn-icon-sm p-2"
                aria-label="Retour au scan caméra"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex gap-3 mb-4">
              <input
                value={manualRef}
                onChange={(e) => setManualRef(e.target.value)}
                placeholder="Numéro de référence (ex: 53980)"
                className="input input-lg flex-1 font-mono text-center"
                style={{
                  background: "var(--background-input)",
                  border: "1px solid var(--border)",
                  color: "var(--foreground)",
                }}
                onKeyDown={(e) => e.key === "Enter" && handleManualScan()}
                autoFocus
                aria-label="Numéro de référence du rapport"
              />
              <button
                onClick={handleManualScan}
                className="btn-primary shrink-0"
                style={{ minWidth: 80, minHeight: "var(--touch-target-lg)" }}
              >
                OK
              </button>
            </div>

            <p style={{
              color: "var(--foreground-subtle)",
              fontSize: "var(--text-sm)",
              textAlign: "center",
              marginBottom: "var(--space-4)",
            }}>
              Références disponibles: 53980 (BENALI), 54189 (KACI)
            </p>

            <button
              onClick={() => { setShowManual(false); handleRetry() }}
              className="btn-ghost w-full"
              style={{ color: "var(--primary)" }}
            >
              ← Retour au scan caméra
            </button>
          </GlassCard>
        )}
      </div>
    </div>
  )
}