import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { FormField, fieldControlClass } from '../components/ui/FormField'
import { GradientButton } from '../components/ui/GradientButton'
import { useProject } from '../hooks/useProject'
import {
  createDefect,
  errorMessage,
  getDefect,
  listProjectOptions,
  listTestCaseOptions,
  updateDefect,
  type DefectInput,
} from '../services/defectService'
import {
  DEFECT_STATUSES,
  SEVERITIES,
  type DefectStatus,
  type Project,
  type Severity,
  type TestCase,
} from '../types'

function asSeverity(v: string | null): Severity {
  return SEVERITIES.find((s) => s === v) ?? 'Major'
}

export default function DefectFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { projectId: ctxProjectId } = useProject()

  const [projects, setProjects] = useState<Project[]>([])
  const [testCases, setTestCases] = useState<TestCase[]>([])
  const [projectId, setProjectId] = useState<string>(
    params.get('project_id') ?? (ctxProjectId ? String(ctxProjectId) : ''),
  )
  const [testCaseId, setTestCaseId] = useState<string>(params.get('test_case_id') ?? '')
  const [title, setTitle] = useState(params.get('title') ?? '')
  const [description, setDescription] = useState(params.get('description') ?? '')
  const [severity, setSeverity] = useState<Severity>('Major')
  const [status, setStatus] = useState<DefectStatus>('Open')
  const [assignee, setAssignee] = useState('')
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{ title?: string; project?: string }>({})

  useEffect(() => {
    listProjectOptions()
      .then(setProjects)
      .catch((err) => setError(errorMessage(err, 'Failed to load projects')))
  }, [])

  useEffect(() => {
    if (!id) return
    getDefect(Number(id))
      .then((d) => {
        setProjectId(String(d.project_id))
        setTestCaseId(d.test_case_id ? String(d.test_case_id) : '')
        setTitle(d.title)
        setDescription(d.description ?? '')
        setSeverity(asSeverity(d.severity))
        setStatus(d.status)
        setAssignee(d.assignee ?? '')
      })
      .catch((err) => setError(errorMessage(err, 'Failed to load defect')))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!projectId) {
      setTestCases([])
      return
    }
    let cancelled = false
    listTestCaseOptions(Number(projectId))
      .then((list) => {
        if (!cancelled) setTestCases(list)
      })
      .catch(() => {
        if (!cancelled) setTestCases([])
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  function handleProjectChange(value: string) {
    setProjectId(value)
    setTestCaseId('')
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const errs: { title?: string; project?: string } = {}
    if (!title.trim()) errs.title = 'Title is required'
    if (!projectId) errs.project = 'Project is required'
    setFieldErrors(errs)
    if (errs.title || errs.project) return

    const input: DefectInput = {
      project_id: Number(projectId),
      test_case_id: testCaseId ? Number(testCaseId) : null,
      title: title.trim(),
      description: description.trim() || null,
      severity,
      status,
      assignee: assignee.trim() || null,
    }
    setSaving(true)
    setError(null)
    try {
      const saved = isEdit ? await updateDefect(Number(id), input) : await createDefect(input)
      navigate(`/defects/${saved.id}`)
    } catch (err) {
      setError(errorMessage(err, 'Failed to save defect'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="p-8 text-center text-sm text-slate-500">Loading...</p>

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold text-slate-900">{isEdit ? 'Edit defect' : 'New defect'}</h1>
      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
        {error && (
          <p role="alert" className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <FormField label="Title" required error={fieldErrors.title}>
          <input className={fieldControlClass} value={title} onChange={(e) => setTitle(e.target.value)} />
        </FormField>
        <FormField label="Project" required error={fieldErrors.project}>
          <select className={fieldControlClass} value={projectId} onChange={(e) => handleProjectChange(e.target.value)}>
            <option value="">Select a project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Linked test case" hint="Optional. Only test cases from the selected project are listed.">
          <select
            className={fieldControlClass}
            value={testCaseId}
            disabled={!projectId}
            onChange={(e) => setTestCaseId(e.target.value)}
          >
            <option value="">None</option>
            {testCases.map((tc) => (
              <option key={tc.id} value={tc.id}>
                {`TC-${tc.id} ${tc.title}`}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Description">
          <textarea
            rows={5}
            className={fieldControlClass}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </FormField>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Severity">
            <select
              className={fieldControlClass}
              value={severity}
              onChange={(e) => setSeverity(asSeverity(e.target.value))}
            >
              {SEVERITIES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </FormField>
          <FormField label="Status">
            <select
              className={fieldControlClass}
              value={status}
              onChange={(e) => setStatus(e.target.value as DefectStatus)}
            >
              {DEFECT_STATUSES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </FormField>
        </div>
        <FormField label="Assignee">
          <input className={fieldControlClass} value={assignee} onChange={(e) => setAssignee(e.target.value)} />
        </FormField>
        <div className="flex justify-end gap-3">
          <GradientButton variant="secondary" onClick={() => navigate(-1)}>
            Cancel
          </GradientButton>
          <GradientButton type="submit" disabled={saving}>
            {saving ? 'Saving...' : isEdit ? 'Save changes' : 'Create defect'}
          </GradientButton>
        </div>
      </form>
    </div>
  )
}
