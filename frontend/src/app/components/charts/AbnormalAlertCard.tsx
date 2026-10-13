import { AlertTriangle, ChevronDown } from "lucide-react"
import { useState } from "react"

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

function severity(value: number | null | undefined, min?: number | null, max?: number | null): "critical" | "warning" | "info" {
  if (value == null) return "info"
  if (max != null && value > max * 1.5) return "critical"
  if (min != null && value < min * 0.5) return "critical"
  if (max != null && value > max * 1.2) return "warning"
  if (min != null && value < min * 0.8) return "warning"
  return "info"
}

const LEVEL_META = {
  critical: { label: "Critique", badgeClass: "badge-danger" },
  warning: { label: "Anormal", badgeClass: "badge-warning" },
  info: { label: "Alerte", badgeClass: "badge-info" },
} as const

const LEVEL_COLORS = {
  critical: { bg: "var(--danger-subtle)", border: "var(--danger)", text: "var(--danger)" },
  warning: { bg: "var(--warning-subtle)", border: "var(--warning)", text: "var(--warning)" },
  info: { bg: "var(--info-subtle)", border: "var(--info)", text: "var(--info)" },
} as const

export function AbnormalAlertCard({ tests, onSelectCategory }: { tests: TestData[]; onSelectCategory?: (category: string) => void }) {
  const abnormal = tests.filter((t) => t.abnormal)
  const critical = abnormal.filter((t) => severity(t.value, t.range?.min, t.range?.max) === "critical")
  const warnings = abnormal.filter((t) => severity(t.value, t.range?.min, t.range?.max) === "warning")
  const infos = abnormal.filter((t) => severity(t.value, t.range?.min, t.range?.max) === "info")
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})

  if (abnormal.length === 0) return null

  const groups: { key: string; level: "critical" | "warning" | "info"; items: TestData[] }[] = [
    { key: "critical", level: "critical", items: critical },
    { key: "warning", level: "warning", items: warnings },
    { key: "info", level: "info", items: infos },
  ].filter(g => g.items.length > 0)

  return (
    <div className="w-full animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "var(--danger-subtle)" }}>
          <AlertTriangle className="w-5 h-5" style={{ color: "var(--danger)" }} />
        </div>
        <h3 className="text-xl font-bold" style={{ color: "var(--foreground)" }}>
          {abnormal.length} anomalie{abnormal.length > 1 ? "s" : ""}
        </h3>
      </div>

      {/* summary stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="relative rounded-2xl border overflow-hidden p-4 flex flex-col gap-1"
          style={{ background: "var(--danger-subtle)", borderColor: "var(--danger-border)" }}>
          <span className="text-sm font-medium" style={{ color: "var(--danger)" }}>Critiques</span>
          <span className="text-3xl font-extrabold font-mono" style={{ color: "var(--danger)" }}>{critical.length}</span>
        </div>
        <div className="relative rounded-2xl border overflow-hidden p-4 flex flex-col gap-1"
          style={{ background: "var(--warning-subtle)", borderColor: "var(--warning-border)" }}>
          <span className="text-sm font-medium" style={{ color: "var(--warning)" }}>Anormaux</span>
          <span className="text-3xl font-extrabold font-mono" style={{ color: "var(--warning)" }}>{warnings.length}</span>
        </div>
        <div className="relative rounded-2xl border overflow-hidden p-4 flex flex-col gap-1"
          style={{ background: "var(--info-subtle)", borderColor: "var(--info-border)" }}>
          <span className="text-sm font-medium" style={{ color: "var(--info)" }}>Alertes</span>
          <span className="text-3xl font-extrabold font-mono" style={{ color: "var(--info)" }}>{infos.length}</span>
        </div>
      </div>

      {/* grouped anomaly list */}
      <div className="flex flex-col gap-4">
        {groups.map(({ key, level, items }) => {
          const meta = LEVEL_META[level]
          const colors = LEVEL_COLORS[level]
          const isCollapsed = collapsed[key]

          return (
            <div key={key} className="animate-slide-up">
              <button onClick={() => setCollapsed(prev => ({ ...prev, [key]: !prev[key] }))}
                className="flex items-center gap-2 mb-2 w-full text-left">
                <ChevronDown className="w-4 h-4 transition-transform duration-200"
                  style={{ transform: isCollapsed ? "rotate(-90deg)" : "none", color: "var(--foreground-muted)" }} />
                <span className="text-sm font-semibold uppercase tracking-wider" style={{ color: colors.text }}>
                  {meta.label} ({items.length})
                </span>
              </button>

              {!isCollapsed && (
                <div className="flex flex-col gap-2">
                  {items.map((t, i) => (
                    <AlertRow key={`${key}-${i}`} test={t} level={level} onClick={() => onSelectCategory?.(t.dashboard_group || t.category || "")} />
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function AlertRow({ test, level, onClick }: { test: TestData; level: "critical" | "warning" | "info"; onClick: () => void }) {
  const colors = LEVEL_COLORS[level]
  const meta = LEVEL_META[level]

  const rangeStr = () => {
    const r = test.range
    if (!r) return ""
    if (r.comparator === "<") return `< ${r.max ?? ""}`
    if (r.comparator === ">") return `> ${r.min ?? ""}`
    if (r.min != null && r.max != null) return `${r.min} - ${r.max}`
    return ""
  }

  const valStr = test.value_display || test.value?.toString() || "N/A"

  return (
    <button
      className="w-full flex items-center gap-4 p-4 rounded-xl active:scale-[0.98] transition-all duration-150"
      style={{ background: colors.bg, borderLeft: `4px solid ${colors.border}` }}
      onClick={onClick}
    >
      <span className="text-2xl font-bold font-mono" style={{ color: colors.text, minWidth: 80 }}>{valStr}</span>
      <div className="flex-1 text-left">
        <span className="text-base font-semibold" style={{ color: "var(--foreground)" }}>{test.test_name}</span>
        <span className="text-sm block" style={{ color: "var(--foreground-muted)" }}>
          Norme: {rangeStr()} {test.unit}
        </span>
      </div>
      <span className={meta.badgeClass}>{meta.label}</span>
    </button>
  )
}
