const sizeMap = {
  sm: { w: 64, h: 38 },
  md: { w: 100, h: 60 },
  lg: { w: 160, h: 96 },
  xl: { w: 220, h: 133 },
}

const labelMap = {
  ipa: { white: "/logo-ipa-white-processed.png", color: "/logo-ipa.png", mask: "/logo-ipa-white-processed.png", alt: "Institut Pasteur" },
  siha: { white: "/siha-white-processed.png", color: "/siha.jpg", mask: "/siha-white-processed.png", alt: "SIHA" },
}

export function IpaLogo({
  variant = "white",
  size = "md",
  type = "ipa",
  className = "",
}: {
  variant?: "white" | "color" | "mask"
  size?: "sm" | "md" | "lg" | "xl"
  type?: "ipa" | "siha"
  className?: string
}) {
  const dims = sizeMap[size]
  const info = labelMap[type]

  if (variant === "mask") {
    return (
      <div
        className={className}
        style={{
          width: dims.w,
          height: dims.h,
          background: "var(--primary)",
          mask: `url(${info.mask}) no-repeat center/contain`,
          WebkitMask: `url(${info.mask}) no-repeat center/contain`,
        }}
        aria-label={info.alt}
      />
    )
  }

  const src = variant === "white" ? info.white : info.color

  return (
    <img
      src={src}
      alt={info.alt}
      className={className}
      style={{ width: dims.w, height: dims.h, objectFit: "contain" }}
      loading="eager"
    />
  )
}
