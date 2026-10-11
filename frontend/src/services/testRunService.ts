import api from './api'
import type { Project, ResultStatus, TestRunStatus } from '../types'

export interface TestRunSummary {
  id: number
  project_id: number
  name: string
  assignee: string | null
  status: TestRunStatus
  total_cases: number
  executed: number
  passed: number
  created_at: string
  updated_at: string
}

export interface CaseResult {
  status: ResultStatus
  comment: string | null
  executed_at: string | null
}

export interface RunCase {
  id: number
  title: string
  priority: string
  steps: string
  expected_result: string | null
  result: CaseResult | null
}

export interface TestRunDetail extends TestRunSummary {
  cases: RunCase[]
}

export interface TestRunInput {
  project_id: number
  name: string
  assignee: string | null
}

export interface TestRunFilters {
  project_id?: number | null
  status?: TestRunStatus | ''
  q?: string
}

export async function listTestRuns(filters: TestRunFilters = {}): Promise<TestRunSummary[]> {
  const params: Record<string, string | number> = { limit: 500 }
  if (filters.project_id) params.project_id = filters.project_id
  if (filters.status) params.status = filters.status
  if (filters.q) params.q = filters.q
  const { data } = await api.get<TestRunSummary[]>('/api/testruns', { params })
  return data
}

export async function getTestRun(id: number): Promise<TestRunDetail> {
  const { data } = await api.get<TestRunDetail>(`/api/testruns/${id}`)
  return data
}

export async function createTestRun(input: TestRunInput): Promise<TestRunSummary> {
  const { data } = await api.post<TestRunSummary>('/api/testruns', input)
  return data
}

export async function updateTestRun(id: number, input: TestRunInput): Promise<TestRunSummary> {
  const { data } = await api.put<TestRunSummary>(`/api/testruns/${id}`, input)
  return data
}

export async function deleteTestRun(id: number): Promise<void> {
  await api.delete(`/api/testruns/${id}`)
}

export async function recordResult(
  runId: number,
  caseId: number,
  status: ResultStatus,
  comment: string | null,
): Promise<TestRunDetail> {
  const { data } = await api.put<TestRunDetail>(`/api/testruns/${runId}/results/${caseId}`, {
    status,
    comment,
  })
  return data
}

export async function resetResults(runId: number): Promise<void> {
  await api.delete(`/api/testruns/${runId}/results`)
}

export async function listProjectsForSelect(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/api/projects', { params: { limit: 500 } })
  return data
}

export function apiErrorMessage(err: unknown, fallback = 'Something went wrong'): string {
  const e = err as {
    response?: { data?: { error?: { message?: string }; detail?: unknown } }
  }
  const data = e.response?.data
  if (data?.error?.message) return data.error.message
  if (Array.isArray(data?.detail)) {
    const first = data.detail[0] as { msg?: string } | undefined
    if (first?.msg) return first.msg
  }
  return fallback
}

export function progressPct(executed: number, total: number): number {
  return total > 0 ? Math.round((executed / total) * 100) : 0
}

export function countResults(cases: RunCase[]): Record<ResultStatus, number> {
  const counts: Record<ResultStatus, number> = { Passed: 0, Failed: 0, Blocked: 0, Skipped: 0 }
  for (const c of cases) {
    if (c.result) counts[c.result.status] += 1
  }
  return counts
}

export function buildDefectLink(
  run: Pick<TestRunSummary, 'id' | 'project_id' | 'name'>,
  c: Pick<RunCase, 'id' | 'title' | 'expected_result'>,
  comment: string | null,
): string {
  const description = [
    `Found during test run RUN-${run.id} (${run.name}).`,
    c.expected_result ? `Expected: ${c.expected_result}` : '',
    comment ? `Notes: ${comment}` : '',
  ]
    .filter(Boolean)
    .join('\n')
  const qs = new URLSearchParams({
    project_id: String(run.project_id),
    test_case_id: String(c.id),
    title: `Failed: ${c.title}`,
    description,
  })
  return `/defects/new?${qs.toString()}`
}
