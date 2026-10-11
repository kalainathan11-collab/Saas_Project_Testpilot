import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Project } from '../types'
import { getAccessToken, getSelectedProjectId, setSelectedProjectId } from '../lib/storage'
import { listProjects } from '../services/projectService'
import { ProjectContext } from './projectContextValue'
import { useAuth } from '../hooks/useAuth'

export function ProjectProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const userId = user?.id ?? null
  const [projectId, setProjectIdState] = useState<number | null>(() => getSelectedProjectId())
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const setProjectId = useCallback((id: number | null) => {
    setProjectIdState(id)
    setSelectedProjectId(id)
  }, [])

  const reload = useCallback(async () => {
    if (!getAccessToken()) {
      setProjects([])
      return
    }
    setIsLoading(true)
    try {
      const list = await listProjects({ limit: 500 })
      setProjects(list)
      // Drop a persisted selection that no longer exists.
      const stored = getSelectedProjectId()
      if (stored !== null && !list.some((p) => p.id === stored)) {
        setSelectedProjectId(null)
        setProjectIdState(null)
      }
    } catch {
      // Unauthenticated (401) or network error: keep the switcher empty.
      setProjects([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    // Re-run when the signed-in user changes (token is only in memory).
    void reload()
    const onStorage = () => void reload()
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [reload, userId])

  const value = useMemo(
    () => ({ projectId, setProjectId, projects, setProjects, reload, isLoading }),
    [projectId, setProjectId, projects, reload, isLoading],
  )

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>
}
