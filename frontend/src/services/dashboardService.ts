import api from './api'
import type { Defect, ResultStatus, Severity } from '../types'

export interface DashboardRun {
  id: number
  name: string
  progress_pct: number
}

export interface DashboardSummary {
  test_cases: number
  test_runs: number
  executed: number
  pass_rate: number
  open_defects: number
  results: Record<ResultStatus, number>
  defects_by_severity: Record<Severity, number>
  runs: DashboardRun[]
  recent_defects: Defect[]
}

export interface ProjectReportRow {
  project_id: number
  project: string
  test_cases: number
  requirements: number
  coverage_pct: number
  runs: number
  executed: number
  pass_rate: number
  open_defects: number
  defects: number
}

export async function getDashboardSummary(projectId: number | null): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>('/api/dashboard/summary', {
    params: projectId !== null ? { project_id: projectId } : undefined,
  })
  return data
}

export async function getProjectReports(projectId: number | null): Promise<ProjectReportRow[]> {
  const { data } = await api.get<ProjectReportRow[]>('/api/reports/projects', {
    params: { format: 'json', ...(projectId !== null ? { project_id: projectId } : {}) },
  })
  return data
}

/** Downloads the CSV report as a Blob (auth header added by the api interceptor). */
export async function downloadReportCsv(projectId: number | null): Promise<Blob> {
  const { data } = await api.get<Blob>('/api/reports/projects', {
    params: { format: 'csv', ...(projectId !== null ? { project_id: projectId } : {}) },
    responseType: 'blob',
  })
  return data
}
