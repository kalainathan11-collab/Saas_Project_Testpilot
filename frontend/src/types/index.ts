// Types mirror the DATABASE MODELS section of PRPs/testpilot-prp.md.

export const PROJECT_STATUSES = ['Active', 'On Hold', 'Archived'] as const
export type ProjectStatus = (typeof PROJECT_STATUSES)[number]

export const PRIORITIES = ['Low', 'Medium', 'High', 'Critical'] as const
export type Priority = (typeof PRIORITIES)[number]

export const REQUIREMENT_STATUSES = ['Proposed', 'Approved', 'Implemented', 'Verified'] as const
export type RequirementStatus = (typeof REQUIREMENT_STATUSES)[number]

export const TEST_CASE_TYPES = [
  'Functional',
  'Regression',
  'Smoke',
  'API',
  'UI',
  'Performance',
  'Security',
] as const
export type TestCaseType = (typeof TEST_CASE_TYPES)[number]

export const TEST_CASE_STATUSES = ['Draft', 'Ready', 'Deprecated'] as const
export type TestCaseStatus = (typeof TEST_CASE_STATUSES)[number]

export const TEST_RUN_STATUSES = ['Planned', 'In Progress', 'Completed'] as const
export type TestRunStatus = (typeof TEST_RUN_STATUSES)[number]

export const RESULT_STATUSES = ['Passed', 'Failed', 'Blocked', 'Skipped'] as const
export type ResultStatus = (typeof RESULT_STATUSES)[number]

export const SEVERITIES = ['Minor', 'Major', 'Critical', 'Blocker'] as const
export type Severity = (typeof SEVERITIES)[number]

export const DEFECT_STATUSES = ['Open', 'In Progress', 'Resolved', 'Closed'] as const
export type DefectStatus = (typeof DEFECT_STATUSES)[number]

/** ISO-8601 timestamp string as returned by the API. */
export type ISODateString = string

export interface BaseEntity {
  id: number
  created_at: ISODateString
  updated_at: ISODateString
}

export interface User extends BaseEntity {
  email: string
  full_name: string | null
  is_active: boolean
  is_verified: boolean
  oauth_provider: string | null
}

export interface Project extends BaseEntity {
  user_id: number
  name: string
  key: string
  description: string | null
  status: ProjectStatus
}

export interface Requirement extends BaseEntity {
  user_id: number
  project_id: number
  title: string
  description: string | null
  priority: Priority
  status: RequirementStatus
}

export interface TestCase extends BaseEntity {
  user_id: number
  project_id: number
  requirement_id: number | null
  title: string
  module: string | null
  type: TestCaseType
  priority: Priority
  status: TestCaseStatus
  preconditions: string | null
  /** One step per line. */
  steps: string
  expected_result: string | null
}

export interface TestRun extends BaseEntity {
  user_id: number
  project_id: number
  name: string
  assignee: string | null
  status: TestRunStatus
}

export interface TestResult extends BaseEntity {
  user_id: number
  test_run_id: number
  test_case_id: number
  status: ResultStatus
  comment: string | null
  executed_at: ISODateString | null
}

export interface Defect extends BaseEntity {
  user_id: number
  project_id: number
  test_case_id: number | null
  title: string
  description: string | null
  severity: Severity
  status: DefectStatus
  assignee: string | null
}

export interface TokenPair {
  access_token: string
  token_type: string
}
