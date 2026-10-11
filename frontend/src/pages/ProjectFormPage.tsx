import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { FormField, fieldControlClass } from '../components/ui/FormField'
import { GradientButton } from '../components/ui/GradientButton'
import { GlassCard } from '../components/ui/GlassCard'
import { useProject } from '../hooks/useProject'
import {
  apiErrorMessage,
  createProject,
  getProject,
  updateProject,
  type ProjectInput,
} from '../services/projectService'
import { PROJECT_STATUSES, type ProjectStatus } from '../types'

export default function ProjectFormPage() {
  const { id } = useParams()
  const projectId = id ? Number(id) : null
  const isEdit = projectId !== null
  const navigate = useNavigate()
  const { reload } = useProject()

  const [name, setName] = useState('')
  const [key, setKey] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<ProjectStatus>('Active')
  const [errors, setErrors] = useState<{ name?: string; key?: string }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(isEdit)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (projectId === null) return
    let cancelled = false
    getProject(projectId)
      .then((p) => {
        if (cancelled) return
        setName(p.name)
        setKey(p.key)
        setDescription(p.description ?? '')
        setStatus(p.status)
      })
      .catch((e: unknown) => {
        if (!cancelled) setFormError(apiErrorMessage(e, 'Failed to load project'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const next: { name?: string; key?: string } = {}
    if (!name.trim()) next.name = 'Name is required'
    if (!key.trim()) next.key = 'Key is required'
    setErrors(next)
    setFormError(null)
    if (next.name || next.key) return

    const input: ProjectInput = {
      name: name.trim(),
      key: key.trim().toUpperCase(),
      description: description.trim() || null,
      status,
    }
    setIsSaving(true)
    try {
      const saved = projectId === null ? await createProject(input) : await updateProject(projectId, input)
      await reload()
      navigate(`/projects/${saved.id}`)
    } catch (err) {
      setFormError(apiErrorMessage(err, 'Failed to save project'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <PageWrapper title={isEdit ? 'Edit project' : 'New project'}>
      <GlassCard static className="max-w-2xl">
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : (
          <form onSubmit={(e) => void onSubmit(e)} className="space-y-4" noValidate>
            <FormField label="Name" required error={errors.name}>
              <input
                className={fieldControlClass}
                value={name}
                maxLength={120}
                onChange={(e) => setName(e.target.value)}
              />
            </FormField>
            <FormField label="Key" required error={errors.key} hint="Short unique code, e.g. WEB">
              <input
                className={fieldControlClass}
                value={key}
                maxLength={10}
                onChange={(e) => setKey(e.target.value.toUpperCase())}
              />
            </FormField>
            <FormField label="Description">
              <textarea
                className={fieldControlClass}
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </FormField>
            <FormField label="Status">
              <select
                className={fieldControlClass}
                value={status}
                onChange={(e) => setStatus(e.target.value as ProjectStatus)}
              >
                {PROJECT_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </FormField>
            {formError && (
              <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
                {formError}
              </p>
            )}
            <div className="flex gap-2">
              <GradientButton type="submit" disabled={isSaving}>
                {isSaving ? 'Saving...' : isEdit ? 'Save changes' : 'Create project'}
              </GradientButton>
              <GradientButton variant="secondary" onClick={() => navigate('/projects')}>
                Cancel
              </GradientButton>
            </div>
          </form>
        )}
      </GlassCard>
    </PageWrapper>
  )
}
