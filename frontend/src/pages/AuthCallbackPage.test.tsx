import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import axios from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import AuthCallbackPage from './AuthCallbackPage'
import { AuthContext, type AuthContextValue } from '../context/authContextValue'
import { clearTokens, getAccessToken } from '../lib/storage'
import type { User } from '../types'

function renderPage(refreshUser: AuthContextValue['refreshUser']) {
  const value: AuthContextValue = {
    user: null,
    loading: false,
    login: async () => {},
    logout: async () => {},
    refreshUser,
    setUser: () => {},
  }
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={['/auth/callback']}>
        <Routes>
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="/dashboard" element={<div>dashboard page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('AuthCallbackPage', () => {
  beforeEach(() => {
    localStorage.clear()
    clearTokens()
    window.history.replaceState(null, '', '/auth/callback')
  })
  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
    clearTokens()
  })

  it('calls /auth/refresh, loads the user and goes to the dashboard', async () => {
    const post = vi
      .spyOn(axios, 'post')
      .mockResolvedValue({ data: { access_token: 'AAA', token_type: 'bearer' } })
    const user = { id: 1, email: 'a@b.c' } as User
    renderPage(vi.fn(async () => user))

    expect(await screen.findByText('dashboard page')).toBeInTheDocument()
    expect(String(post.mock.calls[0][0])).toMatch(/\/auth\/refresh$/)
    expect(getAccessToken()).toBe('AAA')
    expect(localStorage.length).toBe(0)
  })

  it('ignores tokens in the URL and never stores them', async () => {
    window.history.replaceState(null, '', '/auth/callback?access_token=URL#access_token=URL2')
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('401'))
    renderPage(vi.fn(async () => null))

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(getAccessToken()).toBeNull()
    expect(localStorage.length).toBe(0)
    expect(window.location.search).toBe('')
    expect(window.location.hash).toBe('')
  })

  it('shows an error with a login link when refresh fails', async () => {
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('401'))
    renderPage(vi.fn(async () => null))

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByRole('link', { name: /back to sign in/i })).toHaveAttribute('href', '/login')
  })

  it('shows an error when the user cannot be loaded', async () => {
    vi.spyOn(axios, 'post').mockResolvedValue({ data: { access_token: 'AAA', token_type: 'bearer' } })
    renderPage(vi.fn(async () => null))

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})
