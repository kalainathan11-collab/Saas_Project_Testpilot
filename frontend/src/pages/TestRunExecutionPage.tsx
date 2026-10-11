import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { StatusBadge } from '../components/ui/Badge'
import { GlassCard } from '../components/ui/GlassCard'
import { GradientButton } from '../components/ui/GradientButton'
import {
  apiErrorMessage,
  buildDefectLink,
  countResults,
  getTestRun,
  progressPct,
  recordResult,
  resetResults,
  type RunCase,
  type TestRunDetail,
} from '../services/testRunService'
import { RESULT_STATUSES, type Priority, type ResultStatus } from '../types'

const activeClass: Record<ResultStatus, string> = {
  Passed: 'bg-emerald-600 text-white',
  Failed: 'bg-red-600 text-white',
  Blocked: 'bg-orange-500 text-white',
  Skipped: 'bg-slate-500 text-white',
}

interface CaseRowProps {
  runCase: RunCase
  run: TestRunDetail
  busy: boolean
  onSetStatus: (c: RunCase, status: ResultStatus, comment: string | null) => void
  onSaveComment: (c: RunCase, comment: string) => void
}

function CaseRow({ runCase, run, busy, onSetStatus, onSaveComment }: CaseRowProps) {
  const [open, setOpen] = useState(false)
  const serverComment = runCase.result?.comment ?? ''
  const [comment, setComment] = useState(serverComment)

  // Reconcile with the server value whenever it changes.
  useEffect(() => {
    setComment(serverComment)
  }, [serverComment])

  const current = runCase.result?.status ?? null
  const steps = runCase.steps.split('\n').filter((s) => s.trim())

  return (
    <li className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="font-mono text-xs text-slate-500">TC-{runCase.id}</p>
          <p className="font-medium text-slate-900">{runCase.title}</p>
          <div className="mt-1 flex items-center gap-2">
            <StatusBadge value={runCase.priority as Priority} />
            <button
              type="button"
              aria-expanded={open}
              onClick={() => setOpen((v) => !v)}
              className="text-xs font-medium text-brand-600 hover:underline"
            >
              {open ? 'Hide steps' : 'Show steps'}
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2" role="group" aria-label={`Result for ${runCase.title}`}>
          {RESULT_STATUSES.map((s) => (
            <button
              key={s}
              type="button"
              disabled={busy}
              aria-pressed={current === s}
              onClick={() => onSetStatus(runCase, s, comment.trim() || null)}
              className={`rounded-full px-3 py-1 text-xs font-semibold transition disabled:opacity-50 ${
                current === s ? activeClass[s] : 'border border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
      {open && (
        <div className="mt-3 space-y-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
          <div>
            <p className="text-xs font-semibold uppercase text-slate-500">Steps</p>
            {steps.length > 0 ? (
              <ol className="list-decimal pl-5">
                {steps.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
            ) : (
              <p className="text-slate-500">No steps defined.</p>
            )}
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-slate-500">Expected result</p>
            <p>{runCase.expected_result || '-'}</p>
          </div>
        </div>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <input
          aria-label={`Comment for ${runCase.title}`}
          placeholder="Comment (optional)"
          value={comment}
          disabled={busy}
          onChange={(e) => setComment(e.target.value)}
          onBlur={() => {
            if (current && comment !== serverComment) onSaveComment(runCase, comment)
          }}
          className="min-w-48 flex-1 rounded-xl border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
        />
        {current === 'Failed' && (
          <Link
            to={buildDefectLink(run, runCase, comment.trim() || null)}
            className="text-sm font-medium text-red-600 hover:underline"
          >
            Log defect
          </Link>
        )}
      </div>
    </li>
  )
}

export default function TestRunExecutionPage() {
  const { id } = useParams()
  const runId = Number(id)
  const navigate = useNavigate()
  const [run, setRun] = useState<TestRunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(0)
  const [confirmReset, setConfirmReset] = useState(false)

  useEffect(() => {
    let cancelled = false
    getTestRun(runId)
      .then((r) => {
        if (!cancelled) setRun(r)
      })
      .catch((err) => {
        if (!cancelled) setError(apiErrorMessage(err, 'Failed to load test run'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [runId])

  const save = useCallback(
    async (c: RunCase, status: ResultStatus, comment: string | null) => {
      const previous = run
      // Optimistic update, reconciled with the server response below.
      setRun((r) =>
        r
          ? {
              ...r,
              cases: r.cases.map((x) =>
                x.id === c.id
                  ? { ...x, result: { status, comment, executed_at: x.result?.executed_at ?? null } }
                  : x,
              ),
            }
          : r,
      )
      setError(null)
      setPending((n) => n + 1)
      try {
        setRun(await recordResult(runId, c.id, status, comment))
      } catch (err) {
        setRun(previous)
        setError(apiErrorMessage(err, 'Failed to save result'))
      } finally {
        setPending((n) => n - 1)
      }
    },
    [run, runId],
  )

  async function handleReset() {
    setConfirmReset(false)
    try {
      await resetResults(runId)
      setRun(await getTestRun(runId))
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to reset results'))
    }
  }

  if (loading) {
    return (
      <PageWrapper title="Test run">
        <p className="text-sm text-slate-500">Loading...</p>
      </PageWrapper>
    )
  }
  if (!run) {
    return (
      <PageWrapper title="Test run">
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {error ?? 'Test run not found'}
        </p>
      </PageWrapper>
    )
  }

  const counts = countResults(run.cases)
  const executed = run.cases.filter((c) => c.result).length
  const total = run.cases.length
  const pct = progressPct(executed, total)

  return (
    <PageWrapper
      title={`RUN-${run.id}: ${run.name}`}
      subtitle={run.assignee ? `Assigned to ${run.assignee}` : undefined}
      actions={
        <>
          <StatusBadge value={run.status} />
          <GradientButton variant="secondary" onClick={() => navigate(`/testruns/${run.id}/edit`)}>
            Edit
          </GradientButton>
          {confirmReset ? (
            <>
              <GradientButton variant="danger" onClick={() => void handleReset()}>
                Confirm reset
              </GradientButton>
              <GradientButton variant="secondary" onClick={() => setConfirmReset(false)}>
                Cancel
              </GradientButton>
            </>
          ) : (
            <GradientButton variant="danger" disabled={executed === 0} onClick={() => setConfirmReset(true)}>
              Reset results
            </GradientButton>
          )}
        </>
      }
    >
      <GlassCard static className="mb-6">
        <div className="flex flex-wrap items-center gap-6">
          {RESULT_STATUSES.map((s) => (
            <div key={s} className="text-center">
              <p className="text-2xl font-bold text-slate-900">{counts[s]}</p>
              <p className="text-xs text-slate-500">{s}</p>
            </div>
          ))}
          <div className="min-w-48 flex-1">
            <progress
              className="h-3 w-full accent-brand-600"
              value={pct}
              max={100}
              aria-label="Execution progress"
            />
            <p className="mt-1 text-xs text-slate-500">
              {executed}/{total} executed ({pct}%)
            </p>
          </div>
        </div>
      </GlassCard>
      {error && (
        <p role="alert" className="mb-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}
      {run.cases.length === 0 ? (
        <p className="text-sm text-slate-500">No test cases are in scope for this run.</p>
      ) : (
        <ul className="space-y-3">
          {run.cases.map((c) => (
            <CaseRow
              key={c.id}
              runCase={c}
              run={run}
              busy={pending > 0}
              onSetStatus={(rc, s, cm) => void save(rc, s, cm)}
              onSaveComment={(rc, cm) => {
                if (rc.result) void save(rc, rc.result.status, cm.trim() || null)
              }}
            />
          ))}
        </ul>
      )}
    </PageWrapper>
  )
}
