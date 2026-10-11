/**
 * The access token lives only in this module-level variable (never in
 * localStorage/sessionStorage). The refresh token is an HttpOnly cookie that
 * JavaScript cannot see; the session is restored via POST /auth/refresh.
 */
let accessToken: string | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function clearTokens(): void {
  accessToken = null
}

/** Best-effort removal of token keys left behind by older versions. */
export function purgeLegacyTokens(): void {
  try {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  } catch {
    // storage unavailable
  }
}

purgeLegacyTokens()

export const SELECTED_PROJECT_KEY = 'selected_project_id'

export function getSelectedProjectId(): number | null {
  try {
    const raw = localStorage.getItem(SELECTED_PROJECT_KEY)
    if (raw === null) return null
    const n = Number(raw)
    return Number.isInteger(n) && n > 0 ? n : null
  } catch {
    return null
  }
}

export function setSelectedProjectId(id: number | null): void {
  try {
    if (id === null) localStorage.removeItem(SELECTED_PROJECT_KEY)
    else localStorage.setItem(SELECTED_PROJECT_KEY, String(id))
  } catch {
    // storage unavailable; selection just will not persist
  }
}
