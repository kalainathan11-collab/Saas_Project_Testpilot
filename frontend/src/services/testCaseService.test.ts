import { describe, expect, it } from 'vitest'
import { cleanFilters, parseSteps } from './testCaseService'

describe('testCaseService helpers', () => {
  it('drops empty filters', () => {
    expect(cleanFilters({ project_id: null, q: '', type: 'API', priority: '' })).toEqual({ type: 'API' })
  })

  it('splits steps one per line', () => {
    expect(parseSteps('Open app\n\n  Click login \n')).toEqual(['Open app', 'Click login'])
  })
})
