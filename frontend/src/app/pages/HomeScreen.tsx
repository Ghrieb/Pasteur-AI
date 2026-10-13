import { useState, useEffect } from "react"
import { ParticleField } from "../components/ParticleField"
import { t } from "../data/translations"
import type { Lang } from "../data/types"
import { Activity, ArrowRight, QrCode, Wifi, Database, CheckCircle } from "lucide-react"
import { IpaLogo } from "../components/IpaLogo"

export function HomeScreen({ onStart, lang, setLang }: { onStart: () => void; lang: Lang; setLang: (l: Lang) => void }) {
  const langs: { code: Lang; label: string; native: string; flag: string }[] = [
    { code: "fr", label: "Français", native: "Langue Française", flag: "🇫🇷" },
    { code: "ar", label: "العربية", native: "اللغة العربية", flag: "🇩🇿" },
    { code: "en", label: "English", native: "English Language", flag: "🇬🇧" },
  ]

  const [pulse, setPulse] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const i = setInterval(() => setPulse((p) => !p), 2000)
    return () => clearInterval(i)
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr"
  }, [lang])

  const dir = lang === "ar" ? "rtl" : "ltr"

  return (
    <div
      className="relative min-h-screen flex flex-col overflow-hidden"
      style={{
        background: "var(--background)",
        fontFamily: "var(--font-family-sans)",
        direction: dir,
      }}
    >
      <ParticleField />

      {/* Top Bar */}
      <header className="relative z-10 flex items-center justify-between px-6 md:px-10 lg:px-16 pt-6 opacity-50" role="banner">
        <div className="flex items-center gap-2" dir="ltr">
          <Activity className="w-4 h-4" style={{ color: "var(--primary)" }} aria-hidden="true" />
          <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)" }}>
            Pasteur AI
          </span>
        </div>
        <div className="flex items-center gap-2" dir="ltr">
          <CheckCircle className="w-3.5 h-3.5" style={{ color: "var(--success)" }} aria-hidden="true" />
          <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)" }}>
            Système Actif
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 md:px-10 lg:px-16 py-12">
        {/* Background Visual */}
        <div
          className="absolute right-0 top-1/2 -translate-y-1/2 opacity-5 pointer-events-none hidden lg:block"
          style={{ width: 360 }}
          dir="ltr"
          aria-hidden="true"
        >
          <svg viewBox="0 0 240 240" fill="none" style={{ width: "100%", height: "100%" }}>
            <circle cx="120" cy="120" r="96" stroke="var(--primary)" strokeWidth="1.5" strokeDasharray="12 6" />
            <circle cx="120" cy="120" r="66" stroke="var(--secondary)" strokeWidth="1" />
            <path d="M120 48 L120 192 M48 120 L192 120" stroke="var(--primary)" strokeWidth="1.5" strokeLinecap="round" opacity="0.3" />
            <circle cx="120" cy="120" r="24" fill="var(--primary-subtle)" />
          </svg>
        </div>

        <div className="relative z-10 text-center w-full max-w-4xl">
          {/* Institutional Authority — Hero */}
          <div className="mb-6 flex flex-col items-center gap-3 animate-slide-up" style={{ animationDelay: "100ms" }}>
            {/* Republic & Ministry */}
            <div className="text-center space-y-0.5">
              <p style={{ fontSize: "var(--text-xs)", color: "var(--foreground-muted)", opacity: 0.35, letterSpacing: "0.2em", textTransform: "uppercase" }}>
                République Algérienne Démocratique et Populaire
              </p>
              <p style={{ fontSize: "var(--text-sm)", color: "var(--foreground)", opacity: 0.55, letterSpacing: "0.15em", fontWeight: "var(--font-weight-semibold)", textTransform: "uppercase" }}>
                Ministère de la Santé
              </p>
              <p style={{ fontSize: "var(--text-xs)", color: "var(--foreground-muted)", opacity: 0.45, letterSpacing: "0.15em", fontWeight: "var(--font-weight-semibold)", textTransform: "uppercase" }}>
                INSTITUT PASTEUR D'ALGÉRIE
              </p>
            </div>
            {/* Logos */}
            <div className="flex items-center justify-center mt-1">
              <span className="inline-block transition-all duration-200 hover:scale-105 active:scale-95 hover:brightness-125 cursor-default">
                <IpaLogo type="siha" variant="white" size="xl" />
              </span>
              <div className="w-px mx-7" style={{ height: 90, background: "var(--foreground-muted)", opacity: 0.15 }} />
              <span className="inline-block transition-all duration-200 hover:scale-105 active:scale-95 hover:brightness-125 cursor-default">
                <IpaLogo type="ipa" variant="white" size="xl" />
              </span>
            </div>
          </div>

          <h1 className="animate-slide-up" style={{
            fontSize: "var(--text-4xl)",
            fontWeight: "var(--font-weight-extrabold)",
            color: "var(--foreground)",
            letterSpacing: "var(--tracking-tight)",
            lineHeight: "var(--leading-tight)",
            marginBottom: "var(--space-4)",
            animationDelay: "200ms",
          }}>
            Pasteur AI
          </h1>

          <p className="animate-slide-up" style={{
            fontSize: "var(--text-xl)",
            color: "var(--foreground-muted)",
            marginBottom: "var(--space-6)",
            letterSpacing: "var(--tracking-wide)",
            maxWidth: "600px",
            marginLeft: "auto",
            marginRight: "auto",
            lineHeight: "var(--leading-relaxed)",
            animationDelay: "300ms",
          }}>
            {t[lang].subtitle}
          </p>

          <div className="flex items-center justify-center gap-2 mb-10 animate-slide-up" style={{ animationDelay: "400ms" }}>
            <div className="h-px w-16" style={{ background: "linear-gradient(90deg, transparent, var(--primary))" }} aria-hidden="true" />
            <span style={{
              fontSize: "var(--text-sm)",
              color: "var(--primary)",
              letterSpacing: "var(--tracking-widest)",
              textTransform: "uppercase",
              fontWeight: "var(--font-weight-semibold)",
            }}>
              Laboratoire de Biologie Médicale
            </span>
            <div className="h-px w-16" style={{ background: "linear-gradient(90deg, var(--primary), transparent)" }} aria-hidden="true" />
          </div>

          {/* Language Selector */}
          <div className="mb-12 animate-slide-up" style={{ animationDelay: "500ms" }} role="group" aria-label={t[lang].language}>
            <p style={{
              fontSize: "var(--text-sm)",
              color: "var(--foreground-subtle)",
              textAlign: "center",
              marginBottom: "var(--space-4)",
              letterSpacing: "var(--tracking-wider)",
              textTransform: "uppercase",
            }}>
              {t[lang].language}
            </p>
            <div className="flex justify-center gap-4 flex-wrap">
              {langs.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLang(l.code)}
                  className="flex flex-col items-center gap-2 px-7 py-4 rounded-2xl transition-all duration-300 ease-out"
                  style={{
                    background: lang === l.code
                      ? "linear-gradient(135deg, var(--primary-subtle), var(--secondary-subtle))"
                      : "var(--background-input)",
                    border: lang === l.code
                      ? "1px solid var(--primary-border)"
                      : "1px solid var(--border)",
                    boxShadow: lang === l.code
                      ? "0 0 28px var(--primary-subtle)"
                      : "none",
                    transform: lang === l.code ? "scale(1.03)" : "scale(1)",
                    backdropFilter: "blur(12px)",
                    minWidth: 150,
                  }}
                  aria-pressed={lang === l.code}
                  aria-current={lang === l.code ? "true" : "false"}
                >
                  <span style={{ fontSize: "var(--text-4xl)" }} aria-hidden="true">{l.flag}</span>
                  <span style={{
                    fontSize: "var(--text-lg)",
                    fontWeight: "var(--font-weight-bold)",
                    color: lang === l.code ? "var(--foreground)" : "var(--foreground-muted)",
                  }}>
                    {l.label}
                  </span>
                  <span style={{
                    fontSize: "var(--text-xs)",
                    color: "var(--foreground-subtle)",
                    letterSpacing: "var(--tracking-wide)",
                  }}>
                    {l.native}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Primary CTA */}
          <button
            onClick={onStart}
            className="btn-primary btn-lg group flex items-center gap-4 mx-auto animate-slide-up"
            style={{
              animationDelay: "600ms",
              minWidth: 360,
              boxShadow: "var(--shadow-glow-primary), 0 20px 48px rgba(0,0,0,0.35)",
            }}
            aria-label={t[lang].start}
          >
            <QrCode className="w-6 h-6 shrink-0" aria-hidden="true" />
            <span style={{ fontSize: "var(--text-lg)" }}>{t[lang].start}</span>
            <ArrowRight className="w-6 h-6 shrink-0 transition-transform group-hover:translate-x-1" aria-hidden="true" />
          </button>

        </div>
      </main>

      {/* Bottom Bar */}
      <footer className="relative z-10 flex items-center justify-between px-6 md:px-10 lg:px-16 pb-6 opacity-50">
        <span style={{
          fontSize: "var(--text-sm)",
          color: "var(--foreground-muted)",
        }}>
          © 2025 PasteurAI · Institut Pasteur d'Algérie
        </span>
        <div className="flex items-center gap-6" dir="ltr">
          <div className="flex items-center gap-2">
            <Wifi className="w-4 h-4" style={{ color: "var(--success)" }} aria-hidden="true" />
            <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)" }}>Connecté</span>
          </div>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4" style={{ color: "var(--primary)" }} aria-hidden="true" />
            <span style={{ fontSize: "var(--text-sm)", color: "var(--foreground-muted)" }}>Base synchronisée</span>
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .screen-enter { animation: fadeIn 0.5s var(--ease-out) forwards; }
      `}</style>
    </div>
  )
}