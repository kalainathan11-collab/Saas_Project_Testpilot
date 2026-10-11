import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { FormField, fieldControlClass } from '../components/ui/FormField'
import { GlassCard } from '../components/ui/GlassCard'
import { GradientButton } from '../components/ui/GradientButton'
import { useProject } from '../hooks/useProject'
import {
  apiErrorMessage,
  createTestRun,
  getTestRun,
  listProjectsForSelect,
  updateTestRun,
} from '../services/testRunService'
import type { Project } from '../types'

export default function TestRunFormPage() {
  const { id } = useParams()
  const editId = id ? Number(id) : null
  const navigate = useNavigate()
  const [search] = useSearchParams()
  const { projectId: ctxProjectId } = useProject()
  const [projects, setProjects] = useState<Project[]>([])
  const [projectId, setProjectId] = useState<string>(
    search.get('project_id') ?? (ctxProjectId ? String(ctxProjectId) : ''),
  )
  const [name, setName] = useState('')
  const [assignee, setAssignee] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    listProjectsForSelect()
      .then(setProjects)
      .catch(() => setProjects([]))
  }, [])

  useEffect(() => {
    if (editId === null) return
    getTestRun(editId)
      .then((run) => {
        setProjectId(String(run.project_id))
        setName(run.name)
        setAssignee(run.assignee ?? '')
      })
      .catch((err) => setFormError(apiErrorMessage(err, 'Failed to load test run')))
  }, [editId])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const next: Record<string, string> = {}
    if (!projectId) next.project = 'Project is required'
    if (!name.trim()) next.name = 'Name is required'
    setErrors(next)
    if (Object.keys(next).length > 0) return
    setSaving(true)
    setFormError(null)
    const payload = {
      project_id: Number(projectId),
      name: name.trim(),
      assignee: assignee.trim() || null,
    }
    try {
      if (editId === null) {
        const created = await createTestRun(payload)
        navigate(`/testruns/${created.id}`)
      } else {
        await updateTestRun(editId, payload)
        navigate('/testruns')
      }
    } catch (err) {
      setFormError(apiErrorMessage(err, 'Failed to save test run'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageWrapper title={editId === null ? 'New test run' : `Edit RUN-${editId}`}>
      <GlassCard static className="max-w-xl">
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4" noValidate>
          <FormField label="Project" required error={errors.project}>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              disabled={editId !== null}
              className={fieldControlClass}
            >
              <option value="">Select a project</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Name" required error={errors.name}>
            <input value={name} onChange={(e) => setName(e.target.value)} className={fieldControlClass} />
          </FormField>
          <FormField label="Assignee">
            <input
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              className={fieldControlClass}
            />
          </FormField>
          {formError && (
            <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
              {formError}
            </p>
          )}
          <div className="flex gap-2">
            <GradientButton type="submit" disabled={saving}>
              {saving ? 'Saving...' : 'Save'}
            </GradientButton>
            <GradientButton variant="secondary" onClick={() => navigate('/testruns')}>
              Cancel
            </GradientButton>
          </div>
        </form>
      </GlassCard>
    </PageWrapper>
  )
}
