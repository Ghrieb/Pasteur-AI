import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from "recharts"

interface TestData {
  test_name: string
  code: string
  value?: number | null
  unit: string
  abnormal: boolean
  range?: { comparator?: string; min?: number | null; max?: number | null }
  category?: string
  dashboard_group?: string
}

export function HealthRadarChart({ tests }: { tests: TestData[] }) {
  const groups: Record<string, { total: number; abnormal: number }> = {}
  tests.forEach((t) => {
    const g = t.dashboard_group || t.category || "Autres"
    if (!groups[g]) groups[g] = { total: 0, abnormal: 0 }
    groups[g].total++
    if (t.abnormal) groups[g].abnormal++
  })

  const data = Object.entries(groups).map(([key, val]) => ({
    category: key,
    health: Math.round(((val.total - val.abnormal) / val.total) * 100),
    abnormal: val.abnormal,
  }))

  return (
    <div className="w-full flex flex-col items-center">
      <div style={{ width: 340, height: 340 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid stroke="rgba(255,255,255,0.08)" />
            <PolarAngleAxis dataKey="category" tick={{ fill: "#7FB3D3", fontSize: 12 }} />
            <Radar name="Santé" dataKey="health" stroke="#1A7FD4" fill="#1A7FD4" fillOpacity={0.2} strokeWidth={2} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <p style={{ fontSize: 13, color: "#7FB3D3", marginTop: 8 }}>
        {data.filter((d) => d.abnormal > 0).length} catégorie{data.filter((d) => d.abnormal > 0).length > 1 ? "s" : ""} avec anomalies
      </p>
    </div>
  )
}
