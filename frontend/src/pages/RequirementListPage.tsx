import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { DataTable, type Column } from '../components/ui/DataTable'
import { StatusBadge } from '../components/ui/Badge'
import { GradientButton } from '../components/ui/GradientButton'
import { fieldControlClass } from '../components/ui/FormField'
import { useProject } from '../hooks/useProject'
import {
  deleteRequirement,
  getErrorMessage,
  listRequirements,
  requirementCode,
  type RequirementListItem,
} from '../services/requirementService'
import { PRIORITIES, REQUIREMENT_STATUSES, type Priority, type RequirementStatus } from '../types'

export default function RequirementListPage() {
  const navigate = useNavigate()
  const { projectId, projects } = useProject()
  const [rows, setRows] = useState<RequirementListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [q, setQ] = useState('')
  const [filterProject, setFilterProject] = useState<number | null>(null)
  const [priority, setPriority] = useState<Priority | ''>('')
  const [status, setStatus] = useState<RequirementStatus | ''>('')

  useEffect(() => {
    const t = setTimeout(() => setQ(search), 300)
    return () => clearTimeout(t)
  }, [search])

  const effectiveProject = projectId ?? filterProject

  useEffect(() => {
    let cancelled = false
    listRequirements({ project_id: effectiveProject, priority, status, q })
      .then((data) => {
        if (!cancelled) {
          setRows(data)
          setError(null)
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(getErrorMessage(e, 'Failed to load requirements'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [effectiveProject, priority, status, q])

  const handleDelete = useCallback(async (row: RequirementListItem) => {
    if (!window.confirm(`Delete ${requirementCode(row.id)} "${row.title}"?`)) return
    try {
      await deleteRequirement(row.id)
      setRows((prev) => prev.filter((r) => r.id !== row.id))
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to delete requirement'))
    }
  }, [])

  const projectName = useCallback(
    (id: number) => projects.find((p) => p.id === id)?.name ?? `#${id}`,
    [projects],
  )

  const columns: Column<RequirementListItem>[] = useMemo(
    () => [
      { key: 'id', header: 'ID', render: (r) => <span className="font-mono text-xs">{requirementCode(r.id)}</span> },
      { key: 'title', header: 'Title', render: (r) => <span className="font-medium text-slate-900">{r.title}</span> },
      { key: 'project', header: 'Project', render: (r) => projectName(r.project_id) },
      { key: 'priority', header: 'Priority', render: (r) => <StatusBadge value={r.priority} /> },
      { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
      { key: 'tcs', header: 'Test cases', render: (r) => r.test_case_count },
      {
        key: 'actions',
        header: 'Actions',
        render: (r) => (
          <div className="flex gap-3 text-sm" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="text-brand-600 hover:underline"
              onClick={() => navigate(`/requirements/${r.id}/edit`)}
            >
              Edit
            </button>
            <button type="button" className="text-red-600 hover:underline" onClick={() => void handleDelete(r)}>
              Delete
            </button>
          </div>
        ),
      },
    ],
    [projectName, navigate, handleDelete],
  )

  return (
    <PageWrapper
      title="Requirements"
      subtitle="Track what needs to be tested"
      actions={<GradientButton onClick={() => navigate('/requirements/new')}>New requirement</GradientButton>}
    >
      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <input
          type="search"
          aria-label="Search requirements"
          placeholder="Search requirements..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={fieldControlClass}
        />
        {projectId === null && (
          <select
            aria-label="Filter by project"
            value={filterProject ?? ''}
            onChange={(e) => setFilterProject(e.target.value ? Number(e.target.value) : null)}
            className={fieldControlClass}
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        )}
        <select
          aria-label="Filter by priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value as Priority | '')}
          className={fieldControlClass}
        >
          <option value="">All priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select
          aria-label="Filter by status"
          value={status}
          onChange={(e) => setStatus(e.target.value as RequirementStatus | '')}
          className={fieldControlClass}
        >
          <option value="">All statuses</option>
          {REQUIREMENT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      {error && (
        <p role="alert" className="mb-4 rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(r) => r.id}
        isLoading={loading}
        onRowClick={(r) => navigate(`/requirements/${r.id}`)}
        emptyTitle="No requirements found"
        emptyDescription="Create a requirement or adjust your filters."
      />
    </PageWrapper>
  )
}
