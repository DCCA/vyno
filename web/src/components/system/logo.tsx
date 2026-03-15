import { cn } from "@/lib/utils"

type LogoVariant = "prism" | "signal" | "cascade"

interface VynoMarkProps {
  size?: number
  variant?: LogoVariant
  className?: string
}

const gradientDef = (id: string) => (
  <defs>
    <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stopColor="#6366F1" />
      <stop offset="100%" stopColor="#8B5CF6" />
    </linearGradient>
  </defs>
)

function PrismMark({ size, id }: { size: number; id: string }) {
  return (
    <svg viewBox="0 0 32 32" width={size} height={size} fill="none" xmlns="http://www.w3.org/2000/svg">
      {gradientDef(id)}
      <rect x="1" y="1" width="30" height="30" rx="7" fill={`url(#${id})`} />
      <path d="M9 8L16 24L23 8" stroke="white" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function SignalMark({ size, id }: { size: number; id: string }) {
  return (
    <svg viewBox="0 0 32 32" width={size} height={size} fill="none" xmlns="http://www.w3.org/2000/svg">
      {gradientDef(id)}
      <path d="M7 6C7 6 11 16 16 25C21 16 25 6 25 6" stroke={`url(#${id})`} strokeWidth="3.5" strokeLinecap="round" />
      <circle cx="16" cy="27" r="2" fill={`url(#${id})`} />
    </svg>
  )
}

function CascadeMark({ size, id }: { size: number; id: string }) {
  return (
    <svg viewBox="0 0 32 32" width={size} height={size} fill="none" xmlns="http://www.w3.org/2000/svg">
      {gradientDef(id)}
      <rect x="1" y="1" width="30" height="30" rx="7" fill={`url(#${id})`} />
      <rect x="7" y="4" width="18" height="13" rx="2.5" stroke="rgba(255,255,255,0.35)" strokeWidth="1.2" />
      <rect x="6" y="7" width="18" height="13" rx="2.5" stroke="rgba(255,255,255,0.55)" strokeWidth="1.2" />
      <rect x="5" y="10" width="22" height="16" rx="3" fill="rgba(255,255,255,0.15)" stroke="white" strokeWidth="1.2" />
      <path d="M11 14L16 23L21 14" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

const variants: Record<LogoVariant, typeof PrismMark> = {
  prism: PrismMark,
  signal: SignalMark,
  cascade: CascadeMark,
}

export function VynoMark({ size = 28, variant = "prism", className }: VynoMarkProps) {
  const id = `vyno-g-${variant}`
  const Mark = variants[variant]
  return (
    <span className={cn("inline-flex shrink-0", className)}>
      <Mark size={size} id={id} />
    </span>
  )
}

interface VynoWordmarkProps {
  size?: number
  variant?: LogoVariant
  className?: string
}

export function VynoWordmark({ size = 28, variant = "prism", className }: VynoWordmarkProps) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <VynoMark size={size} variant={variant} />
      <span className="font-display text-sm font-semibold tracking-tight">Vyno</span>
    </span>
  )
}
