import { GlassCard } from "./GlassCard"
import { statusColor, statusBg, statusLabel, categoryStatus } from "../data/utils"
import type { Lang } from "../data/types"
import type { BiomarkerEntry } from "../data/mock-data"
import type { ReactNode } from "react"
import { Droplets, Activity, FlaskConical, Heart, Zap, Thermometer, Star, BarChart3, Shield, Crosshair, Target, Wifi, Pill, CircleDot, BatteryFull, UtensilsCrossed, AlertTriangle } from "lucide-react"

const categoryIcons: Record<string, ReactNode> = {
  blood: <Droplets className="w-6 h-6" />,
  liver: <Activity className="w-6 h-6" />,
  kidney: <FlaskConical className="w-6 h-6" />,
  heart: <Heart className="w-6 h-6" />,
  hormones: <Zap className="w-6 h-6" />,
  inflammation: <Thermometer className="w-6 h-6" />,
  vitamins: <Star className="w-6 h-6" />,
  lipids: <BarChart3 className="w-6 h-6" />,
  diabetes: <Pill className="w-6 h-6" />,
  thyroid: <Shield className="w-6 h-6" />,
  iron: <CircleDot className="w-6 h-6" />,
  bone: <Crosshair className="w-6 h-6" />,
  prostate: <Target className="w-6 h-6" />,
  wbc_diff: <Shield className="w-6 h-6" />,
  adrenal: <Zap className="w-6 h-6" />,
  coagulation: <Wifi className="w-6 h-6" />,
  electrolyte: <BatteryFull className="w-6 h-6" />,
  immunology: <Shield className="w-6 h-6" />,
  tumor: <AlertTriangle className="w-6 h-6" />,
  nutrition: <UtensilsCrossed className="w-6 h-6" />,
  toxicology: <AlertTriangle className="w-6 h-6" />,
  urine: <Droplets className="w-6 h-6" />,
  enzyme: <FlaskConical className="w-6 h-6" />,
  other: <Activity className="w-6 h-6" />,
}

const labelMap: Record<Lang, Record<string, string>> = {
  fr: { blood: "Sang", liver: "Foie", kidney: "Reins", heart: "Cœur", hormones: "Hormones", inflammation: "Inflammation", vitamins: "Vitamines", lipids: "Lipides", diabetes: "Diabète", thyroid: "Thyroïde", iron: "Fer", bone: "Os", prostate: "Prostate", wbc_diff: "Globules Blancs", adrenal: "Surrénales", coagulation: "Coagulation", electrolyte: "Électrolytes", immunology: "Immunologie", tumor: "Tumeurs", nutrition: "Nutrition", toxicology: "Toxicologie", urine: "Urine", enzyme: "Enzymes", other: "Autres" },
  ar: { blood: "الدم", liver: "الكبد", kidney: "الكلى", heart: "القلب", hormones: "الهرمونات", inflammation: "الالتهاب", vitamins: "الفيتامينات", lipids: "الدهون", diabetes: "السكري", thyroid: "الغدة الدرقية", iron: "الحديد", bone: "العظام", prostate: "البروستاتا", wbc_diff: "خلايا الدم البيضاء", adrenal: "الكظرية", coagulation: "التخثر", electrolyte: "الشوارد", immunology: "المناعة", tumor: "الأورام", nutrition: "التغذية", toxicology: "السموم", urine: "البول", enzyme: "الإنزيمات", other: "أخرى" },
  en: { blood: "Blood", liver: "Liver", kidney: "Kidney", heart: "Heart", hormones: "Hormones", inflammation: "Inflammation", vitamins: "Vitamins", lipids: "Lipids", diabetes: "Diabetes", thyroid: "Thyroid", iron: "Iron", bone: "Bone", prostate: "Prostate", wbc_diff: "White Cells", adrenal: "Adrenal", coagulation: "Coagulation", electrolyte: "Electrolytes", immunology: "Immunology", tumor: "Tumors", nutrition: "Nutrition", toxicology: "Toxicology", urine: "Urine", enzyme: "Enzymes", other: "Other" },
}

export function CategoryCard({ catKey, markers, lang, onClick }: { catKey: string; markers: BiomarkerEntry[]; lang: Lang; onClick: () => void }) {
  const s = categoryStatus(markers)
  const color = statusColor(s)
  const bg = statusBg(s)
  const abnormal = markers.filter(m => m.status !== "normal").length
  return (
    <GlassCard onClick={onClick} className="p-6 flex flex-col gap-4 hover:border-white/20 transition-all duration-300" style={{ borderColor: `${color}30` }}>
      <div className="flex items-center justify-between">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: bg, color }}>
          {categoryIcons[catKey]}
        </div>
        <div className="px-3 py-1 rounded-full font-semibold" style={{ fontSize: 12, background: bg, color, fontFamily: "JetBrains Mono" }}>
          {statusLabel[lang][s]}
        </div>
      </div>
      <div>
        <div style={{ fontSize: 20, fontWeight: 700, color: "#E8F4FD" }}>{labelMap[lang][catKey] || catKey}</div>
        <div style={{ fontSize: 14, color: "#7FB3D3", marginTop: 2 }}>{markers.length} paramètres • {abnormal > 0 ? <span style={{ color }}>{abnormal} anormal{abnormal > 1 ? "aux" : ""}</span> : <span style={{ color: "#22C55E" }}>Tous normaux</span>}</div>
      </div>
      <div className="space-y-2">
        {markers.slice(0, 2).map(m => (
          <div key={m.name} className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: statusColor(m.status) }} />
            <span style={{ fontSize: 13, color: "#7FB3D3", flex: 1 }}>{m.name}</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: statusColor(m.status), fontFamily: "JetBrains Mono" }}>{m.value} {m.unit}</span>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-1 text-blue-400 opacity-70">
        <span style={{ fontSize: 13 }}>Voir détails</span>
      </div>
    </GlassCard>
  )
}
