import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import DefectFormPage from './DefectFormPage'

vi.mock('../services/defectService', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/defectService')>()
  return {
    ...actual,
    listProjectOptions: vi.fn().mockResolvedValue([]),
    listTestCaseOptions: vi.fn().mockResolvedValue([]),
  }
})

vi.mock('../hooks/useProject', () => ({
  useProject: () => ({ projectId: null, setProjectId: vi.fn(), projects: [], setProjects: vi.fn() }),
}))

describe('DefectFormPage', () => {
  it('prefills title and description from query params', () => {
    render(
      <MemoryRouter initialEntries={['/defects/new?title=Login%20fails&description=Steps&project_id=2']}>
        <Routes>
          <Route path="/defects/new" element={<DefectFormPage />} />
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByDisplayValue('Login fails')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Steps')).toBeInTheDocument()
  })
})
