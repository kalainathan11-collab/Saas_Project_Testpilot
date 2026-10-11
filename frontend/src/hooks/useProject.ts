import { useContext } from 'react'
import { ProjectContext, type ProjectContextValue } from '../context/projectContextValue'

export function useProject(): ProjectContextValue {
  const ctx = useContext(ProjectContext)
  if (!ctx) {
    throw new Error('useProject must be used within a ProjectProvider')
  }
  return ctx
}
