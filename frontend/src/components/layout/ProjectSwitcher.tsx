import { useProject } from '../../hooks/useProject'
import { fieldControlClass } from '../ui/FormField'
import { cn } from '../../lib/cn'

/** Global project scope selector. Phase 2 populates `projects` from GET /api/projects. */
export function ProjectSwitcher() {
  const { projectId, setProjectId, projects } = useProject()

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="project-switcher" className="text-xs font-semibold uppercase text-slate-500">
        Project
      </label>
      <select
        id="project-switcher"
        value={projectId ?? ''}
        onChange={(e) => setProjectId(e.target.value === '' ? null : Number(e.target.value))}
        className={cn(fieldControlClass, 'w-48 py-1.5')}
      >
        <option value="">All projects</option>
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.key} - {p.name}
          </option>
        ))}
      </select>
    </div>
  )
}
