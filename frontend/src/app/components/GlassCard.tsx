import type { ReactNode } from "react"

export function GlassCard({ children, className = "", onClick, style }: {
  children: ReactNode
  className?: string
  onClick?: () => void
  style?: React.CSSProperties
}) {
  return (
    <div onClick={onClick} className={`relative rounded-2xl border border-white/10 overflow-hidden ${onClick ? "cursor-pointer active:scale-[0.98] transition-transform" : ""} ${className}`}
      style={{ background: "rgba(255,255,255,0.05)", backdropFilter: "blur(20px)", boxShadow: "0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)", ...style }}>
      {children}
    </div>
  )
}
