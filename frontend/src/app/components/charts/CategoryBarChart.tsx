import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell, 
  ReferenceLine,
  CartesianGrid
} from "recharts"

interface TestData {
  test_name: string
  code: string
  value?: number | null
  value_display?: string
  unit: string
  abnormal: boolean
  range?: { comparator?: string; min?: number | null; max?: number | null }
  category?: string
  dashboard_group?: string
}

// Custom Tooltip for pixel-perfect UI control
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    const inRange = d.raw >= d.min && d.raw <= d.max;
    
    return (
      <div 
        className="p-3 shadow-xl flex flex-col gap-1.5" 
        style={{ 
          background: "var(--background-elevated)", 
          border: "1px solid var(--primary-border)", 
          borderRadius: "var(--radius-xl)",
          minWidth: "200px"
        }}
      >
        <div className="text-sm font-medium pb-1 border-b" style={{ color: "var(--foreground-muted)", borderColor: "var(--primary-border)" }}>
          {d.name}
        </div>
        <div className="flex items-baseline gap-1 mt-1">
          <span className="text-xl font-bold" style={{ color: "var(--foreground)" }}>{d.raw}</span>
          <span className="text-sm" style={{ color: "var(--foreground-muted)" }}>{d.unit}</span>
        </div>
        <div className="text-xs" style={{ color: "var(--foreground-muted)" }}>
          Norme: {d.min} – {d.max} {d.unit}
        </div>
        <div 
          className="text-xs font-semibold mt-1 flex items-center gap-1" 
          style={{ color: inRange ? "var(--success)" : "var(--danger)" }}
        >
          {inRange ? "✓ Dans les normes" : "✗ Hors norme"}
        </div>
      </div>
    );
  }
  return null;
};

export function CategoryBarChart({ category, tests }: { category: string; tests: TestData[] }) {
  const data = tests.map((t) => {
    const r = t.range
    const hasRange = r && r.min != null && r.max != null
    const val = t.value ?? 0
    const pct = hasRange && r!.max! - r!.min! > 0
      ? Math.round(((val - r!.min!) / (r!.max! - r!.min!)) * 100)
      : 50
    return {
      name: t.test_name,
      code: t.code,
      value: pct,
      raw: val,
      unit: t.unit,
      min: r?.min ?? 0,
      max: r?.max ?? 100,
    }
  })

  const values = data.map((d) => d.value)
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  // Ensures the domain has enough padding so bars don't hit the absolute edges
  const domain: [number, number] = [Math.min(-10, minValue - 10), Math.max(110, maxValue + 10)]

  return (
    <div className="w-full">
      {/* Polished Legend Area */}
      <div className="flex items-center justify-end gap-8 mb-4 px-4">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-px" style={{ borderTop: "2px dashed var(--success)", opacity: 0.8 }} />
          <span className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--foreground-muted)" }}>Limite inférieure</span>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-px" style={{ borderTop: "2px dashed var(--success)", opacity: 0.8 }} />
          <span className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--foreground-muted)" }}>Limite supérieure</span>
        </div>
      </div>

      {/* Chart Area */}
      <div style={{ height: Math.max(250, tests.length * 52) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 140, right: 40, top: 10, bottom: 10 }}>
            {/* Subtle vertical grid lines for better readability */}
            <CartesianGrid horizontal={false} stroke="var(--primary-border)" strokeDasharray="3 3" opacity={0.4} />
            
            <XAxis type="number" domain={domain} tick={false} axisLine={false} />
            <YAxis 
              type="category" 
              dataKey="name" 
              tick={{ fill: "var(--foreground-muted)", fontSize: 13, fontWeight: 500 }} 
              width={130} 
              tickLine={false}
              axisLine={{ stroke: "var(--primary-border)", opacity: 0.5 }}
            />
            
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: "var(--primary-border)", opacity: 0.15 }} // Highlights the row on hover
              wrapperStyle={{ zIndex: 9999, outline: "none" }}
            />
            
            <ReferenceLine x={0} isAnimationActive={false} stroke="var(--success)" strokeDasharray="4 4" strokeWidth={1.5} opacity={0.8} />
            <ReferenceLine x={100} isAnimationActive={false} stroke="var(--success)" strokeDasharray="4 4" strokeWidth={1.5} opacity={0.8} />
            
            <Bar 
              isAnimationActive={false} 
              dataKey="value" 
              radius={[0, 4, 4, 0]} 
              barSize={24} // Slightly thinner bars look more modern
            >
              {data.map((entry, i) => (
                <Cell 
                  key={`cell-${i}`} 
                  fill={entry.raw < entry.min || entry.raw > entry.max ? "var(--danger)" : "var(--success)"} 
                  style={{ transition: "fill 0.2s ease" }}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}