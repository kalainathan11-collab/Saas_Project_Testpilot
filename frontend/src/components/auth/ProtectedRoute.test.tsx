import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { ProtectedRoute } from './ProtectedRoute'
import { AuthContext, type AuthContextValue } from '../../context/authContextValue'
import type { User } from '../../types'

const noop = async () => {}
function ctx(user: User | null, loading = false): AuthContextValue {
  return { user, loading, login: noop, logout: noop, refreshUser: async () => user, setUser: () => {} }
}

function renderAt(value: AuthContextValue) {
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={['/secret']}>
        <Routes>
          <Route path="/login" element={<div>login page</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/secret" element={<div>secret page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects anonymous users to /login', () => {
    renderAt(ctx(null))
    expect(screen.getByText('login page')).toBeInTheDocument()
  })

  it('renders children for signed-in users', () => {
    const user = { id: 1, email: 'a@b.c', full_name: 'A' } as User
    renderAt(ctx(user))
    expect(screen.getByText('secret page')).toBeInTheDocument()
  })
})
