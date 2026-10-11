import { useEffect, useState } from 'react'
import { Bar, Doughnut } from 'react-chartjs-2'
import type { ChartOptions } from 'chart.js'
import '../lib/theme'
import { PageWrapper } from '../components/layout/PageWrapper'
import { KpiCard } from '../components/ui/KpiCard'
import { GlassCard } from '../components/ui/GlassCard'
import { EmptyState } from '../components/ui/EmptyState'
import { StatusBadge } from '../components/ui/Badge'
import { useProject } from '../hooks/useProject'
import { useTheme } from '../hooks/useTheme'
import { chartColors, RESULT_COLORS, SEVERITY_COLORS } from '../lib/chart'
import { getDashboardSummary, type DashboardSummary } from '../services/dashboardService'
import { RESULT_STATUSES, SEVERITIES } from '../types'

export default function DashboardPage() {
  const { projectId } = useProject()
  const { theme } = useTheme()
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getDashboardSummary(projectId)
      .then((d) => {
        if (!cancelled) setData(d)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load dashboard data.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  const colors = chartColors(theme)
  const axis = { ticks: { color: colors.text, precision: 0 }, grid: { color: colors.grid } }
  const barOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { x: axis, y: { ...axis, beginAtZero: true } },
  }
  const runOptions: ChartOptions<'bar'> = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { x: { ...axis, min: 0, max: 100 }, y: axis },
  }
  const doughnutOptions: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom', labels: { color: colors.text } } },
  }

  let body
  if (loading) {
    body = <p className="p-8 text-center text-sm text-slate-500">Loading dashboard...</p>
  } else if (error || !data) {
    body = <EmptyState title="Dashboard unavailable" description={error ?? 'No data returned.'} />
  } else {
    const totalResults = RESULT_STATUSES.reduce((s, k) => s + data.results[k], 0)
    const totalDefects = SEVERITIES.reduce((s, k) => s + data.defects_by_severity[k], 0)
    body = (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard label="Test cases" value={data.test_cases} />
          <KpiCard label="Test runs" value={data.test_runs} hint={`${data.executed} results executed`} />
          <KpiCard label="Pass rate" value={`${data.pass_rate}%`} accent="green" />
          <KpiCard label="Open defects" value={data.open_defects} accent="red" />
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <GlassCard static>
            <h2 className="mb-3 text-sm font-semibold text-slate-900">Test results</h2>
            {totalResults === 0 ? (
              <p className="py-12 text-center text-sm text-slate-500">No results executed yet.</p>
            ) : (
              <div className="h-64">
                <Doughnut
                  data={{
                    labels: [...RESULT_STATUSES],
                    datasets: [
                      {
                        data: RESULT_STATUSES.map((k) => data.results[k]),
                        backgroundColor: RESULT_STATUSES.map((k) => RESULT_COLORS[k]),
                        borderWidth: 0,
                      },
                    ],
                  }}
                  options={doughnutOptions}
                />
              </div>
            )}
          </GlassCard>

          <GlassCard static>
            <h2 className="mb-3 text-sm font-semibold text-slate-900">Defects by severity</h2>
            {totalDefects === 0 ? (
              <p className="py-12 text-center text-sm text-slate-500">No defects logged.</p>
            ) : (
              <div className="h-64">
                <Bar
                  data={{
                    labels: [...SEVERITIES],
                    datasets: [
                      {
                        label: 'Defects',
                        data: SEVERITIES.map((k) => data.defects_by_severity[k]),
                        backgroundColor: SEVERITIES.map((k) => SEVERITY_COLORS[k]),
                        borderRadius: 6,
                      },
                    ],
                  }}
                  options={barOptions}
                />
              </div>
            )}
          </GlassCard>

          <GlassCard static>
            <h2 className="mb-3 text-sm font-semibold text-slate-900">Run progress (%)</h2>
            {data.runs.length === 0 ? (
              <p className="py-12 text-center text-sm text-slate-500">No test runs yet.</p>
            ) : (
              <div className="h-64">
                <Bar
                  data={{
                    labels: data.runs.map((r) => r.name),
                    datasets: [
                      {
                        label: 'Progress %',
                        data: data.runs.map((r) => r.progress_pct),
                        backgroundColor: '#6366f1',
                        borderRadius: 6,
                      },
                    ],
                  }}
                  options={runOptions}
                />
              </div>
            )}
          </GlassCard>

          <GlassCard static>
            <h2 className="mb-3 text-sm font-semibold text-slate-900">Recent defects</h2>
            {data.recent_defects.length === 0 ? (
              <p className="py-12 text-center text-sm text-slate-500">No defects yet.</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {data.recent_defects.map((d) => (
                  <li key={d.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                    <span className="min-w-0 truncate text-slate-700">
                      <span className="mr-2 font-mono text-xs text-slate-500">BUG-{d.id}</span>
                      {d.title}
                    </span>
                    <span className="flex shrink-0 gap-1.5">
                      <StatusBadge value={d.severity} />
                      <StatusBadge value={d.status} />
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </GlassCard>
        </div>
      </div>
    )
  }

  return (
    <PageWrapper title="Dashboard" subtitle="KPIs, results and recent defects">
      {body}
    </PageWrapper>
  )
}
