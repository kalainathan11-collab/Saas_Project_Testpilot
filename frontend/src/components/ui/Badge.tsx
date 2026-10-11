import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'
import type {
  DefectStatus,
  Priority,
  ProjectStatus,
  RequirementStatus,
  ResultStatus,
  Severity,
  TestCaseStatus,
  TestRunStatus,
} from '../../types'

export type BadgeTone = 'gray' | 'blue' | 'green' | 'yellow' | 'orange' | 'red' | 'purple'

const tones: Record<BadgeTone, string> = {
  gray: 'bg-slate-100 text-slate-700 ring-slate-200',
  blue: 'bg-blue-50 text-blue-700 ring-blue-200',
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  yellow: 'bg-amber-50 text-amber-700 ring-amber-200',
  orange: 'bg-orange-50 text-orange-700 ring-orange-200',
  red: 'bg-red-50 text-red-700 ring-red-200',
  purple: 'bg-purple-50 text-purple-700 ring-purple-200',
}

interface BadgeProps {
  tone?: BadgeTone
  children: ReactNode
  className?: string
}

export function Badge({ tone = 'gray', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}

type AnyStatus =
  | ProjectStatus
  | RequirementStatus
  | TestCaseStatus
  | TestRunStatus
  | ResultStatus
  | DefectStatus
  | Priority
  | Severity

const toneByValue: Record<AnyStatus, BadgeTone> = {
  // Project
  Active: 'green',
  'On Hold': 'yellow',
  Archived: 'gray',
  // Requirement
  Proposed: 'gray',
  Approved: 'blue',
  Implemented: 'purple',
  Verified: 'green',
  // Test case
  Draft: 'gray',
  Ready: 'green',
  Deprecated: 'red',
  // Test run
  Planned: 'gray',
  'In Progress': 'blue',
  Completed: 'green',
  // Result
  Passed: 'green',
  Failed: 'red',
  Blocked: 'orange',
  Skipped: 'gray',
  // Defect
  Open: 'red',
  Resolved: 'green',
  Closed: 'gray',
  // Priority
  Low: 'gray',
  Medium: 'blue',
  High: 'orange',
  Critical: 'red',
  // Severity
  Minor: 'gray',
  Major: 'orange',
  Blocker: 'red',
}

/** Badge whose colour is derived from a known status/priority/severity value. */
export function StatusBadge({ value }: { value: AnyStatus }) {
  return <Badge tone={toneByValue[value]}>{value}</Badge>
}
