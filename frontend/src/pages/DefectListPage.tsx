import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { DataTable, type Column } from '../components/ui/DataTable'
import { fieldControlClass } from '../components/ui/FormField'
import { GradientButton } from '../components/ui/GradientButton'
import { StatusBadge } from '../components/ui/Badge'
import { useProject } from '../hooks/useProject'
import {
  defectDisplayId,
  deleteDefect,
  errorMessage,
  listDefects,
  listProjectOptions,
} from '../services/defectService'
import {
  DEFECT_STATUSES,
  SEVERITIES,
  type Defect,
  type DefectStatus,
  type Project,
  type Severity,
} from '../types'

export default function DefectListPage() {
  const navigate = useNavigate()
  const { projectId } = useProject()
  const [defects, setDefects] = useState<Defect[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [search, setSearch] = useState('')
  const [projectFilter, setProjectFilter] = useState<string>(projectId ? String(projectId) : '')
  const [severity, setSeverity] = useState<Severity | ''>('')
  const [status, setStatus] = useState<DefectStatus | ''>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [confirmId, setConfirmId] = useState<number | null>(null)

  useEffect(() => {
    setProjectFilter(projectId ? String(projectId) : '')
  }, [projectId])

  useEffect(() => {
    listProjectOptions()
      .then(setProjects)
      .catch(() => setProjects([]))
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setDefects(
        await listDefects({
          project_id: projectFilter ? Number(projectFilter) : null,
          severity,
          status,
          q: search,
        }),
      )
    } catch (err) {
      setError(errorMessage(err, 'Failed to load defects'))
    } finally {
      setLoading(false)
    }
  }, [projectFilter, severity, status, search])

  useEffect(() => {
    const timer = setTimeout(() => void load(), 250)
    return () => clearTimeout(timer)
  }, [load])

  async function handleDelete(id: number) {
    try {
      await deleteDefect(id)
      setConfirmId(null)
      await load()
    } catch (err) {
      setError(errorMessage(err, 'Failed to delete defect'))
    }
  }

  const projectName = (id: number) => projects.find((p) => p.id === id)?.name ?? `#${id}`

  const columns: Column<Defect>[] = [
    { key: 'id', header: 'ID', render: (d) => defectDisplayId(d.id), className: 'whitespace-nowrap font-mono' },
    { key: 'title', header: 'Title', render: (d) => <span className="font-medium text-slate-900">{d.title}</span> },
    { key: 'project', header: 'Project', render: (d) => projectName(d.project_id) },
    { key: 'severity', header: 'Severity', render: (d) => <StatusBadge value={d.severity} /> },
    { key: 'status', header: 'Status', render: (d) => <StatusBadge value={d.status} /> },
    { key: 'assignee', header: 'Assignee', render: (d) => d.assignee ?? '-' },
    {
      key: 'actions',
      header: 'Actions',
      render: (d) =>
        confirmId === d.id ? (
          <span className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <span className="text-xs text-slate-600">Delete?</span>
            <GradientButton variant="danger" className="px-3 py-1 text-xs" onClick={() => void handleDelete(d.id)}>
              Confirm
            </GradientButton>
            <GradientButton variant="secondary" className="px-3 py-1 text-xs" onClick={() => setConfirmId(null)}>
              Cancel
            </GradientButton>
          </span>
        ) : (
          <span className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <Link to={`/defects/${d.id}/edit`} className="text-sm font-medium text-brand-600 hover:underline">
              Edit
            </Link>
            <button
              type="button"
              className="text-sm font-medium text-red-600 hover:underline"
              onClick={() => setConfirmId(d.id)}
            >
              Delete
            </button>
          </span>
        ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Defects</h1>
          <p className="text-sm text-slate-500">Track and triage bugs found during testing</p>
        </div>
        <GradientButton onClick={() => navigate('/defects/new')}>New defect</GradientButton>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <input
          type="search"
          aria-label="Search defects"
          placeholder="Search defects..."
          className={fieldControlClass}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          aria-label="Filter by project"
          className={fieldControlClass}
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
        >
          <option value="">All projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <select
          aria-label="Filter by severity"
          className={fieldControlClass}
          value={severity}
          onChange={(e) => setSeverity(e.target.value as Severity | '')}
        >
          <option value="">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <select
          aria-label="Filter by status"
          className={fieldControlClass}
          value={status}
          onChange={(e) => setStatus(e.target.value as DefectStatus | '')}
        >
          <option value="">All statuses</option>
          {DEFECT_STATUSES.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </div>

      {error && (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <DataTable
        columns={columns}
        rows={defects}
        rowKey={(d) => d.id}
        isLoading={loading}
        onRowClick={(d) => navigate(`/defects/${d.id}`)}
        emptyTitle="No defects found"
        emptyDescription="Log a defect from a test run or create one manually."
      />
    </div>
  )
}
