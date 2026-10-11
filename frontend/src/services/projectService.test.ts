import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('./api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))

import api from './api'
import { apiErrorMessage, listProjects } from './projectService'

describe('projectService', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset()
  })

  it('passes only set filters to GET /api/projects', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    await listProjects({ q: 'web', status: '' })
    expect(api.get).toHaveBeenCalledWith('/api/projects', { params: { q: 'web' } })
  })

  it('extracts contract error messages', () => {
    const err = { response: { data: { error: { code: 'conflict', message: 'Key exists' } } } }
    expect(apiErrorMessage(err)).toBe('Key exists')
    expect(apiErrorMessage(new Error('x'), 'fallback')).toBe('fallback')
  })
})
