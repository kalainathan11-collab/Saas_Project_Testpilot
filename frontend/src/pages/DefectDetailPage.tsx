import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { StatusBadge } from '../components/ui/Badge'
import { fieldControlClass } from '../components/ui/FormField'
import { GradientButton } from '../components/ui/GradientButton'
import {
  defectDisplayId,
  deleteDefect,
  errorMessage,
  getDefect,
  getTestCase,
  updateDefect,
} from '../services/defectService'
import { DEFECT_STATUSES, type Defect, type DefectStatus, type TestCase } from '../types'

export default function DefectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [defect, setDefect] = useState<Defect | null>(null)
  const [testCase, setTestCase] = useState<TestCase | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const d = await getDefect(Number(id))
        if (cancelled) return
        setDefect(d)
        if (d.test_case_id) {
          const tc = await getTestCase(d.test_case_id).catch(() => null)
          if (!cancelled) setTestCase(tc)
        }
      } catch (err) {
        if (!cancelled) setError(errorMessage(err, 'Failed to load defect'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [id])

  async function changeStatus(next: DefectStatus) {
    if (!defect) return
    try {
      const updated = await updateDefect(defect.id, {
        project_id: defect.project_id,
        test_case_id: defect.test_case_id,
        title: defect.title,
        description: defect.description,
        severity: defect.severity,
        status: next,
        assignee: defect.assignee,
      })
      setDefect(updated)
      setError(null)
    } catch (err) {
      setError(errorMessage(err, 'Failed to update status'))
    }
  }

  async function handleDelete() {
    if (!defect) return
    try {
      await deleteDefect(defect.id)
      navigate('/defects')
    } catch (err) {
      setError(errorMessage(err, 'Failed to delete defect'))
    }
  }

  if (loading) return <p className="p-8 text-center text-sm text-slate-500">Loading...</p>
  if (!defect) {
    return (
      <p role="alert" className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
        {error ?? 'Defect not found'}
      </p>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Link to="/defects" className="text-sm text-brand-600 hover:underline">
        Back to defects
      </Link>
      {error && (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      <div className="space-y-5 rounded-2xl border border-slate-200 bg-white p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-mono text-xs text-slate-500">{defectDisplayId(defect.id)}</p>
            <h1 className="text-2xl font-bold text-slate-900">{defect.title}</h1>
          </div>
          <div className="flex gap-2">
            <StatusBadge value={defect.severity} />
            <StatusBadge value={defect.status} />
          </div>
        </div>

        <p className="whitespace-pre-wrap text-sm text-slate-700">
          {defect.description || 'No description provided.'}
        </p>

        <dl className="grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs font-semibold uppercase text-slate-500">Assignee</dt>
            <dd className="text-slate-800">{defect.assignee ?? 'Unassigned'}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase text-slate-500">Linked test case</dt>
            <dd>
              {defect.test_case_id ? (
                <Link to={`/testcases/${defect.test_case_id}`} className="text-brand-600 hover:underline">
                  {`TC-${defect.test_case_id}`}
                  {testCase ? ` ${testCase.title}` : ''}
                </Link>
              ) : (
                <span className="text-slate-800">None</span>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase text-slate-500">Created</dt>
            <dd className="text-slate-800">{new Date(defect.created_at).toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase text-slate-500">Quick status change</dt>
            <dd>
              <select
                aria-label="Change status"
                className={fieldControlClass}
                value={defect.status}
                onChange={(e) => void changeStatus(e.target.value as DefectStatus)}
              >
                {DEFECT_STATUSES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </dd>
          </div>
        </dl>

        <div className="flex flex-wrap justify-end gap-3">
          <GradientButton variant="secondary" onClick={() => navigate(`/defects/${defect.id}/edit`)}>
            Edit
          </GradientButton>
          {confirming ? (
            <>
              <GradientButton variant="danger" onClick={() => void handleDelete()}>
                Confirm delete
              </GradientButton>
              <GradientButton variant="secondary" onClick={() => setConfirming(false)}>
                Cancel
              </GradientButton>
            </>
          ) : (
            <GradientButton variant="danger" onClick={() => setConfirming(true)}>
              Delete
            </GradientButton>
          )}
        </div>
      </div>
    </div>
  )
}
