import { Component } from "react"
import type { ReactNode } from "react"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: { componentStack?: string }) {
    console.error('[ErrorBoundary] Caught:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center p-8" style={{ background: "#071A2E", fontFamily: "DM Sans, sans-serif" }}>
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6" style={{ background: "rgba(239,68,68,0.2)", border: "1px solid rgba(239,68,68,0.3)" }}>
            <span style={{ fontSize: 32 }}>!</span>
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: "#E8F4FD", marginBottom: 8 }}>Une erreur est survenue</h2>
          <p style={{ fontSize: 15, color: "#FCA5A5", textAlign: "center", maxWidth: 400, marginBottom: 4 }}>{this.state.error?.message || "Erreur inattendue"}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-6 px-6 py-3 rounded-xl text-white font-bold transition-all active:scale-95"
            style={{ background: "linear-gradient(135deg,#1A7FD4,#14B8A6)" }}>
            Réessayer
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
