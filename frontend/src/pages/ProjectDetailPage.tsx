import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { PageWrapper } from '../components/layout/PageWrapper'
import { StatusBadge } from '../components/ui/Badge'
import { GlassCard } from '../components/ui/GlassCard'
import { KpiCard } from '../components/ui/KpiCard'
import { useProject } from '../hooks/useProject'
import { apiErrorMessage, getProject, type ProjectDetail } from '../services/projectService'

export default function ProjectDetailPage() {
  const { id } = useParams()
  const projectId = Number(id)
  const { setProjectId } = useProject()
  const [project, setProject] = useState<ProjectDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getProject(projectId)
      .then((p) => {
        if (!cancelled) setProject(p)
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(apiErrorMessage(e, 'Project not found'))
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  if (error) {
    return (
      <PageWrapper title="Project">
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
        <Link to="/projects" className="mt-4 inline-block text-sm text-brand-600 hover:underline">
          Back to projects
        </Link>
      </PageWrapper>
    )
  }
  if (!project) {
    return (
      <PageWrapper title="Project">
        <p className="text-sm text-slate-500">Loading...</p>
      </PageWrapper>
    )
  }

  // Scoped list pages read the selected project from useProject(); select it on navigation.
  const links = [
    { label: 'Requirements', to: '/requirements', value: project.counts.requirements },
    { label: 'Test cases', to: '/testcases', value: project.counts.test_cases },
    { label: 'Test runs', to: '/testruns', value: project.counts.test_runs },
    { label: 'Defects', to: '/defects', value: project.counts.defects },
  ]

  return (
    <PageWrapper
      title={`${project.key} - ${project.name}`}
      subtitle={project.description ?? undefined}
      actions={
        <>
          <Link
            to={`/projects/${project.id}/edit`}
            className="rounded-full border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Edit
          </Link>
          <button
            type="button"
            onClick={() => setProjectId(project.id)}
            className="rounded-full bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:shadow-lg"
          >
            Set as current
          </button>
        </>
      }
    >
      <div className="mb-6 flex items-center gap-3">
        <StatusBadge value={project.status} />
        {project.owner && <span className="text-sm text-slate-500">Owner: {project.owner}</span>}
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {links.map((l) => (
          <Link key={l.label} to={l.to} onClick={() => setProjectId(project.id)} className="block">
            <KpiCard label={l.label} value={l.value} hint="View all" />
          </Link>
        ))}
      </div>
      <GlassCard static className="mt-6">
        <p className="text-sm text-slate-600">
          Created {new Date(project.created_at).toLocaleDateString()} - updated{' '}
          {new Date(project.updated_at).toLocaleDateString()}
        </p>
      </GlassCard>
    </PageWrapper>
  )
}
