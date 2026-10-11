import { isAxiosError } from 'axios'
import api from './api'
import type { Priority, Project, Requirement, RequirementStatus, TestCaseStatus } from '../types'

export interface RequirementListItem extends Requirement {
  test_case_count: number
}

export interface LinkedTestCase {
  id: number
  title: string
  status: TestCaseStatus
}

export interface RequirementDetail extends RequirementListItem {
  test_cases: LinkedTestCase[]
}

export interface RequirementFilters {
  project_id?: number | null
  priority?: Priority | ''
  status?: RequirementStatus | ''
  q?: string
}

export interface RequirementInput {
  project_id: number
  title: string
  description: string | null
  priority: Priority
  status: RequirementStatus
}

export function requirementCode(id: number): string {
  return `REQ-${id}`
}

export function buildRequirementParams(filters: RequirementFilters): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.project_id != null) params.project_id = filters.project_id
  if (filters.priority) params.priority = filters.priority
  if (filters.status) params.status = filters.status
  const q = filters.q?.trim()
  if (q) params.q = q
  return params
}

export async function listRequirements(filters: RequirementFilters = {}): Promise<RequirementListItem[]> {
  const { data } = await api.get<RequirementListItem[]>('/api/requirements', {
    params: buildRequirementParams(filters),
  })
  return data
}

export async function getRequirement(id: number): Promise<RequirementDetail> {
  const { data } = await api.get<RequirementDetail>(`/api/requirements/${id}`)
  return data
}

export async function createRequirement(input: RequirementInput): Promise<Requirement> {
  const { data } = await api.post<Requirement>('/api/requirements', input)
  return data
}

export async function updateRequirement(id: number, input: RequirementInput): Promise<Requirement> {
  const { data } = await api.put<Requirement>(`/api/requirements/${id}`, input)
  return data
}

export async function deleteRequirement(id: number): Promise<void> {
  await api.delete(`/api/requirements/${id}`)
}

export async function listProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/api/projects')
  return data
}

interface ValidationDetail {
  loc?: unknown[]
  msg?: string
}

/** Extracts a human readable message from API error payloads (custom or FastAPI 422). */
export function getErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (isAxiosError(error)) {
    const body: unknown = error.response?.data
    if (body && typeof body === 'object') {
      const record = body as { error?: { message?: string }; detail?: unknown }
      if (record.error?.message) return record.error.message
      if (typeof record.detail === 'string') return record.detail
      if (Array.isArray(record.detail)) {
        return (record.detail as ValidationDetail[])
          .map((d) => `${String(d.loc?.[d.loc.length - 1] ?? '')}: ${d.msg ?? ''}`)
          .join('; ')
      }
    }
  }
  return fallback
}
