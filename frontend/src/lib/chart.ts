import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js'
import type { Theme } from './theme'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

export const RESULT_COLORS = {
  Passed: '#16a34a',
  Failed: '#dc2626',
  Blocked: '#d97706',
  Skipped: '#6b7280',
} as const

export const SEVERITY_COLORS = {
  Minor: '#6b7280',
  Major: '#d97706',
  Critical: '#dc2626',
  Blocker: '#7f1d1d',
} as const

export function chartColors(theme: Theme): { text: string; grid: string } {
  return theme === 'dark'
    ? { text: '#e2e8f0', grid: 'rgba(148,163,184,0.25)' }
    : { text: '#334155', grid: 'rgba(100,116,139,0.18)' }
}
