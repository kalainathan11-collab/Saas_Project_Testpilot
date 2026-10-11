import { isAxiosError } from 'axios'
import api from './api'
import type { Defect, DefectStatus, Project, Severity, TestCase } from '../types'

export interface DefectFilters {
  project_id?: number | null
  severity?: Severity | ''
  status?: DefectStatus | ''
  q?: string
}

export interface DefectInput {
  project_id: number
  test_case_id: number | null
  title: string
  description: string | null
  severity: Severity
  status: DefectStatus
  assignee: string | null
}

function toParams(filters: DefectFilters): Record<string, string | number> {
  const params: Record<string, string | number> = { limit: 500 }
  if (filters.project_id) params.project_id = filters.project_id
  if (filters.severity) params.severity = filters.severity
  if (filters.status) params.status = filters.status
  if (filters.q?.trim()) params.q = filters.q.trim()
  return params
}

export async function listDefects(filters: DefectFilters = {}): Promise<Defect[]> {
  const { data } = await api.get<Defect[]>('/api/defects', { params: toParams(filters) })
  return data
}

export async function getDefect(id: number): Promise<Defect> {
  const { data } = await api.get<Defect>(`/api/defects/${id}`)
  return data
}

export async function createDefect(input: DefectInput): Promise<Defect> {
  const { data } = await api.post<Defect>('/api/defects', input)
  return data
}

export async function updateDefect(id: number, input: DefectInput): Promise<Defect> {
  const { data } = await api.put<Defect>(`/api/defects/${id}`, input)
  return data
}

export async function deleteDefect(id: number): Promise<void> {
  await api.delete(`/api/defects/${id}`)
}

export async function listProjectOptions(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/api/projects', { params: { limit: 500 } })
  return data
}

export async function listTestCaseOptions(projectId?: number | null): Promise<TestCase[]> {
  const params: Record<string, number> = { limit: 500 }
  if (projectId) params.project_id = projectId
  const { data } = await api.get<TestCase[]>('/api/testcases', { params })
  return data
}

export async function getTestCase(id: number): Promise<TestCase> {
  const { data } = await api.get<TestCase>(`/api/testcases/${id}`)
  return data
}

export function defectDisplayId(id: number): string {
  return `BUG-${id}`
}

/** Extract a human-readable message from an API error. */
export function errorMessage(err: unknown, fallback = 'Something went wrong'): string {
  if (isAxiosError(err)) {
    const body = err.response?.data as
      | { error?: { message?: string }; detail?: string | { msg?: string }[] }
      | undefined
    if (body?.error?.message) return body.error.message
    if (typeof body?.detail === 'string') return body.detail
    if (Array.isArray(body?.detail)) {
      return (
        body.detail
          .map((d) => d.msg ?? '')
          .filter(Boolean)
          .join('; ') || fallback
      )
    }
  }
  return fallback
}
