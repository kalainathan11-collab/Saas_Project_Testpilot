import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import type { TokenPair } from '../types'
import { clearTokens, getAccessToken, setAccessToken } from '../lib/storage'

const baseURL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/** Dispatched on window when the session cannot be refreshed any more. */
export const AUTH_EXPIRED_EVENT = 'auth:expired'

/** Auth endpoints that must never trigger a refresh-and-retry (/auth/me is NOT one of them). */
const NO_REFRESH_PATHS = new Set([
  '/auth/login',
  '/auth/register',
  '/auth/refresh',
  '/auth/logout',
  '/auth/google',
])

function isNoRefreshPath(url: string | undefined): boolean {
  if (!url) return false
  let path = url.split(/[?#]/)[0] ?? ''
  if (/^https?:\/\//i.test(path)) {
    try {
      path = new URL(path).pathname
    } catch {
      // keep as-is
    }
  }
  if (!path.startsWith('/')) path = `/${path}`
  return NO_REFRESH_PATHS.has(path.replace(/\/+$/, ''))
}

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

const api: AxiosInstance = axios.create({
  baseURL,
  withCredentials: true,
  headers: { 'X-Requested-With': 'TestPilot' },
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Share a single in-flight refresh between concurrent callers.
let refreshPromise: Promise<string> | null = null

/**
 * Obtain a new access token using the HttpOnly refresh cookie. Concurrent
 * callers share one request. Stores the token in memory and returns it.
 */
export function refreshAccessToken(): Promise<string> {
  refreshPromise ??= (async () => {
    // Bare axios call so this request is not intercepted again.
    const { data } = await axios.post<TokenPair>(`${baseURL}/auth/refresh`, undefined, {
      withCredentials: true,
      headers: { 'X-Requested-With': 'TestPilot' },
    })
    setAccessToken(data.access_token)
    return data.access_token
  })().finally(() => {
    refreshPromise = null
  })
  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    const isAuthCall = isNoRefreshPath(original?.url)

    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true
      try {
        const token = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      } catch (refreshError) {
        clearTokens()
        window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  },
)

export default api
