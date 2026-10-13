import { statusColor } from "../data/utils"

export function BiomarkerGauge({ value, min, max, status }: { value: number; min: number; max: number; status: string }) {
  const range = (max * 1.5) - (min * 0.5)
  if (range === 0) return null
  const pct = Math.min(Math.max((value - min * 0.5) / range, 0), 1) * 100
  const normalStart = ((min - min * 0.5) / range) * 100
  const normalEnd = ((max - min * 0.5) / range) * 100
  const color = statusColor(status)
  return (
    <div className="w-full">
      <div className="relative h-3 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.08)" }}>
        <div className="absolute h-full rounded-full opacity-40"
          style={{ left: `${normalStart}%`, width: `${normalEnd - normalStart}%`, background: "#22C55E" }} />
        <div className="absolute h-full rounded-full transition-all duration-1000"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}80, ${color})`, boxShadow: `0 0 8px ${color}` }} />
        <div className="absolute top-0 bottom-0 w-0.5 rounded-full"
          style={{ left: `${pct}%`, background: color, boxShadow: `0 0 6px ${color}` }} />
      </div>
    </div>
  )
}
