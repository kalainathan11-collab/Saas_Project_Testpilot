import { describe, expect, it } from 'vitest'
import { buildDefectLink, countResults, progressPct, type RunCase } from './testRunService'

const mk = (id: number, status: 'Passed' | 'Failed' | null): RunCase => ({
  id,
  title: `Case ${id}`,
  priority: 'High',
  steps: 'a\nb',
  expected_result: 'ok',
  result: status ? { status, comment: null, executed_at: null } : null,
})

describe('test run helpers', () => {
  it('counts results and progress', () => {
    const counts = countResults([mk(1, 'Passed'), mk(2, 'Failed'), mk(3, null)])
    expect(counts.Passed).toBe(1)
    expect(counts.Failed).toBe(1)
    expect(progressPct(2, 3)).toBe(67)
    expect(progressPct(0, 0)).toBe(0)
  })

  it('builds a defect link with prefilled params', () => {
    const link = buildDefectLink({ id: 4, project_id: 2, name: 'Smoke' }, mk(9, 'Failed'), 'boom')
    const url = new URL(link, 'http://x')
    expect(url.pathname).toBe('/defects/new')
    expect(url.searchParams.get('project_id')).toBe('2')
    expect(url.searchParams.get('test_case_id')).toBe('9')
    expect(url.searchParams.get('title')).toContain('Case 9')
  })
})
