export function HealthScoreRing({ score }: { score: number }) {
  const r = 70, c = 2 * Math.PI * r
  const dash = (score / 100) * c
  const color = score >= 80 ? "#22C55E" : score >= 60 ? "#F59E0B" : "#EF4444"
  return (
    <div className="relative flex items-center justify-center" style={{ width: 180, height: 180 }}>
      <svg width="180" height="180" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="90" cy="90" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
        <circle cx="90" cy="90" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={`${dash} ${c}`} strokeLinecap="round"
          style={{ transition: "stroke-dasharray 1.5s ease", filter: `drop-shadow(0 0 8px ${color}80)` }} />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span style={{ fontSize: 42, fontWeight: 800, color, lineHeight: 1, fontFamily: "DM Sans" }}>{score}</span>
        <span style={{ fontSize: 13, color: "#7FB3D3", fontWeight: 500, letterSpacing: "0.1em" }}>/ 100</span>
      </div>
    </div>
  )
}
