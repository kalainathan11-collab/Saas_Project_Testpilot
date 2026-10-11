import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { StatusBadge } from '../components/ui/Badge'
import { DataTable, type Column } from '../components/ui/DataTable'
import { fieldControlClass } from '../components/ui/FormField'
import { GradientButton } from '../components/ui/GradientButton'
import { useProject } from '../hooks/useProject'
import {
  apiErrorMessage,
  deleteTestRun,
  listProjectsForSelect,
  listTestRuns,
  progressPct,
  type TestRunSummary,
} from '../services/testRunService'
import { TEST_RUN_STATUSES, type Project, type TestRunStatus } from '../types'

export default function TestRunListPage() {
  const navigate = useNavigate()
  const { projectId } = useProject()
  const [runs, setRuns] = useState<TestRunSummary[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [q, setQ] = useState('')
  const [status, setStatus] = useState<TestRunStatus | ''>('')
  const [projectFilter, setProjectFilter] = useState<number | null>(projectId)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [confirmId, setConfirmId] = useState<number | null>(null)

  useEffect(() => {
    setProjectFilter(projectId)
  }, [projectId])

  useEffect(() => {
    listProjectsForSelect()
      .then(setProjects)
      .catch(() => setProjects([]))
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setRuns(await listTestRuns({ project_id: projectFilter, status, q: q.trim() }))
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to load test runs'))
    } finally {
      setLoading(false)
    }
  }, [projectFilter, status, q])

  useEffect(() => {
    const t = setTimeout(() => void load(), 250)
    return () => clearTimeout(t)
  }, [load])

  async function handleDelete(id: number) {
    try {
      await deleteTestRun(id)
      setRuns((prev) => prev.filter((r) => r.id !== id))
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to delete test run'))
    } finally {
      setConfirmId(null)
    }
  }

  const projectName = (id: number) => projects.find((p) => p.id === id)?.name ?? `Project ${id}`

  const columns: Column<TestRunSummary>[] = [
    { key: 'id', header: 'ID', render: (r) => <span className="font-mono text-xs">RUN-{r.id}</span> },
    { key: 'name', header: 'Name', render: (r) => <span className="font-medium text-slate-900">{r.name}</span> },
    { key: 'project', header: 'Project', render: (r) => projectName(r.project_id) },
    { key: 'assignee', header: 'Assignee', render: (r) => r.assignee ?? '-' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
    {
      key: 'progress',
      header: 'Progress',
      className: 'min-w-40',
      render: (r) => {
        const pct = progressPct(r.executed, r.total_cases)
        return (
          <div>
            <progress
              className="h-2 w-full overflow-hidden rounded-full accent-brand-600"
              value={pct}
              max={100}
              aria-label={`${r.name} progress`}
            />
            <p className="mt-1 text-xs text-slate-500">
              {r.executed}/{r.total_cases} executed ({pct}%)
            </p>
          </div>
        )
      },
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (r) =>
        confirmId === r.id ? (
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <span className="text-xs text-slate-600">Delete?</span>
            <GradientButton variant="danger" className="!px-3 !py-1" onClick={() => void handleDelete(r.id)}>
              Confirm
            </GradientButton>
            <GradientButton variant="secondary" className="!px-3 !py-1" onClick={() => setConfirmId(null)}>
              Cancel
            </GradientButton>
          </div>
        ) : (
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <GradientButton className="!px-3 !py-1" onClick={() => navigate(`/testruns/${r.id}`)}>
              Execute
            </GradientButton>
            <Link to={`/testruns/${r.id}/edit`} className="text-xs font-medium text-brand-600 hover:underline">
              Edit
            </Link>
            <button
              type="button"
              className="text-xs font-medium text-red-600 hover:underline"
              onClick={() => setConfirmId(r.id)}
            >
              Delete
            </button>
          </div>
        ),
    },
  ]

  return (
    <PageWrapper
      title="Test Runs"
      subtitle="Plan and execute test runs"
      actions={<GradientButton onClick={() => navigate('/testruns/new')}>New test run</GradientButton>}
    >
      <div className="mb-4 flex flex-wrap gap-3">
        <input
          type="search"
          aria-label="Search test runs"
          placeholder="Search test runs..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={`${fieldControlClass} max-w-xs`}
        />
        <select
          aria-label="Filter by status"
          value={status}
          onChange={(e) => setStatus(e.target.value as TestRunStatus | '')}
          className={`${fieldControlClass} max-w-44`}
        >
          <option value="">All statuses</option>
          {TEST_RUN_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          aria-label="Filter by project"
          value={projectFilter ?? ''}
          onChange={(e) => setProjectFilter(e.target.value ? Number(e.target.value) : null)}
          className={`${fieldControlClass} max-w-52`}
        >
          <option value="">All projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>
      {error && (
        <p role="alert" className="mb-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}
      <DataTable
        columns={columns}
        rows={runs}
        rowKey={(r) => r.id}
        isLoading={loading}
        onRowClick={(r) => navigate(`/testruns/${r.id}`)}
        emptyTitle="No test runs"
        emptyDescription="Create a test run to start executing test cases."
      />
    </PageWrapper>
  )
}
