import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { Badge, StatusBadge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { GlassCard } from '../components/ui/GlassCard'
import { GradientButton } from '../components/ui/GradientButton'
import {
  apiErrorMessage,
  deleteTestCase,
  getRequirement,
  getTestCase,
  parseSteps,
} from '../services/testCaseService'
import type { Requirement, TestCase } from '../types'

export default function TestCaseDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [testCase, setTestCase] = useState<TestCase | null>(null)
  const [requirement, setRequirement] = useState<Requirement | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getTestCase(Number(id))
      .then(async (tc) => {
        if (cancelled) return
        setTestCase(tc)
        if (tc.requirement_id !== null) {
          const req = await getRequirement(tc.requirement_id).catch(() => null)
          if (!cancelled) setRequirement(req)
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(apiErrorMessage(e, 'Test case not found'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  const handleDelete = async () => {
    if (!testCase || !window.confirm(`Delete TC-${testCase.id}? This cannot be undone.`)) return
    try {
      await deleteTestCase(testCase.id)
      navigate('/testcases')
    } catch (e: unknown) {
      setError(apiErrorMessage(e, 'Failed to delete test case'))
    }
  }

  if (loading) {
    return (
      <PageWrapper title="Test case">
        <p className="text-sm text-slate-500">Loading...</p>
      </PageWrapper>
    )
  }
  if (!testCase) {
    return (
      <PageWrapper title="Test case">
        <EmptyState title={error ?? 'Test case not found'} action={<Link to="/testcases">Back to list</Link>} />
      </PageWrapper>
    )
  }

  const steps = parseSteps(testCase.steps)

  return (
    <PageWrapper
      title={`TC-${testCase.id}: ${testCase.title}`}
      subtitle={testCase.module ? `Module: ${testCase.module}` : undefined}
      actions={
        <>
          <GradientButton variant="secondary" onClick={() => navigate(`/testcases/${testCase.id}/edit`)}>
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
      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard static className="space-y-4 lg:col-span-2">
          <section>
            <h2 className="mb-1 text-sm font-semibold text-slate-500">Preconditions</h2>
            <p className="whitespace-pre-line text-sm text-slate-800">{testCase.preconditions ?? '-'}</p>
          </section>
          <section>
            <h2 className="mb-2 text-sm font-semibold text-slate-500">Steps</h2>
            {steps.length === 0 ? (
              <p className="text-sm text-slate-800">-</p>
            ) : (
              <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-800">
                {steps.map((s, i) => (
                  <li key={`${i}-${s}`}>{s}</li>
                ))}
              </ol>
            )}
          </section>
          <section>
            <h2 className="mb-1 text-sm font-semibold text-slate-500">Expected result</h2>
            <p className="whitespace-pre-line text-sm text-slate-800">{testCase.expected_result ?? '-'}</p>
          </section>
        </GlassCard>
        <GlassCard static className="space-y-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Status</span>
            <StatusBadge value={testCase.status} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Priority</span>
            <StatusBadge value={testCase.priority} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Type</span>
            <Badge tone="blue">{testCase.type}</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Requirement</span>
            {testCase.requirement_id !== null ? (
              <Link to={`/requirements/${testCase.requirement_id}`} className="text-brand-600 hover:underline">
                REQ-{testCase.requirement_id}
                {requirement ? ` - ${requirement.title}` : ''}
              </Link>
            ) : (
              <span className="text-slate-700">None</span>
            )}
          </div>
        </GlassCard>
      </div>
    </PageWrapper>
  )
}
