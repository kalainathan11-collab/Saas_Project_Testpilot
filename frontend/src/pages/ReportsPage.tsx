import { useEffect, useState } from 'react'
import { Bar } from 'react-chartjs-2'
import type { ChartOptions } from 'chart.js'
import '../lib/theme'
import { PageWrapper } from '../components/layout/PageWrapper'
import { GlassCard } from '../components/ui/GlassCard'
import { GradientButton } from '../components/ui/GradientButton'
import { DataTable, type Column } from '../components/ui/DataTable'
import { useProject } from '../hooks/useProject'
import { useTheme } from '../hooks/useTheme'
import { chartColors } from '../lib/chart'
import {
  downloadReportCsv,
  getProjectReports,
  type ProjectReportRow,
} from '../services/dashboardService'

function Progress({ pct }: { pct: number }) {
  const value = Math.max(0, Math.min(100, pct))
  return (
    <div className="flex items-center gap-2">
      <div
        className="h-2 w-28 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <progress className="sr-only" value={value} max={100} />
        <div className="h-full rounded-full bg-brand-500" style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs tabular-nums text-slate-600">{value}%</span>
    </div>
  )
}

const columns: Column<ProjectReportRow>[] = [
  { key: 'project', header: 'Project', render: (r) => <span className="font-medium">{r.project}</span> },
  { key: 'requirements', header: 'Requirements', render: (r) => r.requirements },
  { key: 'test_cases', header: 'Test cases', render: (r) => r.test_cases },
  { key: 'coverage', header: 'Coverage', render: (r) => <Progress pct={r.coverage_pct} /> },
  { key: 'runs', header: 'Runs', render: (r) => r.runs },
  { key: 'executed', header: 'Executed', render: (r) => r.executed },
  { key: 'pass_rate', header: 'Pass rate', render: (r) => `${r.pass_rate}%` },
  { key: 'open_defects', header: 'Open defects', render: (r) => r.open_defects },
  { key: 'defects', header: 'Defects', render: (r) => r.defects },
]

export default function ReportsPage() {
  const { projectId } = useProject()
  const { theme } = useTheme()
  const [rows, setRows] = useState<ProjectReportRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getProjectReports(projectId)
      .then((r) => {
        if (!cancelled) setRows(r)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load report data.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  async function handleExport() {
    setExporting(true)
    setError(null)
    try {
      const blob = await downloadReportCsv(projectId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'testpilot-report.csv'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch {
      setError('CSV export failed.')
    } finally {
      setExporting(false)
    }
  }

  const colors = chartColors(theme)
  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: colors.text }, grid: { color: colors.grid } },
      y: { min: 0, max: 100, ticks: { color: colors.text }, grid: { color: colors.grid } },
    },
  }

  return (
    <PageWrapper
      title="Reports"
      subtitle="Pass rate, coverage and defects per project"
      actions={
        <GradientButton onClick={handleExport} disabled={exporting || loading}>
          {exporting ? 'Exporting...' : 'Export CSV'}
        </GradientButton>
      }
    >
      {error && (
        <p role="alert" className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      <div className="space-y-6">
        <DataTable
          columns={columns}
          rows={rows}
          rowKey={(r) => r.project_id}
          isLoading={loading}
          emptyTitle="No report data"
          emptyDescription="Create a project with test cases to see reports."
        />
        {!loading && rows.length > 0 && (
          <GlassCard static>
            <h2 className="mb-3 text-sm font-semibold text-slate-900">Pass rate by project (%)</h2>
            <div className="h-64">
              <Bar
                data={{
                  labels: rows.map((r) => r.project),
                  datasets: [
                    {
                      label: 'Pass rate %',
                      data: rows.map((r) => r.pass_rate),
                      backgroundColor: '#16a34a',
                      borderRadius: 6,
                    },
                  ],
                }}
                options={options}
              />
            </div>
          </GlassCard>
        )}
      </div>
    </PageWrapper>
  )
}
