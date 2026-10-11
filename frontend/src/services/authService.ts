import api from './api'
import type { TokenPair, User } from '../types'
import { clearTokens, setAccessToken } from '../lib/storage'

export interface RegisterPayload {
  email: string
  password: string
  full_name: string
}

export async function me(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}

export async function login(email: string, password: string): Promise<User> {
  const { data } = await api.post<TokenPair>('/auth/login', { email, password })
  setAccessToken(data.access_token)
  return me()
}

export async function register(payload: RegisterPayload): Promise<User> {
  const { data } = await api.post<User>('/auth/register', payload)
  return data
}

export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout')
  } catch {
    // Best effort: the local session is cleared regardless.
  } finally {
    clearTokens()
  }
}

export async function updateMe(fullName: string): Promise<User> {
  const { data } = await api.put<User>('/auth/me', { full_name: fullName })
  return data
}

export function googleLoginUrl(): string {
  const base = api.defaults.baseURL ?? ''
  return `${base.replace(/\/$/, '')}/auth/google`
}

/** Extract a human-readable message from an API error. */
export function errorMessage(err: unknown, fallback = 'Something went wrong. Please try again.'): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : ''))
      .filter(Boolean)
    if (msgs.length) return msgs.join('. ')
  }
  return fallback
}
