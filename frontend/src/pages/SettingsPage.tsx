import '../lib/theme'
import { PageWrapper } from '../components/layout/PageWrapper'
import { GlassCard } from '../components/ui/GlassCard'
import { useTheme } from '../hooks/useTheme'

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <PageWrapper title="Settings" subtitle="Theme and project defaults">
      <GlassCard static className="max-w-xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Dark mode</h2>
            <p className="text-sm text-slate-500">Currently using the {theme} theme.</p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={isDark}
            aria-label="Toggle dark mode"
            onClick={() => setTheme(isDark ? 'light' : 'dark')}
            className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
              isDark ? 'bg-brand-600' : 'bg-slate-300'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                isDark ? 'translate-x-5' : ''
              }`}
            />
          </button>
        </div>
      </GlassCard>
    </PageWrapper>
  )
}
