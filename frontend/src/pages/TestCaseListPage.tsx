import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { StatusBadge } from '../components/ui/Badge'
import { DataTable, type Column } from '../components/ui/DataTable'
import { fieldControlClass } from '../components/ui/FormField'
import { GradientButton } from '../components/ui/GradientButton'
import { useProject } from '../hooks/useProject'
import {
  apiErrorMessage,
  deleteTestCase,
  exportTestCasesCsv,
  listTestCases,
  type TestCaseFilters,
} from '../services/testCaseService'
import {
  PRIORITIES,
  TEST_CASE_STATUSES,
  TEST_CASE_TYPES,
  type Priority,
  type TestCase,
  type TestCaseStatus,
  type TestCaseType,
} from '../types'

export default function TestCaseListPage() {
  const navigate = useNavigate()
  const { projectId, projects } = useProject()
  const [rows, setRows] = useState<TestCase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [type, setType] = useState<TestCaseType | ''>('')
  const [priority, setPriority] = useState<Priority | ''>('')
  const [status, setStatus] = useState<TestCaseStatus | ''>('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => clearTimeout(t)
  }, [search])

  const filters: TestCaseFilters = useMemo(
    () => ({ project_id: projectId, q: debouncedSearch, type, priority, status }),
    [projectId, debouncedSearch, type, priority, status],
  )

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    listTestCases(filters)
      .then((data) => {
        if (!cancelled) {
          setRows(data)
          setError(null)
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(apiErrorMessage(e, 'Failed to load test cases'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [filters, reloadKey])

  const handleDelete = useCallback(async (tc: TestCase) => {
    if (!window.confirm(`Delete TC-${tc.id} "${tc.title}"? This cannot be undone.`)) return
    try {
      await deleteTestCase(tc.id)
      setReloadKey((k) => k + 1)
    } catch (e: unknown) {
      setError(apiErrorMessage(e, 'Failed to delete test case'))
    }
  }, [])

  const handleExport = async () => {
    try {
      await exportTestCasesCsv(filters)
    } catch (e: unknown) {
      setError(apiErrorMessage(e, 'Failed to export CSV'))
    }
  }

  const projectKey = (id: number) => projects.find((p) => p.id === id)?.key ?? `#${id}`

  const columns: Column<TestCase>[] = [
    { key: 'id', header: 'ID', render: (r) => <span className="font-mono text-xs">TC-{r.id}</span> },
    { key: 'title', header: 'Title', render: (r) => <span className="font-medium text-slate-900">{r.title}</span> },
    { key: 'project', header: 'Project', render: (r) => projectKey(r.project_id) },
    { key: 'type', header: 'Type', render: (r) => r.type },
    { key: 'priority', header: 'Priority', render: (r) => <StatusBadge value={r.priority} /> },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
    {
      key: 'actions',
      header: 'Actions',
      render: (r) => (
        <div className="flex gap-3 text-sm" onClick={(e) => e.stopPropagation()}>
          <Link to={`/testcases/${r.id}/edit`} className="text-brand-600 hover:underline">
            Edit
          </Link>
          <button
            type="button"
            onClick={() => void handleDelete(r)}
            className="text-red-600 hover:underline"
          >
            Delete
          </button>
        </div>
      ),
    },
  ]

  return (
    <PageWrapper
      title="Test Cases"
      subtitle="Search and filter test cases"
      actions={
        <>
          <GradientButton variant="secondary" onClick={() => void handleExport()}>
            Export CSV
          </GradientButton>
          <GradientButton onClick={() => navigate('/testcases/new')}>New test case</GradientButton>
        </>
      }
    >
      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <input
          type="search"
          aria-label="Search test cases"
          placeholder="Search test cases..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={fieldControlClass}
        />
        <select
          aria-label="Filter by type"
          value={type}
          onChange={(e) => setType(e.target.value as TestCaseType | '')}
          className={fieldControlClass}
        >
          <option value="">All types</option>
          {TEST_CASE_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
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
          onChange={(e) => setStatus(e.target.value as TestCaseStatus | '')}
          className={fieldControlClass}
        >
          <option value="">All statuses</option>
          {TEST_CASE_STATUSES.map((s) => (
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
        onRowClick={(r) => navigate(`/testcases/${r.id}`)}
        emptyTitle="No test cases found"
        emptyDescription="Create a test case or adjust your filters."
      />
    </PageWrapper>
  )
}
