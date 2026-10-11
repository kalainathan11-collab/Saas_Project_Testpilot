import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { DataTable, type Column } from '../components/ui/DataTable'
import { fieldControlClass } from '../components/ui/FormField'
import { GradientButton } from '../components/ui/GradientButton'
import { StatusBadge } from '../components/ui/Badge'
import { useProject } from '../hooks/useProject'
import {
  apiErrorMessage,
  deleteProject,
  listProjects,
  type ProjectSummary,
} from '../services/projectService'
import { PROJECT_STATUSES, type ProjectStatus } from '../types'

export default function ProjectListPage() {
  const navigate = useNavigate()
  const { reload } = useProject()
  const [rows, setRows] = useState<ProjectSummary[]>([])
  const [q, setQ] = useState('')
  const [status, setStatus] = useState<ProjectStatus | ''>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendingDelete, setPendingDelete] = useState<ProjectSummary | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setRows(await listProjects({ q: q.trim(), status }))
    } catch (e) {
      setError(apiErrorMessage(e, 'Failed to load projects'))
    } finally {
      setIsLoading(false)
    }
  }, [q, status])

  useEffect(() => {
    const t = setTimeout(() => void load(), 250)
    return () => clearTimeout(t)
  }, [load])

  async function confirmDelete() {
    if (!pendingDelete) return
    setIsDeleting(true)
    try {
      await deleteProject(pendingDelete.id)
      setPendingDelete(null)
      await Promise.all([load(), reload()])
    } catch (e) {
      setError(apiErrorMessage(e, 'Failed to delete project'))
      setPendingDelete(null)
    } finally {
      setIsDeleting(false)
    }
  }

  const columns: Column<ProjectSummary>[] = [
    { key: 'key', header: 'Key', render: (p) => <span className="font-mono font-semibold">{p.key}</span> },
    {
      key: 'name',
      header: 'Name',
      render: (p) => (
        <Link
          to={`/projects/${p.id}`}
          onClick={(e) => e.stopPropagation()}
          className="font-medium text-brand-600 hover:underline"
        >
          {p.name}
        </Link>
      ),
    },
    { key: 'status', header: 'Status', render: (p) => <StatusBadge value={p.status} /> },
    { key: 'owner', header: 'Owner', render: (p) => p.owner ?? '-' },
    {
      key: 'actions',
      header: 'Actions',
      render: (p) => (
        <div className="flex gap-3 text-sm">
          <Link
            to={`/projects/${p.id}/edit`}
            onClick={(e) => e.stopPropagation()}
            className="text-brand-600 hover:underline"
          >
            Edit
          </Link>
          <button
            type="button"
            className="text-red-600 hover:underline"
            onClick={(e) => {
              e.stopPropagation()
              setPendingDelete(p)
            }}
          >
            Delete
          </button>
        </div>
      ),
    },
  ]

  return (
    <PageWrapper
      title="Projects"
      subtitle="All projects"
      actions={<GradientButton onClick={() => navigate('/projects/new')}>New project</GradientButton>}
    >
      <div className="mb-4 flex flex-wrap gap-3">
        <input
          type="search"
          aria-label="Search projects"
          placeholder="Search projects..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={`${fieldControlClass} sm:w-72`}
        />
        <select
          aria-label="Filter by status"
          value={status}
          onChange={(e) => setStatus(e.target.value as ProjectStatus | '')}
          className={`${fieldControlClass} sm:w-48`}
        >
          <option value="">All statuses</option>
          {PROJECT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
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
        rows={rows}
        rowKey={(p) => p.id}
        isLoading={isLoading}
        onRowClick={(p) => navigate(`/projects/${p.id}`)}
        emptyTitle="No projects found"
        emptyDescription="Create a project to start organising requirements and test cases."
      />

      {pendingDelete && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-project-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
        >
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <h2 id="delete-project-title" className="text-lg font-semibold text-slate-900">
              Delete {pendingDelete.name}?
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              This permanently deletes the project and all its requirements, test cases, test runs and
              defects.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <GradientButton variant="secondary" onClick={() => setPendingDelete(null)}>
                Cancel
              </GradientButton>
              <GradientButton variant="danger" disabled={isDeleting} onClick={() => void confirmDelete()}>
                {isDeleting ? 'Deleting...' : 'Delete'}
              </GradientButton>
            </div>
          </div>
        </div>
      )}
    </PageWrapper>
  )
}
