import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { fieldControlClass, FormField } from '../components/ui/FormField'
import { GlassCard } from '../components/ui/GlassCard'
import { GradientButton } from '../components/ui/GradientButton'
import { useProject } from '../hooks/useProject'
import {
  apiErrorMessage,
  createTestCase,
  getTestCase,
  listProjects,
  listRequirements,
  parseSteps,
  updateTestCase,
} from '../services/testCaseService'
import {
  PRIORITIES,
  TEST_CASE_STATUSES,
  TEST_CASE_TYPES,
  type Priority,
  type Project,
  type Requirement,
  type TestCaseStatus,
  type TestCaseType,
} from '../types'

export default function TestCaseFormPage() {
  const { id } = useParams()
  const editingId = id ? Number(id) : null
  const navigate = useNavigate()
  const { projectId: currentProjectId } = useProject()

  const [projectId, setProjectId] = useState<number | ''>(currentProjectId ?? '')
  const [requirementId, setRequirementId] = useState<number | ''>('')
  const [title, setTitle] = useState('')
  const [moduleName, setModuleName] = useState('')
  const [type, setType] = useState<TestCaseType>('Functional')
  const [priority, setPriority] = useState<Priority>('Medium')
  const [status, setStatus] = useState<TestCaseStatus>('Draft')
  const [preconditions, setPreconditions] = useState('')
  const [steps, setSteps] = useState('')
  const [expected, setExpected] = useState('')
  const [projects, setProjects] = useState<Project[]>([])
  const [requirements, setRequirements] = useState<Requirement[]>([])
  const [loading, setLoading] = useState(editingId !== null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{ title?: string; project?: string; steps?: string }>({})

  useEffect(() => {
    let cancelled = false
    listProjects()
      .then((data) => {
        if (!cancelled) setProjects(data)
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(apiErrorMessage(e, 'Failed to load projects'))
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (editingId === null) return
    let cancelled = false
    getTestCase(editingId)
      .then((tc) => {
        if (cancelled) return
        setProjectId(tc.project_id)
        setRequirementId(tc.requirement_id ?? '')
        setTitle(tc.title)
        setModuleName(tc.module ?? '')
        setType(tc.type)
        setPriority(tc.priority)
        setStatus(tc.status)
        setPreconditions(tc.preconditions ?? '')
        setSteps(tc.steps)
        setExpected(tc.expected_result ?? '')
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(apiErrorMessage(e, 'Failed to load test case'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [editingId])

  useEffect(() => {
    if (projectId === '') {
      setRequirements([])
      return
    }
    let cancelled = false
    listRequirements(projectId)
      .then((data) => {
        if (!cancelled) setRequirements(data)
      })
      .catch(() => {
        if (!cancelled) setRequirements([])
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  const handleProjectChange = (value: string) => {
    setProjectId(value === '' ? '' : Number(value))
    setRequirementId('')
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const errs: typeof fieldErrors = {}
    if (!title.trim()) errs.title = 'Title is required'
    if (projectId === '') errs.project = 'Project is required'
    if (!steps.trim()) errs.steps = 'At least one step is required'
    setFieldErrors(errs)
    if (Object.keys(errs).length > 0 || projectId === '') return

    setSaving(true)
    setError(null)
    const payload = {
      project_id: projectId,
      requirement_id: requirementId === '' ? null : requirementId,
      title: title.trim(),
      module: moduleName.trim() || null,
      type,
      priority,
      status,
      preconditions: preconditions.trim() || null,
      steps: parseSteps(steps).join('\n'),
      expected_result: expected.trim() || null,
    }
    try {
      const saved =
        editingId === null ? await createTestCase(payload) : await updateTestCase(editingId, payload)
      navigate(`/testcases/${saved.id}`)
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Failed to save test case'))
      setSaving(false)
    }
  }

  return (
    <PageWrapper title={editingId === null ? 'New test case' : `Edit TC-${editingId}`}>
      <GlassCard static className="max-w-3xl">
        {loading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : (
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4" noValidate>
            {error && (
              <p role="alert" className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
                {error}
              </p>
            )}
            <FormField label="Title" required error={fieldErrors.title}>
              <input
                className={fieldControlClass}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={255}
              />
            </FormField>
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField label="Project" required error={fieldErrors.project}>
                <select
                  className={fieldControlClass}
                  value={projectId}
                  onChange={(e) => handleProjectChange(e.target.value)}
                >
                  <option value="">Select a project</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.key} - {p.name}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Requirement">
                <select
                  className={fieldControlClass}
                  value={requirementId}
                  disabled={projectId === ''}
                  onChange={(e) => setRequirementId(e.target.value === '' ? '' : Number(e.target.value))}
                >
                  <option value="">None</option>
                  {requirements.map((r) => (
                    <option key={r.id} value={r.id}>
                      REQ-{r.id} - {r.title}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Module">
                <input
                  className={fieldControlClass}
                  value={moduleName}
                  onChange={(e) => setModuleName(e.target.value)}
                />
              </FormField>
              <FormField label="Type">
                <select
                  className={fieldControlClass}
                  value={type}
                  onChange={(e) => setType(e.target.value as TestCaseType)}
                >
                  {TEST_CASE_TYPES.map((t) => (
                    <option key={t}>{t}</option>
                  ))}
                </select>
              </FormField>
              <FormField label="Priority">
                <select
                  className={fieldControlClass}
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as Priority)}
                >
                  {PRIORITIES.map((p) => (
                    <option key={p}>{p}</option>
                  ))}
                </select>
              </FormField>
              <FormField label="Status">
                <select
                  className={fieldControlClass}
                  value={status}
                  onChange={(e) => setStatus(e.target.value as TestCaseStatus)}
                >
                  {TEST_CASE_STATUSES.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </FormField>
            </div>
            <FormField label="Preconditions">
              <textarea
                rows={3}
                className={fieldControlClass}
                value={preconditions}
                onChange={(e) => setPreconditions(e.target.value)}
              />
            </FormField>
            <FormField label="Steps" required hint="One step per line" error={fieldErrors.steps}>
              <textarea
                rows={6}
                className={fieldControlClass}
                value={steps}
                onChange={(e) => setSteps(e.target.value)}
              />
            </FormField>
            <FormField label="Expected result">
              <textarea
                rows={3}
                className={fieldControlClass}
                value={expected}
                onChange={(e) => setExpected(e.target.value)}
              />
            </FormField>
            <div className="flex gap-3">
              <GradientButton type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save test case'}
              </GradientButton>
              <GradientButton variant="secondary" onClick={() => navigate(-1)}>
                Cancel
              </GradientButton>
            </div>
          </form>
        )}
      </GlassCard>
    </PageWrapper>
  )
}
