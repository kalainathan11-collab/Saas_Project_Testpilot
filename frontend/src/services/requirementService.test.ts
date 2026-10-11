import { describe, expect, it } from 'vitest'
import { buildRequirementParams, requirementCode } from './requirementService'

describe('requirementService', () => {
  it('formats display ids', () => {
    expect(requirementCode(7)).toBe('REQ-7')
  })

  it('builds only the set filter params', () => {
    expect(buildRequirementParams({ project_id: 2, priority: '', status: 'Approved', q: '  login ' })).toEqual({
      project_id: 2,
      status: 'Approved',
      q: 'login',
    })
  })
})
