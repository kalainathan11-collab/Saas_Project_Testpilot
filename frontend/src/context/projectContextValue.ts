import { createContext } from 'react'
import type { Project } from '../types'

export interface ProjectContextValue {
  /** Selected project id, or null for "All projects". */
  projectId: number | null
  setProjectId: (id: number | null) => void
  projects: Project[]
  setProjects: (projects: Project[]) => void
  /** Re-fetch the user's projects from GET /api/projects. */
  reload: () => Promise<void>
  isLoading: boolean
}

export const ProjectContext = createContext<ProjectContextValue | undefined>(undefined)
