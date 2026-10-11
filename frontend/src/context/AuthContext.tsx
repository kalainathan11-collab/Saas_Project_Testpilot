import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { User } from '../types'
import { clearTokens, getAccessToken } from '../lib/storage'
import * as authService from '../services/authService'
import { AUTH_EXPIRED_EVENT, refreshAccessToken } from '../services/api'
import { AuthContext } from './authContextValue'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  const refreshUser = useCallback(async (): Promise<User | null> => {
    if (!getAccessToken()) {
      setUser(null)
      return null
    }
    try {
      const current = await authService.me()
      setUser(current)
      return current
    } catch {
      setUser(null)
      return null
    }
  }, [])

  // Restore the session from the HttpOnly refresh cookie on app start.
  useEffect(() => {
    let active = true
    refreshAccessToken()
      .then(() => authService.me())
      .then((current) => {
        if (active) setUser(current)
      })
      .catch(() => {
        clearTokens()
        if (active) setUser(null)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  // api.ts emits this when a token refresh fails and the session is unrecoverable.
  useEffect(() => {
    const onExpired = () => setUser(null)
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setUser(await authService.login(email, password))
  }, [])

  const logout = useCallback(async () => {
    await authService.logout()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshUser, setUser }),
    [user, loading, login, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
