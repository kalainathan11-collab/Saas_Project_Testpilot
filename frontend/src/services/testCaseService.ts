import { isAxiosError } from 'axios'
import api from './api'
import type {
  Priority,
  Project,
  Requirement,
  TestCase,
  TestCaseStatus,
  TestCaseType,
} from '../types'

export interface TestCaseFilters {
  project_id?: number | null
  requirement_id?: number | null
  type?: TestCaseType | ''
  priority?: Priority | ''
  status?: TestCaseStatus | ''
  q?: string
}

export interface TestCasePayload {
  project_id: number
  requirement_id: number | null
  title: string
  module: string | null
  type: TestCaseType
  priority: Priority
  status: TestCaseStatus
  preconditions: string | null
  steps: string
  expected_result: string | null
}

/** Drop empty filter values so they are not sent as query params. */
export function cleanFilters(filters: TestCaseFilters): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== '') {
      params[key] = value
    }
  }
  return params
}

export async function listTestCases(filters: TestCaseFilters = {}): Promise<TestCase[]> {
  const { data } = await api.get<TestCase[]>('/api/testcases', { params: cleanFilters(filters) })
  return data
}

export async function getTestCase(id: number): Promise<TestCase> {
  const { data } = await api.get<TestCase>(`/api/testcases/${id}`)
  return data
}

export async function createTestCase(payload: TestCasePayload): Promise<TestCase> {
  const { data } = await api.post<TestCase>('/api/testcases', payload)
  return data
}

export async function updateTestCase(id: number, payload: TestCasePayload): Promise<TestCase> {
  const { data } = await api.put<TestCase>(`/api/testcases/${id}`, payload)
  return data
}

export async function deleteTestCase(id: number): Promise<void> {
  await api.delete(`/api/testcases/${id}`)
}

/** Downloads the filtered list as CSV (auth header is added by the api client). */
export async function exportTestCasesCsv(filters: TestCaseFilters = {}): Promise<void> {
  const { data } = await api.get<Blob>('/api/testcases/export', {
    params: cleanFilters(filters),
    responseType: 'blob',
  })
  const url = URL.createObjectURL(new Blob([data], { type: 'text/csv' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'test-cases.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function listProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/api/projects')
  return data
}

export async function listRequirements(projectId?: number | null): Promise<Requirement[]> {
  const { data } = await api.get<Requirement[]>('/api/requirements', {
    params: projectId ? { project_id: projectId } : {},
  })
  return data
}

export async function getRequirement(id: number): Promise<Requirement> {
  const { data } = await api.get<Requirement>(`/api/requirements/${id}`)
  return data
}

/** Splits the newline-separated steps string into trimmed, non-empty steps. */
export function parseSteps(steps: string): string[] {
  return steps
    .split('\n')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
}

interface ValidationDetail {
  loc?: unknown[]
  msg?: string
}

/** Extracts a human-readable message from an API/validation error. */
export function apiErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (isAxiosError(error)) {
    const data: unknown = error.response?.data
    if (data && typeof data === 'object') {
      const record = data as { error?: { message?: string }; detail?: unknown }
      if (record.error?.message) return record.error.message
      if (typeof record.detail === 'string') return record.detail
      if (Array.isArray(record.detail)) {
        return (record.detail as ValidationDetail[])
          .map((d) => [d.loc?.slice(1).join('.'), d.msg].filter(Boolean).join(': '))
          .join('; ')
      }
    }
  }
  return fallback
}
