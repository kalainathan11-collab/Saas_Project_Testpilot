import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { GlassCard } from '../components/ui/GlassCard'
import { GradientButton } from '../components/ui/GradientButton'
import { FormField, fieldControlClass } from '../components/ui/FormField'
import { useProject } from '../hooks/useProject'
import {
  createRequirement,
  getErrorMessage,
  getRequirement,
  listProjects,
  updateRequirement,
} from '../services/requirementService'
import {
  PRIORITIES,
  REQUIREMENT_STATUSES,
  type Priority,
  type Project,
  type RequirementStatus,
} from '../types'

export default function RequirementFormPage() {
  const { id } = useParams()
  const editId = id ? Number(id) : null
  const navigate = useNavigate()
  const { projectId: currentProjectId } = useProject()

  const [projects, setProjects] = useState<Project[]>([])
  const [projectId, setProjectId] = useState<number | ''>(currentProjectId ?? '')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<Priority>('Medium')
  const [status, setStatus] = useState<RequirementStatus>('Proposed')
  const [loading, setLoading] = useState(editId !== null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{ title?: string; project?: string }>({})

  useEffect(() => {
    let cancelled = false
    listProjects()
      .then((p) => {
        if (!cancelled) setProjects(p)
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(getErrorMessage(e, 'Failed to load projects'))
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (editId === null) return
    let cancelled = false
    getRequirement(editId)
      .then((r) => {
        if (cancelled) return
        setProjectId(r.project_id)
        setTitle(r.title)
        setDescription(r.description ?? '')
        setPriority(r.priority)
        setStatus(r.status)
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
  }, [editId])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const errs: { title?: string; project?: string } = {}
    if (!title.trim()) errs.title = 'Title is required'
    if (projectId === '') errs.project = 'Project is required'
    setFieldErrors(errs)
    if (errs.title || errs.project || projectId === '') return

    setSaving(true)
    setError(null)
    const input = {
      project_id: projectId,
      title: title.trim(),
      description: description.trim() || null,
      priority,
      status,
    }
    try {
      const saved = editId === null ? await createRequirement(input) : await updateRequirement(editId, input)
      navigate(`/requirements/${saved.id}`)
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to save requirement'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageWrapper title={editId === null ? 'New requirement' : 'Edit requirement'}>
      <GlassCard static className="max-w-2xl">
        {loading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : (
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4" noValidate>
            {error && (
              <p role="alert" className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
                {error}
              </p>
            )}
            <FormField label="Project" required error={fieldErrors.project}>
              <select
                value={projectId}
                onChange={(e) => setProjectId(e.target.value ? Number(e.target.value) : '')}
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
            <FormField label="Title" required error={fieldErrors.title}>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className={fieldControlClass}
              />
            </FormField>
            <FormField label="Description">
              <textarea
                rows={5}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className={fieldControlClass}
              />
            </FormField>
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField label="Priority">
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as Priority)}
                  className={fieldControlClass}
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Status">
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as RequirementStatus)}
                  className={fieldControlClass}
                >
                  {REQUIREMENT_STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </FormField>
            </div>
            <div className="flex gap-3">
              <GradientButton type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save'}
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
