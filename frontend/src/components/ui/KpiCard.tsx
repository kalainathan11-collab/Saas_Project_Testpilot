import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'
import { GlassCard } from './GlassCard'

type Accent = 'brand' | 'green' | 'red' | 'amber'

const accents: Record<Accent, string> = {
  brand: 'text-brand-600',
  green: 'text-emerald-600',
  red: 'text-red-600',
  amber: 'text-amber-600',
}

interface KpiCardProps {
  label: string
  value: ReactNode
  hint?: string
  accent?: Accent
}

export function KpiCard({ label, value, hint, accent = 'brand' }: KpiCardProps) {
  return (
    <GlassCard>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={cn('mt-2 text-3xl font-bold', accents[accent])}>{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </GlassCard>
  )
}
