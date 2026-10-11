import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { GlassCard } from '../components/ui/GlassCard'
import { GradientButton } from '../components/ui/GradientButton'
import { StatusBadge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { useProject } from '../hooks/useProject'
import {
  deleteRequirement,
  getErrorMessage,
  getRequirement,
  requirementCode,
  type RequirementDetail,
} from '../services/requirementService'

export default function RequirementDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { projects } = useProject()
  const [req, setReq] = useState<RequirementDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    getRequirement(Number(id))
      .then((r) => {
        if (!cancelled) setReq(r)
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(getErrorMessage(e, 'Failed to load requirement'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  async function handleDelete() {
    if (!req || !window.confirm(`Delete ${requirementCode(req.id)}?`)) return
    try {
      await deleteRequirement(req.id)
      navigate('/requirements')
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to delete requirement'))
    }
  }

  if (loading) {
    return (
      <PageWrapper title="Requirement">
        <p className="text-sm text-slate-500">Loading...</p>
      </PageWrapper>
    )
  }

  if (!req) {
    return (
      <PageWrapper title="Requirement">
        <EmptyState
          title="Requirement not found"
          description={error ?? undefined}
          action={
            <Link to="/requirements" className="text-brand-600 hover:underline">
              Back to requirements
            </Link>
          }
        />
      </PageWrapper>
    )
  }

  const projectName = projects.find((p) => p.id === req.project_id)?.name ?? `#${req.project_id}`

  return (
    <PageWrapper
      title={`${requirementCode(req.id)} ${req.title}`}
      subtitle={`Project: ${projectName}`}
      actions={
        <>
          <GradientButton variant="secondary" onClick={() => navigate(`/requirements/${req.id}/edit`)}>
            Edit
          </GradientButton>
          <GradientButton variant="danger" onClick={() => void handleDelete()}>
            Delete
          </GradientButton>
        </>
      }
    >
      {error && (
        <p role="alert" className="mb-4 rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard static>
          <h2 className="mb-3 text-base font-semibold text-slate-900">Details</h2>
          <div className="mb-3 flex gap-2">
            <StatusBadge value={req.priority} />
            <StatusBadge value={req.status} />
          </div>
          <p className="whitespace-pre-wrap text-sm text-slate-700">
            {req.description || 'No description provided.'}
          </p>
        </GlassCard>
        <GlassCard static>
          <h2 className="mb-3 text-base font-semibold text-slate-900">
            Linked test cases ({req.test_cases.length})
          </h2>
          {req.test_cases.length === 0 ? (
            <p className="text-sm text-slate-500">No test cases linked yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {req.test_cases.map((tc) => (
                <li key={tc.id} className="flex items-center justify-between py-2">
                  <Link to={`/testcases/${tc.id}`} className="text-sm font-medium text-brand-600 hover:underline">
                    TC-{tc.id} {tc.title}
                  </Link>
                  <StatusBadge value={tc.status} />
                </li>
              ))}
            </ul>
          )}
        </GlassCard>
      </div>
    </PageWrapper>
  )
}
