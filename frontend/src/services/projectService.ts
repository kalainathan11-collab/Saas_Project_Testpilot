import api from './api'
import type { Project, ProjectStatus } from '../types'

export interface ProjectSummary extends Project {
  owner?: string | null
}

export interface ProjectCounts {
  requirements: number
  test_cases: number
  test_runs: number
  defects: number
}

export interface ProjectDetail extends ProjectSummary {
  counts: ProjectCounts
}

export interface ProjectInput {
  name: string
  key: string
  description: string | null
  status: ProjectStatus
}

export interface ProjectListParams {
  q?: string
  status?: ProjectStatus | ''
  limit?: number
  offset?: number
}

export async function listProjects(params: ProjectListParams = {}): Promise<ProjectSummary[]> {
  const query: Record<string, string | number> = {}
  if (params.q) query.q = params.q
  if (params.status) query.status = params.status
  if (params.limit !== undefined) query.limit = params.limit
  if (params.offset !== undefined) query.offset = params.offset
  const { data } = await api.get<ProjectSummary[]>('/api/projects', { params: query })
  return data
}

export async function getProject(id: number): Promise<ProjectDetail> {
  const { data } = await api.get<ProjectDetail>(`/api/projects/${id}`)
  return data
}

export async function createProject(input: ProjectInput): Promise<ProjectSummary> {
  const { data } = await api.post<ProjectSummary>('/api/projects', input)
  return data
}

export async function updateProject(id: number, input: ProjectInput): Promise<ProjectSummary> {
  const { data } = await api.put<ProjectSummary>(`/api/projects/${id}`, input)
  return data
}

export async function deleteProject(id: number): Promise<void> {
  await api.delete(`/api/projects/${id}`)
}

/** Extract a human-readable message from an API error (contract error envelope or FastAPI 422). */
export function apiErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const data = (error as { response?: { data?: unknown } }).response?.data
    if (typeof data === 'object' && data !== null) {
      const body = data as { error?: { message?: unknown }; detail?: unknown }
      if (typeof body.error?.message === 'string') return body.error.message
      if (typeof body.detail === 'string') return body.detail
      if (Array.isArray(body.detail)) {
        const msgs = body.detail
          .map((d: unknown) =>
            typeof d === 'object' && d !== null && 'msg' in d ? String((d as { msg: unknown }).msg) : '',
          )
          .filter(Boolean)
        if (msgs.length) return msgs.join('; ')
      }
    }
  }
  return fallback
}
