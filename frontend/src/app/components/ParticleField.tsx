export function ParticleField() {
  const particles = Array.from({ length: 40 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 3 + 1,
    dur: Math.random() * 12 + 8,
    delay: Math.random() * 8,
    opacity: Math.random() * 0.4 + 0.1,
  }))
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <svg className="absolute inset-0 w-full h-full">
        <defs>
          <radialGradient id="bgGrad" cx="30%" cy="40%">
            <stop offset="0%" stopColor="#1A3A5C" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#071A2E" stopOpacity="1" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#bgGrad)" />
        {particles.map(p => (
          <circle key={p.id} cx={`${p.x}%`} cy={`${p.y}%`} r={p.size}
            fill="#1A7FD4" opacity={p.opacity}>
            <animate attributeName="opacity" values={`${p.opacity};${p.opacity * 2};${p.opacity}`}
              dur={`${p.dur}s`} begin={`${p.delay}s`} repeatCount="indefinite" />
            <animate attributeName="cy" values={`${p.y}%;${p.y - 3}%;${p.y}%`}
              dur={`${p.dur}s`} begin={`${p.delay}s`} repeatCount="indefinite" />
          </circle>
        ))}
        <line x1="0" y1="40%" x2="100%" y2="40%" stroke="rgba(26,127,212,0.06)" strokeWidth="1" />
        <line x1="30%" y1="0" x2="30%" y2="100%" stroke="rgba(20,184,166,0.05)" strokeWidth="1" />
      </svg>
    </div>
  )
}
